# State Detection Patterns: Cascade vs Composite

## Overview

The pattern provides two complementary approaches for combining multiple detection methods:

1. **CascadeDetector** - Cost-optimized, stops at first success
2. **CompositeDetector** - High-confidence, combines all signals

## CascadeDetector (Cost-Optimized)

### When to Use

- Detection methods have **significantly different costs**
  - URL check: ~0ms (fastest)
  - DOM query: ~10ms (medium)
  - Text search: ~50ms (slower)
  - OCR/Visual: ~500ms (slowest)
- A **single positive signal** is sufficient confidence
- You want to **fail fast** on obvious non-matches
- **Cost optimization matters** (e.g., scraping 580M profiles at scale)

### How It Works

```python
detector = CascadeDetector([
    URLPatternDetector(["/login"]),                # Fast, cheap - try first
    DOMElementDetector(["//form[@id='login']"]),  # Medium cost
    TextContentDetector(["Sign in"]),              # Slower
], min_confidence=0.7)
```

- Tries detectors **in order** (cheapest first)
- **Stops immediately** when one succeeds with confidence >= threshold
- Returns first successful result
- If all fail, returns best result (highest confidence)

### Example: Login Page Detection

```python
# Fast path: URL check succeeds immediately
detector = CascadeDetector([
    URLPatternDetector(["/login"]),      # ~0ms - succeeds, stops here
    DOMElementDetector(["//form"]),     # Never runs (URL already matched)
    TextContentDetector(["Sign in"]),    # Never runs
])
```

**Performance**: Only runs the cheapest detector that succeeds.

## CompositeDetector (High-Confidence)

### When to Use

- You need **corroborating evidence** (anti-false-positive)
- Detection costs are **similar** (all methods are fast)
- Dealing with **ambiguous pages** that might share patterns
- **False positives are costly** (e.g., wrong state = data corruption)

### How It Works

```python
# AND logic: Both must match
detector = CompositeDetector(
    [url_detector, dom_detector],
    logic='AND'  # High confidence: need both signals
)

# OR logic: Any one matches
detector = CompositeDetector(
    [url_detector, dom_detector],
    logic='OR'  # Any signal is enough
)
```

- **All detectors run** (no early exit)
- Results combined with AND/OR logic
- Confidence calculated from all results
- Returns aggregated result

### Example: Checkout Page Detection

```python
# Need both signals to be confident it's checkout page
detector = CompositeDetector([
    URLPatternDetector(["/checkout"]),           # URL contains /checkout
    DOMElementDetector(["//div[@id='cart']"]),   # AND cart icon visible
], logic='AND')

# High confidence: both signals present
# Prevents false positive if /checkout appears in other contexts
```

**Reliability**: Multiple signals reduce false positives.

## Comparison Table

| Aspect | CascadeDetector | CompositeDetector |
|--------|----------------|-------------------|
| **Execution** | Stops at first success | Runs all detectors |
| **Cost** | Optimized (cheapest first) | All methods run (no optimization) |
| **Confidence** | Single signal sufficient | Multiple signals required |
| **Use Case** | Cost-sensitive, scale | High-confidence, accuracy |
| **False Positives** | Possible (single signal) | Reduced (multiple signals) |
| **Performance** | Fast (early exit) | Slower (all run) |

## Real-World Examples

### Example 1: Login State (Cascade)

```python
# Cost-optimized: URL is fast and reliable for login pages
login_detector = CascadeDetector([
    URLPatternDetector(["/login", "/sign-in"]),  # Fast, reliable
    DOMElementDetector(["//form[@id='login']"]), # Fallback if URL changes
    TextContentDetector(["Sign in", "Login"]),   # Last resort
], min_confidence=0.7)
```

**Why Cascade?** URL check is ~0ms and very reliable. No need to run slower methods if URL matches.

### Example 2: Checkout State (Composite)

```python
# High-confidence: need multiple signals to confirm checkout
checkout_detector = CompositeDetector([
    URLPatternDetector(["/checkout", "/cart"]),
    DOMElementDetector(["//button[contains(text(), 'Place Order')]"]),
    TextContentDetector(["Total:", "Shipping"]),
], logic='AND')
```

**Why Composite?** False positive (thinking we're on checkout when we're not) could corrupt data. Need multiple signals.

### Example 3: Profile State (Cascade)

```python
# Cost-optimized: DOM check is reliable and fast enough
profile_detector = CascadeDetector([
    DOMElementDetector(["//div[@class='profile-header']"]),  # Most reliable
    URLPatternDetector(["/in/", "/profile/"]),                # Fast fallback
    TextContentDetector(["Profile", "About"]),                 # Last resort
], min_confidence=0.7)
```

**Why Cascade?** DOM check is reliable and fast. URL might change, but DOM structure is more stable.

## Best Practices

1. **Default to Cascade** for most cases (cost optimization)
2. **Use Composite** when false positives are costly
3. **Order Cascade by cost** (cheapest first)
4. **Set appropriate confidence thresholds** (0.7-0.9 for production)
5. **Monitor detection performance** - track which detectors succeed most often

## Performance Impact

### CascadeDetector
- **Best case**: First detector succeeds → only 1 detector runs
- **Worst case**: All detectors fail → all run, but still returns best result
- **Average**: Depends on success rate of first detector

### CompositeDetector
- **Always**: All detectors run (no early exit)
- **Cost**: Sum of all detector costs
- **Benefit**: Highest confidence, lowest false positive rate

## For The Swarm Pitch

This nuanced approach to detection strategies (cost-aware, confidence-weighted) is exactly what matters at scale. When scraping 580M profiles:

- **CascadeDetector** saves milliseconds per detection → hours saved at scale
- **CompositeDetector** prevents false positives → data quality at scale
- **Both tools** give you the right pattern for each situation

