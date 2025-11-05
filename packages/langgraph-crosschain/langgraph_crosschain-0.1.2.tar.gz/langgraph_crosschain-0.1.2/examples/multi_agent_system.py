"""
Multi-Agent System Example

This example demonstrates how to build a multi-agent system where
different specialized chains (agents) collaborate on a task.
"""

from typing import Any

from langgraph.graph import END, StateGraph

from langgraph_crosschain import ChainRegistry, CrossChainNode, SharedStateManager


# Define state type
class State(dict[str, Any]):
    """State type for the chains."""

    pass


def create_coordinator_chain():
    """Create a coordinator chain that orchestrates other agents."""

    def plan_node(state: State) -> State:
        """Plan the task and delegate to specialist agents."""
        print("Coordinator: Planning task...")

        task = state.get("task", "default_task")
        print(f"Coordinator: Task is '{task}'")

        # Delegate to specialist agents
        coordinator = CrossChainNode(chain_id="coordinator", node_id="planner", func=lambda s: s)

        # Broadcast task to all specialists
        print("Coordinator: Broadcasting task to specialists...")
        coordinator.broadcast(
            target_chains=["research_agent", "analysis_agent", "execution_agent"],
            target_node="process",
            payload={"task": task, "delegated_by": "coordinator"},
        )

        state["delegated"] = True
        return state

    def collect_node(state: State) -> State:
        """Collect results from specialist agents."""
        print("Coordinator: Collecting results from specialists...")

        manager = SharedStateManager()

        # Collect results from shared state
        results = {
            "research": manager.get("research_result", "pending"),
            "analysis": manager.get("analysis_result", "pending"),
            "execution": manager.get("execution_result", "pending"),
        }

        print(f"Coordinator: Collected results: {results}")
        state["specialist_results"] = results
        return state

    # Build the graph
    workflow = StateGraph(State)
    workflow.add_node("plan", plan_node)
    workflow.add_node("collect", collect_node)

    workflow.set_entry_point("plan")
    workflow.add_edge("plan", "collect")
    workflow.add_edge("collect", END)

    return workflow.compile()


def create_research_agent():
    """Create a research specialist agent."""

    def process_node(state: State) -> State:
        """Process research tasks."""
        print("Research Agent: Processing task...")

        messages = state.get("cross_chain_messages", [])
        if messages:
            msg = messages[0]
            task = msg["payload"].get("task")
            print(f"Research Agent: Researching '{task}'...")

            # Perform research
            result = f"Research findings for {task}"

            # Store result in shared state
            manager = SharedStateManager()
            manager.set("research_result", result)

            state["research_complete"] = True

        return state

    # Build the graph
    workflow = StateGraph(State)
    workflow.add_node("process", process_node)

    workflow.set_entry_point("process")
    workflow.add_edge("process", END)

    return workflow.compile()


def create_analysis_agent():
    """Create an analysis specialist agent."""

    def process_node(state: State) -> State:
        """Process analysis tasks."""
        print("Analysis Agent: Processing task...")

        messages = state.get("cross_chain_messages", [])
        if messages:
            msg = messages[0]
            task = msg["payload"].get("task")
            print(f"Analysis Agent: Analyzing '{task}'...")

            # Perform analysis
            result = f"Analysis results for {task}"

            # Store result in shared state
            manager = SharedStateManager()
            manager.set("analysis_result", result)

            state["analysis_complete"] = True

        return state

    # Build the graph
    workflow = StateGraph(State)
    workflow.add_node("process", process_node)

    workflow.set_entry_point("process")
    workflow.add_edge("process", END)

    return workflow.compile()


def create_execution_agent():
    """Create an execution specialist agent."""

    def process_node(state: State) -> State:
        """Process execution tasks."""
        print("Execution Agent: Processing task...")

        messages = state.get("cross_chain_messages", [])
        if messages:
            msg = messages[0]
            task = msg["payload"].get("task")
            print(f"Execution Agent: Executing '{task}'...")

            # Perform execution
            result = f"Execution output for {task}"

            # Store result in shared state
            manager = SharedStateManager()
            manager.set("execution_result", result)

            state["execution_complete"] = True

        return state

    # Build the graph
    workflow = StateGraph(State)
    workflow.add_node("process", process_node)

    workflow.set_entry_point("process")
    workflow.add_edge("process", END)

    return workflow.compile()


def main():
    """Run the multi-agent system example."""
    print("=" * 60)
    print("Multi-Agent System Example")
    print("=" * 60)

    # Create registry
    registry = ChainRegistry()

    # Create and register all agents
    coordinator = create_coordinator_chain()
    research = create_research_agent()
    analysis = create_analysis_agent()
    execution = create_execution_agent()

    registry.register("coordinator", coordinator, {"role": "coordinator"})
    registry.register("research_agent", research, {"role": "research"})
    registry.register("analysis_agent", analysis, {"role": "analysis"})
    registry.register("execution_agent", execution, {"role": "execution"})

    print("\nRegistered agents:", registry.list_chains())

    # Run the coordinator
    print("\n" + "-" * 60)
    print("Starting multi-agent task...")
    print("-" * 60)

    task = "Build a recommendation system"
    result = coordinator.invoke({"task": task})

    # Run specialist agents (in real scenario, this would be triggered automatically)
    print("\n" + "-" * 60)
    print("Specialist agents processing...")
    print("-" * 60)

    # In a real implementation, you'd trigger these based on the messages
    # For demonstration, we'll just show the pattern

    print("\n" + "-" * 60)
    print("Final Results:")
    print("-" * 60)
    print(result)


if __name__ == "__main__":
    main()
