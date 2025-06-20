import time
from collections import defaultdict, deque
from threading import Lock
from typing import Dict, Deque

class RateLimiter:
    """Simple rate limiter to prevent API rate limit issues"""
    
    def __init__(self):
        self._requests: Dict[str, Deque[float]] = defaultdict(deque)
        self._lock = Lock()
        
        # Rate limits per provider (requests per minute)
        self._limits = {
            'openai': 500,  # Conservative limit for OpenAI
            'anthropic': 1000,  # Conservative limit for Anthropic
            'exa': 1000,  # Conservative limit for Exa
        }
        
        # Minimum delay between requests (seconds)
        self._min_delays = {
            'openai': 0.1,  # 100ms between requests
            'anthropic': 0.05,  # 50ms between requests  
            'exa': 0.1,  # 100ms between requests
        }
    
    def wait_if_needed(self, provider: str) -> None:
        """Wait if necessary to respect rate limits"""
        with self._lock:
            now = time.time()
            window_start = now - 60  # 1 minute window
            
            # Clean old requests outside the window
            while self._requests[provider] and self._requests[provider][0] < window_start:
                self._requests[provider].popleft()
            
            # Check if we're at the rate limit
            if len(self._requests[provider]) >= self._limits[provider]:
                # Wait until the oldest request is outside the window
                sleep_time = self._requests[provider][0] + 60 - now + 0.1  # Add small buffer
                if sleep_time > 0:
                    print(f"Rate limiting {provider}: waiting {sleep_time:.2f}s")
                    time.sleep(sleep_time)
                    now = time.time()
            
            # Check minimum delay since last request
            if self._requests[provider]:
                time_since_last = now - self._requests[provider][-1]
                min_delay = self._min_delays[provider]
                if time_since_last < min_delay:
                    sleep_time = min_delay - time_since_last
                    time.sleep(sleep_time)
                    now = time.time()
            
            # Record this request
            self._requests[provider].append(now)

# Global rate limiter instance
rate_limiter = RateLimiter()