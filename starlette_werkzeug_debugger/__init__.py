# -*- coding: utf-8 -*-
import re
import typing as t
from io import BytesIO

from starlette.requests import Request
from starlette.responses import Response
from starlette.types import ASGIApp, Receive, Scope, Send
from werkzeug.debug import DebugTraceback, DebuggedApplication
from werkzeug.wrappers import Response as WerkzeugResponse


class WerkzeugDebugMiddleware(DebuggedApplication):
	DEBUGGER_REQUEST_RX = re.compile(r'^(?:.*&)?__debugger__=yes(?:&.*)?$')

	def __init__(
		self, app: ASGIApp,
		**kwargs
	):
		super().__init__(None, **kwargs)
		self.app = app

	def get_wsgi_environ(self, request: Request) -> dict:
		return {
			'REQUEST_METHOD': request.method,
			'HTTP_COOKIE': request.headers.get('cookie'),
			'request': request,
		}

	async def debugger_response(self, scope: Scope, receive: Receive, send: Send) -> bool:
		request = Request(scope, receive, send)
		response = None

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
			response = Response(
				data.getvalue(),
				status_code=response.status_code,
				media_type=response.mimetype,
				headers=response.headers,
			)

		if response is not None:
			await response(scope, receive, send)
			return True
		return False

	async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
		if scope["type"] != 'http':
			await self.app(scope, receive, send)
			return

		query = scope['query_string'].decode('utf-8')
		if self.DEBUGGER_REQUEST_RX.match(query):
			if await self.debugger_response(scope, receive, send):
				return

		try:
			await self.app(scope, receive, send)
		except Exception as e:
			contexts: list[t.ContextManager[t.Any]] = []

			tb = DebugTraceback(e, skip=1, hide=not self.show_hidden_frames)

			for frame in tb.all_frames:
				self.frames[id(frame)] = frame
				self.frame_contexts[id(frame)] = contexts

			request = Request(scope, receive, send)
			is_trusted = bool(self.check_pin_trust(self.get_wsgi_environ(request)))
			html = tb.render_debugger_html(
				evalex=self.evalex,
				secret=self.secret,
				evalex_trusted=is_trusted,
			)
			response = Response(html, status_code=500, media_type="text/html")

			await response(scope, receive, send)
