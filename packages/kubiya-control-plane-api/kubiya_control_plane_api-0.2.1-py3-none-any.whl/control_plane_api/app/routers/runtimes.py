"""Runtime types endpoint for agent execution frameworks"""
from fastapi import APIRouter
from pydantic import BaseModel, Field
from typing import List

router = APIRouter()


class RuntimeInfo(BaseModel):
    """Information about an agent runtime"""
    id: str = Field(..., description="Runtime identifier")
    name: str = Field(..., description="Display name")
    description: str = Field(..., description="Description of the runtime")
    icon: str = Field(..., description="Icon identifier for UI")
    features: List[str] = Field(..., description="Key features of this runtime")
    status: str = Field(..., description="Status: available, beta, coming_soon")


@router.get("/runtimes", response_model=List[RuntimeInfo], tags=["Runtimes"])
def list_runtimes():
    """
    List available agent runtime types.

    Returns information about different agent execution frameworks
    that can be used when creating or configuring agents.
    """
    return [
        RuntimeInfo(
            id="default",
            name="Agno Runtime",
            description="Production-ready agent framework with advanced reasoning and tool execution capabilities. Best for complex workflows and multi-step tasks.",
            icon="agno",
            features=[
                "Advanced reasoning capabilities",
                "Multi-step task execution",
                "Built-in tool integration",
                "Session management",
                "Production-tested reliability"
            ],
            status="available"
        ),
        RuntimeInfo(
            id="claude_code",
            name="Claude Code SDK",
            description="Specialized runtime for code generation and software development tasks. Optimized for writing, reviewing, and refactoring code.",
            icon="code",
            features=[
                "Code-first design",
                "Advanced code generation",
                "Built-in code review",
                "Repository awareness",
                "Development workflow optimization"
            ],
            status="beta"
        )
    ]
