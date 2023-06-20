==========================================
Werkzeug debugger middleware for Starlette
==========================================

|codecov| |version| |downloads| |license|

This package contains interactive debuger middleware for Starlette / FastAPI.

Install
-------

.. code:: bash

	pip install starlette_werkzeug_debugger

Usage with Starlette
--------------------

.. code:: python

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


Usage with FastAPI
------------------

.. code:: python

	from fastapi import FastAPI
	import starlette_werkzeug_debugger


	app = FastAPI()


	app.add_middleware(starlette_werkzeug_debugger.WerkzeugDebugMiddleware, evalex=True)


	@app.get("/")
	async def raise_error():
		local_var = 3
		raise RuntimeError("Raised error")


Screenshots
-----------

.. image:: https://raw.github.com/wiki/mireq/starlette-werkzeug-debugger/debugger.png?v=2023-06-20


.. |codecov| image:: https://codecov.io/gh/mireq/starlette-werkzeug-debugger/branch/master/graph/badge.svg?token=QGY5B5X0F3
	:target: https://codecov.io/gh/mireq/starlette-werkzeug-debugger

.. |version| image:: https://badge.fury.io/py/starlette-werkzeug-debugger.svg
	:target: https://pypi.python.org/pypi/starlette-werkzeug-debugger/

.. |downloads| image:: https://img.shields.io/pypi/dw/starlette-werkzeug-debugger.svg
	:target: https://pypi.python.org/pypi/starlette-werkzeug-debugger/

.. |license| image:: https://img.shields.io/pypi/l/starlette-werkzeug-debugger.svg
	:target: https://pypi.python.org/pypi/starlette-werkzeug-debugger/
