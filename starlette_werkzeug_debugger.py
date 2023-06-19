# -*- coding: utf-8 -*-
import time
import typing as t
from io import BytesIO

from starlette.middleware.base import BaseHTTPMiddleware, DispatchFunction
from starlette.requests import Request
from starlette.responses import Response
from starlette.types import ASGIApp
from werkzeug.debug import DebugTraceback, DebuggedApplication, hash_pin, PIN_TIME
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

	def check_pin_trust(self, environ: dict) -> bool | None:
		"""Checks if the request passed the pin test.  This returns `True` if the
		request is trusted on a pin/cookie basis and returns `False` if not.
		Additionally if the cookie's stored pin hash is wrong it will return
		`None` so that appropriate action can be taken.
		"""
		if self.pin is None:
			return True
		request = environ['request']
		val = request.cookies.get(self.pin_cookie_name)
		if not val or "|" not in val:
			return False
		ts_str, pin_hash = val.split("|", 1)

		try:
			ts = int(ts_str)
		except ValueError:
			return False

		if pin_hash != hash_pin(self.pin):
			return None
		return (time.time() - PIN_TIME) < ts

	async def debug_application(self, request: Request, call_next) -> Response:
		contexts: list[t.ContextManager[t.Any]] = []

		try:
			response = await call_next(request)
		except Exception as e:
			tb = DebugTraceback(e, skip=1, hide=not self.show_hidden_frames)

			for frame in tb.all_frames:
				self.frames[id(frame)] = frame
				self.frame_contexts[id(frame)] = contexts

			is_trusted = bool(self.check_pin_trust({'request': request}))
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
			request.environ = {
				'REQUEST_METHOD': request.method,
				'request': request,
			}
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
				and self.check_pin_trust({'request': request})
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
