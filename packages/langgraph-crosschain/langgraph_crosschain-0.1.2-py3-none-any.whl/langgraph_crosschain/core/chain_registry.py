"""
Chain Registry for managing multiple LangGraph chains.

This module provides a centralized registry for managing and accessing
multiple chain instances across the application.
"""

import threading
from typing import Any, Optional


class ChainRegistry:
    """
    A singleton registry for managing multiple LangGraph chains.

    This registry allows chains to discover and communicate with each other
    by providing a centralized lookup mechanism.

    Example:
        >>> registry = ChainRegistry()
        >>> registry.register("chain1", my_chain_instance)
        >>> chain = registry.get("chain1")
    """

    _instance: Optional["ChainRegistry"] = None
    _lock = threading.Lock()

    def __new__(cls) -> "ChainRegistry":
        """Ensure singleton pattern."""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self) -> None:
        """Initialize the registry."""
        if self._initialized:
            return

        self._chains: dict[str, Any] = {}
        self._metadata: dict[str, dict[str, Any]] = {}
        self._lock = threading.RLock()
        self._initialized = True

    def register(
        self, chain_id: str, chain: Any, metadata: Optional[dict[str, Any]] = None
    ) -> None:
        """
        Register a chain in the registry.

        Args:
            chain_id: Unique identifier for the chain
            chain: The chain instance (typically a compiled StateGraph)
            metadata: Optional metadata about the chain

        Raises:
            ValueError: If chain_id is already registered
        """
        with self._lock:
            if chain_id in self._chains:
                raise ValueError(f"Chain '{chain_id}' is already registered")

            self._chains[chain_id] = chain
            self._metadata[chain_id] = metadata or {}

    def unregister(self, chain_id: str) -> None:
        """
        Unregister a chain from the registry.

        Args:
            chain_id: The chain identifier to unregister

        Raises:
            KeyError: If chain_id is not found
        """
        with self._lock:
            if chain_id not in self._chains:
                raise KeyError(f"Chain '{chain_id}' not found in registry")

            del self._chains[chain_id]
            del self._metadata[chain_id]

    def get(self, chain_id: str) -> Any:
        """
        Get a chain by its identifier.

        Args:
            chain_id: The chain identifier

        Returns:
            The chain instance

        Raises:
            KeyError: If chain_id is not found
        """
        with self._lock:
            if chain_id not in self._chains:
                raise KeyError(f"Chain '{chain_id}' not found in registry")
            return self._chains[chain_id]

    def get_metadata(self, chain_id: str) -> dict[str, Any]:
        """
        Get metadata for a chain.

        Args:
            chain_id: The chain identifier

        Returns:
            The chain's metadata

        Raises:
            KeyError: If chain_id is not found
        """
        with self._lock:
            if chain_id not in self._metadata:
                raise KeyError(f"Chain '{chain_id}' not found in registry")
            return self._metadata[chain_id].copy()

    def list_chains(self) -> set[str]:
        """
        List all registered chain IDs.

        Returns:
            Set of chain identifiers
        """
        with self._lock:
            return set(self._chains.keys())

    def clear(self) -> None:
        """Clear all registered chains."""
        with self._lock:
            self._chains.clear()
            self._metadata.clear()

    def __contains__(self, chain_id: str) -> bool:
        """Check if a chain is registered."""
        with self._lock:
            return chain_id in self._chains

    def __len__(self) -> int:
        """Get the number of registered chains."""
        with self._lock:
            return len(self._chains)
