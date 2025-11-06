"""
Toolsets Module

This module manages all available toolsets (OS-level capabilities) that can be
assigned to agents and teams. Each toolset corresponds to a capability that agents
can use during execution (file system, shell, Docker, Python, etc.).

Toolsets are defined as Python classes that provide:
- Metadata (name, description, icon)
- Default configuration
- Validation logic
- Instantiation logic for the underlying framework
"""

from .base import ToolSetDefinition, ToolSetType, ToolSetCategory
from .registry import toolset_registry, get_toolset, get_all_toolsets, register_toolset

# Import all toolset definitions to auto-register them
from .file_system import FileSystemToolSet
from .shell import ShellToolSet
from .docker import DockerToolSet
from .python import PythonToolSet
from .file_generation import FileGenerationToolSet
from .data_visualization import DataVisualizationToolSet

__all__ = [
    "ToolSetDefinition",
    "ToolSetType",
    "ToolSetCategory",
    "toolset_registry",
    "get_toolset",
    "get_all_toolsets",
    "register_toolset",
    "FileSystemToolSet",
    "ShellToolSet",
    "DockerToolSet",
    "PythonToolSet",
    "FileGenerationToolSet",
    "DataVisualizationToolSet",
]
