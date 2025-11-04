# Toolsets Architecture

## Overview

Toolsets are OS-level capabilities (file system, shell, Docker, Python, etc.) that can be assigned to agents and teams. Each toolset is defined as a Python class that provides metadata, configuration, and validation logic.

## Architecture

```
app/toolsets/
├── __init__.py          # Module exports
├── base.py              # Base classes and types
├── registry.py          # Central registry
├── file_system.py       # File system toolset
├── shell.py             # Shell toolset
├── docker.py            # Docker toolset
├── python.py            # Python toolset
├── file_generation.py   # File generation toolset
└── README.md            # This file
```

## Key Concepts

### Toolset Definition

Each toolset is a subclass of `ToolSetDefinition` that defines:
- **Type**: Unique identifier (e.g., `file_system`, `shell`)
- **Metadata**: Name, description, icon
- **Variants**: Predefined configurations (e.g., "Read Only", "Full Access")
- **Validation**: Configuration validation logic
- **Framework Mapping**: Maps to underlying tool class for instantiation

### Variants

Variants are predefined configurations for a toolset. For example, the File System toolset has:
- **File System - Read Only**: Safe, read-only access
- **File System - Full Access**: Complete read/write access (Recommended)
- **File System - Sandboxed**: Restricted to `/sandbox` directory (Secure)

### Categories

Toolsets are organized into categories:
- **Common**: Frequently used, safe defaults
- **Advanced**: Advanced features, require more privileges
- **Security**: Security-focused, restricted access
- **Custom**: User-defined custom toolsets

## Adding a New Toolset

### 1. Create Toolset Definition

Create a new file in `app/toolsets/` (e.g., `kubernetes.py`):

```python
from typing import Dict, Any, List
from .base import ToolSetDefinition, ToolSetType, ToolSetCategory, ToolSetVariant
from .registry import register_toolset


class KubernetesToolSet(ToolSetDefinition):
    """Kubernetes management toolset"""

    @property
    def type(self) -> ToolSetType:
        # Add to ToolSetType enum in base.py first!
        return ToolSetType.KUBERNETES

    @property
    def name(self) -> str:
        return "Kubernetes"

    @property
    def description(self) -> str:
        return "Manage Kubernetes clusters and resources"

    @property
    def icon(self) -> str:
        return "SiKubernetes"

    @property
    def icon_type(self) -> str:
        return "react-icon"

    def get_variants(self) -> List[ToolSetVariant]:
        return [
            ToolSetVariant(
                id="k8s_read_only",
                name="Kubernetes - Read Only",
                description="Read-only access to cluster resources",
                category=ToolSetCategory.COMMON,
                badge="Safe",
                icon="SiKubernetes",
                configuration={
                    "enable_read": True,
                    "enable_write": False,
                },
                is_default=True,
            ),
            ToolSetVariant(
                id="k8s_full_access",
                name="Kubernetes - Full Access",
                description="Complete cluster management capabilities",
                category=ToolSetCategory.ADVANCED,
                badge="Advanced",
                icon="SiKubernetes",
                configuration={
                    "enable_read": True,
                    "enable_write": True,
                    "enable_delete": True,
                },
                is_default=False,
            ),
        ]

    def validate_configuration(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Validate Kubernetes configuration"""
        validated = {
            "enable_read": config.get("enable_read", True),
            "enable_write": config.get("enable_write", False),
            "enable_delete": config.get("enable_delete", False),
        }

        if "kubeconfig_path" in config:
            validated["kubeconfig_path"] = str(config["kubeconfig_path"])

        if "namespace" in config:
            validated["namespace"] = str(config["namespace"])

        return validated

    def get_default_configuration(self) -> Dict[str, Any]:
        """Default: read-only access"""
        return {
            "enable_read": True,
            "enable_write": False,
            "enable_delete": False,
        }


# Auto-register this toolset
register_toolset(KubernetesToolSet())
```

### 2. Add to Enum

Update `app/toolsets/base.py` to add the new type:

```python
class ToolSetType(str, Enum):
    FILE_SYSTEM = "file_system"
    SHELL = "shell"
    DOCKER = "docker"
    PYTHON = "python"
    FILE_GENERATION = "file_generation"
    KUBERNETES = "kubernetes"  # ADD THIS
    CUSTOM = "custom"
```

### 3. Import in __init__.py

Update `app/toolsets/__init__.py`:

```python
from .kubernetes import KubernetesToolSet

__all__ = [
    # ... existing exports
    "KubernetesToolSet",
]
```

### 4. Create Underlying Tool Class

If you're adding a new capability, create the tool class in the worker:

```python
# In worker or agno integration
from agno.tools import Toolkit

class KubernetesTools(Toolkit):
    def __init__(
        self,
        enable_read: bool = True,
        enable_write: bool = False,
        enable_delete: bool = False,
        kubeconfig_path: Optional[str] = None,
        namespace: Optional[str] = None,
    ):
        self.enable_read = enable_read
        self.enable_write = enable_write
        self.enable_delete = enable_delete
        # ... implementation
```

### 5. Update agno_service.py

Add the new tool class to the registry in `app/services/agno_service.py`:

```python
TOOLSET_REGISTRY = {
    "file_system": FileTools,
    "shell": ShellTools,
    "docker": DockerTools,
    "python": PythonTools,
    "file_generation": FileGenerationTools,
    "kubernetes": KubernetesTools,  # ADD THIS
}
```

## API Endpoints

### Get All Toolset Definitions
```bash
GET /api/v1/toolsets/definitions
```

Returns all available toolset types with their variants.

### Get Specific Toolset Definition
```bash
GET /api/v1/toolsets/definitions/{toolset_type}
```

Returns detailed information for a specific toolset type.

### Get Toolset Variants
```bash
GET /api/v1/toolsets/definitions/{toolset_type}/variants
```

Returns all predefined variants for a toolset type.

### Get All Templates (Flattened)
```bash
GET /api/v1/toolsets/templates
```

Returns all variants from all toolsets as a flat list of templates.

### Validate Configuration
```bash
POST /api/v1/toolsets/definitions/{toolset_type}/validate
{
  "enable_read": true,
  "enable_write": false
}
```

Validates a configuration for a toolset type.

## Benefits of This Architecture

1. **Easy to Extend**: Add new toolsets by creating a single file
2. **Type-Safe**: Pydantic models ensure configuration validity
3. **Self-Documenting**: Each toolset defines its own metadata
4. **Centralized Registry**: All toolsets auto-register on import
5. **Framework-Agnostic**: Not tied to any specific implementation
6. **Validation Built-In**: Each toolset validates its own configuration
7. **Variants System**: Predefined presets for common use cases
8. **Category Organization**: Organize by security level and use case

## Example Usage in UI

The UI can fetch templates and present them to users:

```typescript
// Fetch all templates
const response = await fetch('/api/v1/toolsets/templates');
const { templates } = await response.json();

// Display templates by category
const commonTemplates = templates.filter(t => t.category === 'common');
const advancedTemplates = templates.filter(t => t.category === 'advanced');
const securityTemplates = templates.filter(t => t.category === 'security');

// User selects a template, configuration is ready to use
const selectedTemplate = templates.find(t => t.id === 'file_system_full_access');
const config = selectedTemplate.configuration;
```

## Testing

To test the toolset system:

```python
from app.toolsets import get_all_toolsets, get_toolset, ToolSetType

# Get all registered toolsets
toolsets = get_all_toolsets()
print(f"Found {len(toolsets)} toolsets")

# Get a specific toolset
file_system = get_toolset(ToolSetType.FILE_SYSTEM)
print(f"File System toolset: {file_system.name}")
print(f"Variants: {[v.name for v in file_system.get_variants()]}")

# Validate configuration
config = {"enable_save_file": True, "base_dir": "/tmp"}
validated = file_system.validate_configuration(config)
print(f"Validated config: {validated}")
```
