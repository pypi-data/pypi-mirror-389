#!/usr/bin/env python3
"""
Temporal Worker for Agent Control Plane.

This worker runs workflows and activities for agent execution.
"""

import asyncio
import structlog
from temporalio.worker import Worker

from control_plane_api.app.lib.temporal_client import get_temporal_client
from control_plane_api.app.config import settings

# Import workflows
from control_plane_api.app.workflows.agent_execution import AgentExecutionWorkflow
from control_plane_api.app.workflows.team_execution import TeamExecutionWorkflow

# Import activities
from control_plane_api.app.activities.agent_activities import (
    execute_agent_llm,
    update_execution_status,
    update_agent_status,
)
from control_plane_api.app.activities.team_activities import (
    get_team_agents,
    execute_team_coordination,
)

logger = structlog.get_logger()


async def run_worker():
    """Run the Temporal worker"""
    try:
        logger.info(
            "temporal_worker_starting",
            host=settings.TEMPORAL_HOST,
            namespace=settings.TEMPORAL_NAMESPACE,
        )

        # Connect to Temporal
        client = await get_temporal_client()

        # Create worker
        worker = Worker(
            client,
            task_queue="default",
            workflows=[
                AgentExecutionWorkflow,
                TeamExecutionWorkflow,
            ],
            activities=[
                # Agent activities
                execute_agent_llm,
                update_execution_status,
                update_agent_status,
                # Team activities
                get_team_agents,
                execute_team_coordination,
            ],
        )

        logger.info("temporal_worker_running")
        
        # Run the worker
        await worker.run()

    except Exception as e:
        logger.error("temporal_worker_failed", error=str(e))
        raise


def main():
    """Main entry point for the worker"""
    asyncio.run(run_worker())


if __name__ == "__main__":
    main()
