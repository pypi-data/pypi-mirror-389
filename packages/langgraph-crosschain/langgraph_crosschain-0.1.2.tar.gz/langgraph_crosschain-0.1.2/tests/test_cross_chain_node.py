"""Tests for CrossChainNode."""

import pytest

from langgraph_crosschain.communication.message_router import MessageRouter
from langgraph_crosschain.core.chain_registry import ChainRegistry
from langgraph_crosschain.core.cross_chain_node import CrossChainMessage, CrossChainNode


class TestCrossChainMessage:
    """Test suite for CrossChainMessage."""

    def test_create_message(self):
        """Test creating a cross-chain message."""
        message = CrossChainMessage(
            source_chain="chain1",
            source_node="node1",
            target_chain="chain2",
            target_node="node2",
            payload={"data": "test"},
        )

        assert message.source_chain == "chain1"
        assert message.source_node == "node1"
        assert message.target_chain == "chain2"
        assert message.target_node == "node2"
        assert message.payload == {"data": "test"}
        assert message.metadata is None

    def test_create_message_with_metadata(self):
        """Test creating a message with metadata."""
        message = CrossChainMessage(
            source_chain="chain1",
            source_node="node1",
            target_chain="chain2",
            target_node="node2",
            payload={"data": "test"},
            metadata={"priority": "high"},
        )

        assert message.metadata == {"priority": "high"}

    def test_message_serialization(self):
        """Test that messages can be serialized to dict."""
        message = CrossChainMessage(
            source_chain="chain1",
            source_node="node1",
            target_chain="chain2",
            target_node="node2",
            payload={"data": "test"},
        )

        message_dict = message.model_dump()
        assert message_dict["source_chain"] == "chain1"
        assert message_dict["target_chain"] == "chain2"
        assert message_dict["payload"] == {"data": "test"}


class TestCrossChainNode:
    """Test suite for CrossChainNode."""

    def setup_method(self):
        """Set up test fixtures."""
        # Clear registry and router
        registry = ChainRegistry()
        registry.clear()
        router = MessageRouter()
        router.clear_queues()

        # Register mock chains
        registry.register("chain1", "mock_chain1")
        registry.register("chain2", "mock_chain2")

    def test_create_node(self):
        """Test creating a cross-chain node."""

        def test_func(state):
            return state

        node = CrossChainNode(
            chain_id="chain1",
            node_id="node1",
            func=test_func,
        )

        assert node.chain_id == "chain1"
        assert node.node_id == "node1"
        assert node.func == test_func

    def test_node_execution(self):
        """Test executing a node function."""

        def test_func(state):
            state["processed"] = True
            return state

        node = CrossChainNode(
            chain_id="chain1",
            node_id="node1",
            func=test_func,
        )

        state = {"data": "test"}
        result = node(state)

        assert result["processed"] is True
        assert result["data"] == "test"

    def test_full_id_property(self):
        """Test the full_id property."""

        def test_func(state):
            return state

        node = CrossChainNode(
            chain_id="chain1",
            node_id="node1",
            func=test_func,
        )

        assert node.full_id == "chain1.node1"

    def test_call_remote(self):
        """Test calling a remote node."""

        def test_func(state):
            return state

        node = CrossChainNode(
            chain_id="chain1",
            node_id="node1",
            func=test_func,
        )

        # Call remote without waiting for response
        result = node.call_remote(
            target_chain="chain2",
            target_node="node2",
            payload={"data": "test"},
            wait_for_response=False,
        )

        assert result is None

        # Verify message was queued
        router = MessageRouter()
        messages = router.get_messages_for("chain2", "node2")
        assert len(messages) == 1
        assert messages[0].payload == {"data": "test"}

    def test_call_remote_to_nonexistent_chain_raises_error(self):
        """Test that calling a nonexistent chain raises KeyError."""

        def test_func(state):
            return state

        node = CrossChainNode(
            chain_id="chain1",
            node_id="node1",
            func=test_func,
        )

        with pytest.raises(KeyError, match="not found"):
            node.call_remote(
                target_chain="nonexistent",
                target_node="node2",
                payload={"data": "test"},
            )

    def test_call_remote_with_response(self):
        """Test calling a remote node and waiting for response."""

        def test_func(state):
            return state

        node = CrossChainNode(
            chain_id="chain1",
            node_id="node1",
            func=test_func,
        )

        # Send response before calling
        router = MessageRouter()
        router.send_response("chain1", "node1", {"result": "success"})

        # This will timeout if no response, but we pre-populated the response
        result = node.call_remote(
            target_chain="chain2",
            target_node="node2",
            payload={"data": "test"},
            wait_for_response=True,
            timeout=0.1,
        )

        assert result == {"result": "success"}

    def test_call_remote_timeout(self):
        """Test that waiting for response times out correctly."""

        def test_func(state):
            return state

        node = CrossChainNode(
            chain_id="chain1",
            node_id="node1",
            func=test_func,
        )

        with pytest.raises(TimeoutError, match="Timeout"):
            node.call_remote(
                target_chain="chain2",
                target_node="node2",
                payload={"data": "test"},
                wait_for_response=True,
                timeout=0.1,
            )

    def test_broadcast(self):
        """Test broadcasting to multiple chains."""

        def test_func(state):
            return state

        # Register additional chains
        registry = ChainRegistry()
        registry.register("chain3", "mock_chain3")

        node = CrossChainNode(
            chain_id="chain1",
            node_id="node1",
            func=test_func,
        )

        node.broadcast(
            target_chains=["chain2", "chain3"],
            target_node="receiver",
            payload={"broadcast": "data"},
        )

        # Verify messages were sent to all chains
        router = MessageRouter()
        messages_chain2 = router.get_messages_for("chain2", "receiver")
        messages_chain3 = router.get_messages_for("chain3", "receiver")

        assert len(messages_chain2) == 1
        assert len(messages_chain3) == 1
        assert messages_chain2[0].payload == {"broadcast": "data"}
        assert messages_chain3[0].payload == {"broadcast": "data"}

    def test_process_incoming_messages(self):
        """Test processing incoming cross-chain messages."""

        def test_func(state):
            return state

        node = CrossChainNode(
            chain_id="chain1",
            node_id="node1",
            func=test_func,
        )

        # Send a message to this node
        router = MessageRouter()
        message = CrossChainMessage(
            source_chain="chain2",
            source_node="node2",
            target_chain="chain1",
            target_node="node1",
            payload={"incoming": "data"},
        )
        router.route_message(message)

        # Execute the node
        state = {"existing": "data"}
        result = node(state)

        # Check that incoming messages were added to state
        assert "cross_chain_messages" in result
        assert len(result["cross_chain_messages"]) == 1
        assert result["cross_chain_messages"][0]["payload"] == {"incoming": "data"}

    def test_node_with_custom_registry_and_router(self):
        """Test creating a node with custom registry and router."""
        custom_registry = ChainRegistry()
        custom_router = MessageRouter()

        def test_func(state):
            return state

        node = CrossChainNode(
            chain_id="chain1",
            node_id="node1",
            func=test_func,
            registry=custom_registry,
            router=custom_router,
        )

        assert node.registry is custom_registry
        assert node.router is custom_router
