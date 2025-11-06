"""
Toolset Registry

Central registry for all available toolsets. Toolsets self-register
when their modules are imported.
"""
from typing import Dict, List, Optional
from .base import ToolSetDefinition, ToolSetType
import logging

logger = logging.getLogger(__name__)


class ToolSetRegistry:
    """Registry for all available toolset definitions"""

    def __init__(self):
        self._toolsets: Dict[ToolSetType, ToolSetDefinition] = {}

    def register(self, toolset: ToolSetDefinition):
        """Register a toolset definition"""
        if toolset.type in self._toolsets:
            logger.warning(f"Toolset {toolset.type} is already registered, overwriting")

        self._toolsets[toolset.type] = toolset
        logger.info(f"Registered toolset: {toolset.type} - {toolset.name}")

    def get(self, toolset_type: ToolSetType) -> Optional[ToolSetDefinition]:
        """Get a toolset definition by type"""
        return self._toolsets.get(toolset_type)

    def get_all(self) -> List[ToolSetDefinition]:
        """Get all registered toolsets"""
        return list(self._toolsets.values())

    def get_by_name(self, name: str) -> Optional[ToolSetDefinition]:
        """Get a toolset by name"""
        for toolset in self._toolsets.values():
            if toolset.name.lower() == name.lower():
                return toolset
        return None

    def list_types(self) -> List[ToolSetType]:
        """List all registered toolset types"""
        return list(self._toolsets.keys())


# Global registry instance
toolset_registry = ToolSetRegistry()


def register_toolset(toolset: ToolSetDefinition):
    """Decorator or function to register a toolset"""
    toolset_registry.register(toolset)
    return toolset


def get_toolset(toolset_type: ToolSetType) -> Optional[ToolSetDefinition]:
    """Get a toolset definition by type"""
    return toolset_registry.get(toolset_type)


def get_all_toolsets() -> List[ToolSetDefinition]:
    """Get all registered toolsets"""
    return toolset_registry.get_all()
