# Architecture: Scraping State Machine Pattern

## Overview

The Scraping State Machine Pattern models web scraping workflows as finite state machines (FSMs), where each state represents a distinct page context or interaction phase, and transitions represent navigation actions or state changes.

## Core Components

### 1. BaseState (Abstract State)

Every state in the system inherits from `BaseState`, which defines the contract:

```python
class BaseState:
    def detect(self, context) -> bool:
        """Returns True if this state is currently active"""
        pass
    
    def enter(self, context):
        """Called when entering this state"""
        pass
    
    def execute(self, context):
        """Main state logic (scraping, navigation)"""
        pass
    
    def transition(self, context) -> str:
        """Returns name of next state, or None if complete"""
        pass
    
    def exit(self, context):
        """Called when leaving this state"""
        pass
```

### 2. State Detector

States use detectors to identify when they're active. Multiple detection strategies:

- **URL Pattern Matching** — Regex or string matching on current URL
- **DOM Element Detection** — Presence of specific elements/selectors
- **Text Content Matching** — Search for specific text patterns
- **Visual Detection** — Screenshot analysis or OCR (advanced)

### 3. Cascade Executor

The cascade pattern provides resilience through fallback strategies:

```
Primary Selector (XPath/CSS)
    ↓ (if fails)
Fallback Selector 1
    ↓ (if fails)
Fallback Selector 2
    ↓ (if fails)
Visual/Text Detection
    ↓ (if fails)
Error/Retry
```

Each level in the cascade is tried sequentially until one succeeds.

### 4. State Machine Executor

The executor orchestrates the state machine:

1. **Initialization** — Load state definitions, set initial state
2. **State Detection** — Poll available states to find active one
3. **State Execution** — Run current state's logic
4. **Transition** — Determine and execute next state
5. **Termination** — Handle completion or error states

## State Lifecycle

```
┌─────────┐
│  Start  │
└────┬────┘
     │
     ▼
┌─────────────┐
│ Detect State│
└────┬────────┘
     │
     ▼
┌─────────────┐
│ Enter State │
└────┬────────┘
     │
     ▼
┌─────────────┐
│ Execute     │
│ State Logic │
└────┬────────┘
     │
     ▼
┌─────────────┐
│ Transition? │
└────┬────────┘
     │
     ├──► Yes ──► Next State
     │
     └──► No ──► Complete
```

## Transition Mechanisms

States transition through:

1. **Explicit Return** — State's `transition()` method returns next state name
2. **Action-Based** — User action (click, form submit) triggers transition
3. **Conditional** — Based on scraped data or context
4. **Error Recovery** — Fallback to error state or retry

## Adaptive Behavior Strategy

The pattern implements **adaptive behavior** that dynamically adjusts between machine-like and human-like execution based on bot detection signals.

### Machine-Like Mode (Default)

When no bot detection is present:
- **Fast execution** — Minimal delays, direct interactions
- **Efficient navigation** — No unnecessary mouse movements
- **Optimized performance** — Fastest possible scraping speed

**Rationale:** There's negative value in emulating human behavior on sites that aren't doing any bot detection. Unnecessary delays and movements only slow down execution without providing benefit.

### Human-Like Mode (When Detected)

When bot detection signals are present:
- **Randomized Delays** — Between 1-3 seconds (configurable)
- **Mouse Movement** — Simulated cursor paths before clicks
- **Scroll Patterns** — Natural scroll behavior
- **Typing Cadence** — Variable keystroke timing
- **Viewport Behavior** — Realistic window resizing/focus

### Detection Signals

The system monitors for:
- CAPTCHA challenges
- Rate limiting responses (429 errors)
- Suspicious activity warnings
- Unusual redirects or blocks
- JavaScript-based detection patterns

### Adaptive Switching

The pattern bounces between modes:
1. Start in machine-like mode (fast, efficient)
2. Monitor for detection signals
3. Switch to human-like mode if signals detected
4. Gradually return to machine-like mode when safe
5. Optimize for the best solution: speed when possible, stealth when necessary

## Error Handling

### Retry Strategies

- **State-Level Retries** — Retry state execution N times
- **Selector-Level Retries** — Retry cascade selectors
- **Transition Retries** — Retry failed transitions

### Error States

- **ErrorState** — Handles recoverable errors
- **FailureState** — Handles unrecoverable errors
- **RecoveryState** — Attempts to return to previous valid state

## Context Object

The `context` object passed between states contains:

- **Browser/Driver** — Selenium/Playwright instance
- **Session Data** — Cookies, tokens, authentication
- **Scraped Data** — Accumulated results
- **Configuration** — Rate limits, timeouts, selectors
- **State History** — Previous states for backtracking

## Advantages Over Traditional Scrapers

| Traditional | State Machine Pattern |
|------------|----------------------|
| Linear scripts | Explicit state transitions |
| Hard-coded selectors | Cascading fallbacks |
| Brittle to changes | Resilient detection |
| Hard to debug | Clear state tracking |
| Difficult to test | Isolated state tests |
| No recovery | Built-in error states |

## Scalability

Adding new functionality:

1. **New State** — Create class inheriting `BaseState`
2. **New Selector** — Add to cascade in existing state
3. **New Transition** — Update `transition()` method
4. **New Detector** — Implement detection logic

No modification to existing states required.

## Performance Considerations

- **Lazy State Detection** — Only detect when needed
- **Selector Caching** — Cache successful selectors
- **Parallel States** — Multiple states can run concurrently (advanced)
- **State Pooling** — Reuse state instances

## Security & Ethics

This pattern is designed for:
- ✅ Publicly accessible data
- ✅ Respecting robots.txt
- ✅ Rate limiting
- ✅ Terms of service compliance

Always ensure your scraping activities are legal and ethical.

