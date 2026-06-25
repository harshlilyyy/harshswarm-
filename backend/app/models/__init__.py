"""
SQLAlchemy ORM models for NYX database layer.
Provides persistent storage for simulations, agents, and results.
"""
from sqlalchemy import Column, Integer, String, Float, DateTime, Text, JSON, ForeignKey, Index
from sqlalchemy.orm import relationship, declarative_base
from datetime import datetime
import uuid

Base = declarative_base()


# =============================================================================
# SIMULATION MODELS
# =============================================================================
class Simulation(Base):
    """
    Stores simulation runs with metadata.
    Enables historical analysis and reproducibility.
    """
    __tablename__ = "simulations"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    seed = Column(Integer, nullable=False)
    rounds = Column(Integer, nullable=False)
    agent_count = Column(Integer, nullable=False)
    outcome_vector = Column(JSON, nullable=True)  # Serialized outcome data
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    agents = relationship("AgentState", back_populates="simulation", cascade="all, delete-orphan")
    state_history = relationship("StateHistory", back_populates="simulation", cascade="all, delete-orphan")
    
    __table_args__ = (
        Index('idx_simulations_created', 'created_at'),
        Index('idx_simulations_seed', 'seed'),
    )
    
    def to_dict(self):
        """Convert to dictionary for API responses."""
        return {
            "id": self.id,
            "seed": self.seed,
            "rounds": self.rounds,
            "agent_count": self.agent_count,
            "outcome_vector": self.outcome_vector,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }


class AgentState(Base):
    """
    Stores final state of agents in a simulation.
    """
    __tablename__ = "agent_states"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    simulation_id = Column(String(36), ForeignKey("simulations.id"), nullable=False)
    name = Column(String(255), nullable=False)
    state_data = Column(JSON, nullable=False)  # Serialized agent state
    history_length = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    simulation = relationship("Simulation", back_populates="agents")
    
    __table_args__ = (
        Index('idx_agent_states_simulation', 'simulation_id'),
        Index('idx_agent_states_name', 'name'),
    )
    
    def to_dict(self):
        """Convert to dictionary for API responses."""
        return {
            "id": self.id,
            "simulation_id": self.simulation_id,
            "name": self.name,
            "state_data": self.state_data,
            "history_length": self.history_length
        }


class StateHistory(Base):
    """
    Stores time-series state history for simulations.
    Enables replay and temporal analysis.
    """
    __tablename__ = "state_history"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    simulation_id = Column(String(36), ForeignKey("simulations.id"), nullable=False)
    round_number = Column(Integer, nullable=False)
    state_data = Column(JSON, nullable=False)  # Full state at this round
    timestamp = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    simulation = relationship("Simulation", back_populates="state_history")
    
    __table_args__ = (
        Index('idx_state_history_simulation', 'simulation_id'),
        Index('idx_state_history_round', 'round_number'),
    )
    
    def to_dict(self):
        """Convert to dictionary for API responses."""
        return {
            "id": self.id,
            "simulation_id": self.simulation_id,
            "round_number": self.round_number,
            "state_data": self.state_data,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None
        }


# =============================================================================
# ANALYSIS MODELS
# =============================================================================
class AnalysisResult(Base):
    """
    Stores results from advanced analyses (black swan, counterfactual, etc.).
    """
    __tablename__ = "analysis_results"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    simulation_id = Column(String(36), ForeignKey("simulations.id"), nullable=True)
    analysis_type = Column(String(50), nullable=False)  # "black_swan", "counterfactual", etc.
    parameters = Column(JSON, nullable=False)  # Input parameters
    results = Column(JSON, nullable=False)  # Analysis output
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    
    __table_args__ = (
        Index('idx_analysis_type', 'analysis_type'),
        Index('idx_analysis_created', 'created_at'),
    )
    
    def to_dict(self):
        """Convert to dictionary for API responses."""
        return {
            "id": self.id,
            "simulation_id": self.simulation_id,
            "analysis_type": self.analysis_type,
            "parameters": self.parameters,
            "results": self.results,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }


# =============================================================================
# DEBATE MODELS
# =============================================================================
class Debate(Base):
    """
    Stores debate sessions and exchanges.
    """
    __tablename__ = "debates"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    topic = Column(Text, nullable=False)
    rounds = Column(Integer, nullable=False)
    exchanges = Column(JSON, nullable=False)  # List of debate exchanges
    summary = Column(Text, nullable=True)
    winner = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        Index('idx_debates_topic', 'topic'),
    )
    
    def to_dict(self):
        """Convert to dictionary for API responses."""
        return {
            "id": self.id,
            "topic": self.topic,
            "rounds": self.rounds,
            "exchanges": self.exchanges,
            "summary": self.summary,
            "winner": self.winner,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }


# =============================================================================
# LLM USAGE TRACKING
# =============================================================================
class LLMUsage(Base):
    """
    Tracks LLM API usage for monitoring and cost analysis.
    """
    __tablename__ = "llm_usage"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    provider = Column(String(50), nullable=False)
    model = Column(String(100), nullable=True)
    prompt_tokens = Column(Integer, default=0)
    completion_tokens = Column(Integer, default=0)
    total_tokens = Column(Integer, default=0)
    success = Column(Integer, default=1)  # 1=success, 0=failure
    error_message = Column(Text, nullable=True)
    latency_ms = Column(Float, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    
    __table_args__ = (
        Index('idx_llm_usage_provider', 'provider'),
        Index('idx_llm_usage_created', 'created_at'),
    )
    
    def to_dict(self):
        """Convert to dictionary for API responses."""
        return {
            "id": self.id,
            "provider": self.provider,
            "model": self.model,
            "prompt_tokens": self.prompt_tokens,
            "completion_tokens": self.completion_tokens,
            "total_tokens": self.total_tokens,
            "success": bool(self.success),
            "error_message": self.error_message,
            "latency_ms": self.latency_ms,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }
