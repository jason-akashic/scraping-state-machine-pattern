"""
Scraping State Machine Pattern - Core Package

This package provides the core components for building state machine-based
web scrapers with cascading selectors and adaptive behavior.
"""

from .base_state import BaseState
from .state_detector import (
    StateDetector,
    URLPatternDetector,
    DOMElementDetector,
    TextContentDetector,
    CompositeDetector,
    CascadeDetector,
    CascadingStateDetector,  # Alias for CascadeDetector
)
from .cascade import CascadeExecutor, CascadeSelector, SelectorType, create_cascade

__all__ = [
    "BaseState",
    "StateDetector",
    "URLPatternDetector",
    "DOMElementDetector",
    "TextContentDetector",
    "CompositeDetector",
    "CascadeDetector",
    "CascadingStateDetector",
    "CascadeExecutor",
    "CascadeSelector",
    "SelectorType",
    "create_cascade",
]

