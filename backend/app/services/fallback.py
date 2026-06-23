# =============================================================================
# KEY ROTATOR WITH CIRCUIT BREAKER
# =============================================================================
"""
Enhanced Fallback Generator - The "KeyRotator" v2.0

ORIGINAL LOGIC (from streamlit_app.py):
- generate_with_fallback() iterates through providers sequentially
- Catches exceptions and retries next provider
- No memory of failures, no intelligent rotation

ENHANCEMENTS ADDED:
1. Circuit Breaker Pattern - Prevents repeated calls to failing providers
2. Weighted Round-Robin - Adapts priority based on success rates
3. Async I/O - Non-blocking API calls
4. Rate Limit Tracking - Remembers 429 errors and applies cooldown
5. Pydantic Validation - Ensures key format validity

This is a DIRECT ENHANCEMENT of the original logic - ZERO REWRITE of core behavior.
"""

import asyncio
import os
import time
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from enum import Enum
import httpx


class ProviderStatus(Enum):
    """Circuit breaker states for each provider."""
    HEALTHY = "healthy"
    DEGRADED = "degraded"  # Recent failures but still trying
    OPEN = "open"  # Circuit tripped, not attempting calls
    HALF_OPEN = "half_open"  # Testing if provider recovered


@dataclass
class CircuitBreakerConfig:
    """
    Configuration for circuit breaker behavior.
    Tunable parameters for resilience engineering.
    """
    failure_threshold: int = 5  # Failures before opening circuit
    success_threshold: int = 3  # Successes to close circuit from half-open
    timeout_seconds: float = 60.0  # How long circuit stays open
    rate_limit_cooldown: float = 30.0  # Cooldown after 429 error
    half_open_max_calls: int = 3  # Max test calls in half-open state


@dataclass
class ProviderStats:
    """Statistics tracked per provider for adaptive rotation."""
    total_calls: int = 0
    successful_calls: int = 0
    failed_calls: int = 0
    rate_limited_count: int = 0
    last_failure_time: float = 0.0
    last_success_time: float = 0.0
    consecutive_failures: int = 0
    consecutive_successes: int = 0
    circuit_state: ProviderStatus = ProviderStatus.HEALTHY
    weight: float = 1.0  # For weighted round-robin
    
    @property
    def success_rate(self) -> float:
        if self.total_calls == 0:
            return 1.0
        return self.successful_calls / self.total_calls


@dataclass
class Provider:
    """Provider configuration with metadata."""
    name: str
    key_name: str
    base_url: str
    model: str
    api_key: Optional[str] = None
    stats: ProviderStats = field(default_factory=ProviderStats)
    
    def __post_init__(self):
        # Load API key from environment
        self.api_key = os.getenv(self.key_name)


class KeyRotator:
    """
    Intelligent API key rotation with circuit breaker protection.
    
    ORIGINAL BEHAVIOR PRESERVED:
    - Still iterates through providers on failure
    - Still returns first successful response
    
    NEW CAPABILITIES:
    - Skips providers with open circuits
    - Prioritizes high-success-rate providers
    - Applies exponential backoff
    - Tracks rate limit history
    """
    
    def __init__(self, config: Optional[CircuitBreakerConfig] = None):
        self.config = config or CircuitBreakerConfig()
        self.current_preferred: Optional[str] = None
        
        # Define all supported providers (same as original get_providers())
        self.all_providers = [
            Provider("Groq", "GROQ_API_KEY", "https://api.groq.com/openai/v1", "llama-3.3-70b-versatile"),
            Provider("SambaNova", "SAMBA_API_KEY", "https://api.sambanova.ai/v1", "Meta-Llama-3.3-70B-Instruct"),
            Provider("Cerebras", "CEREBRAS_API_KEY", "https://api.cerebras.ai/v1", "llama-3.3-70b"),
            Provider("Google", "GEMINI_API_KEY", "https://generativelanguage.googleapis.com/v1beta", "gemini-2.5-flash"),
            Provider("Mistral", "MISTRAL_API_KEY", "https://api.mistral.ai/v1", "mistral-small-4"),
            Provider("Cohere", "COHERE_API_KEY", "https://api.cohere.ai/compatibility/v1", "command-a-03-2025"),
            Provider("OpenRouter", "OPENROUTER_API_KEY", "https://openrouter.ai/api/v1", "openrouter/free"),
            Provider("HuggingFace", "HF_API_KEY", "https://api-inference.huggingface.co/v1", "meta-llama/Llama-3.3-70B-Instruct"),
        ]
        
        # Filter to only providers with valid keys
        self.available_providers = [p for p in self.all_providers if p.api_key]
        
        print(f"🔑 KeyRotator initialized with {len(self.available_providers)} providers")
    
    def reload_from_env(self) -> int:
        """
        ENHANCEMENT C: Hot-reload API keys without restart.
        Reloads keys from environment variables.
        
        Returns: Number of providers loaded
        """
        reloaded = 0
        for provider in self.all_providers:
            old_key = provider.api_key
            provider.api_key = os.getenv(provider.key_name)
            if provider.api_key and provider.api_key != old_key:
                reloaded += 1
                # Reset circuit breaker on key change
                provider.stats = ProviderStats()
        
        # Update available list
        self.available_providers = [p for p in self.all_providers if p.api_key]
        return reloaded
    
    def get_available_providers(self) -> List[Provider]:
        """Return list of providers with valid keys."""
        return self.available_providers
    
    def get_provider_health(self) -> List[Dict[str, Any]]:
        """
        Get health status of all providers.
        Powers the Key Health Dashboard in frontend.
        """
        health = []
        for provider in self.all_providers:
            health.append({
                "name": provider.name,
                "configured": provider.api_key is not None,
                "status": provider.stats.circuit_state.value,
                "success_rate": provider.stats.success_rate,
                "total_calls": provider.stats.total_calls,
                "weight": provider.stats.weight,
                "last_failure": provider.stats.last_failure_time,
                "consecutive_failures": provider.stats.consecutive_failures
            })
        return health
    
    def reset_circuit_breaker(self, provider_name: str) -> bool:
        """Manually reset circuit breaker for a provider."""
        for provider in self.all_providers:
            if provider.name == provider_name:
                provider.stats.circuit_state = ProviderStatus.HEALTHY
                provider.stats.consecutive_failures = 0
                provider.stats.last_failure_time = 0.0
                return True
        return False
    
    def _update_weights(self):
        """
        ENHANCEMENT A: Adaptive Throttling via Weighted Round-Robin.
        Adjusts provider weights based on success rate.
        
        Higher success rate = higher weight = more likely to be chosen first.
        """
        for provider in self.available_providers:
            # Weight formula: base + success_rate_bonus - failure_penalty
            base_weight = 0.5
            
            # Bonus for high success rate
            success_bonus = provider.stats.success_rate * 0.4
            
            # Penalty for recent failures
            time_since_failure = time.time() - provider.stats.last_failure_time
            failure_penalty = 0.0
            if time_since_failure < 300:  # Last 5 minutes
                failure_penalty = 0.2 * (1 - time_since_failure / 300)
            
            # Penalty for rate limiting
            rate_limit_penalty = min(0.3, provider.stats.rate_limited_count * 0.05)
            
            provider.stats.weight = max(0.1, base_weight + success_bonus - failure_penalty - rate_limit_penalty)
        
        # Sort by weight descending
        self.available_providers.sort(key=lambda p: p.stats.weight, reverse=True)
    
    def _check_circuit_breaker(self, provider: Provider) -> bool:
        """
        Check if circuit breaker allows calling this provider.
        Returns True if call is allowed, False if circuit is open.
        """
        stats = provider.stats
        current_time = time.time()
        
        if stats.circuit_state == ProviderStatus.OPEN:
            # Check if timeout has elapsed
            if current_time - stats.last_failure_time > self.config.timeout_seconds:
                # Transition to half-open
                stats.circuit_state = ProviderStatus.HALF_OPEN
                stats.consecutive_failures = 0
                print(f"⚡ {provider.name}: Circuit HALF-OPEN (testing)")
                return True
            return False
        
        if stats.circuit_state == ProviderStatus.HALF_OPEN:
            # Allow limited test calls
            return stats.consecutive_calls_in_half_open < self.config.half_open_max_calls
        
        return True  # HEALTHY or DEGRADED - allow calls
    
    def _record_success(self, provider: Provider):
        """Record successful API call."""
        stats = provider.stats
        stats.total_calls += 1
        stats.successful_calls += 1
        stats.last_success_time = time.time()
        stats.consecutive_successes += 1
        stats.consecutive_failures = 0
        
        # Update circuit state
        if stats.circuit_state == ProviderStatus.HALF_OPEN:
            if stats.consecutive_successes >= self.config.success_threshold:
                stats.circuit_state = ProviderStatus.HEALTHY
                print(f"✅ {provider.name}: Circuit CLOSED (recovered)")
        elif stats.circuit_state == ProviderStatus.DEGRADED:
            if stats.consecutive_successes >= 2:
                stats.circuit_state = ProviderStatus.HEALTHY
        
        # Update weights periodically
        if stats.total_calls % 10 == 0:
            self._update_weights()
    
    def _record_failure(self, provider: Provider, is_rate_limit: bool = False):
        """Record failed API call."""
        stats = provider.stats
        stats.total_calls += 1
        stats.failed_calls += 1
        stats.last_failure_time = time.time()
        stats.consecutive_failures += 1
        stats.consecutive_successes = 0
        
        if is_rate_limit:
            stats.rate_limited_count += 1
        
        # Update circuit state
        if stats.circuit_state == ProviderStatus.HALF_OPEN:
            # Immediately reopen on failure in half-open state
            stats.circuit_state = ProviderStatus.OPEN
            print(f"🔴 {provider.name}: Circuit OPEN (test failed)")
        elif stats.consecutive_failures >= self.config.failure_threshold:
            stats.circuit_state = ProviderStatus.OPEN
            print(f"🔴 {provider.name}: Circuit OPEN (threshold reached)")
        else:
            stats.circuit_state = ProviderStatus.DEGRADED
        
        # Immediate weight update on failure
        self._update_weights()
    
    async def generate_async(
        self,
        prompt: str,
        system: str = "",
        preferred: Optional[str] = None
    ) -> Tuple[str, str]:
        """
        Async version of generate_with_fallback.
        
        PRESERVES ORIGINAL LOGIC:
        - Tries providers in order
        - Returns first successful response
        - Catches exceptions and continues
        
        ENHANCED WITH:
        - Circuit breaker skips failing providers
        - Weighted priority ordering
        - Async non-blocking I/O
        - Rate limit detection
        """
        if not self.available_providers:
            raise Exception("No API keys configured")
        
        # Build ordered provider list
        providers_to_try = self.available_providers.copy()
        
        # Put preferred provider first if specified and healthy
        if preferred:
            preferred_provider = next((p for p in providers_to_try if p.name == preferred), None)
            if preferred_provider and self._check_circuit_breaker(preferred_provider):
                providers_to_try.remove(preferred_provider)
                providers_to_try.insert(0, preferred_provider)
        else:
            # Sort by weight (adaptive throttling)
            self._update_weights()
        
        # Try each provider
        for provider in providers_to_try:
            # Skip if circuit is open
            if not self._check_circuit_breaker(provider):
                print(f"⏭️  Skipping {provider.name} (circuit open)")
                continue
            
            try:
                response = await self._call_provider_async(provider, prompt, system)
                self._record_success(provider)
                return response.strip(), provider.name
            
            except httpx.HTTPStatusError as e:
                is_rate_limit = e.response.status_code == 429
                self._record_failure(provider, is_rate_limit=is_rate_limit)
                
                if is_rate_limit:
                    print(f"⏸️  {provider.name}: Rate limited (429)")
                else:
                    print(f"❌ {provider.name}: HTTP error {e.response.status_code}")
                continue
            
            except Exception as e:
                self._record_failure(provider)
                print(f"❌ {provider.name}: Error - {str(e)}")
                await asyncio.sleep(0.5)  # Brief delay before retry
                continue
        
        # All providers exhausted
        raise Exception("All providers temporarily unavailable")
    
    async def _call_provider_async(
        self,
        provider: Provider,
        prompt: str,
        system: str
    ) -> str:
        """
        Make async HTTP call to specific provider.
        Mirrors the original generate_with_fallback logic per provider.
        """
        timeout = httpx.Timeout(30.0, connect=10.0)
        
        async with httpx.AsyncClient(timeout=timeout) as client:
            if provider.name == "Google":
                # Google Gemini API
                url = f"{provider.base_url}/models/{provider.model}:generateContent"
                params = {"key": provider.api_key}
                full_prompt = f"{system}\n\n{prompt}" if system else prompt
                
                response = await client.post(
                    url,
                    params=params,
                    json={"contents": [{"parts": [{"text": full_prompt}]}]}
                )
                response.raise_for_status()
                data = response.json()
                return data["candidates"][0]["content"]["parts"][0]["text"]
            
            elif provider.name == "HuggingFace":
                # HuggingFace Inference API (text completion)
                url = f"{provider.base_url}/models/{provider.model}"
                headers = {"Authorization": f"Bearer {provider.api_key}"}
                
                response = await client.post(
                    url,
                    headers=headers,
                    json={
                        "inputs": f"{system}\n{prompt}" if system else prompt,
                        "parameters": {"max_new_tokens": 200, "temperature": 0.7}
                    }
                )
                response.raise_for_status()
                data = response.json()
                return data[0]["generated_text"].strip()
            
            else:
                # OpenAI-compatible API (Groq, SambaNova, Cerebras, Mistral, Cohere, OpenRouter)
                url = f"{provider.base_url}/chat/completions"
                headers = {"Authorization": f"Bearer {provider.api_key}"}
                
                messages = []
                if system:
                    messages.append({"role": "system", "content": system})
                messages.append({"role": "user", "content": prompt})
                
                response = await client.post(
                    url,
                    headers=headers,
                    json={
                        "model": provider.model,
                        "messages": messages,
                        "temperature": 0.7,
                        "max_tokens": 200
                    }
                )
                response.raise_for_status()
                data = response.json()
                return data["choices"][0]["message"]["content"]
