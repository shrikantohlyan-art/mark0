"""
Rate limiting middleware for JARVIS API
"""
import time
import logging
from typing import Dict, List, Callable
from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from functools import wraps

logger = logging.getLogger(__name__)


class RateLimiter:
    """Simple in-memory rate limiter."""
    
    def __init__(self, max_requests: int = 100, time_window: int = 60):
        """
        Initialize rate limiter.
        
        Args:
            max_requests: Maximum number of requests allowed
            time_window: Time window in seconds
        """
        self.max_requests = max_requests
        self.time_window = time_window
        self.requests: Dict[str, List[float]] = {}
    
    def check_limit(self, client_id: str) -> bool:
        """
        Check if client has exceeded rate limit.
        
        Args:
            client_id: Unique identifier for the client (IP, user ID, etc.)
        
        Returns:
            True if within limit, False if exceeded
        
        Raises:
            HTTPException: If rate limit exceeded
        """
        current_time = time.time()

        if len(self.requests) > 1000:
            self.cleanup()
        
        if client_id not in self.requests:
            self.requests[client_id] = []
        
        # Remove old requests outside the time window
        self.requests[client_id] = [
            req_time for req_time in self.requests[client_id]
            if current_time - req_time < self.time_window
        ]
        
        # Check if limit exceeded
        if len(self.requests[client_id]) >= self.max_requests:
            logger.warning(f"Rate limit exceeded for client {client_id}")
            raise HTTPException(
                status_code=429,
                detail=f"Rate limit exceeded. Max {self.max_requests} requests per {self.time_window} seconds"
            )
        
        # Record this request
        self.requests[client_id].append(current_time)
        return True
    
    def get_remaining_requests(self, client_id: str) -> int:
        """Get number of remaining requests for a client."""
        current_time = time.time()
        
        if client_id not in self.requests:
            return self.max_requests
        
        # Remove old requests
        self.requests[client_id] = [
            req_time for req_time in self.requests[client_id]
            if current_time - req_time < self.time_window
        ]
        
        return max(0, self.max_requests - len(self.requests[client_id]))
    
    def cleanup(self, max_age: int = 3600):
        """Remove stale entries older than max_age seconds."""
        current_time = time.time()
        clients_to_remove = []
        
        for client_id, requests in self.requests.items():
            requests = [t for t in requests if current_time - t < max_age]
            if not requests:
                clients_to_remove.append(client_id)
            else:
                self.requests[client_id] = requests
        
        for client_id in clients_to_remove:
            del self.requests[client_id]
        
        if clients_to_remove:
            logger.debug(f"Cleaned up {len(clients_to_remove)} stale rate limit entries")


# Global rate limiters for different endpoints
chat_limiter = RateLimiter(max_requests=30, time_window=60)  # 30 requests per minute
tts_limiter = RateLimiter(max_requests=60, time_window=60)   # 60 requests per minute
models_limiter = RateLimiter(max_requests=10, time_window=60)  # 10 requests per minute


async def rate_limit_middleware(request: Request, call_next):
    """
    Middleware for rate limiting.
    
    Args:
        request: FastAPI request object
        call_next: Next middleware/route handler
    
    Returns:
        Response from next handler
    """
    # Get client IP
    client_ip = request.client.host if request.client else "unknown"
    
    # Skip rate limiting for health checks
    if request.url.path in ("/health", "/api/health"):
        return await call_next(request)

    # Allow CORS preflight requests to pass through quickly
    if request.method and request.method.upper() == "OPTIONS":
        # Respond to preflight directly to avoid routing into endpoints
        return JSONResponse(status_code=200, content={}, headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "*",
            "Access-Control-Allow-Headers": "*",
        })
    
    # Get appropriate limiter based on path
    if "/chat" in request.url.path:
        limiter = chat_limiter
    elif "/tts" in request.url.path:
        limiter = tts_limiter
    elif "/models" in request.url.path:
        limiter = models_limiter
    else:
        return await call_next(request)
    
    # Check rate limit
    try:
        limiter.check_limit(client_ip)
    except HTTPException as e:
        return JSONResponse(status_code=e.status_code, content={"detail": e.detail})
    
    response = await call_next(request)
    
    # Add rate limit headers
    response.headers["X-RateLimit-Limit"] = str(limiter.max_requests)
    response.headers["X-RateLimit-Remaining"] = str(limiter.get_remaining_requests(client_ip))
    
    return response


def rate_limit_decorator(max_requests: int = 10, time_window: int = 60):
    """
    Decorator for rate limiting functions.
    
    Args:
        max_requests: Maximum number of calls
        time_window: Time window in seconds
    
    Returns:
        Decorated function
    """
    limiter = RateLimiter(max_requests=max_requests, time_window=time_window)
    
    def decorator(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            client_id = kwargs.get('client_id', 'default')
            limiter.check_limit(client_id)
            return func(*args, **kwargs)
        return wrapper
    
    return decorator
