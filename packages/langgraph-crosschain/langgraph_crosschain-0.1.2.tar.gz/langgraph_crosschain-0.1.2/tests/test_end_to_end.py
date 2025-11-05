"""
End-to-end tests simulating real-world usage scenarios.

These tests verify that the framework works correctly in realistic scenarios.
"""

from langgraph_crosschain import (
    ChainRegistry,
    CrossChainNode,
    MessageRouter,
    SharedStateManager,
)


class TestMultiAgentScenario:
    """Test a complete multi-agent scenario."""

    def setup_method(self):
        """Set up test fixtures."""
        ChainRegistry().clear()
        MessageRouter().clear_queues()
        SharedStateManager().clear()

    def test_research_analysis_execution_pipeline(self):
        """
        Test a complete pipeline with three agents:
        1. Research agent collects data
        2. Analysis agent processes data
        3. Execution agent acts on insights
        """
        registry = ChainRegistry()
        state_manager = SharedStateManager()

        # Register all chains
        registry.register("research", "research_chain")
        registry.register("analysis", "analysis_chain")
        registry.register("execution", "execution_chain")

        # Research Agent
        def research_func(state):
            # Simulate research
            research_data = {
                "topic": state.get("topic", "unknown"),
                "findings": ["finding1", "finding2", "finding3"],
            }
            state_manager.set("research_results", research_data)
            state["research_complete"] = True
            return state

        research_node = CrossChainNode("research", "researcher", research_func)

        # Analysis Agent
        def analysis_func(state):
            # Get research results
            research = state_manager.get("research_results")
            if research:
                # Analyze findings
                analysis = {
                    "topic": research["topic"],
                    "key_insights": [f"insight_{f}" for f in research["findings"]],
                    "recommendation": "proceed",
                }
                state_manager.set("analysis_results", analysis)
                state["analysis_complete"] = True
            return state

        analysis_node = CrossChainNode("analysis", "analyzer", analysis_func)

        # Execution Agent
        def execution_func(state):
            # Get analysis results
            analysis = state_manager.get("analysis_results")
            if analysis and analysis["recommendation"] == "proceed":
                # Execute action
                execution_result = {
                    "status": "success",
                    "actions_taken": ["action1", "action2"],
                    "topic": analysis["topic"],
                }
                state_manager.set("execution_results", execution_result)
                state["execution_complete"] = True
            return state

        execution_node = CrossChainNode("execution", "executor", execution_func)

        # Run the pipeline
        initial_state = {"topic": "AI agents"}

        # Step 1: Research
        state = research_node(initial_state)
        assert state["research_complete"]

        # Step 2: Analysis
        state = analysis_node(state)
        assert state["analysis_complete"]

        # Step 3: Execution
        state = execution_node(state)
        assert state["execution_complete"]

        # Verify final results
        execution_results = state_manager.get("execution_results")
        assert execution_results["status"] == "success"
        assert execution_results["topic"] == "AI agents"
        assert len(execution_results["actions_taken"]) == 2


class TestDistributedProcessing:
    """Test distributed processing across multiple workers."""

    def setup_method(self):
        """Set up test fixtures."""
        ChainRegistry().clear()
        MessageRouter().clear_queues()
        SharedStateManager().clear()

    def test_map_reduce_pattern(self):
        """Test a map-reduce pattern with multiple workers."""
        registry = ChainRegistry()
        state_manager = SharedStateManager()
        router = MessageRouter()

        # Register coordinator and workers
        registry.register("coordinator", "coordinator_chain")
        num_workers = 3
        for i in range(num_workers):
            registry.register(f"worker{i}", f"worker{i}_chain")

        # Coordinator distributes work
        def coordinator_func(state):
            data_to_process = [1, 2, 3, 4, 5, 6, 7, 8, 9]
            chunk_size = len(data_to_process) // num_workers

            node = CrossChainNode("coordinator", "distributor", lambda s: s)

            for i in range(num_workers):
                start_idx = i * chunk_size
                end_idx = start_idx + chunk_size if i < num_workers - 1 else None
                chunk = data_to_process[start_idx:end_idx]

                node.call_remote(
                    target_chain=f"worker{i}",
                    target_node="processor",
                    payload={"chunk": chunk, "worker_id": i},
                    wait_for_response=False,
                )

            state["distribution_complete"] = True
            return state

        coordinator = CrossChainNode("coordinator", "distributor", coordinator_func)

        # Worker processes data
        def worker_func(worker_id):
            def func(state):
                # Process incoming messages
                messages = state.get("cross_chain_messages", [])
                for msg in messages:
                    chunk = msg["payload"]["chunk"]
                    # Process: sum the numbers
                    result = sum(chunk)

                    # Store result in shared state
                    results = state_manager.get("worker_results", {})
                    results[f"worker{worker_id}"] = result
                    state_manager.set("worker_results", results)

                return state

            return func

        workers = [
            CrossChainNode(f"worker{i}", "processor", worker_func(i)) for i in range(num_workers)
        ]

        # Execute coordinator
        state = coordinator({})
        assert state["distribution_complete"]

        # Execute all workers
        for i, worker in enumerate(workers):
            messages = router.get_messages_for(f"worker{i}", "processor")
            if messages:
                # Convert CrossChainMessage objects to dicts as the node would
                worker_state = {"cross_chain_messages": [msg.model_dump() for msg in messages]}
                workers[i](worker_state)

        # Reduce: coordinator aggregates results
        def reduce_func(state):
            results = state_manager.get("worker_results", {})
            total = sum(results.values())
            state["final_result"] = total
            return state

        reducer = CrossChainNode("coordinator", "reducer", reduce_func)
        final_state = reducer({})

        # Verify result (sum of 1-9 is 45)
        assert final_state["final_result"] == 45


class TestEventDrivenArchitecture:
    """Test event-driven architecture using state subscriptions."""

    def setup_method(self):
        """Set up test fixtures."""
        ChainRegistry().clear()
        MessageRouter().clear_queues()
        SharedStateManager().clear()

    def test_event_driven_workflow(self):
        """Test event-driven workflow with state subscriptions."""
        registry = ChainRegistry()
        state_manager = SharedStateManager()

        # Register chains
        registry.register("publisher", "publisher_chain")
        registry.register("subscriber1", "subscriber1_chain")
        registry.register("subscriber2", "subscriber2_chain")

        # Track events
        events_received = {"sub1": [], "sub2": []}

        # Subscriber callbacks
        def subscriber1_callback(value):
            events_received["sub1"].append(value)

        def subscriber2_callback(value):
            events_received["sub2"].append(value)

        # Subscribe to events
        state_manager.subscribe("events", subscriber1_callback)
        state_manager.subscribe("events", subscriber2_callback)

        # Publisher publishes events
        def publisher_func(state):
            for i in range(3):
                state_manager.set("events", {"event_id": i, "data": f"event_{i}"})
            return state

        publisher = CrossChainNode("publisher", "event_publisher", publisher_func)

        # Publish events
        publisher({})

        # Verify all subscribers received all events
        assert len(events_received["sub1"]) == 3
        assert len(events_received["sub2"]) == 3
        assert events_received["sub1"][0]["event_id"] == 0
        assert events_received["sub2"][2]["event_id"] == 2


class TestComplexStateSharing:
    """Test complex state sharing scenarios."""

    def setup_method(self):
        """Set up test fixtures."""
        ChainRegistry().clear()
        MessageRouter().clear_queues()
        SharedStateManager().clear()

    def test_nested_state_updates(self):
        """Test updating nested state structures."""
        state_manager = SharedStateManager()

        # Initialize nested state
        initial_state = {
            "users": {"alice": {"score": 0}, "bob": {"score": 0}},
            "metadata": {"version": 1},
        }
        state_manager.set("app_state", initial_state)

        # Update using updater function
        def update_alice_score(current):
            if current:
                current["users"]["alice"]["score"] += 10
            return current

        state_manager.update("app_state", update_alice_score)

        # Verify update
        final_state = state_manager.get("app_state")
        assert final_state["users"]["alice"]["score"] == 10
        assert final_state["users"]["bob"]["score"] == 0

    def test_multiple_chains_collaborating_on_state(self):
        """Test multiple chains collaborating via shared state."""
        registry = ChainRegistry()
        state_manager = SharedStateManager()

        # Register chains
        for i in range(3):
            registry.register(f"chain{i}", f"chain{i}_mock")

        # Initialize shared counter
        state_manager.set("shared_counter", {"count": 0, "contributors": []})

        # Each chain increments the counter
        def increment_func(chain_id):
            def func(state):
                def updater(current):
                    current["count"] += 1
                    current["contributors"].append(chain_id)
                    return current

                state_manager.update("shared_counter", updater)
                return state

            return func

        nodes = [
            CrossChainNode(f"chain{i}", "incrementer", increment_func(f"chain{i}"))
            for i in range(3)
        ]

        # Execute all nodes
        for node in nodes:
            node({})

        # Verify final state
        final = state_manager.get("shared_counter")
        assert final["count"] == 3
        assert len(final["contributors"]) == 3
        assert "chain0" in final["contributors"]
        assert "chain1" in final["contributors"]
        assert "chain2" in final["contributors"]
