"""
Base classes for toolset definitions
"""
from typing import Dict, Any, List, Optional
from enum import Enum
from pydantic import BaseModel, Field
from abc import ABC, abstractmethod


class ToolSetType(str, Enum):
    """Supported toolset types"""
    FILE_SYSTEM = "file_system"
    SHELL = "shell"
    DOCKER = "docker"
    PYTHON = "python"
    FILE_GENERATION = "file_generation"
    DATA_VISUALIZATION = "data_visualization"
    SLEEP = "sleep"
    CUSTOM = "custom"


class ToolSetCategory(str, Enum):
    """Toolset categories for organization"""
    COMMON = "common"          # Frequently used, safe defaults
    ADVANCED = "advanced"       # Advanced features, require more privileges
    SECURITY = "security"       # Security-focused, restricted access
    CUSTOM = "custom"           # User-defined custom toolsets


class ToolSetVariant(BaseModel):
    """A specific variant/preset of a toolset"""
    id: str
    name: str
    description: str
    category: ToolSetCategory
    configuration: Dict[str, Any]
    badge: Optional[str] = None  # e.g., "Safe", "Recommended", "Advanced"
    icon: Optional[str] = None
    is_default: bool = False


class ToolSetDefinition(ABC):
    """
    Base class for all toolset definitions.

    Each toolset type should subclass this and implement the required methods.
    This provides a clean interface for defining new toolsets.
    """

    @property
    @abstractmethod
    def type(self) -> ToolSetType:
        """The type identifier for this toolset"""
        pass

    @property
    @abstractmethod
    def name(self) -> str:
        """Human-readable name"""
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        """Description of what this toolset does"""
        pass

    @property
    @abstractmethod
    def icon(self) -> str:
        """Icon name (Lucide or React Icons)"""
        pass

    @property
    def icon_type(self) -> str:
        """Icon type: 'lucide' or 'react-icon'"""
        return "lucide"

    @abstractmethod
    def get_variants(self) -> List[ToolSetVariant]:
        """
        Get all predefined variants/presets for this toolset.

        Returns a list of variants with different configurations
        (e.g., "Read Only", "Full Access", "Sandboxed")
        """
        pass

    @abstractmethod
    def validate_configuration(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate and normalize configuration.

        Args:
            config: Raw configuration dict

        Returns:
            Validated and normalized configuration

        Raises:
            ValueError: If configuration is invalid
        """
        pass

    @abstractmethod
    def get_default_configuration(self) -> Dict[str, Any]:
        """Get the default configuration for this toolset"""
        pass

    def get_framework_class_name(self) -> str:
        """
        Get the underlying framework tool class name.
        This is used for instantiation during agent execution.

        Returns:
            Class name (e.g., "FileTools", "ShellTools")
        """
        # Default mapping based on type
        mapping = {
            ToolSetType.FILE_SYSTEM: "FileTools",
            ToolSetType.SHELL: "ShellTools",
            ToolSetType.DOCKER: "DockerTools",
            ToolSetType.PYTHON: "PythonTools",
            ToolSetType.FILE_GENERATION: "FileGenerationTools",
            ToolSetType.DATA_VISUALIZATION: "DataVisualizationTools",
            ToolSetType.SLEEP: "SleepTools",
        }
        return mapping.get(self.type, "BaseTool")

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation"""
        return {
            "type": self.type.value,
            "name": self.name,
            "description": self.description,
            "icon": self.icon,
            "icon_type": self.icon_type,
            "default_configuration": self.get_default_configuration(),
            "variants": [v.model_dump() for v in self.get_variants()],
            "framework_class": self.get_framework_class_name(),
        }
