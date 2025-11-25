"""
Simple Example - Conceptual demonstration of the Scraping State Machine Pattern.

⚠️ IMPORTANT: This is CONCEPTUAL/PSEUDOCODE - not production-ready code.

This example illustrates the pattern's structure and philosophy. It shows:
- How states are defined
- How detection works
- How transitions occur
- How cascades provide resilience

It does NOT include:
- Actual browser automation (Selenium/Playwright integration)
- Full error handling
- Production-ready selectors
- Complete state machine executor
- Human emulation implementation
- Data persistence

The goal is to demonstrate understanding of the pattern, not provide a working scraper.
"""

from typing import Dict, Any, Optional
from src.base_state import BaseState
from src.state_detector import URLPatternDetector, DOMElementDetector, TextContentDetector, CascadeDetector
from src.cascade import CascadeExecutor, CascadeSelector, SelectorType


class LoginState(BaseState):
    """
    Example state: Login page.
    
    This demonstrates:
    - State detection (URL pattern)
    - Basic execution logic
    - State transition
    """
    
    def __init__(self):
        super().__init__("LoginState")
        # Cascade detection: DOM (most reliable) → URL → text
        form_detector = DOMElementDetector(["//form[contains(@action, 'login')]"])
        url_detector = URLPatternDetector(["/login", "/sign-in"])
        text_detector = TextContentDetector(["Login", "Sign in"], case_sensitive=False)
        self.detector = CascadeDetector([
            form_detector,     # Most reliable: actual page structure
            url_detector,      # Fast fallback: URL pattern
            text_detector,     # Last resort: text content
        ], min_confidence=0.7)
    
    def detect(self, context: Dict[str, Any]) -> bool:
        """Check if we're on the login page."""
        result = self.detector.detect(context)
        return result.detected
    
    def execute(self, context: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Execute login logic.
        
        In production, this would:
        - Fill username/password fields
        - Handle CAPTCHAs
        - Manage 2FA
        - Wait for navigation
        """
        driver = context.get('driver')
        # Conceptual: actual implementation would interact with form
        print(f"[{self.name}] Executing login...")
        return {"status": "logged_in"}
    
    def transition(self, context: Dict[str, Any]) -> Optional[str]:
        """After login, transition to search state."""
        # Check if login was successful
        if context.get('status') == 'logged_in':
            return "SearchState"
        return None


class SearchState(BaseState):
    """
    Example state: Search page.
    
    Demonstrates state that performs an action and transitions.
    """
    
    def __init__(self):
        super().__init__("SearchState")
        # Cascade detection for search page: DOM → URL → text
        search_input_detector = DOMElementDetector(["//input[@type='search']", "//input[@placeholder*='Search']"])
        url_detector = URLPatternDetector(["/search"])
        text_detector = TextContentDetector(["Search", "Find"], case_sensitive=False)
        self.detector = CascadeDetector([
            search_input_detector,     # Most reliable: actual page structure
            url_detector,              # Fast fallback: URL
            text_detector,             # Last resort: text
        ], min_confidence=0.7)
    
    def detect(self, context: Dict[str, Any]) -> bool:
        result = self.detector.detect(context)
        return result.detected
    
    def execute(self, context: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Execute search action."""
        print(f"[{self.name}] Executing search...")
        # Conceptual: would enter search query and submit
        return {"search_performed": True}
    
    def transition(self, context: Dict[str, Any]) -> Optional[str]:
        """After search, go to results."""
        if context.get('search_performed'):
            return "ResultsState"
        return None


class ResultsState(BaseState):
    """
    Example state: Search results page.
    
    Demonstrates cascade selector usage for resilient element detection.
    """
    
    def __init__(self):
        super().__init__("ResultsState")
        # Cascade detection for results page: DOM → URL → text
        results_detector = DOMElementDetector(["//div[@class='results']", "//ul[@class='result-list']"])
        url_detector = URLPatternDetector(["/search/results"])
        text_detector = TextContentDetector(["Results", "Found"], case_sensitive=False)
        self.detector = CascadeDetector([
            results_detector,      # Most reliable: actual page structure
            url_detector,          # Fast fallback: URL
            text_detector,         # Last resort: text
        ], min_confidence=0.7)
        
        # Create cascade for finding result links
        # Primary: specific selector
        # Fallback: broader selector
        # Last resort: text-based detection
        self.result_cascade = CascadeExecutor([
            CascadeSelector(
                "//div[@class='result-item']//a",
                SelectorType.XPATH,
                "Primary result link selector"
            ),
            CascadeSelector(
                "//a[contains(@href, '/profile/')]",
                SelectorType.XPATH,
                "Fallback: any profile link"
            ),
            CascadeSelector(
                "result-item",
                SelectorType.TEXT,
                "Text-based: search for result indicators"
            ),
        ])
    
    def detect(self, context: Dict[str, Any]) -> bool:
        result = self.detector.detect(context)
        return result.detected
    
    def execute(self, context: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Extract result links using cascade."""
        print(f"[{self.name}] Extracting results...")
        
        # Try cascade selectors
        results = self.result_cascade.execute(context)
        
        if results:
            print(f"[{self.name}] Found {len(results) if isinstance(results, list) else 1} results")
            return {"results": results}
        else:
            print(f"[{self.name}] No results found")
            return None
    
    def transition(self, context: Dict[str, Any]) -> Optional[str]:
        """If results found, go to profile state; otherwise complete."""
        if context.get('results'):
            return "ProfileState"
        return None  # Complete


class ProfileState(BaseState):
    """Example state: Individual profile page."""
    
    def __init__(self):
        super().__init__("ProfileState")
        # Cascade detection for profile page: DOM → URL → text
        profile_detector = DOMElementDetector(["//div[@class='profile']", "//section[contains(@class, 'profile')]"])
        url_detector = URLPatternDetector(["/profile/", "/in/"], use_regex=True)
        text_detector = TextContentDetector(["Profile", "About"], case_sensitive=False)
        self.detector = CascadeDetector([
            profile_detector,      # Most reliable: actual page structure
            url_detector,          # Fast fallback: URL pattern
            text_detector,         # Last resort: text
        ], min_confidence=0.7)
    
    def detect(self, context: Dict[str, Any]) -> bool:
        result = self.detector.detect(context)
        return result.detected
    
    def execute(self, context: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Extract profile data."""
        print(f"[{self.name}] Extracting profile data...")
        # Conceptual: would extract name, title, experience, etc.
        return {"profile_data": {"name": "Example", "title": "Engineer"}}
    
    def transition(self, context: Dict[str, Any]) -> Optional[str]:
        """After profile, check if more profiles to process."""
        # In production, would check if there are more results
        # For this example, just complete
        return None  # Complete


# Conceptual State Machine Executor (not fully implemented)
class StateMachineExecutor:
    """
    Executes the state machine.
    
    This is a conceptual example - production implementation would include:
    - Error handling
    - Retry logic
    - State history tracking
    - Human emulation (delays, mouse movements)
    """
    
    def __init__(self, states: list[BaseState], initial_context: Dict[str, Any]):
        self.states = {state.name: state for state in states}
        self.context = initial_context
        self.current_state = None
    
    def run(self):
        """Run the state machine until completion."""
        # Find initial state
        for state in self.states.values():
            if state.detect(self.context):
                self.current_state = state
                break
        
        if not self.current_state:
            print("No initial state detected")
            return
        
        # Execute state machine loop
        while self.current_state:
            print(f"\n--- Entering {self.current_state.name} ---")
            
            # Enter state
            self.current_state.enter(self.context)
            
            # Execute state
            result = self.current_state.execute(self.context)
            if result:
                self.context.update(result)
            
            # Transition
            next_state_name = self.current_state.transition(self.context)
            
            # Exit state
            self.current_state.exit(self.context)
            
            # Move to next state
            if next_state_name and next_state_name in self.states:
                self.current_state = self.states[next_state_name]
            else:
                print("\n--- State machine complete ---")
                self.current_state = None


# Example usage (conceptual - would require actual browser driver)
if __name__ == "__main__":
    # Create states
    states = [
        LoginState(),
        SearchState(),
        ResultsState(),
        ProfileState(),
    ]
    
    # Create context (conceptual - would have real browser driver)
    context = {
        "driver": None,  # Would be Selenium/Playwright driver
        "url": "https://example.com/login",
        "session_data": {},
    }
    
    # Run state machine (conceptual)
    print("=" * 50)
    print("Scraping State Machine Pattern - Simple Example")
    print("=" * 50)
    print("\nThis is a conceptual demonstration.")
    print("Production implementation would include:")
    print("  - Actual browser automation (Selenium/Playwright)")
    print("  - Error handling and retries")
    print("  - Human emulation (delays, mouse movements)")
    print("  - State persistence and recovery")
    print("  - Data validation and storage")
    print("\n" + "=" * 50)
    
    # executor = StateMachineExecutor(states, context)
    # executor.run()

