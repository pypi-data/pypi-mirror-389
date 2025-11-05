"""Tests for custom exceptions."""

from langgraph_crosschain import exceptions


class TestExceptions:
    """Test suite for custom exceptions."""

    def test_cross_chain_error(self):
        """Test base CrossChainError."""
        error = exceptions.CrossChainError("Test error")
        assert str(error) == "Test error"
        assert isinstance(error, Exception)

    def test_chain_not_found_error(self):
        """Test ChainNotFoundError."""
        error = exceptions.ChainNotFoundError("test_chain")
        assert error.chain_id == "test_chain"
        assert "test_chain" in str(error)
        assert "not found" in str(error)

    def test_chain_already_exists_error(self):
        """Test ChainAlreadyExistsError."""
        error = exceptions.ChainAlreadyExistsError("test_chain")
        assert error.chain_id == "test_chain"
        assert "test_chain" in str(error)
        assert "already registered" in str(error)

    def test_node_not_found_error(self):
        """Test NodeNotFoundError."""
        error = exceptions.NodeNotFoundError("test_chain", "test_node")
        assert error.chain_id == "test_chain"
        assert error.node_id == "test_node"
        assert "test_node" in str(error)
        assert "test_chain" in str(error)

    def test_message_routing_error(self):
        """Test MessageRoutingError."""
        error = exceptions.MessageRoutingError("chain1.node1", "chain2.node2", "Connection failed")
        assert error.source == "chain1.node1"
        assert error.target == "chain2.node2"
        assert error.reason == "Connection failed"
        assert "Connection failed" in str(error)

    def test_message_routing_error_without_reason(self):
        """Test MessageRoutingError without reason."""
        error = exceptions.MessageRoutingError("chain1.node1", "chain2.node2")
        assert error.reason == ""
        assert "chain1.node1" in str(error)
        assert "chain2.node2" in str(error)

    def test_message_timeout_error(self):
        """Test MessageTimeoutError."""
        error = exceptions.MessageTimeoutError("chain2.node2", 5.0)
        assert error.target == "chain2.node2"
        assert error.timeout == 5.0
        assert "5.0" in str(error)
        assert "chain2.node2" in str(error)

    def test_shared_state_error(self):
        """Test SharedStateError."""
        error = exceptions.SharedStateError("Test state error")
        assert str(error) == "Test state error"

    def test_state_key_not_found_error(self):
        """Test StateKeyNotFoundError."""
        error = exceptions.StateKeyNotFoundError("test_key")
        assert error.key == "test_key"
        assert "test_key" in str(error)
        assert "not found" in str(error)

    def test_invalid_message_error(self):
        """Test InvalidMessageError."""
        error = exceptions.InvalidMessageError("Invalid payload format")
        assert error.reason == "Invalid payload format"
        assert "Invalid payload format" in str(error)

    def test_callback_error(self):
        """Test CallbackError."""
        original = ValueError("Original error")
        error = exceptions.CallbackError("test_key", original)
        assert error.key == "test_key"
        assert error.original_error is original
        assert "test_key" in str(error)
        assert "ValueError" in str(error)

    def test_exception_inheritance(self):
        """Test that all custom exceptions inherit from CrossChainError."""
        assert issubclass(exceptions.ChainNotFoundError, exceptions.CrossChainError)
        assert issubclass(exceptions.ChainAlreadyExistsError, exceptions.CrossChainError)
        assert issubclass(exceptions.NodeNotFoundError, exceptions.CrossChainError)
        assert issubclass(exceptions.MessageRoutingError, exceptions.CrossChainError)
        assert issubclass(exceptions.MessageTimeoutError, exceptions.CrossChainError)
        assert issubclass(exceptions.SharedStateError, exceptions.CrossChainError)
        assert issubclass(exceptions.StateKeyNotFoundError, exceptions.SharedStateError)
        assert issubclass(exceptions.InvalidMessageError, exceptions.CrossChainError)
        assert issubclass(exceptions.CallbackError, exceptions.CrossChainError)
