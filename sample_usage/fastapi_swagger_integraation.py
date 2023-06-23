# -*- coding: utf-8 -*-
import json
from pathlib import Path
from typing import Any, Dict, Optional

import starlette_werkzeug_debugger
from fastapi import FastAPI
from fastapi.encoders import jsonable_encoder
from fastapi.staticfiles import StaticFiles
from starlette.responses import HTMLResponse


app = FastAPI(docs_url=None)


app.add_middleware(starlette_werkzeug_debugger.WerkzeugDebugMiddleware, evalex=True)
app.mount('/static/', StaticFiles(directory=Path(__file__).parent / 'static'), name="static")


swagger_ui_default_parameters = {
	"dom_id": "#swagger-ui",
	"layout": "BaseLayout",
	"deepLinking": True,
	"showExtensions": True,
	"showCommonExtensions": True,
}


def get_swagger_ui_html(
	*,
	openapi_url: str,
	title: str,
	swagger_js_url: str = "https://cdn.jsdelivr.net/npm/swagger-ui-dist@4/swagger-ui-bundle.js",
	swagger_css_url: str = "https://cdn.jsdelivr.net/npm/swagger-ui-dist@4/swagger-ui.css",
	swagger_favicon_url: str = "https://fastapi.tiangolo.com/img/favicon.png",
	oauth2_redirect_url: Optional[str] = None,
	init_oauth: Optional[Dict[str, Any]] = None,
	swagger_ui_parameters: Optional[Dict[str, Any]] = None,
) -> HTMLResponse:
	current_swagger_ui_parameters = swagger_ui_default_parameters.copy()
	if swagger_ui_parameters:
		current_swagger_ui_parameters.update(swagger_ui_parameters)

	swagger_js_extra_url = "/static/swagger_extra.js"
	swagger_css_extra_url = "/static/swagger_extra.css"

	html = f"""
	<!DOCTYPE html>
	<html>
	<head>
	<link type="text/css" rel="stylesheet" href="{swagger_css_url}">
	<link type="text/css" rel="stylesheet" href="{swagger_css_extra_url}">
	<link rel="shortcut icon" href="{swagger_favicon_url}">
	<title>{title}</title>
	</head>
	<body>
	<div id="swagger-ui">
	</div>
	<script src="{swagger_js_url}"></script>
	<script src="{swagger_js_extra_url}"></script>
	<!-- `SwaggerUIBundle` is now available on the page -->
	<script>
	const ui = SwaggerUIBundle({{
		url: '{openapi_url}',
		responseInterceptor: window.responseInterceptor,
	"""

	for key, value in current_swagger_ui_parameters.items():
		html += f"{json.dumps(key)}: {json.dumps(jsonable_encoder(value))},\n"

	if oauth2_redirect_url:
		html += f"oauth2RedirectUrl: window.location.origin + '{oauth2_redirect_url}',"

	html += """
	presets: [
		SwaggerUIBundle.presets.apis,
		SwaggerUIBundle.SwaggerUIStandalonePreset
		],
	})"""

	if init_oauth:
		html += f"""
		ui.initOAuth({json.dumps(jsonable_encoder(init_oauth))})
		"""

	html += """
	</script>
	</body>
	</html>
	"""
	return HTMLResponse(html)


@app.get("/docs", include_in_schema=False)
async def custom_swagger_ui_html():
	return get_swagger_ui_html(
		openapi_url=app.openapi_url,
		title=app.title + " - Swagger UI",
	)


@app.get("/")
async def raise_error():
	local_var = 3
	raise RuntimeError("Raised error")
