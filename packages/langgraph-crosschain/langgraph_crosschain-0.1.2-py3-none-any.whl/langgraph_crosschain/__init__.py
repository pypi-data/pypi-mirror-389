"""
LangGraph Cross-Chain Communication Framework

A Python package extending LangGraph to enable cross-chain node communication,
allowing nodes in different chains to call and communicate with each other directly.
"""

__version__ = "0.1.0"
__author__ = "Your Name"
__license__ = "MIT"

from langgraph_crosschain import exceptions
from langgraph_crosschain.communication.message_router import MessageRouter
from langgraph_crosschain.core.chain_registry import ChainRegistry
from langgraph_crosschain.core.cross_chain_node import CrossChainMessage, CrossChainNode
from langgraph_crosschain.logging import configure_logging, get_logger
from langgraph_crosschain.state.shared_state import SharedStateManager

__all__ = [
    "ChainRegistry",
    "CrossChainNode",
    "CrossChainMessage",
    "MessageRouter",
    "SharedStateManager",
    "get_logger",
    "configure_logging",
    "exceptions",
]
