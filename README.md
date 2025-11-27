# Scraping State Machine Pattern

A design pattern for building robust, maintainable web scrapers that handle dynamic content, anti-bot measures, and complex navigation flows through a state machine architecture.

## Philosophy

Traditional scrapers are brittle. They assume pages load predictably, selectors remain stable, and anti-bot measures don't exist. In reality, web scraping requires:

- **Adaptive navigation** — Handling login flows, multi-step forms, and dynamic redirects
- **Resilient selectors** — Cascading fallback strategies when primary selectors fail
- **Human-like behavior** — Timing, mouse movements, and interaction patterns that evade detection
- **State awareness** — Understanding where you are in a complex flow and how to recover

The Scraping State Machine Pattern addresses these challenges by modeling scraping workflows as explicit state machines, where each state represents a distinct page or interaction context, and transitions represent navigation actions.

## Core Concepts

### 1. State-Based Architecture

Instead of linear scripts, scrapers are organized as **states** (e.g., `LoginState`, `SearchResultsState`, `ProfileState`) with defined entry/exit conditions and transition rules.

### 2. Cascading Selector Strategy

Each state uses a **cascade** of selector strategies:
1. Primary XPath/CSS selector (most specific)
2. Fallback selectors (broader patterns)
3. Visual/text-based detection (last resort)

This ensures resilience when sites change their markup.

### 3. State Detection

States can detect their own context through:
- URL patterns
- DOM element presence
- Text content matching
- Visual indicators (screenshots/OCR)

### 4. Adaptive Behavior Scaling

The pattern supports **adaptive behavior scaling** that dynamically adjusts between machine-like and human-like execution based on success metrics:

- **Machine-like mode** (level 0.0) — Fast, efficient execution when no bot detection is present
  - Minimal delays (0.0-0.1s)
  - No mouse movement simulation
  - No scroll behavior
  - Instant text input
  - No randomness (jitter = 0.0)

- **Human-like mode** (level 1.0) — Realistic behavior when bot detection is detected
  - Realistic delays (1.0-3.0s)
  - Mouse movement simulation
  - Natural scroll patterns
  - Human typing cadence (0.05-0.15s per keystroke)
  - Randomness (jitter = 0.3)

**Behavior Scaling Based on Success Metrics and Cascade Performance:**

The `BehaviorScaler` automatically adjusts behavior level based on success rate and cascade selector performance:

```python
from src.behavior import BehaviorScaler, MACHINE_LIKE_PROFILE, HUMAN_LIKE_PROFILE
from src.cascade_metrics import CascadeMetrics

scaler = BehaviorScaler(MACHINE_LIKE_PROFILE, HUMAN_LIKE_PROFILE)
metrics = CascadeMetrics()

# Track cascade performance
result = cascade.execute(context)
if result:
    element, position, selector_type = result
    metrics.record_success(position, selector_type, len(cascade.selectors))

# Get cascade metrics
cascade_metrics = metrics.get_metrics()

# High success rate (>0.95) + primary selectors → decrease humanness (faster)
profile = scaler.escalate(success_rate=0.98, cascade_metrics=cascade_metrics)

# Frequent text/visual fallbacks → increase humanness (more stealth)
# (Even with medium success rate, fallbacks indicate site changes/blocking)
profile = scaler.escalate(success_rate=0.85, cascade_metrics={
    'text_fallback_rate': 0.4,  # 40% fallbacks
    'avg_position': 0.7
})

# Low success rate (<0.7) → increase humanness (more stealth)
profile = scaler.escalate(success_rate=0.60, cascade_metrics=cascade_metrics)
```

**Key insight:** Cascade position is a strong signal. If primary selectors (XPath/CSS) consistently work, the site is stable and we can stay machine-like. If we're frequently falling back to text/visual selectors, that indicates site changes or bot detection, so we should escalate to human-like behavior.

**Key insight:** There's negative value in emulating human behavior on sites that aren't doing any bot detection. The pattern adapts based on success metrics, optimizing for both speed (when safe) and stealth (when needed).

See [Behavior Scaling Documentation](docs/behavior-scaling.md) for detailed examples and thresholds.

## Benefits

✅ **Maintainability** — Clear separation of concerns, easy to modify individual states  
✅ **Resilience** — Automatic fallback strategies when selectors break  
✅ **Debuggability** — Explicit state transitions make failures easy to trace  
✅ **Testability** — Each state can be tested in isolation  
✅ **Scalability** — Add new states without modifying existing code  
✅ **Anti-Bot Evasion** — Human-like behavior patterns reduce detection risk

## Architecture Overview

```
┌─────────────────┐
│  State Machine  │
│    Executor     │
└────────┬────────┘
         │
         ├──► State Detection
         │    (URL, DOM, Visual)
         │
         ├──► State Transitions
         │    (Actions, Delays)
         │
         └──► Cascade Executor
              (Primary → Fallback → Visual)
```

### State Lifecycle

1. **Entry** — State detects it's active (via detector)
2. **Execution** — State performs its actions (scraping, navigation)
3. **Transition** — State determines next state or completion
4. **Exit** — Cleanup and state handoff

## Example Use Cases

- **LinkedIn Scraping** — Login → Search → Profile → Export
- **E-commerce** — Product listing → Detail page → Cart → Checkout
- **Multi-step Forms** — Form 1 → Validation → Form 2 → Submission
- **Dynamic Content** — Infinite scroll → Load more → Extract → Repeat

## Quick Start

See `examples/simple_example.py` for a minimal conceptual demonstration of the pattern.

**Note:** The example code is illustrative pseudocode showing the pattern's structure. It is not production-ready and requires significant implementation work for actual use.

## Documentation

- [Architecture Details](docs/architecture.md) — Deep dive into the pattern
- [Use Cases](docs/use-cases.md) — Real-world applications
- [State Machine Diagram](docs/diagram.md) — Visual representation

## License

MIT License — See [LICENSE](LICENSE) file for details.

## Author

This pattern was developed through practical experience building production scrapers for complex, dynamic websites with anti-bot measures.

---

**Note:** This repository contains the conceptual framework and example code. Production implementations are tailored to specific use cases, rate limiting strategies, and integration requirements.

