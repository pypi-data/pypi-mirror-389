"""Tests for ChainRegistry."""

import pytest

from langgraph_crosschain.core.chain_registry import ChainRegistry


class TestChainRegistry:
    """Test suite for ChainRegistry."""

    def setup_method(self):
        """Set up test fixtures."""
        # Clear registry before each test
        registry = ChainRegistry()
        registry.clear()

    def test_singleton_pattern(self):
        """Test that ChainRegistry implements singleton pattern."""
        registry1 = ChainRegistry()
        registry2 = ChainRegistry()
        assert registry1 is registry2

    def test_register_chain(self):
        """Test registering a chain."""
        registry = ChainRegistry()
        mock_chain = "mock_chain_instance"

        registry.register("test_chain", mock_chain)

        assert "test_chain" in registry
        assert registry.get("test_chain") == mock_chain

    def test_register_duplicate_raises_error(self):
        """Test that registering a duplicate chain raises ValueError."""
        registry = ChainRegistry()
        mock_chain = "mock_chain_instance"

        registry.register("test_chain", mock_chain)

        with pytest.raises(ValueError, match="already registered"):
            registry.register("test_chain", mock_chain)

    def test_register_with_metadata(self):
        """Test registering a chain with metadata."""
        registry = ChainRegistry()
        mock_chain = "mock_chain_instance"
        metadata = {"description": "Test chain", "version": "1.0"}

        registry.register("test_chain", mock_chain, metadata)

        retrieved_metadata = registry.get_metadata("test_chain")
        assert retrieved_metadata == metadata

    def test_unregister_chain(self):
        """Test unregistering a chain."""
        registry = ChainRegistry()
        mock_chain = "mock_chain_instance"

        registry.register("test_chain", mock_chain)
        registry.unregister("test_chain")

        assert "test_chain" not in registry

    def test_unregister_nonexistent_raises_error(self):
        """Test that unregistering a nonexistent chain raises KeyError."""
        registry = ChainRegistry()

        with pytest.raises(KeyError, match="not found"):
            registry.unregister("nonexistent_chain")

    def test_get_nonexistent_raises_error(self):
        """Test that getting a nonexistent chain raises KeyError."""
        registry = ChainRegistry()

        with pytest.raises(KeyError, match="not found"):
            registry.get("nonexistent_chain")

    def test_list_chains(self):
        """Test listing all registered chains."""
        registry = ChainRegistry()

        registry.register("chain1", "instance1")
        registry.register("chain2", "instance2")
        registry.register("chain3", "instance3")

        chains = registry.list_chains()
        assert chains == {"chain1", "chain2", "chain3"}

    def test_clear(self):
        """Test clearing all chains."""
        registry = ChainRegistry()

        registry.register("chain1", "instance1")
        registry.register("chain2", "instance2")

        registry.clear()

        assert len(registry) == 0
        assert registry.list_chains() == set()

    def test_len(self):
        """Test getting the number of registered chains."""
        registry = ChainRegistry()

        assert len(registry) == 0

        registry.register("chain1", "instance1")
        assert len(registry) == 1

        registry.register("chain2", "instance2")
        assert len(registry) == 2
