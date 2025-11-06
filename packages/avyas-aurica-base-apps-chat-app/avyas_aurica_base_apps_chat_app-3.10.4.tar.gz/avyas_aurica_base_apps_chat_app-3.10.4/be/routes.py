"""
Page routes - Serve HTML pages at app root level
These routes are mounted at /chat-app/ (without the /api/ prefix)
"""
from fastapi import APIRouter
from fastapi.responses import HTMLResponse, RedirectResponse
from pathlib import Path

router = APIRouter()

STATIC_DIR = Path(__file__).parent.parent / "fe" / "static"


@router.get("/")
async def root():
    """Serve launcher as the root page"""
    launcher_html = (STATIC_DIR / "index.html").read_text()
    return HTMLResponse(content=launcher_html)


@router.get("/dt/{dt_id}")
async def dt_chat(dt_id: str):
    """Serve chat page for any DT - shows conversations filtered by that DT"""
    # Load chat page and inject the dt_id
    chat_html = (STATIC_DIR / "chat.html").read_text()
    
    # Inject dt_id into the page before the first script tag
    injection = f'<script>window.dtIdInjected = "{dt_id}";</script>'
    chat_html = chat_html.replace('<script>', injection + '\n    <script>', 1)
    
    return HTMLResponse(content=chat_html)


@router.get("/{dt_id_or_app}")
async def root_dt_router(dt_id_or_app: str):
    """Route DT IDs to appropriate pages:
    - dt_app_* → App explorer page (schemas, APIs, docs)
    - Other IDs → Redirect to /dt/{id} chat page
    """
    if dt_id_or_app.startswith("dt_app_"):
        # App DT - show app explorer page with schemas, APIs, docs
        app_html = (STATIC_DIR / "app-explorer.html").read_text()
        
        # Inject dt_id into the page before the first script tag
        injection = f'<script>window.dtIdInjected = "{dt_id_or_app}";</script>'
        app_html = app_html.replace('<script>', injection + '\n    <script>', 1)
        
        return HTMLResponse(content=app_html)
    else:
        # User DT or other - redirect to /dt/{id} for chat page
        return RedirectResponse(url=f"/chat-app/dt/{dt_id_or_app}")
