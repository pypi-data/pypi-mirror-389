"""
Custom exceptions for the cross-chain framework.

This module defines all custom exceptions used throughout the framework
for more specific error handling and better error messages.
"""


class CrossChainError(Exception):
    """Base exception for all cross-chain errors."""

    pass


class ChainNotFoundError(CrossChainError):
    """Raised when a referenced chain is not found in the registry."""

    def __init__(self, chain_id: str):
        """
        Initialize the exception.

        Args:
            chain_id: The ID of the chain that was not found
        """
        self.chain_id = chain_id
        super().__init__(f"Chain '{chain_id}' not found in registry")


class ChainAlreadyExistsError(CrossChainError):
    """Raised when attempting to register a chain that already exists."""

    def __init__(self, chain_id: str):
        """
        Initialize the exception.

        Args:
            chain_id: The ID of the chain that already exists
        """
        self.chain_id = chain_id
        super().__init__(f"Chain '{chain_id}' is already registered")


class NodeNotFoundError(CrossChainError):
    """Raised when a referenced node is not found."""

    def __init__(self, chain_id: str, node_id: str):
        """
        Initialize the exception.

        Args:
            chain_id: The ID of the chain
            node_id: The ID of the node that was not found
        """
        self.chain_id = chain_id
        self.node_id = node_id
        super().__init__(f"Node '{node_id}' not found in chain '{chain_id}'")


class MessageRoutingError(CrossChainError):
    """Raised when a message cannot be routed to its destination."""

    def __init__(self, source: str, target: str, reason: str = ""):
        """
        Initialize the exception.

        Args:
            source: The source chain.node
            target: The target chain.node
            reason: Optional reason for the failure
        """
        self.source = source
        self.target = target
        self.reason = reason
        message = f"Failed to route message from '{source}' to '{target}'"
        if reason:
            message += f": {reason}"
        super().__init__(message)


class MessageTimeoutError(CrossChainError):
    """Raised when waiting for a message response times out."""

    def __init__(self, target: str, timeout: float):
        """
        Initialize the exception.

        Args:
            target: The target chain.node
            timeout: The timeout value in seconds
        """
        self.target = target
        self.timeout = timeout
        super().__init__(f"Timeout waiting for response from '{target}' after {timeout}s")


class SharedStateError(CrossChainError):
    """Raised when there's an error with shared state operations."""

    pass


class StateKeyNotFoundError(SharedStateError):
    """Raised when a requested state key doesn't exist."""

    def __init__(self, key: str):
        """
        Initialize the exception.

        Args:
            key: The state key that was not found
        """
        self.key = key
        super().__init__(f"State key '{key}' not found")


class InvalidMessageError(CrossChainError):
    """Raised when a message has invalid format or content."""

    def __init__(self, reason: str):
        """
        Initialize the exception.

        Args:
            reason: The reason the message is invalid
        """
        self.reason = reason
        super().__init__(f"Invalid message: {reason}")


class CallbackError(CrossChainError):
    """Raised when a callback function fails during execution."""

    def __init__(self, key: str, original_error: Exception):
        """
        Initialize the exception.

        Args:
            key: The state key associated with the callback
            original_error: The original exception that was raised
        """
        self.key = key
        self.original_error = original_error
        super().__init__(
            f"Callback error for key '{key}': {type(original_error).__name__}: {str(original_error)}"
        )
