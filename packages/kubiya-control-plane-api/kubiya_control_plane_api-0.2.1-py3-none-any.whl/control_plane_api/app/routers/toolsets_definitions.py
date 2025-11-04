"""
Toolset Definitions Router

Provides endpoints to query available toolset types, variants, and templates
from the toolset registry.
"""
from fastapi import APIRouter
from typing import List, Dict, Any
import structlog

from control_plane_api.app.toolsets import get_all_toolsets, get_toolset, ToolSetType

logger = structlog.get_logger()

router = APIRouter()


@router.get("/definitions")
async def list_toolset_definitions():
    """
    Get all available toolset definitions with their variants.

    This returns the registry of all toolset types that can be instantiated,
    along with their predefined variants/presets.
    """
    toolsets = get_all_toolsets()

    result = []
    for toolset in toolsets:
        result.append(toolset.to_dict())

    logger.info(f"Returning {len(result)} toolset definitions")
    return {"toolsets": result}


@router.get("/definitions/{toolset_type}")
async def get_toolset_definition(toolset_type: str):
    """
    Get a specific toolset definition by type.

    Returns detailed information about a toolset type including all variants.
    """
    try:
        ts_type = ToolSetType(toolset_type)
    except ValueError:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail=f"Toolset type '{toolset_type}' not found")

    toolset = get_toolset(ts_type)
    if not toolset:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail=f"Toolset type '{toolset_type}' not registered")

    return toolset.to_dict()


@router.get("/definitions/{toolset_type}/variants")
async def list_toolset_variants(toolset_type: str):
    """
    Get all variants/presets for a specific toolset type.

    Variants are predefined configurations (e.g., "Read Only", "Full Access")
    that users can quickly apply.
    """
    try:
        ts_type = ToolSetType(toolset_type)
    except ValueError:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail=f"Toolset type '{toolset_type}' not found")

    toolset = get_toolset(ts_type)
    if not toolset:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail=f"Toolset type '{toolset_type}' not registered")

    variants = toolset.get_variants()
    return {
        "type": toolset.type.value,
        "name": toolset.name,
        "variants": [v.model_dump() for v in variants]
    }


@router.get("/templates")
async def list_toolset_templates():
    """
    Get all predefined toolset templates (flattened variants).

    This is a convenience endpoint that returns all variants from all toolsets
    as a flat list of ready-to-use templates.
    """
    toolsets = get_all_toolsets()

    templates = []
    for toolset in toolsets:
        for variant in toolset.get_variants():
            templates.append({
                "id": variant.id,
                "name": variant.name,
                "type": toolset.type.value,
                "description": variant.description,
                "icon": variant.icon or toolset.icon,
                "icon_type": toolset.icon_type,
                "category": variant.category.value,
                "badge": variant.badge,
                "configuration": variant.configuration,
                "is_default": variant.is_default,
            })

    logger.info(f"Returning {len(templates)} toolset templates")
    return {"templates": templates}


@router.post("/definitions/{toolset_type}/validate")
async def validate_toolset_configuration(toolset_type: str, configuration: Dict[str, Any]):
    """
    Validate a configuration for a specific toolset type.

    Returns the validated and normalized configuration.
    """
    try:
        ts_type = ToolSetType(toolset_type)
    except ValueError:
        from fastapi import HTTPException
        raise HTTPException(status_code=400, detail=f"Invalid toolset type: {toolset_type}")

    toolset = get_toolset(ts_type)
    if not toolset:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail=f"Toolset type '{toolset_type}' not registered")

    try:
        validated_config = toolset.validate_configuration(configuration)
        return {
            "valid": True,
            "configuration": validated_config
        }
    except Exception as e:
        from fastapi import HTTPException
        raise HTTPException(status_code=400, detail=f"Invalid configuration: {str(e)}")
