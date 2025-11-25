"""
Error States - Examples of rate limiting and soft blocking states.

This demonstrates the distinction between recoverable errors (rate limits)
and potentially permanent errors (soft blocks) in the state machine pattern.
"""

from typing import Dict, Any, Optional
from src.base_state import BaseState
from src.state_detector import URLPatternDetector, TextContentDetector, CascadeDetector
from src.detection_result import DetectionResult


class RateLimitedState(BaseState):
    """
    State: Rate limit detected (HTTP 429 or similar).
    
    This is a RECOVERABLE error state. The scraper should:
    - Wait with exponential backoff
    - Retry after the rate limit window expires
    - Potentially switch to a different proxy/IP
    
    Transitions: → Previous state (retry) or → BackoffState
    """
    
    def __init__(self):
        super().__init__("RateLimitedState")
        # Cascade detection: text patterns (most reliable for error detection)
        text_detector = TextContentDetector([
            "rate limit",
            "too many requests",
            "429",
            "try again later"
        ], case_sensitive=False)
        # Note: In production, would also check HTTP status code
        self.detector = CascadeDetector([
            text_detector,  # Most reliable: error message text
        ], min_confidence=0.8)
    
    def detect(self, context: Dict[str, Any]) -> bool:
        """Check if rate limit is detected."""
        result = self.detector.detect(context)
        return result.detected
    
    def execute(self, context: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Handle rate limit: calculate backoff time and wait.
        
        Production implementation would:
        - Check Retry-After header if available
        - Calculate exponential backoff based on attempt count
        - Log rate limit event
        - Potentially rotate proxy/IP
        """
        print(f"[{self.name}] Rate limit detected. Calculating backoff...")
        
        # Conceptual: would calculate actual backoff time
        attempt_count = context.get('rate_limit_attempts', 0) + 1
        backoff_seconds = min(2 ** attempt_count, 300)  # Cap at 5 minutes
        
        return {
            "rate_limit_attempts": attempt_count,
            "backoff_seconds": backoff_seconds,
            "retry_after": context.get('current_time', 0) + backoff_seconds
        }
    
    def transition(self, context: Dict[str, Any]) -> Optional[str]:
        """After backoff, return to previous state or continue."""
        retry_after = context.get('retry_after', 0)
        current_time = context.get('current_time', 0)
        
        if current_time >= retry_after:
            # Backoff complete, return to previous state
            previous_state = context.get('previous_state', 'LoginState')
            return previous_state
        else:
            # Still in backoff period
            return "BackoffState"  # Would wait here


class SoftBlockedState(BaseState):
    """
    State: Soft block detected (account/IP temporarily blocked).
    
    This is a POTENTIALLY PERMANENT error state. The scraper should:
    - Stop scraping immediately
    - Log the block event
    - Potentially switch accounts/IPs
    - May require manual intervention
    
    Transitions: → AccountSwitchState or → FailureState
    """
    
    def __init__(self):
        super().__init__("SoftBlockedState")
        # Cascade detection: text patterns for soft block
        text_detector = TextContentDetector([
            "account suspended",
            "temporarily blocked",
            "access denied",
            "suspicious activity",
            "verify your account"
        ], case_sensitive=False)
        self.detector = CascadeDetector([
            text_detector,  # Most reliable: error message text
        ], min_confidence=0.8)
    
    def detect(self, context: Dict[str, Any]) -> bool:
        """Check if soft block is detected."""
        result = self.detector.detect(context)
        return result.detected
    
    def execute(self, context: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Handle soft block: log and determine recovery strategy.
        
        Production implementation would:
        - Log block details (IP, account, timestamp)
        - Check if account/IP rotation is available
        - Determine if block is temporary or permanent
        - Alert monitoring system
        """
        print(f"[{self.name}] Soft block detected. Evaluating recovery options...")
        
        # Conceptual: would check available recovery options
        has_backup_account = context.get('backup_accounts', [])
        has_backup_ip = context.get('backup_proxies', [])
        
        return {
            "soft_blocked": True,
            "block_timestamp": context.get('current_time', 0),
            "can_switch_account": len(has_backup_account) > 0,
            "can_switch_ip": len(has_backup_ip) > 0
        }
    
    def transition(self, context: Dict[str, Any]) -> Optional[str]:
        """Determine recovery path based on available options."""
        can_switch_account = context.get('can_switch_account', False)
        can_switch_ip = context.get('can_switch_ip', False)
        
        if can_switch_account:
            return "AccountSwitchState"
        elif can_switch_ip:
            return "ProxySwitchState"
        else:
            # No recovery options available
            return "FailureState"


class BackoffState(BaseState):
    """
    State: Waiting during rate limit backoff period.
    
    This state simply waits until the backoff period expires,
    then transitions back to the previous state.
    """
    
    def __init__(self):
        super().__init__("BackoffState")
        # Always active when in backoff
        self.detector = lambda context: True
    
    def detect(self, context: Dict[str, Any]) -> bool:
        """Check if still in backoff period."""
        retry_after = context.get('retry_after', 0)
        current_time = context.get('current_time', 0)
        return current_time < retry_after
    
    def execute(self, context: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Wait during backoff period."""
        retry_after = context.get('retry_after', 0)
        current_time = context.get('current_time', 0)
        remaining = retry_after - current_time
        
        print(f"[{self.name}] Waiting {remaining} seconds before retry...")
        # Conceptual: would actually sleep here
        return {"current_time": retry_after}  # Simulate time passing
    
    def transition(self, context: Dict[str, Any]) -> Optional[str]:
        """After backoff, return to previous state."""
        retry_after = context.get('retry_after', 0)
        current_time = context.get('current_time', retry_after)
        
        if current_time >= retry_after:
            previous_state = context.get('previous_state', 'LoginState')
            return previous_state
        return None


# Example usage (conceptual)
if __name__ == "__main__":
    print("=" * 60)
    print("Error States Example - Rate Limited vs Soft Blocked")
    print("=" * 60)
    print("\nKey Distinctions:")
    print("  RateLimitedState:")
    print("    - Recoverable (wait and retry)")
    print("    - Temporary (expires after backoff)")
    print("    - Can use exponential backoff")
    print("\n  SoftBlockedState:")
    print("    - Potentially permanent")
    print("    - May require account/IP rotation")
    print("    - May require manual intervention")
    print("\n" + "=" * 60)

