"""
Docs hub service — dev only.

Serves a single Swagger UI page at /api/docs that aggregates the OpenAPI
specs from all Campus Assist microservices.  The browser fetches each spec
directly through the ingress, so this service needs no DB, no secrets and no
inter-service communication.
"""
from fastapi import FastAPI
from fastapi.responses import HTMLResponse

app = FastAPI(docs_url=None, redoc_url=None, openapi_url=None)

_SERVICES = [
    ("Auth Service",        "/api/auth/openapi.json"),
    ("Community Service",   "/api/community/openapi.json"),
    ("Post Service",        "/api/posts/openapi.json"),
    ("Comment Service",     "/api/comments/openapi.json"),
    ("Attachment Service",  "/api/attachments/openapi.json"),
    ("College Service",     "/api/college/openapi.json"),
]

_OPTIONS_HTML = "\n      ".join(
    f'<option value="{url}">{name}</option>' for name, url in _SERVICES
)

_HTML = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Campus Assist — API Docs</title>
  <link rel="stylesheet" href="https://unpkg.com/swagger-ui-dist@5/swagger-ui.css" />
  <style>
    body {{ margin: 0; font-family: sans-serif; }}
    #service-bar {{
      background: #1b1b2f;
      padding: 10px 20px;
      display: flex;
      align-items: center;
      gap: 12px;
    }}
    #service-bar label {{ color: #fff; font-size: 14px; font-weight: 600; }}
    #service-select {{
      padding: 6px 12px;
      font-size: 14px;
      border-radius: 4px;
      border: none;
      cursor: pointer;
    }}
    /* hide the default swagger topbar — we have our own */
    .swagger-ui .topbar {{ display: none; }}
  </style>
</head>
<body>
  <div id="service-bar">
    <label for="service-select">Service:</label>
    <select id="service-select">
      {_OPTIONS_HTML}
    </select>
  </div>
  <div id="swagger-ui"></div>
  <script src="https://unpkg.com/swagger-ui-dist@5/swagger-ui-bundle.js"></script>
  <script>
    let ui;
    const select = document.getElementById("service-select");

    function loadSpec(url) {{
      if (ui) {{
        ui.specActions.updateUrl(url);
        ui.specActions.download(url);
      }} else {{
        ui = SwaggerUIBundle({{
          url: url,
          dom_id: "#swagger-ui",
          deepLinking: true,
          presets: [SwaggerUIBundle.presets.apis],
          layout: "BaseLayout",
          persistAuthorization: true,
        }});
      }}
    }}

    select.addEventListener("change", () => loadSpec(select.value));
    loadSpec(select.value);
  </script>
</body>
</html>
"""


@app.get("/api/docs", response_class=HTMLResponse, include_in_schema=False)
async def api_docs() -> HTMLResponse:
    """Aggregated Swagger UI for all Campus Assist microservices (dev only)."""
    return HTMLResponse(content=_HTML)


@app.get("/api/docs/health", include_in_schema=False)
async def health() -> dict:
    return {"status": "ok"}
