"""
Retry and pacing policies for job execution.

This module provides decorators and utilities for implementing retry logic,
rate limiting, and provider pacing compliance.
"""

import time
import random
import logging
from functools import wraps
from typing import Callable, Any, Optional, Dict
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class RetryPolicy:
    """Retry policy configuration."""
    max_attempts: int = 3
    backoff_seconds: float = 1.0
    jitter: bool = True
    exponential_backoff: bool = True


@dataclass
class RateLimitPolicy:
    """Rate limiting policy configuration."""
    requests_per_minute: int = 60
    burst_size: int = 10
    cooldown_seconds: float = 1.0


class TokenBucket:
    """Token bucket rate limiter implementation."""
    
    def __init__(self, capacity: int, refill_rate: float):
        """
        Initialize token bucket.
        
        Args:
            capacity: Maximum number of tokens
            refill_rate: Tokens added per second
        """
        self.capacity = capacity
        self.refill_rate = refill_rate
        self.tokens = capacity
        self.last_refill = time.time()
    
    def consume(self, tokens: int = 1) -> bool:
        """
        Try to consume tokens from the bucket.
        
        Args:
            tokens: Number of tokens to consume
            
        Returns:
            True if tokens were consumed, False if rate limited
        """
        now = time.time()
        
        # Refill tokens based on time elapsed
        time_elapsed = now - self.last_refill
        tokens_to_add = time_elapsed * self.refill_rate
        self.tokens = min(self.capacity, self.tokens + tokens_to_add)
        self.last_refill = now
        
        # Check if we have enough tokens
        if self.tokens >= tokens:
            self.tokens -= tokens
            return True
        
        return False
    
    def wait_for_tokens(self, tokens: int = 1) -> float:
        """
        Wait until tokens are available.
        
        Args:
            tokens: Number of tokens needed
            
        Returns:
            Time waited in seconds
        """
        start_time = time.time()
        
        while not self.consume(tokens):
            time.sleep(0.01)  # Small sleep to avoid busy waiting
        
        return time.time() - start_time


def retry(max_attempts: int = 3, backoff_seconds: float = 1.0, 
          jitter: bool = True, exponential_backoff: bool = True):
    """
    Decorator for retrying function calls with backoff.
    
    Args:
        max_attempts: Maximum number of attempts
        backoff_seconds: Base backoff time in seconds
        jitter: Add random jitter to backoff
        exponential_backoff: Use exponential backoff
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            
            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    
                    if attempt == max_attempts - 1:
                        logger.error(f"Function {func.__name__} failed after {max_attempts} attempts: {e}")
                        raise
                    
                    # Calculate backoff time
                    if exponential_backoff:
                        backoff = backoff_seconds * (2 ** attempt)
                    else:
                        backoff = backoff_seconds
                    
                    # Add jitter if enabled
                    if jitter:
                        jitter_amount = random.uniform(0, backoff * 0.1)
                        backoff += jitter_amount
                    
                    logger.warning(f"Function {func.__name__} failed (attempt {attempt + 1}/{max_attempts}): {e}")
                    logger.info(f"Retrying in {backoff:.2f} seconds...")
                    time.sleep(backoff)
            
            # This should never be reached, but just in case
            raise last_exception
        
        return wrapper
    return decorator


def respect_budget(provider_budget: Optional[RateLimitPolicy] = None):
    """
    Decorator for respecting provider rate limits.
    
    Args:
        provider_budget: Rate limiting policy for the provider
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            if provider_budget:
                # Create token bucket for this provider
                bucket = TokenBucket(
                    capacity=provider_budget.burst_size,
                    refill_rate=provider_budget.requests_per_minute / 60.0
                )
                
                # Wait for tokens if needed
                wait_time = bucket.wait_for_tokens()
                if wait_time > 0:
                    logger.debug(f"Rate limited, waited {wait_time:.2f}s for tokens")
                
                # Add cooldown if specified
                if provider_budget.cooldown_seconds > 0:
                    time.sleep(provider_budget.cooldown_seconds)
            
            return func(*args, **kwargs)
        
        return wrapper
    return decorator


def with_telemetry(telemetry_func: Optional[Callable] = None):
    """
    Decorator for adding telemetry to function calls.
    
    Args:
        telemetry_func: Function to call for telemetry recording
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            success = False
            error = None
            
            try:
                result = func(*args, **kwargs)
                success = True
                return result
            except Exception as e:
                error = e
                raise
            finally:
                duration = time.time() - start_time
                if telemetry_func:
                    try:
                        telemetry_func(success=success, duration=duration, error=error)
                    except Exception as te:
                        logger.warning(f"Telemetry recording failed: {te}")
        
        return wrapper
    return decorator


class PolicyManager:
    """Manages retry and pacing policies for job execution."""
    
    def __init__(self):
        self.rate_limiters: Dict[str, TokenBucket] = {}
        self.retry_policies: Dict[str, RetryPolicy] = {}
    
    def get_rate_limiter(self, provider: str, policy: RateLimitPolicy) -> TokenBucket:
        """Get or create rate limiter for a provider."""
        if provider not in self.rate_limiters:
            self.rate_limiters[provider] = TokenBucket(
                capacity=policy.burst_size,
                refill_rate=policy.requests_per_minute / 60.0
            )
        return self.rate_limiters[provider]
    
    def get_retry_policy(self, job_name: str, policy: RetryPolicy) -> RetryPolicy:
        """Get or create retry policy for a job."""
        if job_name not in self.retry_policies:
            self.retry_policies[job_name] = policy
        return self.retry_policies[job_name]
    
    def apply_retry_policy(self, func: Callable, policy: RetryPolicy) -> Callable:
        """Apply retry policy to a function."""
        return retry(
            max_attempts=policy.max_attempts,
            backoff_seconds=policy.backoff_seconds,
            jitter=policy.jitter,
            exponential_backoff=policy.exponential_backoff
        )(func)
    
    def apply_rate_limit(self, func: Callable, provider: str, policy: RateLimitPolicy) -> Callable:
        """Apply rate limiting to a function."""
        return respect_budget(policy)(func)


# Global policy manager
_policy_manager = PolicyManager()


def get_policy_manager() -> PolicyManager:
    """Get the global policy manager."""
    return _policy_manager
