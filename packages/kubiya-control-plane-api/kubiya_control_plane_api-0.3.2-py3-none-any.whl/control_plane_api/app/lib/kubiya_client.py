"""Kubiya API client for authentication and runner management"""

import httpx
import os
from typing import Optional, Dict, List
import structlog

logger = structlog.get_logger()

KUBIYA_API_BASE = os.environ.get("KUBIYA_API_BASE", "https://api.kubiya.ai")


class KubiyaClient:
    """Client for Kubiya API"""

    def __init__(self, api_base: str = KUBIYA_API_BASE):
        self.api_base = api_base.rstrip("/")
        self.client = httpx.AsyncClient(timeout=30.0)

    async def validate_token_and_get_org(self, token: str) -> Optional[Dict]:
        """
        Validate bearer token with Kubiya API and get organization details.

        Args:
            token: Bearer/UserKey token from request

        Returns:
            Dict with organization details:
            {
                "id": "org-uuid",
                "name": "Organization Name",
                "slug": "org-slug"
            }
            None if invalid token
        """
        try:
            # Call Kubiya API to validate token and get user/org info
            # Kubiya uses "UserKey" prefix for API keys instead of "Bearer"
            response = await self.client.get(
                f"{self.api_base}/api/v1/users/me",
                headers={"Authorization": f"UserKey {token}"},
            )

            if response.status_code == 200:
                data = response.json()

                # Log full response for debugging
                logger.info(
                    "kubiya_api_response",
                    response_keys=list(data.keys()),
                    has_org=bool(data.get("org")),
                    has_org_id=bool(data.get("org_id")),
                )

                # Extract organization from response
                # Kubiya API returns org/org_id at root level, not nested
                org_id = data.get("org") or data.get("org_id") or data.get("organization", {}).get("uuid")
                org_name = data.get("org_name") or data.get("organization_name") or data.get("organization", {}).get("name")
                org_slug = data.get("org_slug") or data.get("organization_slug") or data.get("organization", {}).get("slug")

                org_data = {
                    "id": org_id,
                    "name": org_name,
                    "slug": org_slug,
                    "user_id": data.get("uuid") or data.get("id"),
                    "user_email": data.get("email"),
                    "user_name": data.get("name"),
                }

                logger.info(
                    "kubiya_token_validated",
                    org_id=org_data["id"],
                    org_name=org_data["name"],
                    user_email=org_data.get("user_email"),
                )

                return org_data

            else:
                logger.warning(
                    "kubiya_token_invalid",
                    status_code=response.status_code,
                )
                return None

        except Exception as e:
            logger.error("kubiya_api_error", error=str(e))
            return None

    async def get_runners(self, token: str, org_id: str) -> List[Dict]:
        """
        Get available runners for organization from Kubiya API.

        Args:
            token: Bearer token
            org_id: Organization UUID

        Returns:
            List of runner dicts:
            [
                {
                    "id": "runner-uuid",
                    "name": "runner-name",
                    "status": "active",
                    "capabilities": ["llm", "tools"],
                    "metadata": {}
                }
            ]
        """
        try:
            # Call Kubiya API to get runners
            # Assuming endpoint: GET /api/v1/runners or /api/v1/organizations/{org_id}/runners
            response = await self.client.get(
                f"{self.api_base}/api/v1/runners",
                headers={"Authorization": f"UserKey {token}"},
                params={"organization_id": org_id},
            )

            if response.status_code == 200:
                runners = response.json()

                logger.info(
                    "kubiya_runners_fetched",
                    org_id=org_id,
                    runner_count=len(runners),
                )

                return runners

            else:
                logger.warning(
                    "kubiya_runners_fetch_failed",
                    status_code=response.status_code,
                )
                return []

        except Exception as e:
            logger.error("kubiya_runners_error", error=str(e))
            return []

    async def register_runner_heartbeat(
        self, token: str, org_id: str, runner_name: str, metadata: Dict = None
    ) -> bool:
        """
        Register runner heartbeat with Kubiya API.

        Called by workers to report they're alive and polling.

        Args:
            token: Service token for worker
            org_id: Organization UUID
            runner_name: Runner name
            metadata: Additional metadata (capabilities, version, etc.)

        Returns:
            True if successful, False otherwise
        """
        try:
            response = await self.client.post(
                f"{self.api_base}/api/v1/runners/heartbeat",
                headers={"Authorization": f"UserKey {token}"},
                json={
                    "organization_id": org_id,
                    "runner_name": runner_name,
                    "status": "active",
                    "metadata": metadata or {},
                    "task_queue": f"{org_id}.{runner_name}",
                },
            )

            if response.status_code in [200, 201, 204]:
                logger.info(
                    "kubiya_heartbeat_sent",
                    org_id=org_id,
                    runner_name=runner_name,
                )
                return True
            else:
                logger.warning(
                    "kubiya_heartbeat_failed",
                    status_code=response.status_code,
                )
                return False

        except Exception as e:
            logger.error("kubiya_heartbeat_error", error=str(e))
            return False

    async def close(self):
        """Close the HTTP client"""
        await self.client.aclose()


# Singleton instance
_kubiya_client: Optional[KubiyaClient] = None


def get_kubiya_client() -> KubiyaClient:
    """Get or create Kubiya client singleton"""
    global _kubiya_client

    if _kubiya_client is None:
        _kubiya_client = KubiyaClient()

    return _kubiya_client
