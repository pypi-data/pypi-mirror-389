"""
Shared State Manager for cross-chain communication.

This module provides mechanisms for sharing state between different chains.
"""

import builtins
import threading
from copy import deepcopy
from typing import Any, Callable, Optional


class SharedStateManager:
    """
    Manages shared state across multiple chains.

    This manager allows chains to share and synchronize state data,
    enabling coordination and data sharing between separate chain instances.

    Example:
        >>> manager = SharedStateManager()
        >>> manager.set("shared_data", {"key": "value"})
        >>> data = manager.get("shared_data")
    """

    _instance: Optional["SharedStateManager"] = None
    _lock = threading.Lock()

    def __new__(cls) -> "SharedStateManager":
        """Ensure singleton pattern."""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self) -> None:
        """Initialize the shared state manager."""
        if self._initialized:
            return

        self._state: dict[str, Any] = {}
        self._subscribers: dict[str, set[Callable[[Any], None]]] = {}
        self._lock = threading.RLock()
        self._initialized = True

    def set(self, key: str, value: Any, notify: bool = True) -> None:
        """
        Set a value in the shared state.

        Args:
            key: The state key
            value: The value to set
            notify: Whether to notify subscribers of the change
        """
        with self._lock:
            self._state.get(key)
            self._state[key] = deepcopy(value)

            if notify and key in self._subscribers:
                for callback in self._subscribers[key]:
                    try:
                        callback(value)
                    except Exception as e:
                        # Log error but don't fail the set operation
                        print(f"Error in subscriber callback: {e}")

    def get(self, key: str, default: Any = None) -> Any:
        """
        Get a value from the shared state.

        Args:
            key: The state key
            default: Default value if key doesn't exist

        Returns:
            The state value or default
        """
        with self._lock:
            return deepcopy(self._state.get(key, default))

    def update(
        self, key: str, updater: Callable[[Any], Any] | dict[str, Any], notify: bool = True
    ) -> None:
        """
        Update a value using an updater function or dict merge.

        Args:
            key: The state key
            updater: Function that takes current value and returns new value,
                    OR a dict to merge with the current value
            notify: Whether to notify subscribers of the change

        Examples:
            # With function
            manager.update('counter', lambda x: (x or 0) + 1)

            # With dict merge
            manager.update('config', {'new_key': 'value'})
        """
        with self._lock:
            current = self._state.get(key)

            # Handle dict merge
            if isinstance(updater, dict):
                if isinstance(current, dict):
                    new_value = {**current, **updater}
                else:
                    new_value = updater
            # Handle callable updater
            elif callable(updater):
                new_value = updater(current)
            else:
                raise TypeError("updater must be either a callable or a dict")

            self.set(key, new_value, notify)

    def delete(self, key: str) -> None:
        """
        Delete a key from the shared state.

        Args:
            key: The state key to delete

        Raises:
            KeyError: If key doesn't exist
        """
        with self._lock:
            if key not in self._state:
                raise KeyError(f"Key '{key}' not found in shared state")
            del self._state[key]

    def subscribe(self, key: str, callback: Callable[[Any], None]) -> None:
        """
        Subscribe to changes for a specific key.

        Args:
            key: The state key to subscribe to
            callback: Function to call when the key's value changes
        """
        with self._lock:
            if key not in self._subscribers:
                self._subscribers[key] = set()
            self._subscribers[key].add(callback)

    def unsubscribe(self, key: str, callback: Callable[[Any], None]) -> None:
        """
        Unsubscribe from changes for a specific key.

        Args:
            key: The state key
            callback: The callback to remove

        Raises:
            KeyError: If key or callback not found
        """
        with self._lock:
            if key not in self._subscribers:
                raise KeyError(f"No subscribers for key '{key}'")
            if callback not in self._subscribers[key]:
                raise KeyError(f"Callback not found for key '{key}'")
            self._subscribers[key].remove(callback)

    def clear(self) -> None:
        """Clear all shared state."""
        with self._lock:
            self._state.clear()
            self._subscribers.clear()

    def keys(self) -> builtins.set[str]:
        """
        Get all keys in the shared state.

        Returns:
            Set of state keys
        """
        with self._lock:
            return set(self._state.keys())

    def __contains__(self, key: str) -> bool:
        """Check if a key exists in the shared state."""
        with self._lock:
            return key in self._state

    def __len__(self) -> int:
        """Get the number of keys in the shared state."""
        with self._lock:
            return len(self._state)

    def snapshot(self) -> dict[str, Any]:
        """
        Get a snapshot of the entire shared state.

        Returns:
            Deep copy of the current state
        """
        with self._lock:
            return deepcopy(self._state)
