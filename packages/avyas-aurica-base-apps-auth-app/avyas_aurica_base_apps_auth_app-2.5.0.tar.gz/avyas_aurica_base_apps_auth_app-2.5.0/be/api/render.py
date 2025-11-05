"""
Rendering API for Auth App
Provides rendering templates for authentication-related data
"""
from fastapi import APIRouter
from typing import Dict, Any

import sys
from pathlib import Path
auth_be_dir = Path(__file__).parent.parent
if str(auth_be_dir) not in sys.path:
    sys.path.insert(0, str(auth_be_dir))

from rendering_templates import get_templates, detect_data_type

router = APIRouter()


@router.get("/templates")
async def get_rendering_templates():
    """
    Get all rendering templates provided by auth-app.
    
    Returns templates that can be used by chat interfaces to render
    authentication-related data.
    """
    templates = get_templates()
    
    return {
        "app": "auth-app",
        "version": "1.0.0",
        "templates": templates,
        "template_count": len(templates)
    }


@router.post("/detect")
async def detect_render_type(data: Dict[str, Any]):
    """
    Detect what rendering template should be used for given data.
    
    Args:
        data: The data to analyze
        
    Returns:
        Template name and metadata
    """
    template_name = detect_data_type(data)
    
    if template_name:
        templates = get_templates()
        template = templates.get(template_name)
        
        return {
            "detected": True,
            "template": template_name,
            "template_info": {
                "name": template["name"],
                "description": template["description"],
                "type": template["type"]
            }
        }
    else:
        return {
            "detected": False,
            "template": None,
            "message": "No matching template found for this data"
        }


@router.get("/css")
async def get_all_css():
    """
    Get combined CSS for all auth-app rendering templates.
    
    This can be loaded once by the chat interface.
    """
    templates = get_templates()
    
    css_parts = [
        "/* Auth App Rendering Styles */",
        "/* Generated from auth-app rendering templates */",
        ""
    ]
    
    for template_name, template in templates.items():
        css_parts.append(f"/* Template: {template_name} */")
        css_parts.append(template["css"])
        css_parts.append("")
    
    return {
        "app": "auth-app",
        "css": "\n".join(css_parts)
    }
