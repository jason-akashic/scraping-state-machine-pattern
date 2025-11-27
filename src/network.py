"""
Network - Proxy and network rotation for scraping state machine.

This module implements proxy pool management, rotation strategies, and
integration with behavior scaling based on network-level failures.
"""

from dataclasses import dataclass
from typing import List, Dict, Optional
from enum import Enum
from datetime import datetime, timedelta


class RotationTrigger(Enum):
    """Reasons for rotating to a new proxy."""
    RATE_LIMIT = "rate_limit"  # Got rate limited, rotate immediately
    CAPTCHA = "captcha"  # Hit captcha, rotate + increase humanness
    BLOCK = "block"  # IP blocked, quarantine + rotate
    GEOGRAPHIC = "geographic"  # Need different region for content
    SCHEDULED = "scheduled"  # Proactive rotation after N requests


@dataclass
class ProxyConfig:
    """
    Configuration for a proxy server.
    
    Represents a single proxy endpoint with metadata for tracking
    and selection.
    """
    
    host: str
    """Proxy hostname or IP address."""
    
    port: int
    """Proxy port number."""
    
    protocol: str = "http"
    """
    Proxy protocol: 'http', 'https', or 'socks5'.
    
    Defaults to 'http' for most use cases.
    """
    
    region: Optional[str] = None
    """
    Geographic region identifier.
    
    Examples: 'us-east', 'eu-west', 'asia-pacific'
    Useful for geographic rotation or region-specific content.
    """
    
    provider: Optional[str] = None
    """
    Proxy provider/service name.
    
    Examples: 'brightdata', 'oxylabs', 'custom'
    Useful for tracking which proxy service performs best.
    """
    
    def __repr__(self) -> str:
        region_str = f", region={self.region}" if self.region else ""
        provider_str = f", provider={self.provider}" if self.provider else ""
        return f"ProxyConfig({self.protocol}://{self.host}:{self.port}{region_str}{provider_str})"


class NetworkRotator:
    """
    Manages proxy pool and rotation strategies.
    
    Tracks per-proxy success/failure rates and automatically rotates
    based on failure types (rate limits, blocks, captchas).
    """
    
    def __init__(self, proxies: List[ProxyConfig]):
        """
        Initialize network rotator with proxy pool.
        
        Args:
            proxies: List of ProxyConfig instances to manage
        """
        self.proxies = proxies
        self.proxy_metrics: Dict[ProxyConfig, Dict] = {}
        self.quarantined: Dict[ProxyConfig, datetime] = {}
        self.current_proxy: Optional[ProxyConfig] = None
        
        # Initialize metrics for each proxy
        for proxy in proxies:
            self.proxy_metrics[proxy] = {
                'total_requests': 0,
                'successes': 0,
                'failures': 0,
                'rate_limits': 0,
                'captchas': 0,
                'blocks': 0,
                'last_failure': None,
                'last_success': None,
            }
    
    def get_proxy(self) -> Optional[ProxyConfig]:
        """
        Get the best available proxy based on success rates.
        
        Returns:
            ProxyConfig with highest success rate that's not quarantined,
            or None if no proxies available
        """
        available = [p for p in self.proxies if p not in self.quarantined]
        
        if not available:
            # All proxies quarantined - check if any can be unquarantined
            self._check_quarantine_expiry()
            available = [p for p in self.proxies if p not in self.quarantined]
        
        if not available:
            return None
        
        # Weight by success rate
        def get_success_rate(proxy):
            metrics = self.proxy_metrics[proxy]
            total = metrics['total_requests']
            if total == 0:
                return 1.0  # New proxy gets benefit of doubt
            return metrics['successes'] / total
        
        # Return proxy with highest success rate
        best_proxy = max(available, key=get_success_rate)
        self.current_proxy = best_proxy
        return best_proxy
    
    def report_success(self, proxy: ProxyConfig):
        """
        Record a successful request for a proxy.
        
        Args:
            proxy: The proxy that succeeded
        """
        metrics = self.proxy_metrics[proxy]
        metrics['total_requests'] += 1
        metrics['successes'] += 1
        metrics['last_success'] = datetime.utcnow()
    
    def report_failure(self, proxy: ProxyConfig, reason: RotationTrigger, 
                      details: Optional[str] = None):
        """
        Record a failed request and handle rotation if needed.
        
        Args:
            proxy: The proxy that failed
            reason: Type of failure (determines response)
            details: Optional additional failure information
        """
        metrics = self.proxy_metrics[proxy]
        metrics['total_requests'] += 1
        metrics['failures'] += 1
        metrics['last_failure'] = datetime.utcnow()
        
        # Track specific failure types
        if reason == RotationTrigger.RATE_LIMIT:
            metrics['rate_limits'] += 1
        elif reason == RotationTrigger.CAPTCHA:
            metrics['captchas'] += 1
        elif reason == RotationTrigger.BLOCK:
            metrics['blocks'] += 1
        
        # Handle rotation based on failure type
        if reason in [RotationTrigger.RATE_LIMIT, RotationTrigger.CAPTCHA, RotationTrigger.BLOCK]:
            self.rotate(reason.value)
            if reason == RotationTrigger.BLOCK:
                # Quarantine blocked proxy
                self.quarantine(proxy, duration_seconds=3600)  # 1 hour
    
    def rotate(self, reason: str = "scheduled"):
        """
        Force rotation to a new proxy.
        
        Args:
            reason: Reason for rotation (for logging/debugging)
        """
        # Get next best proxy (different from current)
        available = [p for p in self.proxies 
                     if p != self.current_proxy and p not in self.quarantined]
        
        if available:
            self.current_proxy = self.get_proxy()
        else:
            # No alternatives, keep current or return None
            if self.current_proxy and self.current_proxy in self.quarantined:
                self.current_proxy = None
    
    def quarantine(self, proxy: ProxyConfig, duration_seconds: int = 3600):
        """
        Temporarily remove a proxy from the pool.
        
        Args:
            proxy: Proxy to quarantine
            duration_seconds: How long to keep it quarantined
        """
        expiry = datetime.utcnow() + timedelta(seconds=duration_seconds)
        self.quarantined[proxy] = expiry
    
    def _check_quarantine_expiry(self):
        """Remove proxies from quarantine if their time has expired."""
        now = datetime.utcnow()
        expired = [p for p, expiry in self.quarantined.items() if expiry < now]
        for proxy in expired:
            del self.quarantined[proxy]
    
    def get_metrics(self) -> Dict:
        """
        Get aggregated metrics for all proxies.
        
        Returns:
            Dictionary with:
            - 'per_proxy': Dict mapping ProxyConfig to metrics
            - 'per_region': Dict mapping region to aggregated metrics
            - 'per_provider': Dict mapping provider to aggregated metrics
            - 'overall_success_rate': Overall success rate across all proxies
            - 'quarantined_count': Number of currently quarantined proxies
        """
        per_proxy = {}
        per_region = {}
        per_provider = {}
        
        total_requests = 0
        total_successes = 0
        
        for proxy, metrics in self.proxy_metrics.items():
            per_proxy[proxy] = {
                'success_rate': metrics['successes'] / max(1, metrics['total_requests']),
                'total_requests': metrics['total_requests'],
                'rate_limits': metrics['rate_limits'],
                'captchas': metrics['captchas'],
                'blocks': metrics['blocks'],
                'quarantined': proxy in self.quarantined,
            }
            
            total_requests += metrics['total_requests']
            total_successes += metrics['successes']
            
            # Aggregate by region
            if proxy.region:
                if proxy.region not in per_region:
                    per_region[proxy.region] = {'requests': 0, 'successes': 0}
                per_region[proxy.region]['requests'] += metrics['total_requests']
                per_region[proxy.region]['successes'] += metrics['successes']
            
            # Aggregate by provider
            if proxy.provider:
                if proxy.provider not in per_provider:
                    per_provider[proxy.provider] = {'requests': 0, 'successes': 0}
                per_provider[proxy.provider]['requests'] += metrics['total_requests']
                per_provider[proxy.provider]['successes'] += metrics['successes']
        
        # Calculate region/provider success rates
        for region, data in per_region.items():
            data['success_rate'] = data['successes'] / max(1, data['requests'])
        
        for provider, data in per_provider.items():
            data['success_rate'] = data['successes'] / max(1, data['requests'])
        
        return {
            'per_proxy': per_proxy,
            'per_region': per_region,
            'per_provider': per_provider,
            'overall_success_rate': total_successes / max(1, total_requests),
            'quarantined_count': len(self.quarantined),
        }
    
    def reset_metrics(self, proxy: Optional[ProxyConfig] = None):
        """
        Reset metrics for a specific proxy or all proxies.
        
        Args:
            proxy: Specific proxy to reset, or None to reset all
        """
        if proxy:
            self.proxy_metrics[proxy] = {
                'total_requests': 0,
                'successes': 0,
                'failures': 0,
                'rate_limits': 0,
                'captchas': 0,
                'blocks': 0,
                'last_failure': None,
                'last_success': None,
            }
        else:
            for proxy in self.proxies:
                self.reset_metrics(proxy)

