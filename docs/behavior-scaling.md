# Adaptive Behavior Scaling

## Overview

Adaptive behavior scaling allows the scraping state machine to dynamically adjust between machine-like (fast, efficient) and human-like (slow, stealthy) behavior based on success metrics and bot detection signals.

## Why Behavior Scaling Matters

### The Problem

Traditional scrapers use a one-size-fits-all approach:
- **Always human-like**: Slow and inefficient on sites that don't check
- **Always machine-like**: Gets blocked on sites with bot detection
- **Fixed behavior**: Can't adapt to changing conditions

### The Solution

Adaptive behavior scaling provides:
- **Speed when safe**: Machine-like behavior on sites without detection
- **Stealth when needed**: Human-like behavior when detection is present
- **Automatic adjustment**: Feedback loop adjusts behavior based on success

**Key insight:** There's negative value in emulating human behavior on sites that aren't doing any bot detection. Unnecessary delays and movements only slow down execution without providing benefit.

## Behavior Profiles

### Machine-Like Profile (Level 0.0)

```python
MACHINE_LIKE_PROFILE = BehaviorProfile(
    delay_range=(0.0, 0.1),      # Minimal delays
    mouse_movement=False,         # No mouse simulation
    scroll_behavior=False,        # No scroll simulation
    typing_cadence=None,          # Instant text input
    jitter=0.0                    # No randomness
)
```

**Use when:**
- No bot detection signals
- High success rate (>0.95)
- Speed is priority
- Site doesn't check behavior patterns

### Human-Like Profile (Level 1.0)

```python
HUMAN_LIKE_PROFILE = BehaviorProfile(
    delay_range=(1.0, 3.0),      # Realistic delays
    mouse_movement=True,          # Simulate mouse movements
    scroll_behavior=True,         # Natural scrolling
    typing_cadence=(0.05, 0.15),  # Human typing speed
    jitter=0.3                    # Moderate randomness
)
```

**Use when:**
- Bot detection signals present
- Low success rate (<0.7)
- Stealth is priority
- Site actively checks behavior patterns

## Behavior Scaling

### Interpolation

The `BehaviorScaler` interpolates between machine-like and human-like profiles:

```python
scaler = BehaviorScaler(MACHINE_LIKE_PROFILE, HUMAN_LIKE_PROFILE)

# Machine-like (level 0.0)
profile = scaler.scale(0.0)  # Fast, no mouse, no delays

# Halfway (level 0.5)
profile = scaler.scale(0.5)  # Moderate delays, some mouse movement

# Human-like (level 1.0)
profile = scaler.scale(1.0)  # Slow, full mouse simulation
```

### Success-Based Escalation

The scaler automatically adjusts behavior based on success metrics:

```python
# High success rate (>0.95) → decrease humanness (faster)
profile = scaler.escalate(success_rate=0.98)
# Result: Moves toward machine-like (level decreases)

# Medium success rate (0.7-0.95) → maintain current
profile = scaler.escalate(success_rate=0.85)
# Result: Stays at current level

# Low success rate (<0.7) → increase humanness (more stealth)
profile = scaler.escalate(success_rate=0.60)
# Result: Moves toward human-like (level increases)
```

## The Feedback Loop

### How It Works

```
1. Start with machine-like behavior (level 0.0)
   ↓
2. Execute scraping operations
   ↓
3. Track success rate (successful operations / total operations)
   ↓
4. Adjust behavior level based on success rate:
   - High success (>0.95) → decrease level (faster)
   - Medium success (0.7-0.95) → maintain level
   - Low success (<0.7) → increase level (more stealth)
   ↓
5. Use new behavior profile for next operations
   ↓
6. Repeat (continuous feedback loop)
```

### Example: Adaptive Scaling in Action

```python
from src.behavior import BehaviorScaler, MACHINE_LIKE_PROFILE, HUMAN_LIKE_PROFILE

# Initialize scaler
scaler = BehaviorScaler(MACHINE_LIKE_PROFILE, HUMAN_LIKE_PROFILE)

# Start machine-like
context['behavior_profile'] = scaler.get_current_profile()  # Level 0.0

# After 100 operations: 98% success rate
success_rate = 0.98
context['behavior_profile'] = scaler.escalate(success_rate)
# Behavior stays machine-like (high success)

# After 200 operations: 65% success rate (detection detected!)
success_rate = 0.65
context['behavior_profile'] = scaler.escalate(success_rate)
# Behavior escalates toward human-like (level increases)

# After 300 operations: 92% success rate (human-like behavior working)
success_rate = 0.92
context['behavior_profile'] = scaler.escalate(success_rate)
# Behavior maintains current level (medium success)

# After 400 operations: 99% success rate (site stopped checking)
success_rate = 0.99
context['behavior_profile'] = scaler.escalate(success_rate)
# Behavior gradually returns to machine-like (level decreases)
```

## Example Thresholds and Profiles

### Recommended Thresholds

| Success Rate | Action | Behavior Level Change |
|--------------|--------|---------------------|
| > 0.95 | Decrease humanness | Level -= 0.1 (faster) |
| 0.7 - 0.95 | Maintain | Level unchanged |
| < 0.7 | Increase humanness | Level += 0.1 (more stealth) |

### Adjustment Rate

The `adjustment_rate` parameter controls how quickly behavior adapts:

- **Fast adjustment (0.2)**: Quick response to changes, but may oscillate
- **Medium adjustment (0.1)**: Balanced response (recommended default)
- **Slow adjustment (0.05)**: Gradual changes, more stable

```python
# Fast adjustment
profile = scaler.escalate(success_rate=0.60, adjustment_rate=0.2)
# Level increases by 0.2 per call

# Medium adjustment (default)
profile = scaler.escalate(success_rate=0.60, adjustment_rate=0.1)
# Level increases by 0.1 per call

# Slow adjustment
profile = scaler.escalate(success_rate=0.60, adjustment_rate=0.05)
# Level increases by 0.05 per call
```

## Integration with States

### Using Behavior Profile in States

States can access the behavior profile from the context:

```python
class LoginState(BaseState):
    def execute(self, context: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        behavior = context.get('behavior_profile')
        
        if behavior:
            # Use behavior profile for delays
            delay = random.uniform(*behavior.delay_range)
            time.sleep(delay)
            
            # Simulate mouse movement if enabled
            if behavior.mouse_movement:
                self._simulate_mouse_movement(context['driver'])
            
            # Use typing cadence for text input
            if behavior.typing_cadence:
                self._type_with_cadence(context['driver'], text, behavior.typing_cadence)
            else:
                # Instant input
                element.send_keys(text)
        
        # ... rest of login logic
```

### State Machine Executor Integration

The state machine executor should update behavior scaling based on operation results:

```python
class StateMachineExecutor:
    def __init__(self):
        self.scaler = BehaviorScaler(MACHINE_LIKE_PROFILE, HUMAN_LIKE_PROFILE)
        self.operation_results = []  # Track success/failure
    
    def run(self):
        while self.current_state:
            # Get current behavior profile
            context['behavior_profile'] = self.scaler.get_current_profile()
            
            # Execute state
            try:
                result = self.current_state.execute(context)
                self.operation_results.append(True)  # Success
            except Exception as e:
                self.operation_results.append(False)  # Failure
            
            # Update behavior scaling based on recent success rate
            if len(self.operation_results) >= 10:  # After 10 operations
                recent_results = self.operation_results[-100:]  # Last 100
                success_rate = sum(recent_results) / len(recent_results)
                context['behavior_profile'] = self.scaler.escalate(success_rate)
```

## Performance Impact

### Machine-Like Behavior

- **Delay overhead**: ~0.05s average per action
- **Total overhead**: Minimal (fast execution)
- **Use case**: Sites without bot detection

### Human-Like Behavior

- **Delay overhead**: ~2.0s average per action
- **Mouse movement**: ~0.5s per click
- **Typing cadence**: ~0.1s per keystroke
- **Total overhead**: Significant (stealth execution)
- **Use case**: Sites with bot detection

### Adaptive Scaling

- **Average overhead**: Varies based on success rate
- **Optimization**: Automatically minimizes overhead when safe
- **Benefit**: Best of both worlds (speed + stealth)

## Best Practices

1. **Start machine-like**: Begin with level 0.0, escalate only when needed
2. **Track success rate**: Monitor over recent operations (last 50-100)
3. **Adjust gradually**: Use moderate adjustment_rate (0.1) to avoid oscillation
4. **Reset on site change**: Reset to machine-like when switching sites
5. **Monitor performance**: Track behavior level vs. success rate over time

## For The Swarm Pitch

This adaptive behavior scaling demonstrates:

- **Cost optimization**: Machine-like behavior saves time when safe
- **Resilience**: Automatically adapts to detection signals
- **Intelligence**: Feedback loop learns optimal behavior per site
- **Scale efficiency**: Critical for scraping 580M profiles efficiently

The pattern optimizes for both speed (when possible) and stealth (when necessary), exactly what's needed for large-scale scraping operations.

