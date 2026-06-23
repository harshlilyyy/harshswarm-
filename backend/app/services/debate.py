# =============================================================================
# DEBATE ORCHESTRATOR
# =============================================================================
"""
Multi-Agent Debate Service

PRESERVES ORIGINAL LOGIC from streamlit_app.py:
- DebateAgent class
- run_standard_debate() function

WRAPPED for async FastAPI usage.
"""

import asyncio
from typing import List, Dict, Tuple, Optional
from app.services.fallback import KeyRotator


class DebateAgent:
    """
    LLM-powered debate participant.
    Direct port from streamlit_app.py with async support.
    """
    
    def __init__(self, name: str, stance: str):
        self.name = name
        self.stance = stance
        self.history: List[str] = []
    
    async def speak(
        self,
        topic: str,
        last_msg: str,
        round_num: int,
        key_rotator: KeyRotator,
        preferred_provider: Optional[str] = None
    ) -> Tuple[str, str]:
        """
        Generate argument for this debate round.
        
        Returns:
            Tuple of (argument_text, provider_used)
        """
        prompt = f'''Debate round {round_num} on: "{topic}".
You are {self.name} ({self.stance}). Last message: "{last_msg}".
Give a short, sharp argument (1-3 sentences).'''
        
        system = f"You are {self.name}. {self.stance}. Keep it concise."
        
        response, provider = await key_rotator.generate_async(
            prompt=prompt,
            system=system,
            preferred=preferred_provider
        )
        
        self.history.append(response)
        return response, provider


class DebateOrchestrator:
    """
    Orchestrates multi-round debates between agents.
    """
    
    def __init__(self, key_rotator: KeyRotator):
        self.key_rotator = key_rotator
    
    async def run_debate(
        self,
        topic: str,
        agents: List[Dict[str, str]],
        rounds: int = 3,
        preferred_provider: Optional[str] = None
    ) -> Tuple[List[str], str]:
        """
        Run a complete multi-round debate.
        
        Args:
            topic: Debate topic
            agents: List of {name, stance} dicts
            rounds: Number of rounds
            preferred_provider: Optional preferred LLM provider
        
        Returns:
            Tuple of (debate_log, winner_name)
        """
        # Create agent instances
        agent_instances = [
            DebateAgent(a["name"], a["stance"])
            for a in agents
        ]
        
        if len(agent_instances) < 2:
            return ["Need at least 2 agents for a debate"], "None"
        
        log = []
        last_msg = topic
        
        # Run debate rounds
        for r in range(1, rounds + 1):
            for agent in agent_instances:
                msg, provider = await agent.speak(
                    topic=topic,
                    last_msg=last_msg,
                    round_num=r,
                    key_rotator=self.key_rotator,
                    preferred_provider=preferred_provider
                )
                
                log.append(f"**Round {r} – {agent.name}** (via {provider}): {msg}")
                last_msg = msg
        
        # Determine winner by total argument length (heuristic from original)
        winner = max(
            agent_instances,
            key=lambda a: sum(len(m) for m in a.history) / max(1, len(a.history))
        ).name
        
        return log, winner
