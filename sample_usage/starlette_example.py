# -*- coding: utf-8 -*-
from starlette.applications import Starlette
from starlette.middleware import Middleware
from starlette.routing import Route
import starlette_werkzeug_debugger


async def raise_error(request):
	local_var = 3
	raise RuntimeError("Raised error")


middleware = [
	Middleware(starlette_werkzeug_debugger.WerkzeugDebugMiddleware, evalex=True)
]


app = Starlette(debug=True, middleware=middleware, routes=[
	Route('/', raise_error),
])
