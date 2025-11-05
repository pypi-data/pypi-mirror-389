"""
Basic Cross-Chain Communication Example

This example demonstrates how to set up two chains that can communicate
with each other using the cross-chain framework.
"""

from typing import Any

from langgraph.graph import END, StateGraph

from langgraph_crosschain import ChainRegistry, CrossChainNode


# Define state type
class State(dict[str, Any]):
    """State type for the chains."""

    pass


def create_chain1():
    """Create the first chain with a node that calls chain2."""

    def analyzer_node(state: State) -> State:
        """Analyze data and prepare for processing."""
        print("Chain1: Analyzing data...")
        data = state.get("data", "default_data")

        # Create a cross-chain node to call chain2
        node = CrossChainNode(chain_id="chain1", node_id="analyzer", func=lambda s: s)

        # Call a node in chain2
        result = node.call_remote(
            target_chain="chain2",
            target_node="processor",
            payload={"analyzed_data": f"analyzed_{data}"},
            wait_for_response=True,
            timeout=5.0,
        )

        state["analysis_result"] = result
        print(f"Chain1: Received result from chain2: {result}")
        return state

    def finalize_node(state: State) -> State:
        """Finalize the results."""
        print("Chain1: Finalizing results...")
        state["finalized"] = True
        return state

    # Build the graph
    workflow = StateGraph(State)
    workflow.add_node("analyzer", analyzer_node)
    workflow.add_node("finalize", finalize_node)

    workflow.set_entry_point("analyzer")
    workflow.add_edge("analyzer", "finalize")
    workflow.add_edge("finalize", END)

    return workflow.compile()


def create_chain2():
    """Create the second chain that processes data."""

    def processor_node(state: State) -> State:
        """Process data received from chain1."""
        print("Chain2: Processing data...")

        # Check for cross-chain messages
        messages = state.get("cross_chain_messages", [])
        if messages:
            msg = messages[0]
            data = msg["payload"].get("analyzed_data")
            print(f"Chain2: Received data from chain1: {data}")

            # Process the data
            processed = f"processed_{data}"
            state["processed_result"] = processed

            # Send response back
            from langgraph_crosschain.communication.message_router import MessageRouter

            router = MessageRouter()
            router.send_response(msg["source_chain"], msg["source_node"], {"processed": processed})

        return state

    def output_node(state: State) -> State:
        """Output the final result."""
        print("Chain2: Outputting result...")
        result = state.get("processed_result", "no_result")
        print(f"Chain2: Final result: {result}")
        return state

    # Build the graph
    workflow = StateGraph(State)
    workflow.add_node("processor", processor_node)
    workflow.add_node("output", output_node)

    workflow.set_entry_point("processor")
    workflow.add_edge("processor", "output")
    workflow.add_edge("output", END)

    return workflow.compile()


def main():
    """Run the basic communication example."""
    print("=" * 60)
    print("Basic Cross-Chain Communication Example")
    print("=" * 60)

    # Create registry
    registry = ChainRegistry()

    # Create and register chains
    chain1 = create_chain1()
    chain2 = create_chain2()

    registry.register("chain1", chain1, {"description": "Analysis chain"})
    registry.register("chain2", chain2, {"description": "Processing chain"})

    print("\nRegistered chains:", registry.list_chains())

    # Run chain1 (which will call chain2)
    print("\n" + "-" * 60)
    print("Running chain1...")
    print("-" * 60)

    initial_state = {"data": "sample_data"}
    result = chain1.invoke(initial_state)

    print("\n" + "-" * 60)
    print("Final Result:")
    print("-" * 60)
    print(result)


if __name__ == "__main__":
    main()
