# Network Rotation Strategy

## Overview

Network rotation (proxy/VPN management) is a critical component of production web scraping. The scraping state machine pattern integrates proxy rotation with behavior scaling, creating a unified strategy for handling network-level failures.

## Why Network Rotation Matters

### The Problem

- **IP Blocks** — Sites block IPs that make too many requests
- **Rate Limits** — Sites limit requests per IP address
- **Geographic Restrictions** — Some content requires specific regions
- **CAPTCHAs** — Triggered by suspicious IP patterns
- **Single Point of Failure** — One blocked IP stops entire scraper

### The Solution

Proxy rotation provides:
- **IP Diversity** — Multiple IPs reduce block risk
- **Geographic Flexibility** — Access region-specific content
- **Failure Isolation** — One blocked proxy doesn't stop the system
- **Load Distribution** — Spread requests across multiple IPs
- **Automatic Recovery** — Quarantine failed proxies, rotate to working ones

## Proxy Configuration

### ProxyConfig

Each proxy is configured with:

```python
from src.network import ProxyConfig

proxy = ProxyConfig(
    host="proxy.example.com",
    port=8080,
    protocol="http",  # or "https", "socks5"
    region="us-east",  # Optional: geographic region
    provider="brightdata"  # Optional: proxy service name
)
```

**Key Fields:**
- `host` / `port` — Proxy endpoint
- `protocol` — Connection protocol (http, https, socks5)
- `region` — Geographic region (for geographic rotation)
- `provider` — Service name (for tracking provider performance)

## Network Rotator

### Proxy Pool Management

The `NetworkRotator` maintains a pool of proxies and tracks performance:

```python
from src.network import NetworkRotator, ProxyConfig

# Initialize with proxy pool
proxies = [
    ProxyConfig("proxy1.com", 8080, region="us-east"),
    ProxyConfig("proxy2.com", 8080, region="eu-west"),
    ProxyConfig("proxy3.com", 8080, region="asia-pacific"),
]

rotator = NetworkRotator(proxies)

# Get best available proxy
current_proxy = rotator.get_proxy()
```

### Success-Based Selection

Proxies are selected based on success rates:

- **New proxies** get benefit of doubt (1.0 success rate)
- **Proven proxies** with high success rates are preferred
- **Failed proxies** are automatically deprioritized
- **Quarantined proxies** are excluded until expiry

### Per-Proxy Metrics

Each proxy tracks:
- Total requests
- Successes vs failures
- Rate limit count
- CAPTCHA count
- Block count
- Last success/failure timestamps

## Rotation Triggers

### Automatic Rotation

Rotation happens automatically based on failure type:

```python
from src.network import RotationTrigger

# Rate limit detected → rotate immediately
rotator.report_failure(current_proxy, RotationTrigger.RATE_LIMIT)

# CAPTCHA detected → rotate + escalate behavior
rotator.report_failure(current_proxy, RotationTrigger.CAPTCHA)

# IP blocked → quarantine + rotate
rotator.report_failure(current_proxy, RotationTrigger.BLOCK)
```

### Rotation Trigger Types

| Trigger | Action | Behavior Impact |
|---------|--------|----------------|
| **RATE_LIMIT** | Rotate immediately | Moderate escalation |
| **CAPTCHA** | Rotate + escalate | Strong escalation (more human-like) |
| **BLOCK** | Quarantine + rotate | Strong escalation (more human-like) |
| **GEOGRAPHIC** | Rotate to different region | No behavior change |
| **SCHEDULED** | Proactive rotation | No behavior change |

## Quarantine System

### Temporary Removal

Failed proxies are quarantined (temporarily removed from pool):

```python
# Quarantine a blocked proxy for 1 hour
rotator.quarantine(blocked_proxy, duration_seconds=3600)
```

**Quarantine Duration:**
- **Rate limits**: Short quarantine (15-30 minutes)
- **CAPTCHAs**: Medium quarantine (1-2 hours)
- **IP blocks**: Long quarantine (4-24 hours)

### Automatic Expiry

Quarantined proxies are automatically restored after expiry:
- System checks quarantine expiry on each `get_proxy()` call
- Expired proxies return to pool
- Allows recovery from temporary blocks

## Integration with Behavior Scaling

### Unified Failure Signals

Network failures feed into the same behavior scaling system as cascade failures:

```python
from src.behavior import BehaviorScaler
from src.network import NetworkRotator

scaler = BehaviorScaler(MACHINE_LIKE_PROFILE, HUMAN_LIKE_PROFILE)
rotator = NetworkRotator(proxies)

# After scraping operations
cascade_metrics = cascade_metrics_tracker.get_metrics()
network_metrics = rotator.get_metrics()

# Escalate behavior with both signals
profile = scaler.escalate(
    success_rate=0.85,
    cascade_metrics=cascade_metrics,
    network_metrics={
        'overall_success_rate': network_metrics['overall_success_rate'],
        'recent_captchas': count_recent_captchas(),
        'recent_blocks': count_recent_blocks(),
        'recent_rate_limits': count_recent_rate_limits(),
    }
)
```

### Failure Response

| Failure Type | Proxy Action | Behavior Action |
|--------------|--------------|-----------------|
| **Rate Limit** | Rotate to new proxy | Moderate escalation |
| **CAPTCHA** | Rotate + quarantine | Strong escalation (level += 0.2) |
| **IP Block** | Quarantine + rotate | Strong escalation (level += 0.2) |
| **Cascade Failure** | No proxy change | Escalate based on cascade position |

**Key insight:** CAPTCHA or IP block triggers both proxy rotation AND immediate behavior escalation. The system responds to network-level failures with both network and behavior changes.

## Metrics and Monitoring

### Per-Proxy Metrics

```python
metrics = rotator.get_metrics()

# Per-proxy success rates
for proxy, proxy_metrics in metrics['per_proxy'].items():
    print(f"{proxy}: {proxy_metrics['success_rate']:.2%} success")
```

### Per-Region Metrics

```python
# Aggregate by geographic region
for region, region_metrics in metrics['per_region'].items():
    print(f"{region}: {region_metrics['success_rate']:.2%} success")
```

### Per-Provider Metrics

```python
# Aggregate by proxy provider
for provider, provider_metrics in metrics['per_provider'].items():
    print(f"{provider}: {provider_metrics['success_rate']:.2%} success")
```

## Best Practices

### 1. Proxy Pool Size

- **Minimum**: 3-5 proxies (redundancy)
- **Recommended**: 10-20 proxies (better distribution)
- **Large scale**: 50+ proxies (geographic diversity)

### 2. Rotation Strategy

- **Proactive**: Rotate after N requests (e.g., every 100 requests)
- **Reactive**: Rotate on failures (rate limits, CAPTCHAs, blocks)
- **Geographic**: Rotate when region-specific content needed

### 3. Quarantine Duration

- **Rate limits**: 15-30 minutes (temporary)
- **CAPTCHAs**: 1-2 hours (moderate)
- **IP blocks**: 4-24 hours (severe)

### 4. Success Tracking

- Track success rates over recent window (last 100-1000 requests)
- Weight recent performance more than historical
- Reset metrics periodically to adapt to changing conditions

### 5. Integration Points

- **State execution**: Check proxy before each state
- **Cascade failures**: Consider proxy health in cascade metrics
- **Behavior scaling**: Use network metrics in escalation decisions

## Example: Complete Flow

```python
from src.network import NetworkRotator, ProxyConfig, RotationTrigger
from src.behavior import BehaviorScaler, MACHINE_LIKE_PROFILE, HUMAN_LIKE_PROFILE

# Initialize
proxies = [ProxyConfig(f"proxy{i}.com", 8080) for i in range(10)]
rotator = NetworkRotator(proxies)
scaler = BehaviorScaler(MACHINE_LIKE_PROFILE, HUMAN_LIKE_PROFILE)

# Get proxy for request
proxy = rotator.get_proxy()
context['proxy'] = proxy

# Execute scraping
try:
    result = state.execute(context)
    rotator.report_success(proxy)
except RateLimitException:
    rotator.report_failure(proxy, RotationTrigger.RATE_LIMIT)
    # Rotator automatically rotates to new proxy
except CaptchaException:
    rotator.report_failure(proxy, RotationTrigger.CAPTCHA)
    # Rotator rotates AND escalates behavior
    network_metrics = rotator.get_metrics()
    profile = scaler.escalate(
        success_rate=0.7,
        network_metrics={
            'recent_captchas': 1,
            'overall_success_rate': network_metrics['overall_success_rate']
        }
    )
    context['behavior_profile'] = profile
except BlockException:
    rotator.report_failure(proxy, RotationTrigger.BLOCK)
    # Rotator quarantines proxy, rotates, AND escalates behavior
```

## For The Swarm Pitch

This network rotation strategy demonstrates:

- **Resilience**: Automatic recovery from network failures
- **Intelligence**: Success-based proxy selection
- **Integration**: Unified failure signals across network and behavior
- **Scale**: Handles 580M profiles with distributed IP load
- **Cost optimization**: Quarantine prevents wasting requests on bad proxies

The pattern treats network failures as first-class signals, just like cascade failures, feeding into the same behavior scaling system for unified response.

