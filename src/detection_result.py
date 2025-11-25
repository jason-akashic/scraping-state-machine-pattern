"""
DetectionResult - Result object for state detection with confidence scoring.

This module provides the DetectionResult class that encapsulates detection
outcomes with confidence scores and reasoning, enabling more sophisticated
state detection logic.
"""

from typing import Optional
from dataclasses import dataclass


@dataclass
class DetectionResult:
    """
    Result of a state detection operation.
    
    Encapsulates whether a state is detected, with confidence score and
    reasoning for debugging and decision-making.
    """
    
    detected: bool
    """Whether the state is currently active."""
    
    confidence: float = 1.0
    """
    Confidence score between 0.0 and 1.0.
    
    - 1.0: Certain match (e.g., exact URL match)
    - 0.7-0.9: Strong match (e.g., multiple indicators)
    - 0.4-0.6: Moderate match (e.g., single weak indicator)
    - 0.0-0.3: Weak match or no match
    """
    
    reasoning: Optional[str] = None
    """
    Human-readable explanation of why this result was returned.
    
    Useful for debugging and understanding detection logic.
    Example: "URL pattern '/login' matched with high confidence"
    """
    
    def __bool__(self) -> bool:
        """Allow DetectionResult to be used in boolean contexts."""
        return self.detected
    
    def __repr__(self) -> str:
        confidence_str = f"{self.confidence:.2f}"
        reasoning_str = f" ({self.reasoning})" if self.reasoning else ""
        return f"DetectionResult(detected={self.detected}, confidence={confidence_str}{reasoning_str})"

