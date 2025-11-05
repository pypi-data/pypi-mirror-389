"""
Message Router for cross-chain communication.

This module handles routing of messages between chains and nodes.
"""

import threading
from queue import Empty, Queue
from typing import TYPE_CHECKING, Any, Optional

if TYPE_CHECKING:
    from langgraph_crosschain.core.chain_registry import ChainRegistry


class MessageRouter:
    """
    Routes messages between chains and nodes.

    The router maintains message queues for each chain/node combination
    and handles message delivery and synchronization.

    Example:
        >>> router = MessageRouter()
        >>> router.route_message(message)
    """

    _instance: Optional["MessageRouter"] = None
    _lock = threading.Lock()

    def __new__(cls) -> "MessageRouter":
        """Ensure singleton pattern."""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self, registry: Optional["ChainRegistry"] = None):
        """
        Initialize the message router.

        Args:
            registry: Optional chain registry (uses global if not provided)
        """
        if self._initialized:
            return

        if registry is None:
            # Lazy import to avoid circular dependency
            from langgraph_crosschain.core.chain_registry import ChainRegistry

            registry = ChainRegistry()
        self.registry = registry
        self._message_queues: dict[str, Queue] = {}
        self._response_queues: dict[str, Queue] = {}
        self._lock = threading.RLock()
        self._initialized = True

    def route_message(
        self,
        message: Any,
        wait_for_response: bool = False,
        timeout: Optional[float] = None,
    ) -> Optional[Any]:
        """
        Route a message to the target chain/node.

        Args:
            message: The CrossChainMessage to route
            wait_for_response: Whether to wait for a response
            timeout: Timeout in seconds (if wait_for_response=True)

        Returns:
            Response if wait_for_response=True, else None

        Raises:
            KeyError: If target chain is not registered
            TimeoutError: If waiting for response times out
        """
        target_key = f"{message.target_chain}.{message.target_node}"

        # Ensure target chain exists
        if message.target_chain not in self.registry:
            raise KeyError(f"Target chain '{message.target_chain}' not found in registry")

        # Get or create message queue for target
        with self._lock:
            if target_key not in self._message_queues:
                self._message_queues[target_key] = Queue()

            # Add message to queue
            self._message_queues[target_key].put(message)

        # If waiting for response, set up response queue and wait
        if wait_for_response:
            response_key = f"{message.source_chain}.{message.source_node}"

            with self._lock:
                if response_key not in self._response_queues:
                    self._response_queues[response_key] = Queue()

            try:
                response = self._response_queues[response_key].get(timeout=timeout)
                return response
            except Empty:
                raise TimeoutError(f"Timeout waiting for response from {target_key}")

        return None

    def route(
        self,
        message: Any,
        wait_for_response: bool = False,
        timeout: Optional[float] = None,
    ) -> Optional[Any]:
        """
        Convenience alias for route_message().

        Args:
            message: The CrossChainMessage to route
            wait_for_response: Whether to wait for a response
            timeout: Timeout in seconds (if wait_for_response=True)

        Returns:
            Response if wait_for_response=True, else None
        """
        return self.route_message(message, wait_for_response, timeout)

    def get_messages_for(
        self, chain_id: str, node_id: str, block: bool = False, timeout: Optional[float] = None
    ) -> list[Any]:
        """
        Get all pending messages for a specific chain/node.

        Args:
            chain_id: The chain ID
            node_id: The node ID
            block: Whether to block waiting for messages
            timeout: Timeout in seconds (if block=True)

        Returns:
            List of pending messages
        """
        key = f"{chain_id}.{node_id}"
        messages = []

        with self._lock:
            if key not in self._message_queues:
                return messages

            queue = self._message_queues[key]

        # Get first message (potentially blocking)
        try:
            if block:
                msg = queue.get(timeout=timeout)
                messages.append(msg)
            else:
                # Try to get without blocking
                try:
                    msg = queue.get_nowait()
                    messages.append(msg)
                except Empty:
                    return messages
        except Empty:
            return messages

        # Get all remaining messages (non-blocking)
        while True:
            try:
                msg = queue.get_nowait()
                messages.append(msg)
            except Empty:
                break

        return messages

    def send_response(self, target_chain: str, target_node: str, response: Any) -> None:
        """
        Send a response back to a requesting node.

        Args:
            target_chain: The chain ID of the requester
            target_node: The node ID of the requester
            response: The response data
        """
        key = f"{target_chain}.{target_node}"

        with self._lock:
            if key not in self._response_queues:
                self._response_queues[key] = Queue()

            self._response_queues[key].put(response)

    def clear_queues(self, chain_id: Optional[str] = None) -> None:
        """
        Clear message queues.

        Args:
            chain_id: If provided, only clear queues for this chain.
                     Otherwise, clear all queues.
        """
        with self._lock:
            if chain_id:
                # Clear only queues for specified chain
                keys_to_clear = [
                    k for k in self._message_queues.keys() if k.startswith(f"{chain_id}.")
                ]
                for key in keys_to_clear:
                    self._message_queues[key] = Queue()
                    if key in self._response_queues:
                        self._response_queues[key] = Queue()
            else:
                # Clear all queues
                self._message_queues.clear()
                self._response_queues.clear()
