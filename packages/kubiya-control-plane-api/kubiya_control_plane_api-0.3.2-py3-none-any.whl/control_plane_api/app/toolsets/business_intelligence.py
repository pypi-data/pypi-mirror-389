"""
Business Intelligence Toolset

Provides comprehensive BI capabilities including database querying, analytics,
visualization generation, and multi-agent analysis. Supports PostgreSQL, MySQL,
MongoDB, and file-based data sources (CSV, JSON, Parquet, Excel).
"""
from typing import Dict, Any, List
from .base import ToolSetDefinition, ToolSetType, ToolSetCategory, ToolSetVariant
from .registry import register_toolset


class BusinessIntelligenceToolSet(ToolSetDefinition):
    """Business Intelligence and Analytics toolset"""

    @property
    def type(self) -> ToolSetType:
        return ToolSetType.BUSINESS_INTELLIGENCE

    @property
    def name(self) -> str:
        return "Business Intelligence"

    @property
    def description(self) -> str:
        return "Advanced BI and analytics with multi-agent analysis, database querying, and interactive visualizations"

    @property
    def icon(self) -> str:
        return "BarChart"

    def get_variants(self) -> List[ToolSetVariant]:
        return [
            ToolSetVariant(
                id="bi_full",
                name="Full BI Suite",
                description="Complete BI capabilities with all data sources and analytics features",
                category=ToolSetCategory.ADVANCED,
                badge="Recommended",
                icon="BarChart",
                configuration={
                    "data_sources": [
                        {
                            "id": "default_postgres",
                            "name": "PostgreSQL Database",
                            "type": "postgresql",
                            "connection": {
                                "host": "${POSTGRES_HOST}",
                                "port": "${POSTGRES_PORT:5432}",
                                "database": "${POSTGRES_DB}",
                                "username": "${POSTGRES_USER}",
                                "password": "${POSTGRES_PASSWORD}",
                                "ssl": True,
                                "pool_size": 5
                            },
                            "query_limits": {
                                "max_rows": 10000,
                                "timeout_seconds": 30
                            }
                        }
                    ],
                    "security": {
                        "allowed_sql_commands": ["SELECT"],
                        "deny_patterns": ["DROP", "DELETE", "TRUNCATE", "ALTER", "INSERT", "UPDATE"]
                    },
                    "features": {
                        "enable_multi_agent": True,
                        "enable_visualizations": True,
                        "enable_schema_introspection": True,
                        "enable_query_validation": True
                    }
                },
                is_default=True,
            ),
            ToolSetVariant(
                id="bi_read_only",
                name="Read-Only BI",
                description="Safe, read-only analytics with SELECT-only permissions",
                category=ToolSetCategory.COMMON,
                badge="Safe",
                icon="Eye",
                configuration={
                    "data_sources": [],  # Configured per agent
                    "security": {
                        "allowed_sql_commands": ["SELECT"],
                        "deny_patterns": ["DROP", "DELETE", "TRUNCATE", "ALTER", "INSERT", "UPDATE", "CREATE"]
                    },
                    "features": {
                        "enable_multi_agent": True,
                        "enable_visualizations": True,
                        "enable_schema_introspection": True,
                        "enable_query_validation": True
                    }
                },
                is_default=False,
            ),
            ToolSetVariant(
                id="bi_file_analysis",
                name="File Analysis",
                description="Analyze CSV, JSON, Parquet, and Excel files without database access",
                category=ToolSetCategory.COMMON,
                badge="Simple",
                icon="FileSpreadsheet",
                configuration={
                    "data_sources": [],
                    "security": {
                        "allowed_sql_commands": ["SELECT"],
                        "deny_patterns": []
                    },
                    "features": {
                        "enable_multi_agent": True,
                        "enable_visualizations": True,
                        "enable_schema_introspection": True,
                        "enable_query_validation": False,
                        "supported_formats": ["csv", "json", "parquet", "excel"]
                    }
                },
                is_default=False,
            ),
            ToolSetVariant(
                id="bi_custom",
                name="Custom BI Configuration",
                description="Fully customizable BI setup with user-defined data sources and security policies",
                category=ToolSetCategory.ADVANCED,
                badge="Flexible",
                icon="Settings",
                configuration={
                    "data_sources": [],
                    "security": {
                        "allowed_sql_commands": ["SELECT"],
                        "deny_patterns": []
                    },
                    "features": {
                        "enable_multi_agent": True,
                        "enable_visualizations": True,
                        "enable_schema_introspection": True,
                        "enable_query_validation": True
                    }
                },
                is_default=False,
            ),
        ]

    def validate_configuration(self, config: Dict[str, Any]) -> bool:
        """Validate BI toolset configuration"""
        required_keys = ["data_sources", "security", "features"]

        # Check required top-level keys
        for key in required_keys:
            if key not in config:
                return False

        # Validate security config
        if "security" in config:
            security = config["security"]
            if "allowed_sql_commands" not in security:
                return False
            if not isinstance(security["allowed_sql_commands"], list):
                return False

        # Validate data sources
        if "data_sources" in config:
            for ds in config["data_sources"]:
                if "id" not in ds or "type" not in ds:
                    return False
                if "connection" not in ds:
                    return False

        return True

    def get_default_configuration(self) -> Dict[str, Any]:
        """Get default configuration for BI toolset"""
        return {
            "data_sources": [],
            "security": {
                "allowed_sql_commands": ["SELECT"],
                "deny_patterns": ["DROP", "DELETE", "TRUNCATE", "ALTER", "INSERT", "UPDATE"]
            },
            "features": {
                "enable_multi_agent": True,
                "enable_visualizations": True,
                "enable_schema_introspection": True,
                "enable_query_validation": True
            }
        }


# Register the toolset
register_toolset(BusinessIntelligenceToolSet())
