# Use Cases: Scraping State Machine Pattern

## 1. LinkedIn Profile Scraping

### Challenge
LinkedIn has complex navigation flows, dynamic content loading, and aggressive anti-bot measures.

### State Machine Flow

```
LoginState
    ↓
SearchState
    ↓
ResultsListState
    ↓
ProfileState (for each profile)
    ↓
ExportState
```

### Key States

**LoginState**
- Detects: Login page URL or login form presence
- Actions: Enter credentials, handle 2FA if needed
- Transitions: → SearchState on success, → ErrorState on failure

**SearchState**
- Detects: Search page with search bar
- Actions: Enter search query, submit
- Transitions: → ResultsListState

**ResultsListState**
- Detects: Search results page
- Actions: Extract profile links, handle pagination
- Transitions: → ProfileState (for each link), → SearchState (next page)

**ProfileState**
- Detects: Individual profile page
- Actions: Extract profile data (name, title, experience, etc.)
- Transitions: → ResultsListState (next profile), → ExportState (if done)

### Cascade Example (ProfileState)

```python
# Primary: Specific LinkedIn selector
"//div[@class='pv-text-details__left-panel']//h1"

# Fallback 1: Alternative class name
"//h1[contains(@class, 'text-heading-xlarge')]"

# Fallback 2: Text-based
"//h1[contains(text(), '')]"  # Any h1 with text

# Fallback 3: Visual detection
# Screenshot + OCR to find name
```

## 2. E-commerce Product Scraping

### Challenge
Product pages have varying layouts, dynamic pricing, and checkout flows.

### State Machine Flow

```
CategoryState
    ↓
ProductListState
    ↓
ProductDetailState
    ↓
CartState (optional)
    ↓
CheckoutState (optional)
```

### Key States

**CategoryState**
- Detects: Category page URL pattern
- Actions: Navigate to category, extract category metadata
- Transitions: → ProductListState

**ProductListState**
- Detects: Product listing page
- Actions: Extract product links, handle infinite scroll/pagination
- Transitions: → ProductDetailState (for each product)

**ProductDetailState**
- Detects: Individual product page
- Actions: Extract product data (title, price, description, images)
- Transitions: → ProductListState (next product), → CartState (if adding to cart)

## 3. Multi-Step Form Submission

### Challenge
Complex forms with validation, conditional fields, and multi-page flows.

### State Machine Flow

```
FormPage1State
    ↓
ValidationState
    ↓
FormPage2State
    ↓
ValidationState
    ↓
ConfirmationState
```

### Key States

**FormPage1State**
- Detects: First form page (URL or form element)
- Actions: Fill form fields, handle conditional logic
- Transitions: → ValidationState

**ValidationState**
- Detects: Validation errors or success message
- Actions: Check for errors, extract validation messages
- Transitions: → FormPage1State (if errors), → FormPage2State (if success)

**ConfirmationState**
- Detects: Confirmation page or success message
- Actions: Extract confirmation data
- Transitions: → Complete

## 4. Dynamic Content with Infinite Scroll

### Challenge
Content loads dynamically via JavaScript, requiring scroll-triggered loading.

### State Machine Flow

```
InitialLoadState
    ↓
ScrollState
    ↓
ContentExtractionState
    ↓
ScrollState (repeat)
    ↓
CompleteState
```

### Key States

**InitialLoadState**
- Detects: Initial page load
- Actions: Wait for initial content, extract first batch
- Transitions: → ScrollState

**ScrollState**
- Detects: Scrollable container, "load more" indicators
- Actions: Simulate scroll, wait for new content
- Transitions: → ContentExtractionState, → CompleteState (if no more content)

**ContentExtractionState**
- Detects: New content elements
- Actions: Extract newly loaded items
- Transitions: → ScrollState (continue), → CompleteState (if done)

## 5. Authentication with OAuth/SSO

### Challenge
Complex authentication flows with redirects, OAuth callbacks, and session management.

### State Machine Flow

```
LoginInitState
    ↓
OAuthRedirectState
    ↓
CallbackState
    ↓
SessionValidationState
    ↓
AuthenticatedState
```

### Key States

**LoginInitState**
- Detects: Login page
- Actions: Click "Sign in with OAuth" button
- Transitions: → OAuthRedirectState

**OAuthRedirectState**
- Detects: OAuth provider page (external domain)
- Actions: Handle OAuth provider login
- Transitions: → CallbackState

**CallbackState**
- Detects: Callback URL with tokens
- Actions: Extract tokens, handle redirect
- Transitions: → SessionValidationState

**SessionValidationState**
- Detects: Returned to original site
- Actions: Validate session, check authentication status
- Transitions: → AuthenticatedState (if valid), → LoginInitState (if invalid)

## Common Patterns Across Use Cases

### 1. Pagination Handling
Most list-based scrapers need pagination states:
- Detect "next page" button/link
- Extract current page data
- Transition to next page or completion

### 2. Error Recovery
All scrapers benefit from error states:
- **RateLimitState** — Handle 429 errors, implement backoff
- **CaptchaState** — Detect and handle CAPTCHAs
- **RetryState** — Retry failed operations

### 3. Data Validation
States can validate scraped data:
- Check for required fields
- Validate data format
- Retry if validation fails

## Benefits Demonstrated

✅ **Maintainability** — Each use case shows clear state separation  
✅ **Resilience** — Cascade selectors handle site changes  
✅ **Scalability** — Easy to add new states (e.g., new form pages)  
✅ **Testability** — Each state can be tested independently  
✅ **Debuggability** — Clear state transitions show where failures occur

## Implementation Notes

These use cases are **conceptual examples**. Production implementations would include:

- Site-specific selector cascades
- Custom rate limiting strategies
- Integration with data storage/APIs
- Monitoring and alerting
- Error logging and recovery
- Session management
- Proxy rotation (if needed)

The pattern provides the framework; the implementation provides the production-ready details.


