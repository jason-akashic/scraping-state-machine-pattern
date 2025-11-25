"""
StateDetector - Interface for detecting when states are active.

This module defines detection strategies used by states to identify
their context (URL patterns, DOM elements, text content, etc.).
"""

from typing import List, Callable, Dict, Any, Optional
from abc import ABC, abstractmethod
from .detection_result import DetectionResult


class StateDetector(ABC):
    """
    Abstract base class for state detection strategies.
    
    Detectors determine if a state is active by checking various
    indicators (URL, DOM, text, visual).
    """
    
    @abstractmethod
    def detect(self, context: Dict[str, Any]) -> DetectionResult:
        """
        Check if the state is active.
        
        Args:
            context: Context object with browser, URL, etc.
            
        Returns:
            DetectionResult with detected status, confidence, and reasoning
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
    
    def detect(self, context: Dict[str, Any]) -> DetectionResult:
        """Check if current URL matches any pattern."""
        url = context.get('url', '')
        
        if self.use_regex:
            for pattern in self.compiled_patterns:
                if pattern.search(url):
                    return DetectionResult(
                        detected=True,
                        confidence=1.0,
                        reasoning=f"URL matched regex pattern: {pattern.pattern}"
                    )
        else:
            for pattern in self.patterns:
                if pattern in url:
                    return DetectionResult(
                        detected=True,
                        confidence=1.0,
                        reasoning=f"URL contains pattern: {pattern}"
                    )
        
        return DetectionResult(
            detected=False,
            confidence=0.0,
            reasoning=f"URL '{url}' did not match any patterns"
        )


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
    
    def detect(self, context: Dict[str, Any]) -> DetectionResult:
        """Check if any selector matches elements in the DOM."""
        driver = context.get('driver')
        if not driver:
            return DetectionResult(
                detected=False,
                confidence=0.0,
                reasoning="No driver available in context"
            )
        
        for selector in self.selectors:
            try:
                if self.selector_type == 'xpath':
                    elements = driver.find_elements_by_xpath(selector)
                else:  # css
                    elements = driver.find_elements_by_css_selector(selector)
                
                if elements:
                    return DetectionResult(
                        detected=True,
                        confidence=0.9,
                        reasoning=f"Found {len(elements)} element(s) using {self.selector_type} selector: {selector}"
                    )
            except Exception as e:
                continue
        
        return DetectionResult(
            detected=False,
            confidence=0.0,
            reasoning=f"No elements found matching any {self.selector_type} selectors"
        )


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
    
    def detect(self, context: Dict[str, Any]) -> DetectionResult:
        """Check if any text pattern appears in page content."""
        driver = context.get('driver')
        if not driver:
            return DetectionResult(
                detected=False,
                confidence=0.0,
                reasoning="No driver available in context"
            )
        
        try:
            page_text = driver.page_source
            if not self.case_sensitive:
                page_text = page_text.lower()
            
            for pattern in self.text_patterns:
                search_text = pattern if self.case_sensitive else pattern.lower()
                if search_text in page_text:
                    return DetectionResult(
                        detected=True,
                        confidence=0.7,  # Text matching is less reliable than URL/DOM
                        reasoning=f"Found text pattern in page: '{pattern}'"
                    )
        except Exception as e:
            return DetectionResult(
                detected=False,
                confidence=0.0,
                reasoning=f"Error reading page source: {str(e)}"
            )
        
        return DetectionResult(
            detected=False,
            confidence=0.0,
            reasoning=f"None of the text patterns found in page content"
        )


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
    
    def detect(self, context: Dict[str, Any]) -> DetectionResult:
        """Check detectors based on logic operator."""
        results = [detector.detect(context) for detector in self.detectors]
        
        if self.logic == 'AND':
            detected = all(r.detected for r in results)
            # For AND, use minimum confidence (all must match)
            confidence = min(r.confidence for r in results) if results else 0.0
            reasoning = f"AND logic: {sum(1 for r in results if r.detected)}/{len(results)} detectors matched"
        else:  # OR
            detected = any(r.detected for r in results)
            # For OR, use maximum confidence (best match wins)
            confidence = max(r.confidence for r in results) if results else 0.0
            reasoning = f"OR logic: {sum(1 for r in results if r.detected)}/{len(results)} detectors matched"
        
        return DetectionResult(
            detected=detected,
            confidence=confidence,
            reasoning=reasoning
        )


class CascadeDetector(StateDetector):
    """
    Cascading state detector that tries multiple detection methods in order.
    
    Tries detectors in order of reliability (most likely to succeed first):
    1. DOM element detection (most reliable - checks actual page structure)
    2. URL pattern matching (fast, reliable if URL is stable)
    3. Text content matching (less reliable, slower, prone to false positives)
    4. Visual detection (least reliable, slowest, requires OCR/ML)
    
    Stops at the first detector that returns a positive result with sufficient
    confidence, providing resilience when one detection method fails.
    
    Example:
        detector = CascadeDetector([
            DOMElementDetector(["//form[@id='login']"]),  # Most reliable: page structure
            URLPatternDetector(["/login"]),                # Fast fallback: URL
            TextContentDetector(["Sign in"]),              # Last resort: text
        ])
    """
    
    def __init__(self, detectors: List[StateDetector], min_confidence: float = 0.5):
        """
        Initialize cascade detector.
        
        Args:
            detectors: Ordered list of detectors to try (most reliable first)
            min_confidence: Minimum confidence threshold to accept a result
        """
        self.detectors = detectors
        self.min_confidence = min_confidence
    
    def detect(self, context: Dict[str, Any]) -> DetectionResult:
        """
        Try detectors in cascade order until one succeeds.
        
        Returns the first detector result that:
        - Has detected=True
        - Has confidence >= min_confidence
        
        If no detector meets criteria, returns the best result (highest confidence).
        """
        best_result = DetectionResult(
            detected=False,
            confidence=0.0,
            reasoning="No detectors tried yet"
        )
        
        for i, detector in enumerate(self.detectors):
            try:
                result = detector.detect(context)
                
                # If we get a positive detection with sufficient confidence, use it
                if result.detected and result.confidence >= self.min_confidence:
                    return DetectionResult(
                        detected=True,
                        confidence=result.confidence,
                        reasoning=f"Cascade: {result.reasoning} (stopped at detector {i+1}/{len(self.detectors)})"
                    )
                
                # Track best result so far
                if result.confidence > best_result.confidence:
                    best_result = result
                    
            except Exception as e:
                # Continue to next detector on error
                continue
        
        # Return best result found (may be negative if all failed)
        if not best_result.detected:
            best_result.reasoning = f"Cascade: All {len(self.detectors)} detectors failed. Best: {best_result.reasoning}"
        
        return best_result


