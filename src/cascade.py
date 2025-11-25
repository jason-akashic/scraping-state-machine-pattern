"""
Cascade - Cascading selector strategy for resilient element detection.

This module implements the cascade pattern: try primary selector,
fall back to alternatives if it fails, and finally use visual/text
detection as last resort.
"""

from typing import List, Callable, Dict, Any, Optional, Tuple
from enum import Enum


class SelectorType(Enum):
    """Types of selectors in the cascade."""
    XPATH = "xpath"
    CSS = "css"
    TEXT = "text"
    VISUAL = "visual"


class CascadeSelector:
    """
    Represents a single selector in the cascade.
    
    Each selector has a type (XPath, CSS, text, visual) and
    the actual selector value or detection function.
    """
    
    def __init__(self, selector: str, selector_type: SelectorType, 
                 description: str = ""):
        """
        Initialize cascade selector.
        
        Args:
            selector: The selector string or detection function
            selector_type: Type of selector
            description: Human-readable description
        """
        self.selector = selector
        self.selector_type = selector_type
        self.description = description


class CascadeExecutor:
    """
    Executes cascading selector strategy.
    
    Tries selectors in order until one succeeds. Provides resilience
    when sites change their markup.
    """
    
    def __init__(self, selectors: List[CascadeSelector]):
        """
        Initialize cascade executor.
        
        Args:
            selectors: Ordered list of selectors to try
        """
        self.selectors = selectors
    
    def execute(self, context: Dict[str, Any]) -> Optional[Any]:
        """
        Execute cascade: try each selector until one succeeds.
        
        Args:
            context: Context object with browser/driver
            
        Returns:
            Found element(s) or None if all selectors fail
        """
        driver = context.get('driver')
        if not driver:
            return None
        
        for selector in self.selectors:
            try:
                result = self._try_selector(selector, context)
                if result:
                    return result
            except Exception as e:
                # Log error but continue to next selector
                continue
        
        # All selectors failed
        return None
    
    def _try_selector(self, selector: CascadeSelector, 
                     context: Dict[str, Any]) -> Optional[Any]:
        """
        Try a single selector.
        
        Args:
            selector: CascadeSelector to try
            context: Context object
            
        Returns:
            Found element(s) or None
        """
        driver = context.get('driver')
        
        if selector.selector_type == SelectorType.XPATH:
            elements = driver.find_elements_by_xpath(selector.selector)
            return elements if elements else None
        
        elif selector.selector_type == SelectorType.CSS:
            elements = driver.find_elements_by_css_selector(selector.selector)
            return elements if elements else None
        
        elif selector.selector_type == SelectorType.TEXT:
            # Text-based detection: search page source
            page_text = driver.page_source
            if selector.selector in page_text:
                # Return text match indicator
                return True
            return None
        
        elif selector.selector_type == SelectorType.VISUAL:
            # Visual detection: screenshot + OCR or ML-based element detection
            #
            # This is an extension point for production implementations.
            # Visual detection would typically involve:
            #   1. Taking a screenshot of the page/element
            #   2. Using OCR (e.g., pytesseract, EasyOCR) to extract text
            #   3. Or using ML-based element detection (e.g., computer vision models)
            #   4. Matching against expected visual patterns
            #
            # This is intentionally not implemented here to keep the pattern
            # zero-dependency and focused on architecture, not implementation details.
            # Production implementations would add this based on their specific needs.
            return None
        
        return None


def create_cascade(selectors: List[Tuple[str, SelectorType, str]]) -> CascadeExecutor:
    """
    Helper function to create a CascadeExecutor from a list of tuples.
    
    Args:
        selectors: List of (selector, type, description) tuples
        
    Returns:
        CascadeExecutor instance
        
    Example:
        cascade = create_cascade([
            ("//div[@class='profile-name']", SelectorType.XPATH, "Primary name selector"),
            ("//h1[contains(@class, 'name')]", SelectorType.XPATH, "Fallback name selector"),
            ("Profile Name", SelectorType.TEXT, "Text-based detection")
        ])
    """
    cascade_selectors = [
        CascadeSelector(sel, sel_type, desc)
        for sel, sel_type, desc in selectors
    ]
    return CascadeExecutor(cascade_selectors)


