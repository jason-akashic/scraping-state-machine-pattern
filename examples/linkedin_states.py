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
from src.state_detector import URLPatternDetector, DOMElementDetector, CompositeDetector
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
        # Detect by URL or form presence
        url_detector = URLPatternDetector(["/login", "/uas/login"])
        form_detector = DOMElementDetector(["//form[@id='login-form']"])
        self.detector = CompositeDetector([url_detector, form_detector], logic='OR')
    
    def detect(self, context: Dict[str, Any]) -> bool:
        return self.detector.detect(context)
    
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
        self.detector = URLPatternDetector(["/search"])
        
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
        return self.detector.detect(context)
    
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
        self.detector = URLPatternDetector(["/search/results"])
        
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
        return self.detector.detect(context)
    
    def execute(self, context: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Extract profile links from results."""
        print(f"[{self.name}] Extracting profile links...")
        
        # Use cascade to find profile links
        links = self.profile_link_cascade.execute(context)
        
        if links:
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
            has_next = self.next_page_cascade.execute(context) is not None
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
        self.detector = URLPatternDetector(["/in/"], use_regex=True)
        
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
        return self.detector.detect(context)
    
    def execute(self, context: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Extract profile data using cascades."""
        print(f"[{self.name}] Extracting profile data...")
        
        # Use cascades to extract data
        name_element = self.name_cascade.execute(context)
        title_element = self.title_cascade.execute(context)
        
        # Conceptual: would extract text from elements
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

