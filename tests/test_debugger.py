# -*- coding: utf-8 -*-
import json
import logging
import re

import starlette_werkzeug_debugger
from starlette.applications import Starlette
from starlette.middleware import Middleware
from starlette.responses import JSONResponse
from starlette.routing import Route
from starlette.testclient import TestClient


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


def get_middleware(app):
	return app.middleware_stack.app


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


def test_printpin(caplog):
	caplog.set_level(logging.INFO)

	app = build_app(evalex=True, pin_security=True, pin_logging=True)
	client = TestClient(app)
	client.get('/')
	middleware = get_middleware(app)
	middleware.pin = '4852'

	# dont' print anything
	response = client.get('/', params={'__debugger__': 'yes', 'cmd': 'printpin', 's': middleware.secret + 'x'})
	assert middleware.pin not in caplog.text
	response = client.get('/', params={'__debugger__': 'yes', 'cmd': 'printpin', 's': middleware.secret})
	assert middleware.pin in caplog.text


def test_pinauth():
	app = build_app(evalex=True, pin_security=True, pin_logging=True)
	client = TestClient(app)
	client.get('/')
	middleware = get_middleware(app)
	middleware.pin = '4852'

	# wrong secret
	response = client.get('/', params={'__debugger__': 'yes', 'cmd': 'pinauth', 'pin': middleware.pin, 's': middleware.secret + 'x'})
	assert response.status_code == 500

	# wrong pin
	response = client.get('/', params={'__debugger__': 'yes', 'cmd': 'pinauth', 'pin': middleware.pin + '5', 's': middleware.secret})
	assert response.status_code == 200
	response_content = json.loads(response.content.decode('utf-8'))
	assert not response_content['auth']

	# correct pin
	response = client.get('/', params={'__debugger__': 'yes', 'cmd': 'pinauth', 'pin': middleware.pin, 's': middleware.secret})
	assert response.status_code == 200
	response_content = json.loads(response.content.decode('utf-8'))
	assert response_content['auth']
	assert middleware.pin_cookie_name in response.cookies


def test_console():
	app = build_app(evalex=True, pin_security=True, pin_logging=True)
	client = TestClient(app)
	exception_content = client.get('/').content.decode('utf-8')
	middleware = get_middleware(app)
	middleware.pin = '4852'

	# login
	response = client.get('/', params={'__debugger__': 'yes', 'cmd': 'pinauth', 'pin': middleware.pin, 's': middleware.secret})
	cookies = response.cookies

	frame_ids = re.findall(r'(?:frame-(\d+))', exception_content)

	# content from inner variable
	response = client.get('/', params={'__debugger__': 'yes', 'cmd': 'local_var', 'frm': frame_ids[-1], 's': middleware.secret})
	assert b'inner' in response.content

	# content from outer variable
	response = client.get('/', params={'__debugger__': 'yes', 'cmd': 'local_var', 'frm': frame_ids[-2], 's': middleware.secret})
	assert b'outer' in response.content
