# -*- coding: utf-8 -*-
from starlette.applications import Starlette
from starlette.middleware import Middleware
from starlette.responses import JSONResponse
from starlette.routing import Route
from starlette.testclient import TestClient
import starlette_werkzeug_debugger


async def raise_error(request):
	local_var = 3
	raise RuntimeError("Raised error")


async def ok_response(request):
	return JSONResponse("ok")


middleware = [
	Middleware(starlette_werkzeug_debugger.WerkzeugDebugMiddleware, evalex=True)
]


app = Starlette(debug=True, middleware=middleware, routes=[
	Route('/', raise_error),
	Route('/ok/', ok_response),
])


def test_correct_response():
	client = TestClient(app)
	response = client.get('/ok/')
	assert response.status_code == 200
	assert response.content == b'"ok"'


def test_error_response():
	client = TestClient(app)
	response = client.get('/')
	assert response.status_code == 500
	assert b"Werkzeug Debugger" in response.content
