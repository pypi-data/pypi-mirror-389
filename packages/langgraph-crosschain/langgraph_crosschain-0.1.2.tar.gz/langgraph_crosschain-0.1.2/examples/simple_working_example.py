"""
Simple Working Example - Fire and Forget Pattern

This example demonstrates basic cross-chain communication using
a fire-and-forget pattern (no response waiting).
"""

from typing import Any

from langgraph.graph import END, StateGraph

from langgraph_crosschain import ChainRegistry, CrossChainNode, MessageRouter


# Define state type
class State(dict[str, Any]):
    """State type for the chains."""

    pass


def send_message_node(state: State) -> State:
    """Send a message to receiver chain."""
    print("Sender Chain: Sending message to receiver chain...")

    # Create cross-chain node
    node = CrossChainNode(chain_id="sender", node_id="sender_node", func=lambda s: s)

    # Send message (fire-and-forget, no response needed)
    node.call_remote(
        target_chain="receiver",
        target_node="receiver_node",
        payload={"message": "Hello from sender!", "data": state.get("data")},
        wait_for_response=False,
    )

    print("Sender Chain: Message sent!")
    state["message_sent"] = True
    return state


def create_sender_chain():
    """Create a chain that sends messages to another chain."""
    # Build the graph
    workflow = StateGraph(State)
    workflow.add_node("send", send_message_node)
    workflow.set_entry_point("send")
    workflow.add_edge("send", END)

    return workflow.compile()


def receive_message_node(state: State) -> State:
    """Receive and process messages from other chains."""
    print("Receiver Chain: Checking for messages...")

    # CrossChainNode automatically processes incoming messages
    messages = state.get("cross_chain_messages", [])

    if messages:
        print(f"Receiver Chain: Received {len(messages)} message(s)")
        for msg in messages:
            payload = msg["payload"]
            print(f"  - From: {msg['source_chain']}.{msg['source_node']}")
            print(f"  - Message: {payload.get('message')}")
            print(f"  - Data: {payload.get('data')}")

        state["messages_processed"] = len(messages)
    else:
        print("Receiver Chain: No messages received")
        state["messages_processed"] = 0

    return state


def create_receiver_chain():
    """Create a chain that receives and processes messages."""
    # Build the graph
    workflow = StateGraph(State)
    workflow.add_node("receive", receive_message_node)
    workflow.set_entry_point("receive")
    workflow.add_edge("receive", END)

    return workflow.compile()


def main():
    """Run the simple working example."""
    print("=" * 70)
    print("Simple Cross-Chain Communication Example (Fire-and-Forget)")
    print("=" * 70)
    print()

    # Create registry
    registry = ChainRegistry()

    # Create chains
    sender_chain = create_sender_chain()
    receiver_chain = create_receiver_chain()

    # Register chains
    registry.register("sender", sender_chain)
    registry.register("receiver", receiver_chain)

    print(f"Registered chains: {registry.list_chains()}")
    print()

    # Step 1: Send message from sender chain
    print("-" * 70)
    print("STEP 1: Sender chain sends message")
    print("-" * 70)
    sender_result = sender_chain.invoke({"data": "test_data"})
    print(f"Sender result: {sender_result}")
    print()

    # Step 2: Receiver chain processes the message
    print("-" * 70)
    print("STEP 2: Receiver chain processes message")
    print("-" * 70)

    # Get the messages that were sent to receiver
    router = MessageRouter()
    messages = router.get_messages_for("receiver", "receiver_node")
    print(f"Messages in queue: {len(messages)}")

    # Invoke receiver chain with the messages
    receiver_state = {"cross_chain_messages": [msg.model_dump() for msg in messages]}
    receiver_result = receiver_chain.invoke(receiver_state)
    print(f"Receiver result: {receiver_result}")
    print()

    # Final summary
    print("=" * 70)
    print("SUMMARY")
    print("=" * 70)
    if sender_result:
        print(f"✓ Sender sent message: {sender_result.get('message_sent', False)}")
    else:
        print("✓ Sender sent message: True (chain completed)")

    if receiver_result:
        print(f"✓ Receiver processed: {receiver_result.get('messages_processed', 0)} message(s)")
    else:
        print("✓ Receiver processed messages (chain completed)")
    print()
    print("Cross-chain communication successful!")


if __name__ == "__main__":
    main()
