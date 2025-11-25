# Error Handling, Debug Data Collection, and AI-Assisted XPath Generation

## Current State

### What We Have
- Basic exception catching in cascade selectors (continues on error)
- DetectionResult with reasoning field (some debugging info)
- Error states (RateLimitedState, SoftBlockedState) for specific error types
- Context object for passing data between states

### What's Missing
- **Structured error logging** - No persistent error/debug data collection
- **XPath generation tools** - No utilities to analyze DOM and generate new selectors
- **AI integration** - No framework for agentic XPath generation
- **Failure context capture** - Not saving enough data for post-mortem analysis

---

## Error Handling & Debug Data Collection

### What We Should Save for Future Debug

#### 1. Cascade Failure Data
When all selectors in a cascade fail, we need:
```python
{
    "timestamp": "2025-11-25T20:00:00Z",
    "state": "ProfileState",
    "target_element": "profile_name",
    "failed_selectors": [
        {
            "selector": "//div[@class='pv-text-details__left-panel']//h1",
            "type": "xpath",
            "error": "NoSuchElementException",
            "page_snapshot": "<html>...</html>",  # Or path to saved HTML
            "screenshot": "path/to/screenshot.png",
            "dom_snippet": "<div class='pv-text-details__left-panel'>...</div>"
        },
        # ... more failed selectors
    ],
    "page_url": "https://linkedin.com/in/john-doe",
    "page_title": "John Doe | LinkedIn",
    "dom_structure": {
        "similar_elements": ["//h1", "//h2[@class='name']"],  # Elements that might be the target
        "parent_structure": "//div[@class='profile-container']",
        "text_content": "John Doe\nSoftware Engineer\n..."
    },
    "context": {
        "previous_state": "ResultsState",
        "attempt_count": 3,
        "session_id": "abc123"
    }
}
```

#### 2. State Detection Failure Data
When state detection fails:
```python
{
    "timestamp": "2025-11-25T20:00:00Z",
    "expected_state": "LoginState",
    "actual_url": "https://example.com/login?redirect=/dashboard",
    "detection_results": [
        {
            "detector": "URLPatternDetector",
            "patterns": ["/login"],
            "result": {"detected": False, "confidence": 0.0, "reasoning": "URL contains '/login' but also has query params"},
            "page_snapshot": "..."
        },
        {
            "detector": "DOMElementDetector",
            "selectors": ["//form[@id='login-form']"],
            "result": {"detected": True, "confidence": 0.9, "reasoning": "Found login form"},
            "page_snapshot": "..."
        }
    ],
    "final_result": {"detected": True, "confidence": 0.9}
}
```

#### 3. Transition Failure Data
When state transitions fail:
```python
{
    "timestamp": "2025-11-25T20:00:00Z",
    "from_state": "SearchState",
    "to_state": "ResultsState",
    "transition_action": "click_search_button",
    "failure_reason": "Button not found after 5 seconds",
    "expected_element": {
        "selector": "//button[@type='submit']",
        "description": "Search submit button"
    },
    "page_state": {
        "url": "https://example.com/search?q=test",
        "title": "Search Results",
        "screenshot": "path/to/screenshot.png",
        "dom_snapshot": "..."
    }
}
```

### Implementation: Error Context Manager

```python
class ErrorContext:
    """Collects and stores error/debug data for analysis."""
    
    def __init__(self):
        self.errors = []
        self.failed_selectors = []
        self.state_history = []
        self.page_snapshots = {}  # URL -> HTML/screenshot
    
    def record_cascade_failure(self, state, target, failed_selectors, context):
        """Record when all selectors in a cascade fail."""
        error_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "state": state.name,
            "target_element": target,
            "failed_selectors": [
                {
                    "selector": sel.selector,
                    "type": sel.selector_type.value,
                    "description": sel.description,
                    "error": self._capture_error(sel, context),
                    "page_snapshot": self._capture_page_state(context),
                    "dom_analysis": self._analyze_dom_for_target(context, target)
                }
                for sel in failed_selectors
            ],
            "page_url": context.get('url', ''),
            "page_title": self._get_page_title(context),
            "context": self._sanitize_context(context)
        }
        self.failed_selectors.append(error_data)
        return error_data
    
    def _analyze_dom_for_target(self, context, target):
        """Analyze DOM to find similar elements that might be the target."""
        driver = context.get('driver')
        if not driver:
            return {}
        
        # Find elements with similar attributes/text
        # This is where XPath generation tools would help
        return {
            "similar_elements": self._find_similar_elements(driver, target),
            "parent_structure": self._get_parent_structure(driver, target),
            "text_content": self._extract_relevant_text(driver)
        }
```

---

## XPath Generation Tools

### What We Need

#### 1. DOM Analysis Utilities
```python
class DOMAnalyzer:
    """Analyzes DOM structure to help generate XPath selectors."""
    
    def find_similar_elements(self, driver, target_text, target_attributes=None):
        """
        Find elements similar to a target (by text, attributes, position).
        
        Returns list of candidate XPath selectors.
        """
        pass
    
    def generate_xpath_by_text(self, text_content, partial_match=False):
        """Generate XPath that matches elements containing specific text."""
        pass
    
    def generate_xpath_by_attributes(self, attributes_dict):
        """Generate XPath based on element attributes."""
        pass
    
    def generate_xpath_by_position(self, element, relative_to=None):
        """Generate XPath based on element position in DOM."""
        pass
    
    def generate_robust_xpath(self, element, fallback_strategies=None):
        """
        Generate multiple XPath strategies for an element:
        - By ID (most specific)
        - By class + text
        - By parent structure
        - By position
        - By data attributes
        """
        pass
```

#### 2. Selector Validation
```python
class SelectorValidator:
    """Validates and tests XPath selectors."""
    
    def test_selector(self, driver, xpath, expected_count=None):
        """Test if selector works and returns expected elements."""
        pass
    
    def find_alternative_selectors(self, failed_xpath, page_html):
        """Given a failed XPath, find alternative selectors."""
        pass
    
    def compare_selectors(self, selector1, selector2, test_pages):
        """Compare selector reliability across multiple pages."""
        pass
```

#### 3. Selector Evolution
```python
class SelectorEvolution:
    """Tracks selector performance and suggests improvements."""
    
    def track_selector_performance(self, selector, success_rate, contexts):
        """Track how well a selector performs over time."""
        pass
    
    def suggest_improvements(self, failing_selector, error_context):
        """Suggest improved selectors based on failure data."""
        pass
```

---

## Automatic XPath Generation (Simple Algorithm)

### Architecture

#### 1. XPath Generator Algorithm
```python
class XPathGenerator:
    """
    Simple algorithm to generate XPath selectors on the fly.
    
    Analyzes DOM structure and generates candidate XPath selectors
    based on common patterns and heuristics.
    """
    
    def __init__(self, dom_analyzer):
        self.dom_analyzer = dom_analyzer
    
    def generate_xpath_candidates(self, error_context, target_description):
        """
        Generate new XPath candidates based on error context.
        
        Algorithm:
        1. Analyze failed selector to understand what we were looking for
        2. Search DOM for similar elements (by text, attributes, structure)
        3. Generate XPath variants using heuristics:
           - By ID (if available)
           - By class + text content
           - By parent structure
           - By data attributes
           - By position
        4. Rank by specificity and reliability
        
        Args:
            error_context: ErrorContext with failure data
            target_description: Description of target element
        
        Returns:
            List of candidate XPath selectors, ordered by reliability
        """
        candidates = []
        
        # 1. Extract target info from failed selector
        target_info = self._analyze_failed_selector(error_context)
        
        # 2. Find similar elements in DOM
        similar_elements = self.dom_analyzer.find_similar_elements(
            error_context.driver,
            target_info
        )
        
        # 3. Generate XPath for each similar element
        for element in similar_elements:
            # Strategy 1: By ID (most specific)
            if element.get('id'):
                candidates.append({
                    'xpath': f"//*[@id='{element['id']}']",
                    'confidence': 0.95,
                    'strategy': 'id'
                })
            
            # Strategy 2: By class + text
            if element.get('class') and element.get('text'):
                class_attr = ' '.join(element['class']) if isinstance(element['class'], list) else element['class']
                text = element['text'].strip()
                candidates.append({
                    'xpath': f"//{element['tag']}[@class='{class_attr}' and contains(text(), '{text[:20]}')]",
                    'confidence': 0.85,
                    'strategy': 'class_text'
                })
            
            # Strategy 3: By data attributes
            for attr, value in element.get('data_attrs', {}).items():
                candidates.append({
                    'xpath': f"//{element['tag']}[@{attr}='{value}']",
                    'confidence': 0.80,
                    'strategy': 'data_attr'
                })
            
            # Strategy 4: By parent structure
            if element.get('parent'):
                parent_xpath = self._generate_parent_xpath(element['parent'])
                candidates.append({
                    'xpath': f"{parent_xpath}//{element['tag']}",
                    'confidence': 0.75,
                    'strategy': 'parent_structure'
                })
            
            # Strategy 5: By position (last resort)
            if element.get('position'):
                candidates.append({
                    'xpath': f"//{element['tag']}[{element['position']}]",
                    'confidence': 0.50,
                    'strategy': 'position'
                })
        
        # 4. Remove duplicates and sort by confidence
        unique_candidates = self._deduplicate(candidates)
        return sorted(unique_candidates, key=lambda x: x['confidence'], reverse=True)
    
    def _analyze_failed_selector(self, error_context):
        """Extract what we were looking for from failed selector."""
        # Parse the failed XPath to understand target
        # e.g., "//div[@class='name']//h1" -> looking for h1 inside div.name
        return {
            'tag': 'h1',
            'parent_class': 'name',
            'expected_text': error_context.target_description
        }
```

#### 2. Integration Points

**In CascadeExecutor:**
```python
class CascadeExecutor:
    def __init__(self, selectors, xpath_generator=None):
        self.selectors = selectors
        self.xpath_generator = xpath_generator  # Optional generator
        self.error_context = ErrorContext()
    
    def execute(self, context):
        """Execute cascade, with automatic XPath generation if all fail."""
        result = self._try_cascade(context)
        
        if result is None and self.xpath_generator:
            # All selectors failed - try automatic generation
            error_data = self.error_context.record_cascade_failure(
                self.current_state,
                self.target_element,
                self.selectors,
                context
            )
            
            # Generate new selectors using algorithm
            candidates = self.xpath_generator.generate_xpath_candidates(
                error_data,
                self.target_description
            )
            
            # Try top candidates
            for candidate in candidates[:5]:  # Try top 5
                try:
                    selector = CascadeSelector(
                        candidate['xpath'],
                        SelectorType.XPATH,
                        f"Auto-generated ({candidate['strategy']})"
                    )
                    result = self._try_selector(selector, context)
                    if result:
                        # Success! Log and optionally save
                        self._log_successful_auto_selector(candidate)
                        return result
                except:
                    continue
        
        return result
```

#### 3. Heuristic Strategies

**Priority Order:**
1. **By ID** - Most specific, highest confidence (0.95)
2. **By class + text** - Good balance (0.85)
3. **By data attributes** - Often stable (0.80)
4. **By parent structure** - More resilient (0.75)
5. **By position** - Last resort, fragile (0.50)

**Example Generation:**
```
Failed: //div[@class='pv-text-details__left-panel']//h1

Algorithm finds similar h1 elements:
- <h1 id="profile-name">John Doe</h1>
- <h1 class="text-heading-xlarge">John Doe</h1>
- <h1 data-testid="profile-name">John Doe</h1>

Generates:
1. //h1[@id='profile-name'] (confidence: 0.95)
2. //h1[@class='text-heading-xlarge' and contains(text(), 'John Doe')] (confidence: 0.85)
3. //h1[@data-testid='profile-name'] (confidence: 0.80)
4. //div[contains(@class, 'text-details')]//h1 (confidence: 0.75)
```

---

## Implementation Plan

### Phase 1: Error Context Collection
1. Create `ErrorContext` class
2. Integrate into `CascadeExecutor`
3. Add page snapshot capture (HTML + screenshot)
4. Store error data in structured format (JSON/DB)

### Phase 2: DOM Analysis Tools
1. Create `DOMAnalyzer` class
2. Implement similarity finding
3. Implement XPath generation utilities
4. Add selector validation

### Phase 3: Automatic XPath Generation
1. Create `XPathGenerator` class with heuristic algorithm
2. Implement DOM analysis to find similar elements
3. Implement XPath generation strategies (ID, class, data-attr, parent, position)
4. Add candidate ranking by confidence
5. Integrate into cascade failure path

### Phase 4: Learning & Improvement
1. Track selector success rates
2. Learn from successful AI-generated selectors
3. Build selector knowledge base
4. Auto-update cascades with better selectors

---

## Key Design Decisions

### 1. When to Use Auto-Generation
- **Only on cascade failure** - Don't slow down successful paths
- **Configurable** - Allow disabling for performance reasons
- **Cached results** - Don't regenerate for same error context

### 2. What Data to Analyze
- **Failed selector structure** - Parse to understand what we were looking for
- **DOM around target area** - Analyze relevant section, not full page
- **Similar elements** - Find elements with similar attributes/text/structure

### 3. How to Validate Generated Selectors
- **Test against actual DOM** - Validate each candidate
- **Rank by confidence** - Try most likely first (ID > class > position)
- **Learn from results** - Track what works, improve heuristics

### 4. Performance Considerations
- **Fast DOM queries** - Use efficient XPath/CSS queries
- **Limit candidates** - Only generate top 5-10, don't exhaustively search
- **Caching** - Cache successful auto-generated selectors

---

## Example: Complete Flow

```
1. CascadeExecutor tries all selectors → All fail
2. ErrorContext captures:
   - Failed selectors
   - Page HTML snippet
   - DOM structure around target
   - Screenshot
3. XPathGenerator receives error context
4. Algorithm analyzes:
   - Parses failed selector: "//div[@class='name']//h1"
   - Searches DOM for similar h1 elements
   - Finds: <h1 id="profile-name">, <h1 class="heading">, etc.
5. Algorithm generates candidates using heuristics:
   - //h1[@id='profile-name'] (ID strategy)
   - //h1[@class='heading' and contains(text(), 'John')] (class+text)
   - //div[@class='profile']//h1 (parent structure)
6. Algorithm validates each against DOM
7. Algorithm tries top 5 candidates in order
8. If successful, logs new selector for future use
9. If all fail, logs for manual review
```

---

## Future Enhancement: Agentic AI

While the current approach uses simple heuristics and algorithms, a natural next step would be to integrate **agentic AI** for more sophisticated XPath generation:

### When Agentic AI Would Help

- **Complex DOM structures** - When heuristics fail on deeply nested or dynamic pages
- **Semantic understanding** - When you need to understand "what" the element represents, not just "where" it is
- **Learning from patterns** - When you want the system to learn from successful selectors across multiple sites
- **Natural language descriptions** - When you can describe the target in plain English ("the submit button in the login form")

### Potential Architecture

```python
class AgenticXPathGenerator:
    """
    Future enhancement: Uses LLM to generate XPath with semantic understanding.
    
    Would complement the heuristic generator:
    - Heuristics for fast, common cases
    - Agentic AI for complex, edge cases
    """
    
    def generate_with_ai(self, error_context, target_description):
        """
        Use LLM to understand context and generate XPath.
        
        Prompt would include:
        - What failed and why
        - DOM structure
        - Target description in natural language
        - Examples of successful selectors from similar contexts
        """
        # Future implementation
        pass
```

### Benefits of Agentic AI

- **Semantic reasoning** - Understands "profile name" means the person's name, not just "h1 element"
- **Cross-site learning** - Can apply patterns learned from one site to another
- **Adaptive** - Gets better over time as it sees more examples
- **Handles edge cases** - Better at unusual DOM structures

### Implementation Considerations

- **Cost** - LLM API calls cost money, so use sparingly
- **Latency** - Slower than heuristics, so use as fallback
- **Hybrid approach** - Try heuristics first, use AI only when needed
- **Caching** - Cache AI-generated selectors to avoid repeated API calls

---

## Next Steps

1. **Design review** - Does this algorithmic approach make sense?
2. **Heuristic refinement** - Which strategies work best in practice?
3. **Data storage** - Where to store error context? (DB, files, etc.)
4. **Implementation priority** - Which phase first?
5. **Future: Agentic AI** - Consider LLM integration for complex cases after heuristics are proven

