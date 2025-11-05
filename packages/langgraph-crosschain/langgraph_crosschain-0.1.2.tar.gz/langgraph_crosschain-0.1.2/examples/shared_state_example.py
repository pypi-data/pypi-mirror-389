"""
Advanced Example - Using Shared State for Coordination

This example shows how multiple chains can coordinate using shared state.
"""

from typing import Any

from langgraph.graph import END, StateGraph

from langgraph_crosschain import (
    ChainRegistry,
    SharedStateManager,
)


# Define state type
class State(dict[str, Any]):
    """State type for the chains."""

    pass


def create_producer_chain():
    """Create a chain that produces data and stores in shared state."""

    def produce_node(state: State) -> State:
        """Produce data and store in shared state."""
        print("Producer: Producing data...")

        manager = SharedStateManager()

        # Produce some data
        data = {
            "items": ["item1", "item2", "item3"],
            "timestamp": "2025-11-04",
            "producer": "producer_chain",
        }

        # Store in shared state
        manager.set("shared_data", data)
        print(f"Producer: Stored data in shared state: {data}")

        state["data_produced"] = True
        return state

    workflow = StateGraph(State)
    workflow.add_node("produce", produce_node)
    workflow.set_entry_point("produce")
    workflow.add_edge("produce", END)

    return workflow.compile()


def create_consumer_chain():
    """Create a chain that consumes data from shared state."""

    def consume_node(state: State) -> State:
        """Consume data from shared state."""
        print("Consumer: Reading from shared state...")

        manager = SharedStateManager()

        # Read data from shared state
        data = manager.get("shared_data")

        if data:
            print(f"Consumer: Received data: {data}")
            state["data_consumed"] = data
            state["items_count"] = len(data.get("items", []))
        else:
            print("Consumer: No data available")
            state["data_consumed"] = None

        return state

    workflow = StateGraph(State)
    workflow.add_node("consume", consume_node)
    workflow.set_entry_point("consume")
    workflow.add_edge("consume", END)

    return workflow.compile()


def create_processor_chain():
    """Create a chain that processes shared data."""

    def process_node(state: State) -> State:
        """Process data from shared state."""
        print("Processor: Processing shared data...")

        manager = SharedStateManager()

        # Get data
        data = manager.get("shared_data")

        if data:
            # Process the data
            processed_items = [item.upper() for item in data.get("items", [])]
            result = {
                "original_items": data.get("items"),
                "processed_items": processed_items,
                "processed_by": "processor_chain",
            }

            # Store processed result
            manager.set("processed_data", result)
            print(f"Processor: Processed {len(processed_items)} items")

            state["processing_complete"] = True
        else:
            print("Processor: No data to process")
            state["processing_complete"] = False

        return state

    workflow = StateGraph(State)
    workflow.add_node("process", process_node)
    workflow.set_entry_point("process")
    workflow.add_edge("process", END)

    return workflow.compile()


def main():
    """Run the shared state example."""
    print("=" * 70)
    print("Shared State Coordination Example")
    print("=" * 70)
    print()

    # Create registry and state manager
    registry = ChainRegistry()
    state_manager = SharedStateManager()

    # Create and register chains
    producer = create_producer_chain()
    consumer = create_consumer_chain()
    processor = create_processor_chain()

    registry.register("producer", producer)
    registry.register("consumer", consumer)
    registry.register("processor", processor)

    print(f"Registered chains: {registry.list_chains()}")
    print()

    # Step 1: Producer produces data
    print("-" * 70)
    print("STEP 1: Producer produces data")
    print("-" * 70)
    producer.invoke({})
    print()

    # Step 2: Consumer reads the data
    print("-" * 70)
    print("STEP 2: Consumer reads data")
    print("-" * 70)
    consumer.invoke({})
    print()

    # Step 3: Processor processes the data
    print("-" * 70)
    print("STEP 3: Processor processes data")
    print("-" * 70)
    processor.invoke({})
    print()

    # Step 4: Show final state
    print("-" * 70)
    print("STEP 4: Final shared state")
    print("-" * 70)
    final_snapshot = state_manager.snapshot()
    print("Shared state snapshot:")
    for key, value in final_snapshot.items():
        print(f"  {key}: {value}")
    print()

    # Summary
    print("=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print("✓ Producer: Completed successfully")
    print("✓ Consumer: Completed successfully")
    print("✓ Processor: Completed successfully")
    print()
    print("Shared state coordination successful!")
    print()
    print("Note: All chains executed and coordinated via shared state!")


if __name__ == "__main__":
    main()
