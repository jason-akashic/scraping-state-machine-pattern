"""
CascadeMetrics - Tracks cascade selector performance for behavior scaling.

This module provides utilities to track which selectors in a cascade succeed,
enabling behavior scaling to adjust based on cascade position (primary vs fallback).
"""

from typing import Dict, Optional
from .cascade import SelectorType


class CascadeMetrics:
    """
    Tracks cascade selector performance metrics.
    
    Monitors which selectors succeed in cascades to provide signals for
    behavior scaling. If we're frequently falling back to text/visual
    selectors, that indicates site changes or bot detection.
    """
    
    def __init__(self):
        """Initialize empty metrics."""
        self.total_attempts: int = 0
        self.primary_successes: int = 0  # Position 0 (primary selector)
        self.fallback_successes: int = 0  # Position > 0
        self.text_fallbacks: int = 0  # SelectorType.TEXT
        self.visual_fallbacks: int = 0  # SelectorType.VISUAL
        self.position_sum: float = 0.0  # Sum of positions for average calculation
        self.cascade_length: int = 0  # Length of cascade (for normalization)
    
    def record_success(self, position: int, selector_type: SelectorType, cascade_length: int):
        """
        Record a successful cascade execution.
        
        Args:
            position: Index of selector that succeeded (0 = primary)
            selector_type: Type of selector that succeeded
            cascade_length: Total length of cascade (for normalization)
        """
        self.total_attempts += 1
        self.cascade_length = cascade_length
        
        if position == 0:
            self.primary_successes += 1
        else:
            self.fallback_successes += 1
        
        # Normalize position to 0.0-1.0 scale
        normalized_position = position / max(1, cascade_length - 1) if cascade_length > 1 else 0.0
        self.position_sum += normalized_position
        
        if selector_type == SelectorType.TEXT:
            self.text_fallbacks += 1
        elif selector_type == SelectorType.VISUAL:
            self.visual_fallbacks += 1
    
    def record_failure(self):
        """Record a failed cascade (all selectors failed)."""
        self.total_attempts += 1
    
    def get_metrics(self) -> Dict[str, float]:
        """
        Get current metrics as a dictionary for behavior scaling.
        
        Returns:
            Dictionary with:
            - 'avg_position': Average cascade position (0.0 = primary, 1.0 = last)
            - 'text_fallback_rate': Rate of text selector fallbacks (0.0-1.0)
            - 'visual_fallback_rate': Rate of visual selector fallbacks (0.0-1.0)
            - 'primary_success_rate': Success rate of primary selectors (0.0-1.0)
            - 'overall_success_rate': Overall success rate (0.0-1.0)
        """
        if self.total_attempts == 0:
            return {
                'avg_position': 0.0,
                'text_fallback_rate': 0.0,
                'visual_fallback_rate': 0.0,
                'primary_success_rate': 1.0,
                'overall_success_rate': 1.0,
            }
        
        total_successes = self.primary_successes + self.fallback_successes
        
        return {
            'avg_position': self.position_sum / max(1, total_successes),
            'text_fallback_rate': self.text_fallbacks / self.total_attempts,
            'visual_fallback_rate': self.visual_fallbacks / self.total_attempts,
            'primary_success_rate': self.primary_successes / max(1, self.total_attempts),
            'overall_success_rate': total_successes / self.total_attempts,
        }
    
    def reset(self):
        """Reset all metrics to zero."""
        self.total_attempts = 0
        self.primary_successes = 0
        self.fallback_successes = 0
        self.text_fallbacks = 0
        self.visual_fallbacks = 0
        self.position_sum = 0.0
        self.cascade_length = 0
    
    def __repr__(self) -> str:
        metrics = self.get_metrics()
        return (f"CascadeMetrics(attempts={self.total_attempts}, "
                f"primary_success={self.primary_successes}, "
                f"avg_position={metrics['avg_position']:.2f}, "
                f"text_fallback={metrics['text_fallback_rate']:.2f})")

