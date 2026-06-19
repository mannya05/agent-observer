"""
AgentObserver — Real-time observability and auto-debugging toolkit for AI agents.
"""

from .core.observer import AgentObserver
from .core.hallucination_scorer import HallucinationScorer
from .core.rag_monitor import RAGMonitor
from .core.comparator import AgentComparator
from .core.postmortem import generate_postmortem

try:
    from .core.langchain_plugin import AgentObserverCallback
except ImportError:
    pass

__version__ = "0.1.0"
__author__ = "Manya"
__all__ = [
    "AgentObserver",
    "HallucinationScorer", 
    "RAGMonitor",
    "AgentComparator",
    "generate_postmortem",
    "AgentObserverCallback",
]
