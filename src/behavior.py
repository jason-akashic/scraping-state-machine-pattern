"""
Behavior - Adaptive behavior scaling for scraping state machine.

This module implements adaptive behavior profiles that scale between
machine-like (fast, efficient) and human-like (slow, stealthy) based
on success metrics and bot detection signals.
"""

from dataclasses import dataclass
from typing import Tuple, Optional


@dataclass
class BehaviorProfile:
    """
    Defines behavior parameters for state execution.
    
    Represents a point on the spectrum between machine-like (fast, efficient)
    and human-like (slow, stealthy) behavior.
    """
    
    delay_range: Tuple[float, float]
    """
    Min/max delay between actions in seconds.
    
    Example:
        (0.0, 0.1) - Machine-like: minimal delays
        (1.0, 3.0) - Human-like: realistic delays
    """
    
    mouse_movement: bool
    """Whether to simulate mouse movements before clicks."""
    
    scroll_behavior: bool
    """Whether to simulate natural scrolling patterns."""
    
    typing_cadence: Optional[Tuple[float, float]]
    """
    Min/max delay between keystrokes in seconds.
    
    None = no typing simulation (instant text input)
    (0.05, 0.15) = human-like typing speed
    """
    
    jitter: float
    """
    Randomness factor (0.0-1.0).
    
    - 0.0: No randomness (perfectly consistent)
    - 1.0: Maximum randomness (highly variable)
    """
    
    def __repr__(self) -> str:
        delay_str = f"{self.delay_range[0]:.2f}-{self.delay_range[1]:.2f}s"
        typing_str = f"{self.typing_cadence[0]:.2f}-{self.typing_cadence[1]:.2f}s" if self.typing_cadence else "instant"
        return (f"BehaviorProfile(delay={delay_str}, mouse={self.mouse_movement}, "
                f"scroll={self.scroll_behavior}, typing={typing_str}, jitter={self.jitter:.2f})")


class BehaviorScaler:
    """
    Scales behavior between machine-like and human-like profiles.
    
    Adapts behavior based on success metrics:
    - High success rate → decrease humanness (faster, more efficient)
    - Low success rate → increase humanness (slower, more stealthy)
    
    This implements the "bounce between machine-like and human-like"
    strategy: optimize for speed when safe, stealth when needed.
    """
    
    def __init__(self, min_profile: BehaviorProfile, max_profile: BehaviorProfile):
        """
        Initialize behavior scaler.
        
        Args:
            min_profile: Machine-like profile (fast, efficient, level 0.0)
            max_profile: Human-like profile (slow, stealthy, level 1.0)
        """
        self.min_profile = min_profile
        self.max_profile = max_profile
        self.current_level: float = 0.0  # Start machine-like
    
    def scale(self, level: float) -> BehaviorProfile:
        """
        Interpolate between min and max profiles based on level.
        
        Args:
            level: Behavior level (0.0 = machine-like, 1.0 = human-like)
        
        Returns:
            Interpolated BehaviorProfile
        """
        # Clamp level to [0.0, 1.0]
        level = max(0.0, min(1.0, level))
        
        # Linear interpolation for numeric values
        delay_min = self._interpolate(
            self.min_profile.delay_range[0],
            self.max_profile.delay_range[0],
            level
        )
        delay_max = self._interpolate(
            self.min_profile.delay_range[1],
            self.max_profile.delay_range[1],
            level
        )
        
        typing_cadence = None
        if self.min_profile.typing_cadence and self.max_profile.typing_cadence:
            typing_min = self._interpolate(
                self.min_profile.typing_cadence[0],
                self.max_profile.typing_cadence[0],
                level
            )
            typing_max = self._interpolate(
                self.min_profile.typing_cadence[1],
                self.max_profile.typing_cadence[1],
                level
            )
            typing_cadence = (typing_min, typing_max)
        elif self.max_profile.typing_cadence:
            # If only max has typing, interpolate from 0
            typing_min = self._interpolate(0.0, self.max_profile.typing_cadence[0], level)
            typing_max = self._interpolate(0.0, self.max_profile.typing_cadence[1], level)
            typing_cadence = (typing_min, typing_max)
        
        jitter = self._interpolate(
            self.min_profile.jitter,
            self.max_profile.jitter,
            level
        )
        
        # Boolean values: switch at 0.5 threshold
        mouse_movement = level >= 0.5 if self.max_profile.mouse_movement else False
        scroll_behavior = level >= 0.5 if self.max_profile.scroll_behavior else False
        
        return BehaviorProfile(
            delay_range=(delay_min, delay_max),
            mouse_movement=mouse_movement,
            scroll_behavior=scroll_behavior,
            typing_cadence=typing_cadence,
            jitter=jitter
        )
    
    def escalate(self, success_rate: float, cascade_metrics: Optional[Dict[str, float]] = None,
                 adjustment_rate: float = 0.1) -> BehaviorProfile:
        """
        Adjust behavior level based on success metrics and cascade performance.
        
        Args:
            success_rate: Recent success rate (0.0-1.0)
            cascade_metrics: Optional dict with cascade performance metrics:
                - 'avg_position': Average cascade position (0.0 = primary, 1.0 = last)
                - 'xpath_success_rate': Success rate of XPath selectors (0.0-1.0)
                - 'css_success_rate': Success rate of CSS selectors (0.0-1.0)
                - 'text_fallback_rate': Rate of falling back to text selectors (0.0-1.0)
                - 'visual_fallback_rate': Rate of falling back to visual selectors (0.0-1.0)
                - 'primary_success_rate': Success rate of primary selectors (0.0-1.0)
            adjustment_rate: How much to adjust level per call (default 0.1)
        
        Returns:
            Updated BehaviorProfile
        
        Logic:
            - High success (>0.95) + primary selectors working → decrease humanness (faster)
            - Frequent text/visual fallbacks → increase humanness (more stealth)
            - Medium success (0.7-0.95) → maintain current
            - Low success (<0.7) → increase humanness (more stealth)
        """
        # Adjust success rate based on cascade position
        adjusted_success_rate = success_rate
        
        if cascade_metrics:
            avg_position = cascade_metrics.get('avg_position', 0.0)
            xpath_success_rate = cascade_metrics.get('xpath_success_rate', 1.0)
            css_success_rate = cascade_metrics.get('css_success_rate', 1.0)
            text_fallback_rate = cascade_metrics.get('text_fallback_rate', 0.0)
            visual_fallback_rate = cascade_metrics.get('visual_fallback_rate', 0.0)
            primary_success_rate = cascade_metrics.get('primary_success_rate', 1.0)
            
            # If XPath/CSS (primary selectors) are failing, that's a strong signal
            # XPath and CSS are the most reliable - if they fail, site structure changed
            primary_selector_rate = (xpath_success_rate + css_success_rate) / 2.0
            if primary_selector_rate < 0.7:  # Less than 70% success on XPath/CSS
                adjusted_success_rate = success_rate * 0.8  # Penalize significantly
            
            # If we're frequently falling back to text/visual, that's a bad sign
            # Penalize success rate (indicates site changes or blocking)
            total_fallback_rate = text_fallback_rate + visual_fallback_rate
            if total_fallback_rate > 0.2:  # More than 20% fallbacks
                adjusted_success_rate = success_rate * (1.0 - total_fallback_rate * 0.4)
            
            # If primary selectors (XPath/CSS) consistently work, boost success rate
            # (indicates stable site structure, no detection)
            if primary_selector_rate > 0.9 and avg_position < 0.1:
                adjusted_success_rate = min(1.0, success_rate * 1.1)
            
            # If average position is high (frequently using fallbacks), penalize
            if avg_position > 0.5:  # More than halfway through cascade
                adjusted_success_rate = success_rate * (1.0 - avg_position * 0.3)
        
        # Use adjusted success rate for escalation
        if adjusted_success_rate > 0.95:
            # High success: decrease humanness (move toward machine-like)
            self.current_level = max(0.0, self.current_level - adjustment_rate)
        elif adjusted_success_rate < 0.7:
            # Low success: increase humanness (move toward human-like)
            self.current_level = min(1.0, self.current_level + adjustment_rate)
        # Medium success (0.7-0.95): maintain current level
        
        return self.scale(self.current_level)
    
    def _interpolate(self, min_val: float, max_val: float, level: float) -> float:
        """Linear interpolation between min and max values."""
        return min_val + (max_val - min_val) * level
    
    def get_current_profile(self) -> BehaviorProfile:
        """Get the current behavior profile."""
        return self.scale(self.current_level)
    
    def reset(self):
        """Reset to machine-like behavior (level 0.0)."""
        self.current_level = 0.0


# Predefined profiles for common use cases

MACHINE_LIKE_PROFILE = BehaviorProfile(
    delay_range=(0.0, 0.1),      # Minimal delays
    mouse_movement=False,         # No mouse simulation
    scroll_behavior=False,        # No scroll simulation
    typing_cadence=None,          # Instant text input
    jitter=0.0                    # No randomness
)

HUMAN_LIKE_PROFILE = BehaviorProfile(
    delay_range=(1.0, 3.0),      # Realistic delays
    mouse_movement=True,          # Simulate mouse movements
    scroll_behavior=True,         # Natural scrolling
    typing_cadence=(0.05, 0.15),  # Human typing speed
    jitter=0.3                    # Moderate randomness
)

