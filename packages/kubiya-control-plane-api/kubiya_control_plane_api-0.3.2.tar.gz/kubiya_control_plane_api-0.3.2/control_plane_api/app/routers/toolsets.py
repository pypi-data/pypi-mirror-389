"""
Multi-tenant toolsets router.

This router handles toolset CRUD operations and associations with agents/teams/environments.
All operations are scoped to the authenticated organization.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel, Field
import structlog
import uuid

from control_plane_api.app.middleware.auth import get_current_organization
from control_plane_api.app.lib.supabase import get_supabase
from control_plane_api.app.toolsets import get_all_toolsets, get_toolset, ToolSetType

logger = structlog.get_logger()

router = APIRouter()


# Pydantic schemas
class ToolSetConfiguration(BaseModel):
    """Configuration for a toolset"""
    # File System
    base_dir: Optional[str] = None
    enable_save_file: Optional[bool] = None
    enable_read_file: Optional[bool] = None
    enable_list_files: Optional[bool] = None
    enable_search_files: Optional[bool] = None

    # Shell
    allowed_commands: Optional[List[str]] = None
    blocked_commands: Optional[List[str]] = None
    timeout: Optional[int] = None

    # Docker
    enable_container_management: Optional[bool] = None
    enable_image_management: Optional[bool] = None
    enable_volume_management: Optional[bool] = None
    enable_network_management: Optional[bool] = None

    # Python
    enable_code_execution: Optional[bool] = None
    allowed_imports: Optional[List[str]] = None
    blocked_imports: Optional[List[str]] = None

    # File Generation
    enable_json_generation: Optional[bool] = None
    enable_csv_generation: Optional[bool] = None
    enable_pdf_generation: Optional[bool] = None
    enable_txt_generation: Optional[bool] = None
    output_directory: Optional[str] = None

    # Data Visualization
    max_diagram_size: Optional[int] = None
    enable_flowchart: Optional[bool] = None
    enable_sequence: Optional[bool] = None
    enable_class_diagram: Optional[bool] = None
    enable_er_diagram: Optional[bool] = None
    enable_gantt: Optional[bool] = None
    enable_pie_chart: Optional[bool] = None
    enable_state_diagram: Optional[bool] = None
    enable_git_graph: Optional[bool] = None
    enable_user_journey: Optional[bool] = None
    enable_quadrant_chart: Optional[bool] = None

    # Custom
    custom_class: Optional[str] = None
    custom_config: Optional[dict] = None


class ToolSetCreate(BaseModel):
    name: str = Field(..., description="Toolset name")
    type: str = Field(..., description="Toolset type (file_system, shell, docker, python, etc.)")
    description: Optional[str] = Field(None, description="Toolset description")
    icon: Optional[str] = Field("Wrench", description="Icon name")
    enabled: bool = Field(True, description="Whether toolset is enabled")
    configuration: ToolSetConfiguration = Field(default_factory=ToolSetConfiguration)


class ToolSetUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    icon: Optional[str] = None
    enabled: Optional[bool] = None
    configuration: Optional[ToolSetConfiguration] = None


class ToolSetResponse(BaseModel):
    id: str
    organization_id: str
    name: str
    type: str
    description: Optional[str]
    icon: str
    enabled: bool
    configuration: dict
    created_at: str
    updated_at: str


class ToolSetAssociationCreate(BaseModel):
    toolset_id: str = Field(..., description="Toolset ID to associate")
    configuration_override: Optional[ToolSetConfiguration] = Field(None, description="Entity-specific config overrides")


class ResolvedToolSet(BaseModel):
    id: str
    name: str
    type: str
    description: Optional[str]
    icon: str
    enabled: bool
    configuration: dict
    source: str  # "environment", "team", "agent"
    inherited: bool


# Helper functions
def get_toolset_by_id(client, organization_id: str, toolset_id: str) -> dict:
    """Get a toolset by ID, scoped to organization"""
    result = (
        client.table("toolsets")
        .select("*")
        .eq("organization_id", organization_id)
        .eq("id", toolset_id)
        .execute()
    )

    if not result.data:
        raise HTTPException(status_code=404, detail=f"Toolset {toolset_id} not found")

    return result.data[0]


def get_entity_toolsets(client, organization_id: str, entity_type: str, entity_id: str) -> List[dict]:
    """Get toolsets associated with an entity"""
    # Get associations
    result = (
        client.table("toolset_associations")
        .select("toolset_id, configuration_override, toolsets(*)")
        .eq("organization_id", organization_id)
        .eq("entity_type", entity_type)
        .eq("entity_id", entity_id)
        .execute()
    )

    toolsets = []
    for item in result.data:
        toolset_data = item.get("toolsets")
        if toolset_data and toolset_data.get("enabled", True):
            # Merge configuration with override
            config = toolset_data.get("configuration", {})
            override = item.get("configuration_override")
            if override:
                config = {**config, **override}

            toolsets.append({
                **toolset_data,
                "configuration": config
            })

    return toolsets


def merge_configurations(base: dict, override: dict) -> dict:
    """Merge two configuration dictionaries, with override taking precedence"""
    result = base.copy()
    for key, value in override.items():
        if value is not None:
            result[key] = value
    return result


# API Endpoints

@router.post("", response_model=ToolSetResponse, status_code=status.HTTP_201_CREATED)
async def create_toolset(
    toolset_data: ToolSetCreate,
    organization: dict = Depends(get_current_organization),
):
    """Create a new toolset in the organization"""
    try:
        client = get_supabase()

        toolset_id = str(uuid.uuid4())
        now = datetime.utcnow().isoformat()

        # Validate toolset type
        valid_types = ["file_system", "shell", "python", "docker", "sleep", "file_generation", "data_visualization", "custom"]
        if toolset_data.type not in valid_types:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid toolset type. Must be one of: {', '.join(valid_types)}"
            )

        toolset_record = {
            "id": toolset_id,
            "organization_id": organization["id"],
            "name": toolset_data.name,
            "type": toolset_data.type,
            "description": toolset_data.description,
            "icon": toolset_data.icon,
            "enabled": toolset_data.enabled,
            "configuration": toolset_data.configuration.dict(exclude_none=True),
            "created_at": now,
            "updated_at": now,
        }

        result = client.table("toolsets").insert(toolset_record).execute()

        logger.info(
            "toolset_created",
            toolset_id=toolset_id,
            name=toolset_data.name,
            type=toolset_data.type,
            organization_id=organization["id"]
        )

        return ToolSetResponse(**result.data[0])

    except Exception as e:
        logger.error("toolset_creation_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("", response_model=List[ToolSetResponse])
async def list_toolsets(
    organization: dict = Depends(get_current_organization),
):
    """List all toolsets for the organization"""
    try:
        client = get_supabase()

        result = (
            client.table("toolsets")
            .select("*")
            .eq("organization_id", organization["id"])
            .order("created_at", desc=True)
            .execute()
        )

        return [ToolSetResponse(**toolset) for toolset in result.data]

    except Exception as e:
        logger.error("toolset_list_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{toolset_id}", response_model=ToolSetResponse)
async def get_toolset(
    toolset_id: str,
    organization: dict = Depends(get_current_organization),
):
    """Get a specific toolset"""
    try:
        client = get_supabase()
        toolset = get_toolset_by_id(client, organization["id"], toolset_id)
        return ToolSetResponse(**toolset)

    except HTTPException:
        raise
    except Exception as e:
        logger.error("toolset_get_failed", error=str(e), toolset_id=toolset_id)
        raise HTTPException(status_code=500, detail=str(e))


@router.patch("/{toolset_id}", response_model=ToolSetResponse)
async def update_toolset(
    toolset_id: str,
    toolset_data: ToolSetUpdate,
    organization: dict = Depends(get_current_organization),
):
    """Update a toolset"""
    try:
        client = get_supabase()

        # Verify toolset exists
        get_toolset_by_id(client, organization["id"], toolset_id)

        # Build update dict
        update_data = toolset_data.dict(exclude_none=True)
        if "configuration" in update_data:
            update_data["configuration"] = update_data["configuration"]
        update_data["updated_at"] = datetime.utcnow().isoformat()

        result = (
            client.table("toolsets")
            .update(update_data)
            .eq("id", toolset_id)
            .eq("organization_id", organization["id"])
            .execute()
        )

        logger.info("toolset_updated", toolset_id=toolset_id, organization_id=organization["id"])

        return ToolSetResponse(**result.data[0])

    except HTTPException:
        raise
    except Exception as e:
        logger.error("toolset_update_failed", error=str(e), toolset_id=toolset_id)
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{toolset_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_toolset(
    toolset_id: str,
    organization: dict = Depends(get_current_organization),
):
    """Delete a toolset"""
    try:
        client = get_supabase()

        # Verify toolset exists
        get_toolset_by_id(client, organization["id"], toolset_id)

        # Delete toolset (cascade will handle associations)
        client.table("toolsets").delete().eq("id", toolset_id).eq("organization_id", organization["id"]).execute()

        logger.info("toolset_deleted", toolset_id=toolset_id, organization_id=organization["id"])

    except HTTPException:
        raise
    except Exception as e:
        logger.error("toolset_delete_failed", error=str(e), toolset_id=toolset_id)
        raise HTTPException(status_code=500, detail=str(e))


# Association endpoints for agents
@router.post("/associations/{entity_type}/{entity_id}/toolsets", status_code=status.HTTP_201_CREATED)
async def associate_toolset(
    entity_type: str,
    entity_id: str,
    association_data: ToolSetAssociationCreate,
    organization: dict = Depends(get_current_organization),
):
    """Associate a toolset with an entity (agent, team, environment)"""
    try:
        client = get_supabase()

        # Validate entity type
        if entity_type not in ["agent", "team", "environment"]:
            raise HTTPException(status_code=400, detail="Invalid entity type. Must be: agent, team, or environment")

        # Verify toolset exists
        get_toolset_by_id(client, organization["id"], association_data.toolset_id)

        # Verify entity exists (check appropriate table)
        # Note: "environment" entity type maps to "environments" table
        entity_table = "environments" if entity_type == "environment" else f"{entity_type}s"
        entity_result = (
            client.table(entity_table)
            .select("id")
            .eq("organization_id", organization["id"])
            .eq("id", entity_id)
            .execute()
        )

        if not entity_result.data:
            raise HTTPException(status_code=404, detail=f"{entity_type.capitalize()} {entity_id} not found")

        # Create association
        association_id = str(uuid.uuid4())
        association_record = {
            "id": association_id,
            "organization_id": organization["id"],
            "toolset_id": association_data.toolset_id,
            "entity_type": entity_type,
            "entity_id": entity_id,
            "configuration_override": association_data.configuration_override.dict(exclude_none=True) if association_data.configuration_override else {},
            "created_at": datetime.utcnow().isoformat(),
        }

        client.table("toolset_associations").insert(association_record).execute()

        # Also update denormalized toolset_ids array
        current_entity = entity_result.data[0]
        current_ids = current_entity.get("toolset_ids", []) or []
        if association_data.toolset_id not in current_ids:
            updated_ids = current_ids + [association_data.toolset_id]
            client.table(entity_table).update({"toolset_ids": updated_ids}).eq("id", entity_id).execute()

        logger.info(
            "toolset_associated",
            toolset_id=association_data.toolset_id,
            entity_type=entity_type,
            entity_id=entity_id,
            organization_id=organization["id"]
        )

        return {"message": "Toolset associated successfully"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error("toolset_association_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/associations/{entity_type}/{entity_id}/toolsets", response_model=List[ToolSetResponse])
async def list_entity_toolsets(
    entity_type: str,
    entity_id: str,
    organization: dict = Depends(get_current_organization),
):
    """List toolsets associated with an entity"""
    try:
        client = get_supabase()

        if entity_type not in ["agent", "team", "environment"]:
            raise HTTPException(status_code=400, detail="Invalid entity type")

        toolsets = get_entity_toolsets(client, organization["id"], entity_type, entity_id)
        return [ToolSetResponse(**toolset) for toolset in toolsets]

    except HTTPException:
        raise
    except Exception as e:
        logger.error("list_entity_toolsets_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/associations/{entity_type}/{entity_id}/toolsets/{toolset_id}", status_code=status.HTTP_204_NO_CONTENT)
async def dissociate_toolset(
    entity_type: str,
    entity_id: str,
    toolset_id: str,
    organization: dict = Depends(get_current_organization),
):
    """Remove a toolset association from an entity"""
    try:
        client = get_supabase()

        if entity_type not in ["agent", "team", "environment"]:
            raise HTTPException(status_code=400, detail="Invalid entity type")

        # Delete association
        client.table("toolset_associations").delete().eq("toolset_id", toolset_id).eq("entity_type", entity_type).eq("entity_id", entity_id).execute()

        # Update denormalized toolset_ids array
        # Note: "environment" entity type maps to "environments" table
        entity_table = "environments" if entity_type == "environment" else f"{entity_type}s"
        entity_result = client.table(entity_table).select("toolset_ids").eq("id", entity_id).execute()
        if entity_result.data:
            current_ids = entity_result.data[0].get("toolset_ids", []) or []
            updated_ids = [tid for tid in current_ids if tid != toolset_id]
            client.table(entity_table).update({"toolset_ids": updated_ids}).eq("id", entity_id).execute()

        logger.info(
            "toolset_dissociated",
            toolset_id=toolset_id,
            entity_type=entity_type,
            entity_id=entity_id,
            organization_id=organization["id"]
        )

    except Exception as e:
        logger.error("toolset_dissociation_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/associations/agents/{agent_id}/toolsets/resolved", response_model=List[ResolvedToolSet])
async def resolve_agent_toolsets(
    agent_id: str,
    organization: dict = Depends(get_current_organization),
):
    """
    Resolve all toolsets for an agent (including inherited from ALL environments and team).

    Inheritance order (with deduplication):
    1. All agent environments
    2. All team environments (if agent has team)
    3. Team toolsets
    4. Agent toolsets

    Later layers override earlier ones if there are conflicts.
    """
    try:
        client = get_supabase()

        # Get agent details
        agent_result = (
            client.table("agents")
            .select("id, team_id")
            .eq("organization_id", organization["id"])
            .eq("id", agent_id)
            .execute()
        )

        if not agent_result.data:
            raise HTTPException(status_code=404, detail=f"Agent {agent_id} not found")

        agent = agent_result.data[0]
        resolved_toolsets = []
        seen_ids = set()

        # 1. Load toolsets from ALL agent environments (many-to-many)
        agent_env_result = (
            client.table("agent_environments")
            .select("environment_id")
            .eq("agent_id", agent_id)
            .execute()
        )

        agent_environment_ids = [env["environment_id"] for env in (agent_env_result.data or [])]

        for environment_id in agent_environment_ids:
            env_toolsets = get_entity_toolsets(client, organization["id"], "environment", environment_id)
            for toolset in env_toolsets:
                if toolset["id"] not in seen_ids:
                    resolved_toolsets.append(ResolvedToolSet(
                        **toolset,
                        source="environment",
                        inherited=True
                    ))
                    seen_ids.add(toolset["id"])

        # 2. Load toolsets from ALL team environments (if agent has team)
        team_id = agent.get("team_id")
        if team_id:
            team_env_result = (
                client.table("team_environments")
                .select("environment_id")
                .eq("team_id", team_id)
                .execute()
            )

            team_environment_ids = [env["environment_id"] for env in (team_env_result.data or [])]

            for environment_id in team_environment_ids:
                env_toolsets = get_entity_toolsets(client, organization["id"], "environment", environment_id)
                for toolset in env_toolsets:
                    if toolset["id"] not in seen_ids:
                        resolved_toolsets.append(ResolvedToolSet(
                            **toolset,
                            source="environment",
                            inherited=True
                        ))
                        seen_ids.add(toolset["id"])

            # 3. Load team toolsets
            team_toolsets = get_entity_toolsets(client, organization["id"], "team", team_id)
            for toolset in team_toolsets:
                if toolset["id"] not in seen_ids:
                    resolved_toolsets.append(ResolvedToolSet(
                        **toolset,
                        source="team",
                        inherited=True
                    ))
                    seen_ids.add(toolset["id"])

        # 4. Load agent toolsets (highest priority)
        agent_toolsets = get_entity_toolsets(client, organization["id"], "agent", agent_id)
        for toolset in agent_toolsets:
            if toolset["id"] not in seen_ids:
                resolved_toolsets.append(ResolvedToolSet(
                    **toolset,
                    source="agent",
                    inherited=False
                ))
                seen_ids.add(toolset["id"])

        logger.info(
            "agent_toolsets_resolved",
            agent_id=agent_id,
            toolset_count=len(resolved_toolsets),
            agent_env_count=len(agent_environment_ids),
            team_env_count=len(team_environment_ids) if team_id else 0,
            organization_id=organization["id"]
        )

        return resolved_toolsets

    except HTTPException:
        raise
    except Exception as e:
        logger.error("resolve_agent_toolsets_failed", error=str(e), agent_id=agent_id)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/associations/teams/{team_id}/toolsets/resolved", response_model=List[ResolvedToolSet])
async def resolve_team_toolsets(
    team_id: str,
    organization: dict = Depends(get_current_organization),
):
    """
    Resolve all toolsets for a team (including inherited from ALL environments).

    Inheritance order (with deduplication):
    1. All team environments
    2. Team toolsets

    Later layers override earlier ones if there are conflicts.
    """
    try:
        client = get_supabase()

        # Get team details
        team_result = (
            client.table("teams")
            .select("id")
            .eq("organization_id", organization["id"])
            .eq("id", team_id)
            .execute()
        )

        if not team_result.data:
            raise HTTPException(status_code=404, detail=f"Team {team_id} not found")

        resolved_toolsets = []
        seen_ids = set()

        # 1. Load toolsets from ALL team environments (many-to-many)
        team_env_result = (
            client.table("team_environments")
            .select("environment_id")
            .eq("team_id", team_id)
            .execute()
        )

        team_environment_ids = [env["environment_id"] for env in (team_env_result.data or [])]

        for environment_id in team_environment_ids:
            env_toolsets = get_entity_toolsets(client, organization["id"], "environment", environment_id)
            for toolset in env_toolsets:
                if toolset["id"] not in seen_ids:
                    resolved_toolsets.append(ResolvedToolSet(
                        **toolset,
                        source="environment",
                        inherited=True
                    ))
                    seen_ids.add(toolset["id"])

        # 2. Load team toolsets (highest priority)
        team_toolsets = get_entity_toolsets(client, organization["id"], "team", team_id)
        for toolset in team_toolsets:
            if toolset["id"] not in seen_ids:
                resolved_toolsets.append(ResolvedToolSet(
                    **toolset,
                    source="team",
                    inherited=False
                ))
                seen_ids.add(toolset["id"])

        logger.info(
            "team_toolsets_resolved",
            team_id=team_id,
            toolset_count=len(resolved_toolsets),
            team_env_count=len(team_environment_ids),
            organization_id=organization["id"]
        )

        return resolved_toolsets

    except HTTPException:
        raise
    except Exception as e:
        logger.error("resolve_team_toolsets_failed", error=str(e), team_id=team_id)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/types")
async def get_toolset_types():
    """Get available toolset types and their descriptions"""
    return {
        "types": [
            {
                "type": "file_system",
                "name": "File System",
                "description": "Read, write, list, and search files",
                "icon": "FileText"
            },
            {
                "type": "shell",
                "name": "Shell",
                "description": "Execute shell commands",
                "icon": "Terminal"
            },
            {
                "type": "docker",
                "name": "Docker",
                "description": "Manage containers, images, volumes, and networks",
                "icon": "Container"
            },
            {
                "type": "python",
                "name": "Python",
                "description": "Execute Python code",
                "icon": "Code"
            },
            {
                "type": "file_generation",
                "name": "File Generation",
                "description": "Generate JSON, CSV, PDF, and TXT files",
                "icon": "FileOutput"
            },
            {
                "type": "sleep",
                "name": "Sleep",
                "description": "Pause execution for a specified duration",
                "icon": "Clock"
            },
            {
                "type": "custom",
                "name": "Custom",
                "description": "User-defined custom toolset",
                "icon": "Wrench"
            }
        ]
    }
