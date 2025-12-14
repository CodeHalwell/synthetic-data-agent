"""
Resilience utilities for error recovery and fault tolerance.

Provides retry logic with exponential backoff and circuit breakers
to handle transient failures gracefully.
"""

import asyncio
import time
from typing import Callable, Any, Optional, Dict
from functools import wraps
from enum import Enum


class CircuitState(Enum):
    """Circuit breaker states."""
    CLOSED = "closed"  # Normal operation
    OPEN = "open"  # Failing, reject requests
    HALF_OPEN = "half_open"  # Testing if service recovered


class CircuitBreaker:
    """
    Simple circuit breaker implementation.
    
    Prevents cascading failures by stopping requests to failing services.
    """
    
    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: int = 60,
        expected_exception: type = Exception
    ):
        """
        Initialize circuit breaker.
        
        Args:
            failure_threshold: Number of failures before opening circuit
            recovery_timeout: Seconds to wait before attempting recovery
            expected_exception: Exception type that triggers circuit breaker
        """
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.expected_exception = expected_exception
        
        self.failure_count = 0
        self.last_failure_time: Optional[float] = None
        self.state = CircuitState.CLOSED
    
    def call(self, func: Callable, *args, **kwargs) -> Any:
        """
        Execute function with circuit breaker protection.
        
        Args:
            func: Function to execute
            *args: Positional arguments
            **kwargs: Keyword arguments
            
        Returns:
            Function result
            
        Raises:
            CircuitBreakerOpenError: If circuit is open
            Exception: Original exception if function fails
        """
        # Check circuit state
        if self.state == CircuitState.OPEN:
            # Check if recovery timeout has passed
            if self.last_failure_time and \
               (time.time() - self.last_failure_time) >= self.recovery_timeout:
                # Try to recover
                self.state = CircuitState.HALF_OPEN
                self.failure_count = 0
            else:
                raise CircuitBreakerOpenError(
                    f"Circuit breaker is OPEN. "
                    f"Last failure: {self.last_failure_time}. "
                    f"Retry after {self.recovery_timeout} seconds."
                )
        
        # Execute function
        try:
            result = func(*args, **kwargs)
            
            # Success - reset circuit if half-open
            if self.state == CircuitState.HALF_OPEN:
                self.state = CircuitState.CLOSED
                self.failure_count = 0
            
            return result
            
        except self.expected_exception as e:
            # Failure - increment counter
            self.failure_count += 1
            self.last_failure_time = time.time()
            
            # Open circuit if threshold reached
            if self.failure_count >= self.failure_threshold:
                self.state = CircuitState.OPEN
            
            # Re-raise exception
            raise e
    
    async def call_async(self, func: Callable, *args, **kwargs) -> Any:
        """
        Execute async function with circuit breaker protection.
        
        Args:
            func: Async function to execute
            *args: Positional arguments
            **kwargs: Keyword arguments
            
        Returns:
            Function result
            
        Raises:
            CircuitBreakerOpenError: If circuit is open
            Exception: Original exception if function fails
        """
        # Check circuit state
        if self.state == CircuitState.OPEN:
            # Check if recovery timeout has passed
            if self.last_failure_time and \
               (time.time() - self.last_failure_time) >= self.recovery_timeout:
                # Try to recover
                self.state = CircuitState.HALF_OPEN
                self.failure_count = 0
            else:
                raise CircuitBreakerOpenError(
                    f"Circuit breaker is OPEN. "
                    f"Last failure: {self.last_failure_time}. "
                    f"Retry after {self.recovery_timeout} seconds."
                )
        
        # Execute function
        try:
            result = await func(*args, **kwargs)
            
            # Success - reset circuit if half-open
            if self.state == CircuitState.HALF_OPEN:
                self.state = CircuitState.CLOSED
                self.failure_count = 0
            
            return result
            
        except self.expected_exception as e:
            # Failure - increment counter
            self.failure_count += 1
            self.last_failure_time = time.time()
            
            # Open circuit if threshold reached
            if self.failure_count >= self.failure_threshold:
                self.state = CircuitState.OPEN
            
            # Re-raise exception
            raise e


class CircuitBreakerOpenError(Exception):
    """Raised when circuit breaker is open."""
    pass


def retry_with_backoff(
    max_attempts: int = 3,
    initial_delay: float = 1.0,
    max_delay: float = 10.0,
    exponential_base: float = 2.0,
    retry_on: tuple = (Exception,)
):
    """
    Decorator for retry logic with exponential backoff.
    
    Args:
        max_attempts: Maximum number of retry attempts
        initial_delay: Initial delay in seconds
        max_delay: Maximum delay in seconds
        exponential_base: Base for exponential backoff
        retry_on: Tuple of exception types to retry on
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def async_wrapper(*args, **kwargs) -> Any:
            last_exception = None
            
            for attempt in range(max_attempts):
                try:
                    return await func(*args, **kwargs)
                except retry_on as e:
                    last_exception = e
                    
                    # Don't retry on last attempt
                    if attempt == max_attempts - 1:
                        raise
                    
                    # Calculate delay with exponential backoff
                    delay = min(
                        initial_delay * (exponential_base ** attempt),
                        max_delay
                    )
                    
                    # Wait before retry
                    await asyncio.sleep(delay)
                    
                    # Log retry attempt
                    print(f"  [RETRY] Attempt {attempt + 1}/{max_attempts} for {func.__name__}: {e}")
            
            # Should not reach here, but just in case
            if last_exception:
                raise last_exception
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs) -> Any:
            last_exception = None
            
            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except retry_on as e:
                    last_exception = e
                    
                    # Don't retry on last attempt
                    if attempt == max_attempts - 1:
                        raise
                    
                    # Calculate delay with exponential backoff
                    delay = min(
                        initial_delay * (exponential_base ** attempt),
                        max_delay
                    )
                    
                    # Wait before retry
                    time.sleep(delay)
                    
                    # Log retry attempt
                    print(f"  [RETRY] Attempt {attempt + 1}/{max_attempts} for {func.__name__}: {e}")
            
            # Should not reach here, but just in case
            if last_exception:
                raise last_exception
        
        # Return appropriate wrapper based on function type
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator


# Global circuit breakers for different services
research_circuit_breaker = CircuitBreaker(
    failure_threshold=5,
    recovery_timeout=60,
    expected_exception=Exception
)

generation_circuit_breaker = CircuitBreaker(
    failure_threshold=5,
    recovery_timeout=60,
    expected_exception=Exception
)

review_circuit_breaker = CircuitBreaker(
    failure_threshold=5,
    recovery_timeout=60,
    expected_exception=Exception
)

database_circuit_breaker = CircuitBreaker(
    failure_threshold=3,
    recovery_timeout=30,
    expected_exception=Exception
)
