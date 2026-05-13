"""
core/orchestrator.py
Central dispatch layer — receives incoming requests and routes them
to the appropriate agent based on task type and provider availability.
"""

import logging
from enum import Enum
from typing import AsyncIterator

logger = logging.getLogger(__name__)


class TaskType(str, Enum):
    AUTOMATION = "automation"
    ASSISTANT = "assistant"
    RELIABILITY = "reliability"
    DEFAULT = "default"


def classify_task(user_input: str) -> TaskType:
    """
    Simple keyword-based task classifier.
    Replace with an LLM-based classifier for production.
    """
    text = user_input.lower()
    if any(k in text for k in ["schedule", "automate", "run", "execute", "task"]):
        return TaskType.AUTOMATION
    if any(k in text for k in ["check", "test", "ping", "status", "health"]):
        return TaskType.RELIABILITY
    return TaskType.ASSISTANT


async def dispatch(user_input: str, streaming: bool = False) -> str | AsyncIterator[str]:
    """
    Main entry point for all incoming requests.
    Classifies the task, selects the right agent, and returns the response.
    """
    task_type = classify_task(user_input)
    logger.info(f"[Orchestrator] Dispatching task type: {task_type}")

    if task_type == TaskType.AUTOMATION:
        from agents.task_agent import run as run_task
        return await run_task(user_input, streaming=streaming)

    elif task_type == TaskType.RELIABILITY:
        from agents.reliability_agent import run as run_reliability
        return await run_reliability(user_input)

    else:
        # Default: personal assistant via provider router
        from core.provider_router import route_request
        return await route_request(user_input, task_type=task_type.value)
