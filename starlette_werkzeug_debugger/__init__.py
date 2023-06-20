# -*- coding: utf-8 -*-
import typing as t
from io import BytesIO

from starlette.middleware.base import BaseHTTPMiddleware, DispatchFunction
from starlette.requests import Request
from starlette.responses import Response
from starlette.types import ASGIApp
from werkzeug.debug import DebugTraceback, DebuggedApplication
from werkzeug.wrappers import Response as WerkzeugResponse


class WerkzeugDebugMiddleware(DebuggedApplication):
	def __init__(
		self, app: ASGIApp,
		dispatch: t.Optional[DispatchFunction] = None,
		**kwargs
	):
		super().__init__(None, **kwargs)
		self.app = app
		self.dispatch_func = self.dispatch if dispatch is None else dispatch

	def get_wsgi_environ(self, request: Request) -> dict:
		return {
			'REQUEST_METHOD': request.method,
			'HTTP_COOKIE': request.headers.get('cookie'),
			'request': request,
		}

	async def debug_application(self, request: Request, call_next) -> Response:
		contexts: list[t.ContextManager[t.Any]] = []

		try:
			response = await call_next(request)
		except Exception as e:
			tb = DebugTraceback(e, skip=1, hide=not self.show_hidden_frames)

			for frame in tb.all_frames:
				self.frames[id(frame)] = frame
				self.frame_contexts[id(frame)] = contexts

			is_trusted = bool(self.check_pin_trust(self.get_wsgi_environ(request)))
			html = tb.render_debugger_html(
				evalex=self.evalex,
				secret=self.secret,
				evalex_trusted=is_trusted,
			)
			response = Response(html, status_code=500, media_type="text/html")
			return response
		return response

	async def dispatch(self, request: Request, call_next) -> Response:
		response = self.debug_application

		if request.query_params.get("__debugger__") == "yes":
			# emulate werkzeug Request
			request.environ = self.get_wsgi_environ(request)
			request.args = request.query_params
			request.is_secure = False

			cmd = request.query_params.get("cmd")
			arg = request.query_params.get("f")
			secret = request.query_params.get("s")
			frm = request.query_params.get("frm")
			if frm is not None:
				frm = int(frm)
			frame = self.frames.get(frm)  # type: ignore
			if cmd == "resource" and arg:
				response = self.get_resource(request, arg)  # type: ignore
			elif cmd == "pinauth" and secret == self.secret:
				response = self.pin_auth(request)  # type: ignore
			elif cmd == "printpin" and secret == self.secret:
				response = self.log_pin_request()  # type: ignore
			elif (
				self.evalex
				and cmd is not None
				and frame is not None
				and self.secret == secret
				and self.check_pin_trust(self.get_wsgi_environ(request))
			):
				response = self.execute_command(request, cmd, frame)  # type: ignore

		if isinstance(response, WerkzeugResponse):
			data = BytesIO()
			for chunk in response.get_app_iter(request.environ):
				data.write(chunk)
			return Response(
				data.getvalue(),
				status_code=response.status_code,
				media_type=response.mimetype,
				headers=response.headers,
			)

		return await response(request, call_next)


WerkzeugDebugMiddleware.__call__ = BaseHTTPMiddleware.__call__
