"""
Cross-Chain Node implementation.

This module provides the base class for nodes that can communicate
across different LangGraph chains.
"""

from typing import TYPE_CHECKING, Any, Callable, Generic, Optional, TypeVar

from pydantic import BaseModel

from langgraph_crosschain.core.chain_registry import ChainRegistry

if TYPE_CHECKING:
    from langgraph_crosschain.communication.message_router import MessageRouter

StateT = TypeVar("StateT", bound=dict[str, Any])


class CrossChainMessage(BaseModel):
    """
    Message structure for cross-chain communication.

    Attributes:
        source_chain: ID of the source chain
        source_node: ID of the source node
        target_chain: ID of the target chain
        target_node: ID of the target node
        payload: The actual message payload
        metadata: Optional metadata
    """

    source_chain: str
    source_node: str
    target_chain: str
    target_node: str
    payload: dict[str, Any]
    metadata: Optional[dict[str, Any]] = None


class CrossChainNode(Generic[StateT]):
    """
    Base class for nodes that can communicate across chains.

    This class wraps a standard LangGraph node and adds cross-chain
    communication capabilities.

    Example:
        >>> def my_node_func(state: Dict) -> Dict:
        ...     return {"result": "processed"}
        ...
        >>> node = CrossChainNode(
        ...     chain_id="chain1",
        ...     node_id="processor",
        ...     func=my_node_func
        ... )
        >>> result = node.call_remote("chain2", "analyzer", {"data": "test"})
    """

    def __init__(
        self,
        chain_id: str,
        node_id: str,
        func: Callable[[StateT], StateT],
        registry: Optional[ChainRegistry] = None,
        router: Optional["MessageRouter"] = None,
    ):
        """
        Initialize a cross-chain node.

        Args:
            chain_id: ID of the chain this node belongs to
            node_id: Unique ID for this node within the chain
            func: The actual node function to execute
            registry: Optional chain registry (uses global if not provided)
            router: Optional message router (uses global if not provided)
        """
        self.chain_id = chain_id
        self.node_id = node_id
        self.func = func
        self.registry = registry or ChainRegistry()

        if router is None:
            # Lazy import to avoid circular dependency
            from langgraph_crosschain.communication.message_router import MessageRouter

            router = MessageRouter()
        self.router = router

    def __call__(self, state: StateT) -> StateT:
        """
        Execute the node function.

        Args:
            state: The current state

        Returns:
            The updated state
        """
        # Check for any pending cross-chain messages
        messages = self.router.get_messages_for(self.chain_id, self.node_id)

        # Process incoming messages
        if messages:
            state = self._process_incoming_messages(state, messages)

        # Execute the wrapped function
        result = self.func(state)

        return result

    def call_remote(
        self,
        target_chain: str,
        target_node: str,
        payload: dict[str, Any],
        wait_for_response: bool = False,
        timeout: Optional[float] = None,
    ) -> Optional[Any]:
        """
        Call a node in a different chain.

        Args:
            target_chain: ID of the target chain
            target_node: ID of the target node
            payload: Data to send to the target node
            wait_for_response: Whether to wait for a response
            timeout: Timeout in seconds (if wait_for_response=True)

        Returns:
            Response from the target node if wait_for_response=True, else None

        Raises:
            KeyError: If target chain is not registered
            TimeoutError: If waiting for response times out
        """
        message = CrossChainMessage(
            source_chain=self.chain_id,
            source_node=self.node_id,
            target_chain=target_chain,
            target_node=target_node,
            payload=payload,
        )

        return self.router.route_message(message, wait_for_response, timeout)

    def broadcast(
        self,
        target_chains: list[str],
        target_node: str,
        payload: dict[str, Any],
    ) -> None:
        """
        Broadcast a message to the same node across multiple chains.

        Args:
            target_chains: List of target chain IDs
            target_node: ID of the target node in each chain
            payload: Data to send
        """
        for chain_id in target_chains:
            self.call_remote(chain_id, target_node, payload, wait_for_response=False)

    def _process_incoming_messages(
        self, state: StateT, messages: list[CrossChainMessage]
    ) -> StateT:
        """
        Process incoming cross-chain messages.

        Args:
            state: Current state
            messages: List of incoming messages

        Returns:
            Updated state with processed messages
        """
        # Add messages to state for processing
        if "cross_chain_messages" not in state:
            state["cross_chain_messages"] = []

        state["cross_chain_messages"].extend([msg.model_dump() for msg in messages])

        return state

    @property
    def full_id(self) -> str:
        """Get the full identifier for this node (chain_id.node_id)."""
        return f"{self.chain_id}.{self.node_id}"
