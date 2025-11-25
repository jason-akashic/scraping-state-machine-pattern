"""
BaseState - Abstract base class for all states in the scraping state machine.

⚠️ NOTE: This is a conceptual interface definition. Production implementations
would include additional methods, error handling, logging, and integration with
browser automation frameworks.

This module defines the core interface that all states must implement.
"""

from abc import ABC, abstractmethod
from typing import Optional, Dict, Any


class BaseState(ABC):
    """
    Abstract base class for states in the scraping state machine.
    
    Each state represents a distinct page context or interaction phase.
    States are responsible for:
    1. Detecting when they're active
    2. Executing their logic (scraping, navigation)
    3. Determining the next state
    4. Cleaning up when exiting
    """
    
    def __init__(self, name: str):
        """
        Initialize the state.
        
        Args:
            name: Unique identifier for this state
        """
        self.name = name
    
    @abstractmethod
    def detect(self, context: Dict[str, Any]) -> bool:
        """
        Determine if this state is currently active.
        
        Detection strategies can include:
        - URL pattern matching
        - DOM element presence
        - Text content matching
        - Visual indicators
        
        Args:
            context: Context object containing browser, session data, etc.
            
        Returns:
            True if this state is active, False otherwise
        """
        pass
    
    def enter(self, context: Dict[str, Any]) -> None:
        """
        Called when entering this state.
        
        Use this for:
        - Setting up state-specific resources
        - Logging state entry
        - Initializing state variables
        
        Args:
            context: Context object
        """
        pass
    
    @abstractmethod
    def execute(self, context: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Execute the main logic of this state.
        
        This is where the actual scraping, navigation, or interaction happens.
        
        Args:
            context: Context object
            
        Returns:
            Optional data extracted or modified by this state
        """
        pass
    
    @abstractmethod
    def transition(self, context: Dict[str, Any]) -> Optional[str]:
        """
        Determine the next state to transition to.
        
        Args:
            context: Context object
            
        Returns:
            Name of next state, or None if workflow is complete
        """
        pass
    
    def exit(self, context: Dict[str, Any]) -> None:
        """
        Called when exiting this state.
        
        Use this for:
        - Cleaning up resources
        - Logging state exit
        - Saving state data
        
        Args:
            context: Context object
        """
        pass
    
    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}(name='{self.name}')>"

