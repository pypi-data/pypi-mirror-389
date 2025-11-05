"""
Validation utilities for the cross-chain framework.

This module provides validation functions for common operations.
"""

from typing import Any, Optional

from langgraph_crosschain.exceptions import InvalidMessageError


def validate_chain_id(chain_id: Any) -> None:
    """
    Validate a chain ID.

    Args:
        chain_id: The chain ID to validate

    Raises:
        InvalidMessageError: If the chain ID is invalid
    """
    if not isinstance(chain_id, str):
        raise InvalidMessageError(f"Chain ID must be a string, got {type(chain_id)}")

    if not chain_id:
        raise InvalidMessageError("Chain ID cannot be empty")

    if not chain_id.strip():
        raise InvalidMessageError("Chain ID cannot be only whitespace")


def validate_node_id(node_id: Any) -> None:
    """
    Validate a node ID.

    Args:
        node_id: The node ID to validate

    Raises:
        InvalidMessageError: If the node ID is invalid
    """
    if not isinstance(node_id, str):
        raise InvalidMessageError(f"Node ID must be a string, got {type(node_id)}")

    if not node_id:
        raise InvalidMessageError("Node ID cannot be empty")

    if not node_id.strip():
        raise InvalidMessageError("Node ID cannot be only whitespace")


def validate_message_payload(payload: Any) -> None:
    """
    Validate a message payload.

    Args:
        payload: The payload to validate

    Raises:
        InvalidMessageError: If the payload is invalid
    """
    if not isinstance(payload, dict):
        raise InvalidMessageError(f"Message payload must be a dictionary, got {type(payload)}")


def validate_timeout(timeout: Optional[float]) -> None:
    """
    Validate a timeout value.

    Args:
        timeout: The timeout value to validate

    Raises:
        InvalidMessageError: If the timeout is invalid
    """
    if timeout is not None:
        if not isinstance(timeout, (int, float)):
            raise InvalidMessageError(f"Timeout must be a number, got {type(timeout)}")

        if timeout <= 0:
            raise InvalidMessageError(f"Timeout must be positive, got {timeout}")


def validate_state_key(key: Any) -> None:
    """
    Validate a state key.

    Args:
        key: The state key to validate

    Raises:
        InvalidMessageError: If the key is invalid
    """
    if not isinstance(key, str):
        raise InvalidMessageError(f"State key must be a string, got {type(key)}")

    if not key:
        raise InvalidMessageError("State key cannot be empty")


def validate_metadata(metadata: Any) -> None:
    """
    Validate metadata.

    Args:
        metadata: The metadata to validate

    Raises:
        InvalidMessageError: If the metadata is invalid
    """
    if metadata is not None and not isinstance(metadata, dict):
        raise InvalidMessageError(f"Metadata must be a dictionary or None, got {type(metadata)}")


def is_valid_full_node_id(full_id: str) -> bool:
    """
    Check if a string is a valid full node ID (chain_id.node_id).

    Args:
        full_id: The full node ID to check

    Returns:
        True if valid, False otherwise

    Example:
        >>> is_valid_full_node_id("chain1.node1")
        True
        >>> is_valid_full_node_id("invalid")
        False
    """
    if not isinstance(full_id, str):
        return False

    parts = full_id.split(".")
    if len(parts) != 2:
        return False

    chain_id, node_id = parts
    return bool(chain_id.strip() and node_id.strip())


def parse_full_node_id(full_id: str) -> tuple[str, str]:
    """
    Parse a full node ID into chain_id and node_id.

    Args:
        full_id: The full node ID (chain_id.node_id)

    Returns:
        Tuple of (chain_id, node_id)

    Raises:
        InvalidMessageError: If the full ID is invalid

    Example:
        >>> parse_full_node_id("chain1.node1")
        ('chain1', 'node1')
    """
    if not is_valid_full_node_id(full_id):
        raise InvalidMessageError(
            f"Invalid full node ID format: '{full_id}'. Expected 'chain_id.node_id'"
        )

    chain_id, node_id = full_id.split(".", 1)
    return chain_id.strip(), node_id.strip()
