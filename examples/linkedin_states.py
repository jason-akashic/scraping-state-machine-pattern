"""
LinkedIn States - Conceptual example of state definitions for LinkedIn scraping.

⚠️ IMPORTANT: This is CONCEPTUAL - illustrative pseudocode, not production code.

This demonstrates how states would be structured for a real-world use case.
It shows the pattern and architecture, but does NOT include:
- Full production implementation
- Actual LinkedIn selectors (these are examples)
- Complete error handling
- Rate limiting strategies
- Session management
- Data validation
- Integration with storage/APIs

The purpose is to illustrate the pattern's application to a complex use case,
not to provide a working LinkedIn scraper.
"""

from typing import Dict, Any, Optional
from src.base_state import BaseState
from src.state_detector import URLPatternDetector, DOMElementDetector, TextContentDetector, CascadeDetector
from src.cascade import CascadeExecutor, CascadeSelector, SelectorType


class LinkedInLoginState(BaseState):
    """
    State: LinkedIn login page.
    
    Detects: /login URL or login form presence
    Actions: Enter credentials, handle 2FA
    Transitions: → SearchState on success
    """
    
    def __init__(self):
        super().__init__("LinkedInLoginState")
        # Cascade detection: DOM (most reliable) → URL → text
        form_detector = DOMElementDetector(["//form[@id='login-form']"])
        url_detector = URLPatternDetector(["/login", "/uas/login"])
        text_detector = TextContentDetector(["Sign in", "Welcome back"], case_sensitive=False)
        self.detector = CascadeDetector([
            form_detector,     # Most reliable: actual page structure
            url_detector,      # Fast fallback: URL match
            text_detector,     # Last resort: text content
        ], min_confidence=0.7)
    
    def detect(self, context: Dict[str, Any]) -> bool:
        result = self.detector.detect(context)
        return result.detected
    
    def execute(self, context: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Execute login.
        
        Production implementation would:
        - Fill username field (with cascade selector)
        - Fill password field
        - Click submit
        - Handle 2FA if present
        - Wait for navigation
        - Detect CAPTCHA and handle
        """
        print(f"[{self.name}] Logging into LinkedIn...")
        # Conceptual - actual implementation would interact with form
        return {"authenticated": True}
    
    def transition(self, context: Dict[str, Any]) -> Optional[str]:
        if context.get('authenticated'):
            return "LinkedInSearchState"
        return None


class LinkedInSearchState(BaseState):
    """
    State: LinkedIn search page.
    
    Detects: /search URL
    Actions: Enter search query, submit
    Transitions: → ResultsState
    """
    
    def __init__(self):
        super().__init__("LinkedInSearchState")
        # Cascade detection: DOM → URL → text
        search_input_detector = DOMElementDetector(["//input[@placeholder='Search' and @role='combobox']"])
        url_detector = URLPatternDetector(["/search"])
        text_detector = TextContentDetector(["Search", "Find people"], case_sensitive=False)
        self.detector = CascadeDetector([
            search_input_detector,     # Most reliable: actual page structure
            url_detector,              # Fast fallback: URL
            text_detector,             # Last resort: text
        ], min_confidence=0.7)
        
        # Cascade for search input field
        self.search_input_cascade = CascadeExecutor([
            CascadeSelector(
                "//input[@placeholder='Search' and @role='combobox']",
                SelectorType.XPATH,
                "Primary search input"
            ),
            CascadeSelector(
                "input[type='text'][placeholder*='Search']",
                SelectorType.CSS,
                "Fallback search input"
            ),
        ])
    
    def detect(self, context: Dict[str, Any]) -> bool:
        result = self.detector.detect(context)
        return result.detected
    
    def execute(self, context: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Enter search query and submit."""
        print(f"[{self.name}] Performing search...")
        # Conceptual - would use cascade to find input, enter query, submit
        return {"search_query": context.get('search_query', 'software engineer')}
    
    def transition(self, context: Dict[str, Any]) -> Optional[str]:
        return "LinkedInResultsState"


class LinkedInResultsState(BaseState):
    """
    State: LinkedIn search results page.
    
    Detects: /search/results URL
    Actions: Extract profile links, handle pagination
    Transitions: → ProfileState (for each profile), → SearchState (next page)
    """
    
    def __init__(self):
        super().__init__("LinkedInResultsState")
        # Cascade detection: DOM → URL → text
        results_detector = DOMElementDetector(["//div[@class='search-result']", "//ul[contains(@class, 'results')]"])
        url_detector = URLPatternDetector(["/search/results"])
        text_detector = TextContentDetector(["Search results", "People"], case_sensitive=False)
        self.detector = CascadeDetector([
            results_detector,      # Most reliable: actual page structure
            url_detector,          # Fast fallback: URL
            text_detector,         # Last resort: text
        ], min_confidence=0.7)
        
        # Cascade for finding profile result links
        self.profile_link_cascade = CascadeExecutor([
            CascadeSelector(
                "//div[@class='search-result__info']//a[@href]",
                SelectorType.XPATH,
                "Primary: result info link"
            ),
            CascadeSelector(
                "//a[contains(@href, '/in/') and contains(@href, '/')]",
                SelectorType.XPATH,
                "Fallback: any /in/ link"
            ),
            CascadeSelector(
                "//li[@class='search-result']//a",
                SelectorType.XPATH,
                "Fallback: any link in result item"
            ),
        ])
        
        # Cascade for "next page" button
        self.next_page_cascade = CascadeExecutor([
            CascadeSelector(
                "//button[@aria-label='Next']",
                SelectorType.XPATH,
                "Primary: next button"
            ),
            CascadeSelector(
                "//span[text()='Next']",
                SelectorType.XPATH,
                "Fallback: next text"
            ),
        ])
    
    def detect(self, context: Dict[str, Any]) -> bool:
        result = self.detector.detect(context)
        return result.detected
    
    def execute(self, context: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Extract profile links from results."""
        print(f"[{self.name}] Extracting profile links...")
        
        # Use cascade to find profile links
        # In production, would unpack and track metrics
        cascade_result = self.profile_link_cascade.execute(context)
        
        if cascade_result:
            links, position, selector_type = cascade_result
            # In production: metrics.record_success(position, selector_type, len(cascade.selectors))
            # Extract hrefs (conceptual)
            profile_urls = []  # Would extract from link elements
            return {"profile_urls": profile_urls, "current_page": 1}
        
        return None
    
    def transition(self, context: Dict[str, Any]) -> Optional[str]:
        """Transition to profile state or next page."""
        profile_urls = context.get('profile_urls', [])
        
        if profile_urls:
            # Process first profile
            return "LinkedInProfileState"
        else:
            # Check for next page
            next_page_result = self.next_page_cascade.execute(context)
            has_next = next_page_result is not None
            if has_next:
                return "LinkedInResultsState"  # Stay in results, go to next page
            else:
                return None  # Complete


class LinkedInProfileState(BaseState):
    """
    State: Individual LinkedIn profile page.
    
    Detects: /in/ URL pattern
    Actions: Extract profile data (name, title, experience, etc.)
    Transitions: → ResultsState (next profile), → ExportState (if done)
    """
    
    def __init__(self):
        super().__init__("LinkedInProfileState")
        # Cascade detection: DOM → URL → text
        profile_detector = DOMElementDetector(["//div[@class='pv-text-details__left-panel']", "//section[contains(@class, 'profile')]"])
        url_detector = URLPatternDetector(["/in/"], use_regex=True)
        text_detector = TextContentDetector(["Profile", "Experience", "Education"], case_sensitive=False)
        self.detector = CascadeDetector([
            profile_detector,      # Most reliable: actual page structure
            url_detector,          # Fast fallback: URL pattern
            text_detector,         # Last resort: text content
        ], min_confidence=0.7)
        
        # Cascade for profile name
        self.name_cascade = CascadeExecutor([
            CascadeSelector(
                "//div[@class='pv-text-details__left-panel']//h1",
                SelectorType.XPATH,
                "Primary: name in left panel"
            ),
            CascadeSelector(
                "//h1[contains(@class, 'text-heading-xlarge')]",
                SelectorType.XPATH,
                "Fallback: large heading"
            ),
            CascadeSelector(
                "//h1",
                SelectorType.XPATH,
                "Last resort: any h1"
            ),
        ])
        
        # Cascade for job title
        self.title_cascade = CascadeExecutor([
            CascadeSelector(
                "//div[@class='text-body-medium break-words']",
                SelectorType.XPATH,
                "Primary: title selector"
            ),
            CascadeSelector(
                "//span[@class='text-body-medium']",
                SelectorType.XPATH,
                "Fallback: title span"
            ),
        ])
    
    def detect(self, context: Dict[str, Any]) -> bool:
        result = self.detector.detect(context)
        return result.detected
    
    def execute(self, context: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Extract profile data using cascades."""
        print(f"[{self.name}] Extracting profile data...")
        
        # Use cascades to extract data
        # In production, would unpack and track metrics
        name_result = self.name_cascade.execute(context)
        title_result = self.title_cascade.execute(context)
        
        # Conceptual: would extract text from elements
        name_element = name_result[0] if name_result else None
        title_element = title_result[0] if title_result else None
        
        profile_data = {
            "name": "Extracted Name",  # Would come from name_element
            "title": "Extracted Title",  # Would come from title_element
            "url": context.get('url', ''),
        }
        
        return {"profile_data": profile_data}
    
    def transition(self, context: Dict[str, Any]) -> Optional[str]:
        """After extracting profile, check for more profiles."""
        profile_urls = context.get('profile_urls', [])
        processed_count = context.get('processed_profiles', 0)
        
        if processed_count < len(profile_urls):
            # More profiles to process
            return "LinkedInResultsState"  # Would navigate to next profile
        else:
            # All profiles processed
            return "LinkedInExportState"


class LinkedInExportState(BaseState):
    """
    State: Export collected data.
    
    Detects: Always active (terminal state)
    Actions: Format and export scraped data
    Transitions: None (completion state)
    """
    
    def __init__(self):
        super().__init__("LinkedInExportState")
        # Always detect as active (terminal state)
        self.detector = lambda context: True
    
    def detect(self, context: Dict[str, Any]) -> bool:
        return True  # Terminal state
    
    def execute(self, context: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Export collected profile data."""
        print(f"[{self.name}] Exporting data...")
        profiles = context.get('scraped_profiles', [])
        print(f"[{self.name}] Exported {len(profiles)} profiles")
        return {"exported": True}
    
    def transition(self, context: Dict[str, Any]) -> Optional[str]:
        return None  # Complete


# Example state definitions (conceptual)
# Production implementation would include:
# - Full selector cascades for all elements
# - Error handling and retry logic
# - Human emulation (delays, mouse movements)
# - Rate limiting
# - Session management
# - Data validation
# - Integration with storage/APIs

