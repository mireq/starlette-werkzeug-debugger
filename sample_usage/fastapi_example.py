# -*- coding: utf-8 -*-
from fastapi import FastAPI
import starlette_werkzeug_debugger


app = FastAPI()


app.add_middleware(starlette_werkzeug_debugger.WerkzeugDebugMiddleware, evalex=True)


@app.get("/")
async def raise_error():
	local_var = 3
	raise RuntimeError("Raised error")
