"""
StateDetector - Interface for detecting when states are active.

This module defines detection strategies used by states to identify
their context (URL patterns, DOM elements, text content, etc.).
"""

from typing import List, Callable, Dict, Any, Optional
from abc import ABC, abstractmethod


class StateDetector(ABC):
    """
    Abstract base class for state detection strategies.
    
    Detectors determine if a state is active by checking various
    indicators (URL, DOM, text, visual).
    """
    
    @abstractmethod
    def detect(self, context: Dict[str, Any]) -> bool:
        """
        Check if the state is active.
        
        Args:
            context: Context object with browser, URL, etc.
            
        Returns:
            True if state is active
        """
        pass


class URLPatternDetector(StateDetector):
    """
    Detects state based on URL patterns.
    
    Example:
        detector = URLPatternDetector([r"/login", r"/sign-in"])
    """
    
    def __init__(self, patterns: List[str], use_regex: bool = False):
        """
        Initialize URL pattern detector.
        
        Args:
            patterns: List of URL patterns to match
            use_regex: If True, treat patterns as regex; otherwise string matching
        """
        self.patterns = patterns
        self.use_regex = use_regex
        
        if use_regex:
            import re
            self.compiled_patterns = [re.compile(p) for p in patterns]
        else:
            self.compiled_patterns = None
    
    def detect(self, context: Dict[str, Any]) -> bool:
        """Check if current URL matches any pattern."""
        url = context.get('url', '')
        
        if self.use_regex:
            return any(pattern.search(url) for pattern in self.compiled_patterns)
        else:
            return any(pattern in url for pattern in self.patterns)


class DOMElementDetector(StateDetector):
    """
    Detects state based on presence of DOM elements.
    
    Example:
        detector = DOMElementDetector("//form[@id='login-form']")
    """
    
    def __init__(self, selectors: List[str], selector_type: str = 'xpath'):
        """
        Initialize DOM element detector.
        
        Args:
            selectors: List of XPath or CSS selectors
            selector_type: 'xpath' or 'css'
        """
        self.selectors = selectors
        self.selector_type = selector_type
    
    def detect(self, context: Dict[str, Any]) -> bool:
        """Check if any selector matches elements in the DOM."""
        driver = context.get('driver')
        if not driver:
            return False
        
        for selector in self.selectors:
            try:
                if self.selector_type == 'xpath':
                    elements = driver.find_elements_by_xpath(selector)
                else:  # css
                    elements = driver.find_elements_by_css_selector(selector)
                
                if elements:
                    return True
            except Exception:
                continue
        
        return False


class TextContentDetector(StateDetector):
    """
    Detects state based on text content in the page.
    
    Example:
        detector = TextContentDetector(["Welcome", "Dashboard"])
    """
    
    def __init__(self, text_patterns: List[str], case_sensitive: bool = False):
        """
        Initialize text content detector.
        
        Args:
            text_patterns: List of text strings to search for
            case_sensitive: Whether matching is case-sensitive
        """
        self.text_patterns = text_patterns
        self.case_sensitive = case_sensitive
    
    def detect(self, context: Dict[str, Any]) -> bool:
        """Check if any text pattern appears in page content."""
        driver = context.get('driver')
        if not driver:
            return False
        
        try:
            page_text = driver.page_source
            if not self.case_sensitive:
                page_text = page_text.lower()
            
            for pattern in self.text_patterns:
                search_text = pattern if self.case_sensitive else pattern.lower()
                if search_text in page_text:
                    return True
        except Exception:
            pass
        
        return False


class CompositeDetector(StateDetector):
    """
    Combines multiple detectors with AND/OR logic.
    
    Example:
        detector = CompositeDetector(
            [url_detector, dom_detector],
            logic='AND'
        )
    """
    
    def __init__(self, detectors: List[StateDetector], logic: str = 'OR'):
        """
        Initialize composite detector.
        
        Args:
            detectors: List of StateDetector instances
            logic: 'AND' (all must match) or 'OR' (any must match)
        """
        self.detectors = detectors
        self.logic = logic.upper()
    
    def detect(self, context: Dict[str, Any]) -> bool:
        """Check detectors based on logic operator."""
        results = [detector.detect(context) for detector in self.detectors]
        
        if self.logic == 'AND':
            return all(results)
        else:  # OR
            return any(results)


