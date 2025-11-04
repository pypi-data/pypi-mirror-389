"""Runners endpoint - proxies to Kubiya API"""

from fastapi import APIRouter, Depends, Request
from typing import List
import structlog

from control_plane_api.app.middleware.auth import get_current_organization
from control_plane_api.app.lib.kubiya_client import get_kubiya_client

logger = structlog.get_logger()

router = APIRouter()


@router.get("")
async def list_runners(
    request: Request,
    organization: dict = Depends(get_current_organization),
):
    """
    List available runners for the organization.

    Proxies to Kubiya API to get runners.
    """
    try:
        kubiya_client = get_kubiya_client()
        token = request.state.kubiya_token

        runners = await kubiya_client.get_runners(token, organization["id"])

        logger.info(
            "runners_listed",
            org_id=organization["id"],
            runner_count=len(runners),
        )

        return {
            "runners": runners,
            "count": len(runners),
        }

    except Exception as e:
        logger.error("runners_list_failed", error=str(e), org_id=organization["id"])
        # Return empty list if Kubiya API fails
        return {
            "runners": [],
            "count": 0,
            "error": "Failed to fetch runners from Kubiya API"
        }
