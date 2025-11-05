"""Tests for MessageRouter."""

import pytest

from langgraph_crosschain.communication.message_router import MessageRouter
from langgraph_crosschain.core.chain_registry import ChainRegistry
from langgraph_crosschain.core.cross_chain_node import CrossChainMessage


class TestMessageRouter:
    """Test suite for MessageRouter."""

    def setup_method(self):
        """Set up test fixtures."""
        # Clear router and registry before each test
        router = MessageRouter()
        router.clear_queues()

        registry = ChainRegistry()
        registry.clear()

        # Register mock chains
        registry.register("chain1", "mock_chain1")
        registry.register("chain2", "mock_chain2")

    def test_singleton_pattern(self):
        """Test that MessageRouter implements singleton pattern."""
        router1 = MessageRouter()
        router2 = MessageRouter()
        assert router1 is router2

    def test_route_message(self):
        """Test routing a message."""
        router = MessageRouter()

        message = CrossChainMessage(
            source_chain="chain1",
            source_node="node1",
            target_chain="chain2",
            target_node="node2",
            payload={"data": "test"},
        )

        # Should not raise an error
        router.route_message(message)

    def test_route_to_nonexistent_chain_raises_error(self):
        """Test that routing to a nonexistent chain raises KeyError."""
        router = MessageRouter()

        message = CrossChainMessage(
            source_chain="chain1",
            source_node="node1",
            target_chain="nonexistent",
            target_node="node2",
            payload={"data": "test"},
        )

        with pytest.raises(KeyError, match="not found"):
            router.route_message(message)

    def test_get_messages_for_node(self):
        """Test getting messages for a specific node."""
        router = MessageRouter()

        message = CrossChainMessage(
            source_chain="chain1",
            source_node="node1",
            target_chain="chain2",
            target_node="node2",
            payload={"data": "test"},
        )

        router.route_message(message)

        messages = router.get_messages_for("chain2", "node2")
        assert len(messages) == 1
        assert messages[0].payload == {"data": "test"}

    def test_get_messages_returns_empty_for_no_messages(self):
        """Test that getting messages returns empty list when there are none."""
        router = MessageRouter()

        messages = router.get_messages_for("chain2", "node2")
        assert messages == []

    def test_send_response(self):
        """Test sending a response."""
        router = MessageRouter()

        router.send_response("chain1", "node1", {"result": "success"})

        # Response should be queued (we can't easily test retrieval without async)

    def test_clear_queues_all(self):
        """Test clearing all queues."""
        router = MessageRouter()

        message = CrossChainMessage(
            source_chain="chain1",
            source_node="node1",
            target_chain="chain2",
            target_node="node2",
            payload={"data": "test"},
        )

        router.route_message(message)
        router.clear_queues()

        messages = router.get_messages_for("chain2", "node2")
        assert messages == []

    def test_clear_queues_specific_chain(self):
        """Test clearing queues for a specific chain."""
        router = MessageRouter()

        message1 = CrossChainMessage(
            source_chain="chain1",
            source_node="node1",
            target_chain="chain2",
            target_node="node2",
            payload={"data": "test1"},
        )

        message2 = CrossChainMessage(
            source_chain="chain1",
            source_node="node1",
            target_chain="chain1",
            target_node="node3",
            payload={"data": "test2"},
        )

        router.route_message(message1)
        router.route_message(message2)

        router.clear_queues("chain2")

        messages_chain2 = router.get_messages_for("chain2", "node2")
        messages_chain1 = router.get_messages_for("chain1", "node3")

        assert messages_chain2 == []
        assert len(messages_chain1) == 1

    def test_route_alias(self):
        """Test that route() is an alias for route_message()."""
        router = MessageRouter()

        message = CrossChainMessage(
            source_chain="chain1",
            source_node="node1",
            target_chain="chain2",
            target_node="node2",
            payload={"data": "test"},
        )

        # route() should work the same as route_message()
        result = router.route(message)
        assert result is None  # No response expected

        # Verify message was routed
        messages = router.get_messages_for("chain2", "node2")
        assert len(messages) == 1
        assert messages[0].payload == {"data": "test"}

    def test_route_alias_with_params(self):
        """Test route() alias with wait_for_response and timeout parameters."""
        router = MessageRouter()

        message = CrossChainMessage(
            source_chain="chain1",
            source_node="node1",
            target_chain="chain2",
            target_node="node2",
            payload={"data": "test"},
        )

        # Test with parameters (should timeout)
        with pytest.raises(TimeoutError):
            router.route(message, wait_for_response=True, timeout=0.1)
