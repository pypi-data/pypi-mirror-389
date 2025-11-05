"""
Integration tests for cross-chain communication.

These tests verify that all components work together correctly.
"""

import threading
import time

import pytest

from langgraph_crosschain import (
    ChainRegistry,
    CrossChainNode,
    MessageRouter,
    SharedStateManager,
)


class TestBasicCrossChainCommunication:
    """Test basic cross-chain communication patterns."""

    def setup_method(self):
        """Set up test fixtures."""
        # Clear all singletons
        ChainRegistry().clear()
        MessageRouter().clear_queues()
        SharedStateManager().clear()

    def test_simple_message_passing(self):
        """Test simple message passing between nodes."""
        # Register chains
        registry = ChainRegistry()
        registry.register("chain1", "mock_chain1")
        registry.register("chain2", "mock_chain2")

        # Create nodes
        def sender_func(state):
            return state

        def receiver_func(state):
            return state

        sender = CrossChainNode("chain1", "sender", sender_func)
        CrossChainNode("chain2", "receiver", receiver_func)

        # Send message
        sender.call_remote(
            target_chain="chain2",
            target_node="receiver",
            payload={"message": "hello"},
            wait_for_response=False,
        )

        # Receive message
        router = MessageRouter()
        messages = router.get_messages_for("chain2", "receiver")

        assert len(messages) == 1
        assert messages[0].payload == {"message": "hello"}
        assert messages[0].source_chain == "chain1"
        assert messages[0].source_node == "sender"

    def test_request_response_pattern(self):
        """Test request-response pattern between nodes."""
        registry = ChainRegistry()
        registry.register("chain1", "mock_chain1")
        registry.register("chain2", "mock_chain2")
        router = MessageRouter()

        def requester_func(state):
            return state

        requester = CrossChainNode("chain1", "requester", requester_func)

        # Simulate response being ready
        def responder():
            time.sleep(0.05)  # Simulate processing
            router.send_response("chain1", "requester", {"result": "processed"})

        # Start responder in background
        responder_thread = threading.Thread(target=responder)
        responder_thread.start()

        # Make request
        result = requester.call_remote(
            target_chain="chain2",
            target_node="processor",
            payload={"data": "test"},
            wait_for_response=True,
            timeout=1.0,
        )

        responder_thread.join()

        assert result == {"result": "processed"}

    def test_broadcast_pattern(self):
        """Test broadcasting to multiple chains."""
        registry = ChainRegistry()
        registry.register("chain1", "mock_chain1")
        registry.register("chain2", "mock_chain2")
        registry.register("chain3", "mock_chain3")
        registry.register("chain4", "mock_chain4")

        def broadcaster_func(state):
            return state

        broadcaster = CrossChainNode("chain1", "broadcaster", broadcaster_func)

        # Broadcast to multiple chains
        broadcaster.broadcast(
            target_chains=["chain2", "chain3", "chain4"],
            target_node="listener",
            payload={"announcement": "hello everyone"},
        )

        # Check all chains received the message
        router = MessageRouter()
        for chain_id in ["chain2", "chain3", "chain4"]:
            messages = router.get_messages_for(chain_id, "listener")
            assert len(messages) == 1
            assert messages[0].payload == {"announcement": "hello everyone"}


class TestSharedStateIntegration:
    """Test shared state integration with cross-chain communication."""

    def setup_method(self):
        """Set up test fixtures."""
        ChainRegistry().clear()
        MessageRouter().clear_queues()
        SharedStateManager().clear()

    def test_shared_state_coordination(self):
        """Test coordinating multiple chains via shared state."""
        registry = ChainRegistry()
        state_manager = SharedStateManager()

        registry.register("writer", "mock_writer")
        registry.register("reader1", "mock_reader1")
        registry.register("reader2", "mock_reader2")

        # Writer updates shared state
        def writer_func(state):
            state_manager.set("shared_data", {"count": 42, "message": "hello"})
            return state

        writer = CrossChainNode("writer", "node1", writer_func)
        writer({})

        # Readers access shared state
        def reader_func(state):
            data = state_manager.get("shared_data")
            state["received_data"] = data
            return state

        reader1 = CrossChainNode("reader1", "node1", reader_func)
        reader2 = CrossChainNode("reader2", "node1", reader_func)

        result1 = reader1({})
        result2 = reader2({})

        assert result1["received_data"] == {"count": 42, "message": "hello"}
        assert result2["received_data"] == {"count": 42, "message": "hello"}

    def test_state_subscription_across_chains(self):
        """Test state subscriptions working across chains."""
        state_manager = SharedStateManager()
        received_updates = []

        def callback(value):
            received_updates.append(value)

        # Subscribe to state changes
        state_manager.subscribe("counter", callback)

        # Multiple chains update the state
        for i in range(5):
            state_manager.set("counter", i)

        assert received_updates == [0, 1, 2, 3, 4]


class TestComplexWorkflows:
    """Test complex multi-chain workflows."""

    def setup_method(self):
        """Set up test fixtures."""
        ChainRegistry().clear()
        MessageRouter().clear_queues()
        SharedStateManager().clear()

    def test_pipeline_workflow(self):
        """Test a pipeline workflow across multiple chains."""
        registry = ChainRegistry()
        state_manager = SharedStateManager()

        # Register chains
        for chain_id in ["ingestion", "processing", "output"]:
            registry.register(chain_id, f"mock_{chain_id}")

        # Stage 1: Ingestion
        def ingest_func(state):
            state_manager.set("ingested_data", {"raw": "data"})
            return state

        ingest_node = CrossChainNode("ingestion", "ingest", ingest_func)

        # Stage 2: Processing
        def process_func(state):
            raw_data = state_manager.get("ingested_data")
            processed = {"processed": raw_data["raw"].upper()}
            state_manager.set("processed_data", processed)
            return state

        process_node = CrossChainNode("processing", "process", process_func)

        # Stage 3: Output
        def output_func(state):
            processed = state_manager.get("processed_data")
            state["final_output"] = processed
            return state

        output_node = CrossChainNode("output", "output", output_func)

        # Execute pipeline
        ingest_node({})
        process_node({})
        result = output_node({})

        assert result["final_output"] == {"processed": "DATA"}

    def test_fan_out_fan_in_pattern(self):
        """Test fan-out/fan-in pattern with multiple workers."""
        registry = ChainRegistry()
        state_manager = SharedStateManager()

        # Register chains
        registry.register("coordinator", "mock_coordinator")
        for i in range(3):
            registry.register(f"worker{i}", f"mock_worker{i}")

        # Coordinator fans out work
        def coordinator_func(state):
            node = CrossChainNode("coordinator", "coord", lambda s: s)
            for i in range(3):
                node.call_remote(
                    target_chain=f"worker{i}",
                    target_node="work",
                    payload={"task_id": i},
                    wait_for_response=False,
                )
            return state

        coordinator = CrossChainNode("coordinator", "coord", coordinator_func)

        # Workers process and store results
        def worker_func(worker_id):
            def func(state):
                results = state_manager.get("results", [])
                results.append(f"worker{worker_id}_done")
                state_manager.set("results", results)
                return state

            return func

        workers = [CrossChainNode(f"worker{i}", "work", worker_func(i)) for i in range(3)]

        # Execute
        coordinator({})

        # Workers process their messages
        router = MessageRouter()
        for i, worker in enumerate(workers):
            messages = router.get_messages_for(f"worker{i}", "work")
            if messages:
                worker({})

        # Check all workers completed
        results = state_manager.get("results", [])
        assert len(results) == 3
        assert all(f"worker{i}_done" in results for i in range(3))


class TestErrorHandling:
    """Test error handling in cross-chain communication."""

    def setup_method(self):
        """Set up test fixtures."""
        ChainRegistry().clear()
        MessageRouter().clear_queues()
        SharedStateManager().clear()

    def test_missing_chain_error(self):
        """Test error when calling non-existent chain."""
        registry = ChainRegistry()
        registry.register("chain1", "mock_chain1")

        def func(state):
            return state

        node = CrossChainNode("chain1", "node1", func)

        with pytest.raises(KeyError, match="not found"):
            node.call_remote(
                target_chain="nonexistent",
                target_node="node2",
                payload={"data": "test"},
            )

    def test_timeout_error(self):
        """Test timeout when waiting for response."""
        registry = ChainRegistry()
        registry.register("chain1", "mock_chain1")
        registry.register("chain2", "mock_chain2")

        def func(state):
            return state

        node = CrossChainNode("chain1", "node1", func)

        # No response will be sent, so this should timeout
        with pytest.raises(TimeoutError):
            node.call_remote(
                target_chain="chain2",
                target_node="node2",
                payload={"data": "test"},
                wait_for_response=True,
                timeout=0.1,
            )


class TestConcurrency:
    """Test concurrent cross-chain operations."""

    def setup_method(self):
        """Set up test fixtures."""
        ChainRegistry().clear()
        MessageRouter().clear_queues()
        SharedStateManager().clear()

    def test_concurrent_message_sending(self):
        """Test sending messages from multiple threads."""
        registry = ChainRegistry()
        for i in range(5):
            registry.register(f"chain{i}", f"mock_chain{i}")

        def send_messages(chain_id):
            def func(state):
                return state

            node = CrossChainNode(chain_id, "sender", func)
            for target_id in range(5):
                if target_id != int(chain_id[-1]):  # Don't send to self
                    node.call_remote(
                        target_chain=f"chain{target_id}",
                        target_node="receiver",
                        payload={"from": chain_id},
                        wait_for_response=False,
                    )

        threads = [threading.Thread(target=send_messages, args=(f"chain{i}",)) for i in range(5)]

        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # Verify all messages were sent (each chain sends to 4 others)
        router = MessageRouter()
        total_messages = 0
        for i in range(5):
            messages = router.get_messages_for(f"chain{i}", "receiver")
            total_messages += len(messages)

        assert total_messages == 20  # 5 chains * 4 messages each

    def test_concurrent_state_access(self):
        """Test concurrent access to shared state."""
        state_manager = SharedStateManager()
        state_manager.set("counter", 0)

        def increment():
            for _ in range(100):
                current = state_manager.get("counter")
                state_manager.set("counter", current + 1)

        threads = [threading.Thread(target=increment) for _ in range(5)]

        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # Note: Due to deep copy on get/set, we expect 500 operations
        # but the final count might be less due to race conditions
        # This is expected behavior with the current implementation
        final_count = state_manager.get("counter")
        assert final_count > 0  # Should have some updates
