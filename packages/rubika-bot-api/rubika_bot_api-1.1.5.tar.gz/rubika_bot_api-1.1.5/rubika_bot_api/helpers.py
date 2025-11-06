"""Helper classes for high-performance bot operations."""
import asyncio
import time
from typing import Dict, Any, Optional, Callable, List
from collections import defaultdict
from collections import deque


class StateManager:
    """High-performance in-memory state manager."""
    
    def __init__(self):
        self._states: Dict[str, str] = {}
        self._expiry: Dict[str, float] = {}
    
    async def set(self, user_id: str, state: str, expire: Optional[int] = None):
        """Set state for a user with optional expiration."""
        self._states[user_id] = state
        if expire:
            self._expiry[user_id] = time.time() + expire
        elif user_id in self._expiry:
            del self._expiry[user_id]
    
    async def get(self, user_id: str) -> Optional[str]:
        """Get state for a user."""
        if user_id in self._expiry and time.time() > self._expiry[user_id]:
            self.clear(user_id)
            return None
        return self._states.get(user_id)
    
    async def clear(self, user_id: str):
        """Clear state for a user."""
        self._states.pop(user_id, None)
        self._expiry.pop(user_id, None)
    
    async def check(self, user_id: str, state: str) -> bool:
        """Check if user has specific state."""
        return await self.get(user_id) == state


class RateLimiter:
    """High-performance rate limiter for preventing spam."""
    
    def __init__(self, limit: int = 5, per_seconds: int = 60):
        self.limit = limit
        self.per_seconds = per_seconds
        self._user_requests: Dict[str, deque] = defaultdict(lambda: deque(maxlen=limit))
    
    async def is_allowed(self, user_id: str) -> bool:
        """Check if user is allowed to make a request."""
        now = time.time()
        user_queue = self._user_requests[user_id]
        
        # Remove old requests
        while user_queue and (now - user_queue[0]) > self.per_seconds:
            user_queue.popleft()
        
        if len(user_queue) >= self.limit:
            return False
        
        user_queue.append(now)
        return True
    
    async def get_remaining_time(self, user_id: str) -> float:
        """Get remaining time until next request is allowed."""
        user_queue = self._user_requests.get(user_id, deque())
        if not user_queue:
            return 0.0
        
        oldest = user_queue[0]
        elapsed = time.time() - oldest
        return max(0.0, self.per_seconds - elapsed)


class Scheduler:
    """High-performance async task scheduler."""
    
    def __init__(self):
        self.tasks: List[asyncio.Task] = []
    
    async def run_after(self, delay: float, func: Callable, *args, **kwargs) -> asyncio.Task:
        """Schedule a function to run after a delay."""
        async def task():
            await asyncio.sleep(delay)
            if asyncio.iscoroutinefunction(func):
                await func(*args, **kwargs)
            else:
                func(*args, **kwargs)
        
        task_obj = asyncio.create_task(task())
        self.tasks.append(task_obj)
        return task_obj
    
    async def run_every(self, interval: float, func: Callable, *args, **kwargs) -> asyncio.Task:
        """Schedule a function to run repeatedly."""
        async def task():
            while True:
                await asyncio.sleep(interval)
                if asyncio.iscoroutinefunction(func):
                    await func(*args, **kwargs)
                else:
                    func(*args, **kwargs)
        
        task_obj = asyncio.create_task(task())
        self.tasks.append(task_obj)
        return task_obj
    
    async def cancel_all(self):
        """Cancel all scheduled tasks."""
        for task in self.tasks:
            if not task.done():
                task.cancel()
        await asyncio.gather(*self.tasks, return_exceptions=True)
        self.tasks.clear()

