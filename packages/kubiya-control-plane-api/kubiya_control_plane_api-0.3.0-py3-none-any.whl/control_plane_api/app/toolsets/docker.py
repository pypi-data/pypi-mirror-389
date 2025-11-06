"""
Docker Toolset

Provides Docker management capabilities (containers, images, volumes, networks).
"""
from typing import Dict, Any, List
from .base import ToolSetDefinition, ToolSetType, ToolSetCategory, ToolSetVariant
from .registry import register_toolset


class DockerToolSet(ToolSetDefinition):
    """Docker management toolset"""

    @property
    def type(self) -> ToolSetType:
        return ToolSetType.DOCKER

    @property
    def name(self) -> str:
        return "Docker"

    @property
    def description(self) -> str:
        return "Manage Docker containers, images, volumes, and networks on the local system"

    @property
    def icon(self) -> str:
        return "FaDocker"

    @property
    def icon_type(self) -> str:
        return "react-icon"

    def get_variants(self) -> List[ToolSetVariant]:
        return [
            ToolSetVariant(
                id="docker_containers",
                name="Docker - Containers",
                description="Manage Docker containers on local system (start, stop, inspect)",
                category=ToolSetCategory.COMMON,
                badge="Safe",
                icon="FaDocker",
                configuration={
                    "enable_container_management": True,
                    "enable_image_management": False,
                    "enable_volume_management": False,
                    "enable_network_management": False,
                },
                is_default=True,
            ),
            ToolSetVariant(
                id="docker_full_control",
                name="Docker - Full Control",
                description="Complete Docker management: containers, images, volumes, and networks",
                category=ToolSetCategory.ADVANCED,
                badge="Advanced",
                icon="FaDocker",
                configuration={
                    "enable_container_management": True,
                    "enable_image_management": True,
                    "enable_volume_management": True,
                    "enable_network_management": True,
                },
                is_default=False,
            ),
        ]

    def validate_configuration(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Validate Docker configuration"""
        validated = {
            "enable_container_management": config.get("enable_container_management", True),
            "enable_image_management": config.get("enable_image_management", False),
            "enable_volume_management": config.get("enable_volume_management", False),
            "enable_network_management": config.get("enable_network_management", False),
        }

        # Add docker_host if specified (e.g., "unix:///var/run/docker.sock")
        if "docker_host" in config:
            validated["docker_host"] = str(config["docker_host"])

        return validated

    def get_default_configuration(self) -> Dict[str, Any]:
        """Default: container management only"""
        return {
            "enable_container_management": True,
            "enable_image_management": False,
            "enable_volume_management": False,
            "enable_network_management": False,
        }


# Auto-register this toolset
register_toolset(DockerToolSet())
