"""
Shared State Example

This example demonstrates how to use the SharedStateManager to share
state between multiple chains.
"""

from typing import Any

from langgraph.graph import END, StateGraph

from langgraph_crosschain import ChainRegistry, SharedStateManager


# Define state type
class State(dict[str, Any]):
    """State type for the chains."""

    pass


def create_writer_chain():
    """Create a chain that writes to shared state."""

    def write_node(state: State) -> State:
        """Write data to shared state."""
        print("Writer Chain: Writing to shared state...")

        manager = SharedStateManager()
        data = state.get("data", {})

        # Write to shared state
        manager.set("shared_counter", data.get("counter", 0))
        manager.set("shared_message", data.get("message", "Hello from writer"))

        print(f"Writer Chain: Wrote counter={data.get('counter')} to shared state")
        state["write_complete"] = True
        return state

    # Build the graph
    workflow = StateGraph(State)
    workflow.add_node("write", write_node)

    workflow.set_entry_point("write")
    workflow.add_edge("write", END)

    return workflow.compile()


def create_reader_chain():
    """Create a chain that reads from shared state."""

    def read_node(state: State) -> State:
        """Read data from shared state."""
        print("Reader Chain: Reading from shared state...")

        manager = SharedStateManager()

        # Read from shared state
        counter = manager.get("shared_counter", 0)
        message = manager.get("shared_message", "No message")

        print(f"Reader Chain: Read counter={counter}, message='{message}'")

        state["counter"] = counter
        state["message"] = message
        return state

    def increment_node(state: State) -> State:
        """Increment the counter in shared state."""
        print("Reader Chain: Incrementing counter...")

        manager = SharedStateManager()
        current = manager.get("shared_counter", 0)
        new_value = current + 1

        manager.set("shared_counter", new_value)
        print(f"Reader Chain: Incremented counter from {current} to {new_value}")

        state["incremented"] = True
        return state

    # Build the graph
    workflow = StateGraph(State)
    workflow.add_node("read", read_node)
    workflow.add_node("increment", increment_node)

    workflow.set_entry_point("read")
    workflow.add_edge("read", "increment")
    workflow.add_edge("increment", END)

    return workflow.compile()


def create_subscriber_chain():
    """Create a chain that subscribes to shared state changes."""

    def subscribe_node(state: State) -> State:
        """Subscribe to shared state changes."""
        print("Subscriber Chain: Setting up subscription...")

        manager = SharedStateManager()

        # Define callback
        def on_counter_change(value):
            print(f"Subscriber Chain: Counter changed to {value}!")

        # Subscribe to changes
        manager.subscribe("shared_counter", on_counter_change)

        state["subscribed"] = True
        return state

    # Build the graph
    workflow = StateGraph(State)
    workflow.add_node("subscribe", subscribe_node)

    workflow.set_entry_point("subscribe")
    workflow.add_edge("subscribe", END)

    return workflow.compile()


def main():
    """Run the shared state example."""
    print("=" * 60)
    print("Shared State Example")
    print("=" * 60)

    # Create registry and state manager
    registry = ChainRegistry()
    manager = SharedStateManager()

    # Create and register chains
    writer_chain = create_writer_chain()
    reader_chain = create_reader_chain()
    subscriber_chain = create_subscriber_chain()

    registry.register("writer", writer_chain, {"description": "Writes to shared state"})
    registry.register("reader", reader_chain, {"description": "Reads from shared state"})
    registry.register("subscriber", subscriber_chain, {"description": "Subscribes to changes"})

    print("\nRegistered chains:", registry.list_chains())

    # Set up subscriber first
    print("\n" + "-" * 60)
    print("Setting up subscriber...")
    print("-" * 60)
    subscriber_chain.invoke({})

    # Write to shared state
    print("\n" + "-" * 60)
    print("Running writer chain...")
    print("-" * 60)
    writer_chain.invoke({"data": {"counter": 10, "message": "Hello from writer!"}})

    # Read and increment
    print("\n" + "-" * 60)
    print("Running reader chain...")
    print("-" * 60)
    reader_chain.invoke({})

    print("\n" + "-" * 60)
    print("Final State Snapshot:")
    print("-" * 60)
    print(manager.snapshot())


if __name__ == "__main__":
    main()
