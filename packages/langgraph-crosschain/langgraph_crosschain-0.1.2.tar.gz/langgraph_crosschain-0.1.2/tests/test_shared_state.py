"""Tests for SharedStateManager."""

import pytest

from langgraph_crosschain.state.shared_state import SharedStateManager


class TestSharedStateManager:
    """Test suite for SharedStateManager."""

    def setup_method(self):
        """Set up test fixtures."""
        # Clear state before each test
        manager = SharedStateManager()
        manager.clear()

    def test_singleton_pattern(self):
        """Test that SharedStateManager implements singleton pattern."""
        manager1 = SharedStateManager()
        manager2 = SharedStateManager()
        assert manager1 is manager2

    def test_set_and_get(self):
        """Test setting and getting state."""
        manager = SharedStateManager()

        manager.set("key1", "value1")
        assert manager.get("key1") == "value1"

    def test_get_nonexistent_returns_default(self):
        """Test that getting a nonexistent key returns default."""
        manager = SharedStateManager()

        assert manager.get("nonexistent") is None
        assert manager.get("nonexistent", "default") == "default"

    def test_update(self):
        """Test updating state with an updater function."""
        manager = SharedStateManager()

        manager.set("counter", 0)
        manager.update("counter", lambda x: x + 1)

        assert manager.get("counter") == 1

    def test_update_with_dict_merge(self):
        """Test updating state with dict merge."""
        manager = SharedStateManager()

        # Set initial dict
        manager.set("config", {"key1": "value1", "key2": "value2"})

        # Update with dict merge
        manager.update("config", {"key2": "updated", "key3": "value3"})

        result = manager.get("config")
        assert result == {"key1": "value1", "key2": "updated", "key3": "value3"}

    def test_update_with_dict_on_non_dict_value(self):
        """Test updating non-dict value with dict replaces it."""
        manager = SharedStateManager()

        # Set non-dict value
        manager.set("value", "string")

        # Update with dict should replace
        manager.update("value", {"key": "value"})

        result = manager.get("value")
        assert result == {"key": "value"}

    def test_update_with_invalid_type_raises_error(self):
        """Test that update with invalid type raises TypeError."""
        manager = SharedStateManager()

        manager.set("key", "value")

        with pytest.raises(TypeError, match="must be either a callable or a dict"):
            manager.update("key", "invalid")

    def test_delete(self):
        """Test deleting a key."""
        manager = SharedStateManager()

        manager.set("key1", "value1")
        manager.delete("key1")

        assert "key1" not in manager

    def test_delete_nonexistent_raises_error(self):
        """Test that deleting a nonexistent key raises KeyError."""
        manager = SharedStateManager()

        with pytest.raises(KeyError, match="not found"):
            manager.delete("nonexistent")

    def test_subscribe(self):
        """Test subscribing to state changes."""
        manager = SharedStateManager()
        callback_values = []

        def callback(value):
            callback_values.append(value)

        manager.subscribe("key1", callback)
        manager.set("key1", "value1")

        assert callback_values == ["value1"]

    def test_unsubscribe(self):
        """Test unsubscribing from state changes."""
        manager = SharedStateManager()
        callback_values = []

        def callback(value):
            callback_values.append(value)

        manager.subscribe("key1", callback)
        manager.set("key1", "value1")
        manager.unsubscribe("key1", callback)
        manager.set("key1", "value2")

        # Should only have received the first value
        assert callback_values == ["value1"]

    def test_keys(self):
        """Test getting all keys."""
        manager = SharedStateManager()

        manager.set("key1", "value1")
        manager.set("key2", "value2")
        manager.set("key3", "value3")

        keys = manager.keys()
        assert keys == {"key1", "key2", "key3"}

    def test_contains(self):
        """Test checking if a key exists."""
        manager = SharedStateManager()

        manager.set("key1", "value1")

        assert "key1" in manager
        assert "nonexistent" not in manager

    def test_len(self):
        """Test getting the number of keys."""
        manager = SharedStateManager()

        assert len(manager) == 0

        manager.set("key1", "value1")
        assert len(manager) == 1

        manager.set("key2", "value2")
        assert len(manager) == 2

    def test_snapshot(self):
        """Test getting a snapshot of state."""
        manager = SharedStateManager()

        manager.set("key1", "value1")
        manager.set("key2", "value2")

        snapshot = manager.snapshot()
        assert snapshot == {"key1": "value1", "key2": "value2"}

        # Snapshot should be a copy
        snapshot["key3"] = "value3"
        assert "key3" not in manager

    def test_clear(self):
        """Test clearing all state."""
        manager = SharedStateManager()

        manager.set("key1", "value1")
        manager.set("key2", "value2")

        manager.clear()

        assert len(manager) == 0
        assert manager.keys() == set()
