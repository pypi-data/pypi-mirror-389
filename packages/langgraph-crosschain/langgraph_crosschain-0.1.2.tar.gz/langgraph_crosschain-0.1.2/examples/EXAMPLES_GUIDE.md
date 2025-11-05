# Working Examples for LangGraph Cross-Chain Framework

This directory contains **working, tested examples** that demonstrate the cross-chain communication framework.

## 🚀 Quick Start - Try These First!

### 1. Simple Working Example (RECOMMENDED)
**File:** `simple_working_example.py`

Demonstrates basic cross-chain message passing (fire-and-forget pattern).

```bash
python examples/simple_working_example.py
```

**What it shows:**
- Registering multiple chains
- Sending messages between chains
- Processing incoming messages
- Message queuing and retrieval

### 2. Shared State Example (RECOMMENDED)
**File:** `shared_state_example.py`

Shows how chains coordinate using shared state.

```bash
python examples/shared_state_example.py
```

**What it shows:**
- Storing data in shared state
- Reading from shared state across chains
- Data processing workflows
- State snapshots

## 📝 Example Descriptions

### simple_working_example.py ⭐
**Complexity:** Beginner
**Pattern:** Fire-and-Forget messaging

A straightforward example showing:
1. Chain A sends a message to Chain B
2. Chain B receives and processes the message
3. No response needed (fire-and-forget)

**Key Concepts:**
- `ChainRegistry` for managing chains
- `CrossChainNode` for cross-chain calls
- `MessageRouter` for message handling
- `call_remote()` with `wait_for_response=False`

### shared_state_example.py ⭐
**Complexity:** Beginner
**Pattern:** Shared State Coordination

Three chains coordinating via shared state:
1. Producer chain creates data
2. Consumer chain reads the data
3. Processor chain processes the data

**Key Concepts:**
- `SharedStateManager` for state sharing
- `set()` and `get()` operations
- State snapshots
- Multi-chain workflows

### basic_communication.py
**Complexity:** Intermediate
**Pattern:** Request-Response (Advanced)

**⚠️ NOTE:** This example demonstrates the request-response pattern but requires
manual coordination. It's kept for reference but not recommended for beginners.

### multi_agent_system.py
**Complexity:** Advanced
**Pattern:** Multi-Agent Coordination

Shows a coordinator pattern with multiple specialist agents.

**⚠️ NOTE:** This is a conceptual example. For working code, see the simple examples above.

## 🎓 Learning Path

**Recommended order:**

1. Start with `simple_working_example.py` - Learn message passing
2. Try `shared_state_example.py` - Learn state coordination
3. Read `basic_communication.py` - Understand advanced patterns
4. Explore `multi_agent_system.py` - See architectural patterns

## 🔧 Running Examples

### Prerequisites

```bash
# Install the package
pip install -e .

# Or with dev dependencies
pip install -e ".[dev]"
```

### Run an Example

```bash
# From project root
python examples/simple_working_example.py

# Or from examples directory
cd examples
python simple_working_example.py
```

### Expected Output

**simple_working_example.py:**
```
======================================================================
Simple Cross-Chain Communication Example (Fire-and-Forget)
======================================================================

Registered chains: {'sender', 'receiver'}

----------------------------------------------------------------------
STEP 1: Sender chain sends message
----------------------------------------------------------------------
Sender Chain: Sending message to receiver chain...
Sender Chain: Message sent!
Sender result: {'data': 'test_data', 'message_sent': True}

----------------------------------------------------------------------
STEP 2: Receiver chain processes message
----------------------------------------------------------------------
Messages in queue: 1
Receiver Chain: Checking for messages...
Receiver Chain: Received 1 message(s)
  - From: sender.sender_node
  - Message: Hello from sender!
  - Data: test_data
Receiver result: {'cross_chain_messages': [...], 'messages_processed': 1}

======================================================================
SUMMARY
======================================================================
✓ Sender sent message: True
✓ Receiver processed: 1 message(s)

Cross-chain communication successful!
```

## 💡 Common Patterns

### Pattern 1: Fire-and-Forget Message
```python
# Send message without waiting for response
node.call_remote(
    target_chain="target",
    target_node="processor",
    payload={"data": "value"},
    wait_for_response=False  # Don't wait
)
```

### Pattern 2: Shared State Coordination
```python
# Chain A: Store data
manager = SharedStateManager()
manager.set("key", {"data": "value"})

# Chain B: Read data
manager = SharedStateManager()
data = manager.get("key")
```

### Pattern 3: Processing Incoming Messages
```python
def node_func(state):
    # Get cross-chain messages
    messages = state.get("cross_chain_messages", [])

    for msg in messages:
        # Process each message
        payload = msg["payload"]
        # Do something with payload

    return state
```

### Pattern 4: Broadcasting
```python
# Send to multiple chains
node.broadcast(
    target_chains=["chain2", "chain3", "chain4"],
    target_node="receiver",
    payload={"broadcast": "data"}
)
```

## 🐛 Troubleshooting

### Issue: Import errors

**Solution:**
```bash
# Make sure package is installed
pip install -e .

# Or reinstall
pip uninstall langgraph-crosschain
pip install -e .
```

### Issue: "Chain not found" error

**Solution:**
Make sure chains are registered before calling:
```python
registry = ChainRegistry()
registry.register("chain1", chain1)
registry.register("chain2", chain2)
```

### Issue: Messages not received

**Solution:**
Remember to manually invoke the receiver chain:
```python
# 1. Send message
sender_chain.invoke({})

# 2. Get messages
messages = router.get_messages_for("target_chain", "target_node")

# 3. Invoke receiver with messages
receiver_chain.invoke({"cross_chain_messages": [msg.model_dump() for msg in messages]})
```

### Issue: "No such file or directory" (Windows)

**Solution:**
Use forward slashes or raw strings:
```python
# Good
python examples/simple_working_example.py

# Or from Windows
python examples\simple_working_example.py
```

## 📚 Next Steps

After running these examples:

1. **Read the documentation:** `../IMPLEMENTATION_GUIDE.md`
2. **Run the tests:** `pytest tests/`
3. **Build your own:** Start with simple_working_example.py as a template
4. **Explore advanced features:** Decorators, validators, error handling

## 🆘 Getting Help

- **Examples not working?** Check you have the latest code: `git pull`
- **Need clarification?** Read `../IMPLEMENTATION_GUIDE.md`
- **Found a bug?** Open an issue on GitHub
- **Want to contribute?** See `../CONTRIBUTING.md`

## ✅ Verification Checklist

Before asking for help, verify:

- [ ] Package installed: `pip install -e .`
- [ ] Running from correct directory
- [ ] Using Python 3.9+
- [ ] All dependencies installed
- [ ] Examples run without modification

---

**Happy Learning!** 🚀

For more information, see the main [README.md](../README.md) and [IMPLEMENTATION_GUIDE.md](../IMPLEMENTATION_GUIDE.md).
