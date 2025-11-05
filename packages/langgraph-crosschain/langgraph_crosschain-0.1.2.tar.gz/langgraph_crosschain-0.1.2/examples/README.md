# Examples

This directory contains example implementations demonstrating various features of the LangGraph Cross-Chain Communication Framework.

## Running the Examples

First, make sure you have the package installed:

```bash
pip install -e ..
```

Then run any example:

```bash
python basic_communication.py
python shared_state.py
python multi_agent_system.py
```

## Example Descriptions

### 1. basic_communication.py

Demonstrates the fundamental cross-chain communication pattern:
- Two chains communicating with each other
- Synchronous message passing
- Response handling

**Key Concepts:**
- `ChainRegistry` for managing chains
- `CrossChainNode` for cross-chain calls
- `MessageRouter` for message routing

### 2. shared_state.py

Shows how to use shared state between chains:
- Writing to shared state
- Reading from shared state
- Subscribing to state changes
- State synchronization

**Key Concepts:**
- `SharedStateManager` for state management
- State subscription and callbacks
- Thread-safe state updates

### 3. multi_agent_system.py

Demonstrates building a multi-agent system:
- Coordinator pattern
- Specialized agent chains
- Broadcasting messages
- Result aggregation

**Key Concepts:**
- Multi-agent architecture
- Task delegation
- Result collection via shared state

## Advanced Patterns

### Pattern 1: Request-Response

```python
# Node in Chain A
result = node.call_remote(
    target_chain="chain_b",
    target_node="processor",
    payload={"data": "test"},
    wait_for_response=True,
    timeout=5.0
)
```

### Pattern 2: Fire-and-Forget

```python
# Node in Chain A
node.call_remote(
    target_chain="chain_b",
    target_node="processor",
    payload={"data": "test"},
    wait_for_response=False
)
```

### Pattern 3: Broadcasting

```python
# Broadcast to multiple chains
node.broadcast(
    target_chains=["chain_b", "chain_c", "chain_d"],
    target_node="receiver",
    payload={"broadcast": "data"}
)
```

### Pattern 4: Shared State

```python
# Write to shared state
manager = SharedStateManager()
manager.set("key", {"data": "value"})

# Read from shared state
data = manager.get("key")

# Subscribe to changes
def on_change(new_value):
    print(f"Changed: {new_value}")

manager.subscribe("key", on_change)
```

## Building Your Own Examples

When creating your own cross-chain workflows:

1. **Register your chains**: Always register chains with the `ChainRegistry`
2. **Use CrossChainNode**: Wrap your node functions with `CrossChainNode` for cross-chain capabilities
3. **Handle messages**: Check for `cross_chain_messages` in your state
4. **Share state carefully**: Use `SharedStateManager` for data that needs to be accessed by multiple chains
5. **Clean up**: Clear registries and managers in tests to avoid interference

## Troubleshooting

### Issue: Messages not being received

**Solution**: Ensure target chain is registered in the `ChainRegistry` before sending messages.

### Issue: State not updating

**Solution**: Remember that `SharedStateManager` returns deep copies. You need to call `set()` to persist changes.

### Issue: Deadlocks

**Solution**: Avoid circular dependencies where Chain A waits for Chain B, and Chain B waits for Chain A.

## Contributing

Have a great example? Please contribute by:
1. Adding your example to this directory
2. Documenting the pattern it demonstrates
3. Adding it to this README
4. Submitting a pull request

Happy building! 🚀
