from typing import List
from fastapi import APIRouter, Depends, Response
from sqlalchemy.orm import Session
from datetime import datetime
from xml.sax.saxutils import escape

from ...api.deps import get_db
from ...crud.product import product_crud, category_crud

router = APIRouter()

FRONTEND_URL = "https://www.setupdream.ma"

import os
from ...core.config import settings
from fastapi import Request

@router.get("/sitemap.xml", response_class=Response)
def get_sitemap():
    """Serve the statically generated XML sitemap"""
    sitemap_path = os.path.join(settings.UPLOAD_DIR, "sitemap.xml")
    
    if os.path.exists(sitemap_path):
        with open(sitemap_path, "r", encoding="utf-8") as f:
            xml_content = f.read()
    else:
        # Fallback empty sitemap
        xml_content = '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"></urlset>'
    
    return Response(
        content=xml_content, 
        media_type="application/xml",
        headers={"Cache-Control": "public, max-age=3600"}
    )

from ...models.user import User
from ...api.deps import get_current_active_superuser

@router.post("/sitemap.xml")
async def update_sitemap(
    request: Request,
    current_user: User = Depends(get_current_active_superuser)
):
    """Receive XML body and save to public sitemap file"""
    xml_content = await request.body()
    
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    sitemap_path = os.path.join(settings.UPLOAD_DIR, "sitemap.xml")
    
    with open(sitemap_path, "wb") as f:
        f.write(xml_content)
        
    return {"message": "Sitemap successfully updated on the server"}
