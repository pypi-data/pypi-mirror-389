"""Tests for validation utilities."""

import pytest

from langgraph_crosschain.exceptions import InvalidMessageError
from langgraph_crosschain.utils.validators import (
    is_valid_full_node_id,
    parse_full_node_id,
    validate_chain_id,
    validate_message_payload,
    validate_metadata,
    validate_node_id,
    validate_state_key,
    validate_timeout,
)


class TestValidateChainId:
    """Tests for validate_chain_id."""

    def test_valid_chain_id(self):
        """Test that valid chain IDs pass validation."""
        validate_chain_id("chain1")
        validate_chain_id("my_chain")
        validate_chain_id("chain-123")

    def test_invalid_type_raises_error(self):
        """Test that non-string chain IDs raise error."""
        with pytest.raises(InvalidMessageError, match="must be a string"):
            validate_chain_id(123)

        with pytest.raises(InvalidMessageError, match="must be a string"):
            validate_chain_id(None)

    def test_empty_string_raises_error(self):
        """Test that empty string raises error."""
        with pytest.raises(InvalidMessageError, match="cannot be empty"):
            validate_chain_id("")

    def test_whitespace_only_raises_error(self):
        """Test that whitespace-only string raises error."""
        with pytest.raises(InvalidMessageError, match="cannot be only whitespace"):
            validate_chain_id("   ")


class TestValidateNodeId:
    """Tests for validate_node_id."""

    def test_valid_node_id(self):
        """Test that valid node IDs pass validation."""
        validate_node_id("node1")
        validate_node_id("my_node")
        validate_node_id("node-123")

    def test_invalid_type_raises_error(self):
        """Test that non-string node IDs raise error."""
        with pytest.raises(InvalidMessageError, match="must be a string"):
            validate_node_id(123)

    def test_empty_string_raises_error(self):
        """Test that empty string raises error."""
        with pytest.raises(InvalidMessageError, match="cannot be empty"):
            validate_node_id("")

    def test_whitespace_only_raises_error(self):
        """Test that whitespace-only string raises error."""
        with pytest.raises(InvalidMessageError, match="cannot be only whitespace"):
            validate_node_id("   ")


class TestValidateMessagePayload:
    """Tests for validate_message_payload."""

    def test_valid_payload(self):
        """Test that valid payloads pass validation."""
        validate_message_payload({"data": "test"})
        validate_message_payload({})
        validate_message_payload({"nested": {"data": "test"}})

    def test_invalid_type_raises_error(self):
        """Test that non-dict payloads raise error."""
        with pytest.raises(InvalidMessageError, match="must be a dictionary"):
            validate_message_payload("not a dict")

        with pytest.raises(InvalidMessageError, match="must be a dictionary"):
            validate_message_payload([1, 2, 3])

        with pytest.raises(InvalidMessageError, match="must be a dictionary"):
            validate_message_payload(123)


class TestValidateTimeout:
    """Tests for validate_timeout."""

    def test_valid_timeout(self):
        """Test that valid timeouts pass validation."""
        validate_timeout(1.0)
        validate_timeout(5)
        validate_timeout(0.1)
        validate_timeout(None)  # None is valid (no timeout)

    def test_invalid_type_raises_error(self):
        """Test that non-numeric timeouts raise error."""
        with pytest.raises(InvalidMessageError, match="must be a number"):
            validate_timeout("not a number")

    def test_negative_timeout_raises_error(self):
        """Test that negative timeouts raise error."""
        with pytest.raises(InvalidMessageError, match="must be positive"):
            validate_timeout(-1)

    def test_zero_timeout_raises_error(self):
        """Test that zero timeout raises error."""
        with pytest.raises(InvalidMessageError, match="must be positive"):
            validate_timeout(0)


class TestValidateStateKey:
    """Tests for validate_state_key."""

    def test_valid_state_key(self):
        """Test that valid state keys pass validation."""
        validate_state_key("key1")
        validate_state_key("my_key")
        validate_state_key("key-123")

    def test_invalid_type_raises_error(self):
        """Test that non-string keys raise error."""
        with pytest.raises(InvalidMessageError, match="must be a string"):
            validate_state_key(123)

    def test_empty_string_raises_error(self):
        """Test that empty string raises error."""
        with pytest.raises(InvalidMessageError, match="cannot be empty"):
            validate_state_key("")


class TestValidateMetadata:
    """Tests for validate_metadata."""

    def test_valid_metadata(self):
        """Test that valid metadata passes validation."""
        validate_metadata({"key": "value"})
        validate_metadata({})
        validate_metadata(None)  # None is valid

    def test_invalid_type_raises_error(self):
        """Test that non-dict metadata raises error."""
        with pytest.raises(InvalidMessageError, match="must be a dictionary or None"):
            validate_metadata("not a dict")

        with pytest.raises(InvalidMessageError, match="must be a dictionary or None"):
            validate_metadata([1, 2, 3])


class TestIsValidFullNodeId:
    """Tests for is_valid_full_node_id."""

    def test_valid_full_node_id(self):
        """Test that valid full node IDs return True."""
        assert is_valid_full_node_id("chain1.node1") is True
        assert is_valid_full_node_id("my_chain.my_node") is True
        assert is_valid_full_node_id("chain-1.node-1") is True

    def test_invalid_format_returns_false(self):
        """Test that invalid formats return False."""
        assert is_valid_full_node_id("invalid") is False
        assert is_valid_full_node_id("chain1.node1.extra") is False
        assert is_valid_full_node_id("") is False
        assert is_valid_full_node_id(".") is False
        assert is_valid_full_node_id("chain1.") is False
        assert is_valid_full_node_id(".node1") is False

    def test_non_string_returns_false(self):
        """Test that non-string input returns False."""
        assert is_valid_full_node_id(123) is False
        assert is_valid_full_node_id(None) is False
        assert is_valid_full_node_id(["chain1", "node1"]) is False


class TestParseFullNodeId:
    """Tests for parse_full_node_id."""

    def test_parse_valid_full_node_id(self):
        """Test parsing valid full node IDs."""
        chain_id, node_id = parse_full_node_id("chain1.node1")
        assert chain_id == "chain1"
        assert node_id == "node1"

        chain_id, node_id = parse_full_node_id("my_chain.my_node")
        assert chain_id == "my_chain"
        assert node_id == "my_node"

    def test_parse_with_whitespace(self):
        """Test parsing strips whitespace."""
        chain_id, node_id = parse_full_node_id(" chain1 . node1 ")
        assert chain_id == "chain1"
        assert node_id == "node1"

    def test_parse_invalid_format_raises_error(self):
        """Test that invalid formats raise error."""
        with pytest.raises(InvalidMessageError, match="Invalid full node ID"):
            parse_full_node_id("invalid")

        with pytest.raises(InvalidMessageError, match="Invalid full node ID"):
            parse_full_node_id("chain1.node1.extra")

        with pytest.raises(InvalidMessageError, match="Invalid full node ID"):
            parse_full_node_id("")
