# =============================================================================
# ADAPTERS - Redis Caching & Celery Task Queue
# =============================================================================
"""
Feature #2: Semantic Request Caching
Feature #17: Autoscaling Worker Pool

This module provides:
1. Redis-backed LRU cache for prompt responses
2. Celery task queue integration for background jobs
3. SHA-256 hashing for cache keys
"""

import hashlib
import json
import asyncio
from typing import Optional, Any, Dict
from datetime import timedelta
import time

try:
    import redis.asyncio as aioredis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    print("⚠️  redis-py not installed, caching disabled")

try:
    from celery import Celery
    CELERY_AVAILABLE = True
except ImportError:
    CELERY_AVAILABLE = False
    print("⚠️  celery not installed, task queue disabled")


# =============================================================================
# SEMANTIC CACHE (Feature #2)
# =============================================================================

class SemanticCache:
    """
    Feature #2: Semantic Request Caching
    
    LRU cache backed by Redis. Uses SHA-256 hash of prompt as cache key.
    If an identical prompt is sent within TTL (1 hour), serves cached response.
    
    Benefits:
    - Reduces API costs by avoiding duplicate calls
    - Improves response latency for repeated queries
    - Preserves token quota
    """
    
    def __init__(
        self,
        redis_url: str = "redis://localhost:6379",
        ttl_seconds: int = 3600,  # 1 hour default
        prefix: str = "nyx:cache"
    ):
        self.redis_url = redis_url
        self.ttl_seconds = ttl_seconds
        self.prefix = prefix
        self._redis: Optional[aioredis.Redis] = None
    
    async def connect(self):
        """Initialize Redis connection."""
        if not REDIS_AVAILABLE:
            return
        
        try:
            self._redis = await aioredis.from_url(
                self.redis_url,
                decode_responses=True,
                encoding="utf-8"
            )
            await self._redis.ping()
            print(f"✅ Redis connected for semantic caching @ {self.redis_url}")
        except Exception as e:
            print(f"⚠️  Redis connection failed: {e}. Caching disabled.")
            self._redis = None
    
    def _generate_cache_key(self, prompt: str, system: str = "", model: str = "") -> str:
        """
        Generate SHA-256 hash of prompt + context as cache key.
        
        Args:
            prompt: User prompt
            system: System prompt (optional)
            model: Model identifier (optional, for cache segregation)
        
        Returns:
            Cache key string: "nyx:cache:<sha256_hash>"
        """
        content = f"{model}:{system}:{prompt}"
        hash_digest = hashlib.sha256(content.encode('utf-8')).hexdigest()
        return f"{self.prefix}:{hash_digest}"
    
    async def get(self, prompt: str, system: str = "", model: str = "") -> Optional[str]:
        """
        Retrieve cached response if exists.
        
        Returns:
            Cached response string or None if not found
        """
        if not self._redis:
            return None
        
        try:
            cache_key = self._generate_cache_key(prompt, system, model)
            cached = await self._redis.get(cache_key)
            
            if cached:
                print(f"💾 CACHE HIT: {cache_key[:20]}...")
                return cached
            else:
                print(f"🔍 CACHE MISS: {cache_key[:20]}...")
                return None
        except Exception as e:
            print(f"❌ Cache get error: {e}")
            return None
    
    async def set(
        self,
        prompt: str,
        response: str,
        system: str = "",
        model: str = ""
    ) -> bool:
        """
        Store response in cache with TTL.
        
        Args:
            prompt: Original prompt
            response: LLM response to cache
            system: System prompt used
            model: Model identifier
        
        Returns:
            True if successful, False otherwise
        """
        if not self._redis:
            return False
        
        try:
            cache_key = self._generate_cache_key(prompt, system, model)
            await self._redis.setex(
                cache_key,
                timedelta(seconds=self.ttl_seconds),
                response
            )
            print(f"💾 CACHE SET: {cache_key[:20]}... (TTL: {self.ttl_seconds}s)")
            return True
        except Exception as e:
            print(f"❌ Cache set error: {e}")
            return False
    
    async def delete(self, prompt: str, system: str = "", model: str = "") -> bool:
        """Delete specific cache entry."""
        if not self._redis:
            return False
        
        try:
            cache_key = self._generate_cache_key(prompt, system, model)
            await self._redis.delete(cache_key)
            return True
        except Exception as e:
            print(f"❌ Cache delete error: {e}")
            return False
    
    async def clear_all(self) -> bool:
        """Clear all cache entries with our prefix."""
        if not self._redis:
            return False
        
        try:
            pattern = f"{self.prefix}:*"
            keys = []
            async for key in self._redis.scan_iter(match=pattern):
                keys.append(key)
            
            if keys:
                await self._redis.delete(*keys)
                print(f"🗑️  Cleared {len(keys)} cache entries")
            return True
        except Exception as e:
            print(f"❌ Cache clear error: {e}")
            return False
    
    async def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        if not self._redis:
            return {"enabled": False}
        
        try:
            pattern = f"{self.prefix}:*"
            count = 0
            async for _ in self._redis.scan_iter(match=pattern):
                count += 1
            
            info = await self._redis.info("memory")
            return {
                "enabled": True,
                "keys_count": count,
                "ttl_seconds": self.ttl_seconds,
                "memory_used_bytes": info.get("used_memory", 0)
            }
        except Exception as e:
            return {"enabled": True, "error": str(e)}


# =============================================================================
# CELERY TASK QUEUE (Feature #17)
# =============================================================================

def create_celery_app(broker_url: str = "redis://localhost:6379/1") -> Optional[Celery]:
    """
    Feature #17: Autoscaling Worker Pool
    
    Creates Celery app for background task processing.
    Use this for long-running simulations that shouldn't block HTTP requests.
    
    Configuration:
    - Broker: Redis (for task queue)
    - Backend: Redis (for result storage)
    - Auto-scaling: Configure via Celery worker options
    """
    if not CELERY_AVAILABLE:
        return None
    
    celery_app = Celery(
        'nyx_tasks',
        broker=broker_url,
        backend=broker_url,
        include=['app.services.adapters']
    )
    
    # Optimize for CPU-bound simulation tasks
    celery_app.conf.update(
        task_serializer='json',
        accept_content=['json'],
        result_serializer='json',
        timezone='UTC',
        enable_utc=True,
        task_track_started=True,
        task_time_limit=300,  # 5 minute max per task
        worker_prefetch_multiplier=1,  # Fair distribution
        worker_max_tasks_per_child=100,  # Prevent memory leaks
    )
    
    print(f"✅ Celery app created with broker @ {broker_url}")
    return celery_app


# Example Celery task for background simulation
if CELERY_AVAILABLE:
    celery_app = create_celery_app()
    
    if celery_app:
        @celery_app.task(bind=True, max_retries=3)
        def run_simulation_background(self, agent_names: list, rounds: int, seed: int):
            """
            Background task for running simulations.
            Use this for large-scale simulations (>50 rounds, >20 agents).
            
            Automatically retries on failure (max 3 times).
            Results stored in Celery backend.
            """
            try:
                # Import here to avoid circular dependency
                from app.core.nyx_kernel import run_simulation
                
                result = run_simulation(
                    agent_names=agent_names,
                    rounds=rounds,
                    seed=seed
                )
                
                return {
                    "status": "success",
                    "result": result,
                    "task_id": self.request.id
                }
            
            except Exception as exc:
                # Retry with exponential backoff
                raise self.retry(exc=exc, countdown=60 * (2 ** (self.request.retries or 0)))


# =============================================================================
# USAGE EXAMPLES
# =============================================================================

"""
# Using Semantic Cache in your endpoint:

cache = SemanticCache(redis_url="redis://your-redis:6379")
await cache.connect()

@app.post("/api/generate")
async def generate(prompt: str):
    # Check cache first
    cached = await cache.get(prompt, system="You are helpful")
    if cached:
        return {"response": cached, "source": "cache"}
    
    # Generate new response
    response = await llm_call(prompt)
    
    # Store in cache
    await cache.set(prompt, response, system="You are helpful")
    
    return {"response": response, "source": "llm"}


# Using Celery for background tasks:

from app.services.adapters import run_simulation_background

@app.post("/api/simulate/large")
async def large_simulation(agent_names: list, rounds: int = 100):
    # Offload to Celery worker
    task = run_simulation_background.delay(agent_names, rounds, 42)
    
    return {
        "task_id": task.id,
        "status": "queued",
        "message": f"Simulation queued. Check status at /api/tasks/{task.id}"
    }
"""
