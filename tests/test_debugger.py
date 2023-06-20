# -*- coding: utf-8 -*-
from starlette.applications import Starlette
from starlette.middleware import Middleware
from starlette.responses import JSONResponse
from starlette.routing import Route
from starlette.testclient import TestClient
import starlette_werkzeug_debugger


def inner_error():
	local_var = 'inner'
	raise RuntimeError("Raised error")


async def raise_error(request):
	local_var = 'outer'
	inner_error()


async def ok_response(request):
	return JSONResponse("ok")



def build_app(**kwargs):
	middleware = [
		Middleware(starlette_werkzeug_debugger.WerkzeugDebugMiddleware, **kwargs)
	]

	return Starlette(debug=True, middleware=middleware, routes=[
		Route('/', raise_error),
		Route('/ok/', ok_response),
	])


def test_correct_response():
	app = build_app()
	client = TestClient(app)
	response = client.get('/ok/')
	assert response.status_code == 200
	assert response.content == b'"ok"'


def test_error_response():
	app = build_app()
	client = TestClient(app)
	response = client.get('/')
	assert response.status_code == 500
	assert b"Werkzeug Debugger" in response.content


def test_serve_static():
	app = build_app()
	client = TestClient(app)
	client.get('/')
	response = client.get('/', params={'__debugger__': 'yes', 'cmd': 'resource', 'f': 'style.css'})
	assert response.status_code == 200
	assert response.headers['content-type'].startswith('text/css')
