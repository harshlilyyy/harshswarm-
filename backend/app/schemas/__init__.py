"""
Pydantic schemas for NYX API request/response validation.
Provides type-safe input validation and OpenAPI documentation.
"""
from pydantic import BaseModel, Field, HttpUrl, validator
from typing import List, Optional, Dict, Any
from datetime import datetime


# =============================================================================
# SIMULATION SCHEMAS
# =============================================================================
class SimulationRequest(BaseModel):
    """Request schema for running simulations."""
    agent_names: List[str] = Field(
        ..., 
        min_items=1, 
        max_items=20,
        description="List of agent names for the simulation"
    )
    rounds: int = Field(
        default=8,
        ge=1,
        le=100,
        description="Number of simulation rounds"
    )
    seed: int = Field(
        default=42,
        ge=0,
        description="Random seed for reproducibility"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "agent_names": ["Alice", "Bob", "Charlie"],
                "rounds": 10,
                "seed": 42
            }
        }


class AgentState(BaseModel):
    """Serialized agent state."""
    name: str
    state: Dict[str, Any]
    history_length: int


class SimulationResponse(BaseModel):
    """Response schema for simulation results."""
    simulation_id: str
    state_history: List[Dict[str, Any]]
    outcome_vector: Dict[str, float]
    agents: List[AgentState]
    influence_matrix: List[List[float]]
    seed: int
    
    class Config:
        json_schema_extra = {
            "example": {
                "simulation_id": "sim_1234567890_42",
                "state_history": [],
                "outcome_vector": {"cooperation": 0.75},
                "agents": [],
                "influence_matrix": [],
                "seed": 42
            }
        }


# =============================================================================
# ANALYSIS SCHEMAS
# =============================================================================
class BlackSwanRequest(BaseModel):
    """Request schema for black swan analysis."""
    agent_names: List[str] = Field(..., min_items=1, max_items=20)
    rounds: int = Field(default=8, ge=1, le=100)
    seed: int = Field(default=42, ge=0)


class CounterfactualRequest(BaseModel):
    """Request schema for counterfactual analysis."""
    agent_names: List[str] = Field(..., min_items=1, max_items=20)
    rounds: int = Field(default=8, ge=1, le=100)
    base_seed: int = Field(default=42, ge=0)
    intervention: Optional[str] = Field(
        default=None,
        description="What-if intervention scenario"
    )


class MultiTrialRequest(BaseModel):
    """Request schema for multi-trial analysis."""
    agent_names: List[str] = Field(..., min_items=1, max_items=20)
    rounds: int = Field(default=8, ge=1, le=100)
    base_seed: int = Field(default=42, ge=0)
    trials: int = Field(default=10, ge=1, le=1000)


class GameTheoryRequest(BaseModel):
    """Request schema for game theory analysis."""
    agent_names: List[str] = Field(..., min_items=1, max_items=20)
    rounds: int = Field(default=8, ge=1, le=100)
    seed: int = Field(default=42, ge=0)


# =============================================================================
# LLM GENERATION SCHEMAS
# =============================================================================
class GenerateRequest(BaseModel):
    """Request schema for LLM text generation."""
    prompt: str = Field(..., min_length=1, max_length=10000)
    system: str = Field(default="", max_length=2000)
    preferred_provider: Optional[str] = Field(
        default=None,
        description="Preferred LLM provider (openai, anthropic, etc.)"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "prompt": "Explain quantum entanglement",
                "system": "You are a helpful physics tutor.",
                "preferred_provider": "openai"
            }
        }


class GenerateResponse(BaseModel):
    """Response schema for LLM generation."""
    response: str
    provider: str
    timestamp: datetime


# =============================================================================
# RETRIEVAL SCHEMAS
# =============================================================================
class RetrieveRequest(BaseModel):
    """Request schema for RAG retrieval."""
    query: str = Field(..., min_length=1, max_length=5000)
    top_k: int = Field(default=5, ge=1, le=50)
    source: Optional[str] = Field(
        default=None,
        description="Data source: 'sql' or 'vector'"
    )


class RetrieveResponse(BaseModel):
    """Response schema for retrieval results."""
    query: str
    results: List[Dict[str, Any]]
    count: int


# =============================================================================
# KEY MANAGEMENT SCHEMAS
# =============================================================================
class ProviderHealth(BaseModel):
    """Health status of an API provider."""
    name: str
    status: str  # "active", "cooldown", "failed"
    success_rate: float
    last_error: Optional[str]
    cooldown_until: Optional[datetime]


class KeyStatusResponse(BaseModel):
    """Response schema for API key status."""
    providers: List[ProviderHealth]
    active_provider: str
    rotation_strategy: str


# =============================================================================
# DEBATE SCHEMAS
# =============================================================================
class DebateAgent(BaseModel):
    """Agent configuration for debate."""
    name: str
    stance: str = Field(..., min_length=1, max_length=500)


class DebateRequest(BaseModel):
    """Request schema for running debates."""
    topic: str = Field(..., min_length=1, max_length=2000)
    agents: List[DebateAgent] = Field(..., min_items=2, max_items=10)
    rounds: int = Field(default=3, ge=1, le=10)


class DebateResponse(BaseModel):
    """Response schema for debate results."""
    topic: str
    exchanges: List[Dict[str, Any]]
    summary: str
    winner: Optional[str]


# =============================================================================
# HEALTH CHECK SCHEMAS
# =============================================================================
class HealthCheckResponse(BaseModel):
    """Response schema for health checks."""
    status: str
    timestamp: datetime
    version: str


class ReadinessIssues(BaseModel):
    """Detailed readiness check issues."""
    status: str
    issues: List[str]


# =============================================================================
# CONFIGURATION SCHEMAS
# =============================================================================
class ReloadConfigResponse(BaseModel):
    """Response schema for config reload."""
    status: str
    providers_loaded: int
    timestamp: datetime
