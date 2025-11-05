"""Pytest configuration and fixtures."""

import pytest

from langgraph_crosschain.communication.message_router import MessageRouter
from langgraph_crosschain.core.chain_registry import ChainRegistry
from langgraph_crosschain.state.shared_state import SharedStateManager


@pytest.fixture(autouse=True)
def reset_singletons():
    """Reset all singletons before each test."""
    registry = ChainRegistry()
    registry.clear()

    router = MessageRouter()
    router.clear_queues()

    manager = SharedStateManager()
    manager.clear()

    yield

    # Clean up after test
    registry.clear()
    router.clear_queues()
    manager.clear()
