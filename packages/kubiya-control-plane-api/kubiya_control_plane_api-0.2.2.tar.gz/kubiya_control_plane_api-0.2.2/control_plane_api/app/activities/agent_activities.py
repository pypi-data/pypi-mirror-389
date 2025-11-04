"""Agent-related Temporal activities"""

from dataclasses import dataclass
from typing import Optional
from datetime import datetime, timezone
from temporalio import activity
import structlog
import os

from control_plane_api.app.lib.supabase import get_supabase
from control_plane_api.app.services.litellm_service import litellm_service
from control_plane_api.app.services.agno_service import agno_service

logger = structlog.get_logger()


@dataclass
class ActivityExecuteAgentInput:
    """Input for execute_agent_llm activity"""
    execution_id: str
    agent_id: str
    organization_id: str
    prompt: str
    system_prompt: Optional[str] = None
    model_id: Optional[str] = None
    model_config: dict = None
    mcp_servers: dict = None  # MCP servers configuration
    session_id: Optional[str] = None  # Session ID for Agno session management (use execution_id)
    user_id: Optional[str] = None  # User ID for multi-user support
    control_plane_url: Optional[str] = None  # Control Plane URL for fetching toolsets
    api_key: Optional[str] = None  # API key for authentication

    def __post_init__(self):
        if self.model_config is None:
            self.model_config = {}
        if self.mcp_servers is None:
            self.mcp_servers = {}


@dataclass
class ActivityUpdateExecutionInput:
    """Input for update_execution_status activity"""
    execution_id: str
    status: str
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    response: Optional[str] = None
    error_message: Optional[str] = None
    usage: dict = None
    execution_metadata: dict = None

    def __post_init__(self):
        if self.usage is None:
            self.usage = {}
        if self.execution_metadata is None:
            self.execution_metadata = {}


@dataclass
class ActivityUpdateAgentInput:
    """Input for update_agent_status activity"""
    agent_id: str
    organization_id: str
    status: str
    last_active_at: str
    error_message: Optional[str] = None
    state: dict = None

    def __post_init__(self):
        if self.state is None:
            self.state = {}


@activity.defn
async def execute_agent_llm(input: ActivityExecuteAgentInput) -> dict:
    """
    Execute an agent's LLM call with Agno Teams and session management.

    This activity uses Agno Teams with session support for persistent conversation history.
    The session_id should be set to execution_id for 1:1 mapping.

    Args:
        input: Activity input with execution details

    Returns:
        Dict with response, usage, success flag, session messages, etc.
    """
    activity.logger.info(
        f"Executing agent LLM call with Agno Sessions",
        extra={
            "execution_id": input.execution_id,
            "agent_id": input.agent_id,
            "model_id": input.model_id,
            "has_mcp_servers": bool(input.mcp_servers),
            "session_id": input.session_id,
        }
    )

    try:
        # Get model from input or use default
        model = input.model_id or os.environ.get("LITELLM_DEFAULT_MODEL", "kubiya/claude-sonnet-4")

        # Fetch resolved toolsets from Control Plane if available
        toolsets = []
        if input.control_plane_url and input.api_key and input.agent_id:
            import httpx
            try:
                async with httpx.AsyncClient(timeout=30.0) as client:
                    response = await client.get(
                        f"{input.control_plane_url}/api/v1/toolsets/associations/agents/{input.agent_id}/toolsets/resolved",
                        headers={"Authorization": f"Bearer {input.api_key}"}
                    )

                    if response.status_code == 200:
                        toolsets = response.json()
                        activity.logger.info(
                            f"Resolved toolsets from Control Plane",
                            extra={
                                "agent_id": input.agent_id,
                                "toolset_count": len(toolsets),
                                "toolset_types": [t.get("type") for t in toolsets],
                                "toolset_sources": [t.get("source") for t in toolsets]
                            }
                        )
                    else:
                        activity.logger.warning(
                            f"Failed to fetch toolsets from Control Plane: {response.status_code}",
                            extra={
                                "status_code": response.status_code,
                                "response_text": response.text[:500]
                            }
                        )
            except Exception as e:
                activity.logger.error(
                    f"Error fetching toolsets from Control Plane: {str(e)}",
                    extra={"error": str(e)}
                )
                # Continue execution without toolsets

        # Use Agno Teams with session management
        activity.logger.info(
            f"Using Agno Teams with sessions and toolsets",
            extra={
                "execution_id": input.execution_id,
                "session_id": input.session_id,
                "has_mcp_servers": bool(input.mcp_servers),
                "mcp_servers": list(input.mcp_servers.keys()) if input.mcp_servers else [],
                "toolset_count": len(toolsets),
            }
        )

        # Execute with session support and streaming - Agno handles conversation history automatically
        result = await agno_service.execute_agent_async(
            prompt=input.prompt,
            model=model,
            system_prompt=input.system_prompt,
            mcp_servers=input.mcp_servers,
            toolsets=toolsets,  # Pass resolved toolsets
            session_id=input.session_id,  # Pass session_id for persistence
            user_id=input.user_id,  # Pass user_id for multi-user support
            stream=True,  # Enable real-time streaming for UI updates
            **(input.model_config or {})
        )

        activity.logger.info(
            f"Agent LLM call completed",
            extra={
                "execution_id": input.execution_id,
                "success": result.get("success"),
                "model": result.get("model"),
                "mcp_tools_used": result.get("mcp_tools_used", 0),
                "session_messages": len(result.get("messages", [])),
            }
        )

        return result

    except Exception as e:
        activity.logger.error(
            f"Agent LLM call failed",
            extra={
                "execution_id": input.execution_id,
                "error": str(e),
            }
        )
        return {
            "success": False,
            "error": str(e),
            "model": input.model_id,
            "usage": None,
            "finish_reason": "error",
        }


@activity.defn
async def update_execution_status(input: ActivityUpdateExecutionInput) -> dict:
    """
    Update execution status in database.

    This activity updates the execution record with status, results, timestamps, etc.

    Args:
        input: Activity input with update details

    Returns:
        Dict with success flag
    """
    activity.logger.info(
        f"Updating execution status",
        extra={
            "execution_id": input.execution_id,
            "status": input.status,
        }
    )

    try:
        client = get_supabase()

        # Build update dict - normalize status to uppercase for consistency
        update_data = {
            "status": input.status.upper(),  # Normalize to uppercase (PENDING, RUNNING, FAILED, etc.)
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }

        if input.started_at:
            update_data["started_at"] = input.started_at

        if input.completed_at:
            update_data["completed_at"] = input.completed_at

        if input.response is not None:
            update_data["response"] = input.response

        if input.error_message is not None:
            update_data["error_message"] = input.error_message

        if input.usage:
            update_data["usage"] = input.usage

        if input.execution_metadata:
            update_data["execution_metadata"] = input.execution_metadata

        # Update execution
        result = (
            client.table("executions")
            .update(update_data)
            .eq("id", input.execution_id)
            .execute()
        )

        if not result.data:
            raise Exception("Failed to update execution")

        activity.logger.info(
            f"Execution status updated",
            extra={
                "execution_id": input.execution_id,
                "status": input.status,
            }
        )

        return {"success": True}

    except Exception as e:
        activity.logger.error(
            f"Failed to update execution status",
            extra={
                "execution_id": input.execution_id,
                "error": str(e),
            }
        )
        raise


@activity.defn
async def update_agent_status(input: ActivityUpdateAgentInput) -> dict:
    """
    Update agent status in database.

    This activity updates the agent record with status, error messages, etc.

    Args:
        input: Activity input with update details

    Returns:
        Dict with success flag
    """
    activity.logger.info(
        f"Updating agent status",
        extra={
            "agent_id": input.agent_id,
            "status": input.status,
        }
    )

    try:
        client = get_supabase()

        # Build update dict
        update_data = {
            "status": input.status,
            "last_active_at": input.last_active_at,
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }

        if input.error_message is not None:
            update_data["error_message"] = input.error_message

        if input.state:
            update_data["state"] = input.state

        # Update agent
        result = (
            client.table("agents")
            .update(update_data)
            .eq("id", input.agent_id)
            .eq("organization_id", input.organization_id)
            .execute()
        )

        # For team executions, the "agent_id" is actually a team_id, so it won't be found in agents table
        # This is expected and not an error - just log and return success
        if not result.data:
            activity.logger.info(
                f"Agent not found (likely a team execution) - skipping agent status update",
                extra={
                    "agent_id": input.agent_id,
                    "status": input.status,
                }
            )
            return {"success": True, "skipped": True}

        activity.logger.info(
            f"Agent status updated",
            extra={
                "agent_id": input.agent_id,
                "status": input.status,
            }
        )

        return {"success": True}

    except Exception as e:
        activity.logger.error(
            f"Failed to update agent status",
            extra={
                "agent_id": input.agent_id,
                "error": str(e),
            }
        )
        raise
