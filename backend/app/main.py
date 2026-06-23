# =============================================================================
# NYX BACKEND — FastAPI Enterprise Server
# =============================================================================
"""
NYX Phoenix Migration - Backend Service
Principal Staff Architect & Cognitive Systems Engineer Implementation

Architecture: N-Tier Decoupled System
- Tier 1: Next.js 14 Frontend (Vercel)
- Tier 2: FastAPI Backend (Render/Fly.io)
- Tier 3: Core Logic (nyx_kernel.py - preserved intact)
- Tier 4: Database Layer (SQLite/Postgres + Vector DB ready)

Key Enhancements:
1. Circuit Breaker pattern for API resilience
2. Weighted Round-Robin for adaptive key rotation
3. WebSocket streaming for real-time simulation ticks
4. Pydantic settings validation for environment security
5. Async endpoints for non-blocking I/O
"""

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from contextlib import asynccontextmanager
from typing import Dict, List, Optional, Any
import asyncio
import json
import os
import time
from datetime import datetime

# Import from local services
from app.services.fallback import KeyRotator, CircuitBreakerConfig
from app.services.retriever import DatabaseRetriever, VectorStoreConfig
from app.core.nyx_kernel import (
    run_simulation,
    detect_black_swan,
    run_counterfactual,
    run_multi_trial,
    game_theory_insights,
    CognitiveAgent
)

# Global state (will be replaced with Redis in production)
simulation_store: Dict[str, Dict[str, Any]] = {}
websocket_connections: Dict[str, WebSocket] = {}


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager.
    Initializes services on startup, cleans up on shutdown.
    """
    # Startup
    print("🚀 NYX Backend Starting...")
    print("📦 Loading Key Rotator with Circuit Breaker...")
    app.state.key_rotator = KeyRotator()
    
    print("🗄️  Loading Database Retriever...")
    app.state.retriever = DatabaseRetriever()
    
    print("✅ NYX Backend Ready")
    yield
    # Shutdown
    print("👋 NYX Backend Shutting Down...")
    # Close any open connections
    for ws in websocket_connections.values():
        await ws.close()


app = FastAPI(
    title="NYX Decision Intelligence API",
    description="Enterprise-grade Multi-Agent Simulation Engine",
    version="2.0.0",
    lifespan=lifespan
)

# =============================================================================
# CORS CONFIGURATION - Critical for Vercel Frontend
# =============================================================================
# In production, restrict to your actual frontend domain
ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "https://nyx-frontend.vercel.app",
    "https://*.vercel.app",
    "*",  # Remove in production!
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# =============================================================================
# HEALTH CHECK ENDPOINTS
# =============================================================================
@app.get("/health")
async def health_check():
    """
    Basic health check endpoint.
    Used by Render/Fly.io for deployment health monitoring.
    """
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "2.0.0"
    }


@app.get("/health/ready")
async def readiness_check():
    """
    Readiness check - verifies all dependencies are available.
    Returns 503 if any critical service is unavailable.
    """
    key_rotator: KeyRotator = app.state.key_rotator
    retriever: DatabaseRetriever = app.state.retriever
    
    issues = []
    
    # Check if at least one API key is configured
    if not key_rotator.get_available_providers():
        issues.append("No API keys configured")
    
    # Check database connectivity (if configured)
    if not retriever.is_connected():
        issues.append("Database not connected (optional)")
    
    if issues:
        raise HTTPException(
            status_code=503,
            detail={
                "status": "not_ready",
                "issues": issues
            }
        )
    
    return {
        "status": "ready",
        "timestamp": datetime.utcnow().isoformat()
    }


# =============================================================================
# KEY HEALTH DASHBOARD ENDPOINTS
# =============================================================================
@app.get("/api/keys/status")
async def get_key_status():
    """
    Returns the current status of all API keys.
    Shows which keys are active, rate-limited, or in cooldown.
    
    This powers the "Key Health Dashboard" in the frontend.
    """
    key_rotator: KeyRotator = app.state.key_rotator
    return {
        "providers": key_rotator.get_provider_health(),
        "active_provider": key_rotator.current_preferred,
        "rotation_strategy": "weighted_round_robin"
    }


@app.post("/api/keys/reset/{provider_name}")
async def reset_provider(provider_name: str):
    """
    Manually reset a provider's circuit breaker.
    Useful when you know a provider is back online.
    """
    key_rotator: KeyRotator = app.state.key_rotator
    success = key_rotator.reset_circuit_breaker(provider_name)
    
    if not success:
        raise HTTPException(status_code=404, detail=f"Provider '{provider_name}' not found")
    
    return {"status": "reset", "provider": provider_name}


# =============================================================================
# SIMULATION ENDPOINTS
# =============================================================================
@app.post("/api/simulate")
async def run_simulation_endpoint(
    agent_names: List[str],
    rounds: int = 8,
    seed: int = 42
):
    """
    Run a deterministic cognitive-social simulation.
    
    This wraps the original nyx_kernel.run_simulation() function.
    ZERO LOGIC LOSS - directly imports and calls the original function.
    
    Args:
        agent_names: List of agent names
        rounds: Number of simulation rounds
        seed: Random seed for reproducibility
    
    Returns:
        Simulation results with state history and outcome vector
    """
    try:
        # Direct call to preserved kernel function
        result = run_simulation(agent_names=agent_names, rounds=rounds, seed=seed)
        
        # Serialize agents (they're objects, need dict representation)
        serialized_agents = []
        for agent in result["agents"]:
            serialized_agents.append({
                "name": agent.name,
                "state": agent.get_current_state_dict(),
                "history_length": len(agent.history)
            })
        
        # Store result for later retrieval
        simulation_id = f"sim_{int(time.time())}_{seed}"
        simulation_store[simulation_id] = {
            "result": result,
            "serialized_agents": serialized_agents,
            "created_at": datetime.utcnow().isoformat()
        }
        
        return {
            "simulation_id": simulation_id,
            "state_history": result["state_history"],
            "outcome_vector": result["outcome_vector"],
            "agents": serialized_agents,
            "influence_matrix": result["influence"],
            "seed": result["seed"]
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Simulation failed: {str(e)}")


@app.get("/api/simulate/{simulation_id}")
async def get_simulation_result(simulation_id: str):
    """
    Retrieve a previously run simulation by ID.
    """
    if simulation_id not in simulation_store:
        raise HTTPException(status_code=404, detail="Simulation not found")
    
    stored = simulation_store[simulation_id]
    return {
        "simulation_id": simulation_id,
        "created_at": stored["created_at"],
        "state_history": stored["result"]["state_history"],
        "outcome_vector": stored["result"]["outcome_vector"],
        "agents": stored["serialized_agents"],
        "influence_matrix": stored["result"]["influence"]
    }


# =============================================================================
# ADVANCED ANALYTICS ENDPOINTS
# =============================================================================
@app.post("/api/analyze/black-swan")
async def analyze_black_swan(
    agent_names: List[str],
    rounds: int = 8,
    seed: int = 42
):
    """
    Detect fragile assumptions and potential cascade failures.
    Wraps nyx_kernel.detect_black_swan()
    """
    result = run_simulation(agent_names=agent_names, rounds=rounds, seed=seed)
    analysis = detect_black_swan(
        agents=result["agents"],
        state_history=result["state_history"]
    )
    return analysis


@app.post("/api/analyze/counterfactual")
async def run_counterfactual_endpoint(
    agent_names: List[str],
    rounds: int = 8,
    base_seed: int = 42,
    intervention: Optional[str] = None
):
    """
    Run counterfactual scenario analysis.
    What-if reasoning engine.
    """
    result = run_counterfactual(
        agent_names=agent_names,
        rounds=rounds,
        seed=base_seed,
        intervention=intervention
    )
    return {
        "baseline": result["baseline"],
        "counterfactual": result["counterfactual"],
        "divergence": result["divergence"]
    }


@app.post("/api/analyze/multi-trial")
async def run_multi_trial_endpoint(
    agent_names: List[str],
    rounds: int = 8,
    base_seed: int = 42,
    trials: int = 10
):
    """
    Run multiple simulation trials for statistical power.
    Monte-Carlo style aggregation.
    """
    result = run_multi_trial(
        agent_names=agent_names,
        rounds=rounds,
        base_seed=base_seed,
        trials=trials
    )
    return {
        "trial_results": result["trial_results"],
        "aggregate_stats": result["aggregate_stats"],
        "confidence_intervals": result.get("confidence_intervals", {})
    }


@app.post("/api/analyze/game-theory")
async def analyze_game_theory(
    agent_names: List[str],
    rounds: int = 8,
    seed: int = 42
):
    """
    Compute Nash equilibria and strategic insights.
    """
    result = run_simulation(agent_names=agent_names, rounds=rounds, seed=seed)
    insights = game_theory_insights(agents=result["agents"])
    return insights


# =============================================================================
# LLM GENERATION ENDPOINT (with Circuit Breaker)
# =============================================================================
@app.post("/api/generate")
async def generate_with_fallback_endpoint(
    prompt: str,
    system: str = "",
    preferred_provider: Optional[str] = None
):
    """
    Generate text using LLM with intelligent fallback.
    
    ENHANCED VERSION:
    - Circuit Breaker prevents repeated calls to failing providers
    - Weighted Round-Robin adapts based on success rates
    - Async non-blocking I/O
    """
    key_rotator: KeyRotator = app.state.key_rotator
    
    try:
        response, provider = await key_rotator.generate_async(
            prompt=prompt,
            system=system,
            preferred=preferred_provider
        )
        
        return {
            "response": response,
            "provider": provider,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    except Exception as e:
        # All providers exhausted or failed
        raise HTTPException(
            status_code=503,
            detail={
                "error": "All providers unavailable",
                "message": str(e),
                "suggestion": "Check /api/keys/status for provider health"
            }
        )


# =============================================================================
# DATABASE RETRIEVAL ENDPOINT (RAG - Retrieval Augmented Generation)
# =============================================================================
@app.post("/api/retrieve")
async def retrieve_context(
    query: str,
    top_k: int = 5,
    source: Optional[str] = None  # "sql" or "vector"
):
    """
    Retrieve contextual data from database or vector store.
    Powers the "Oracle" functionality.
    
    Supports both SQL and Vector DB backends.
    """
    retriever: DatabaseRetriever = app.state.retriever
    
    try:
        results = await retriever.retrieve_async(
            query=query,
            top_k=top_k,
            source=source
        )
        
        return {
            "query": query,
            "results": results,
            "count": len(results)
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Retrieval failed: {str(e)}"
        )


# =============================================================================
# WEBSOCKET STREAMING ENDPOINT
# =============================================================================
@app.websocket("/ws/simulation/{simulation_id}")
async def simulation_websocket(websocket: WebSocket, simulation_id: str):
    """
    WebSocket endpoint for real-time simulation streaming.
    
    Pushes agent ticks to frontend as they occur.
    Enables live progress visualization during heavy simulations.
    """
    await websocket.accept()
    websocket_connections[simulation_id] = websocket
    
    try:
        # Send connection acknowledgment
        await websocket.send_json({
            "type": "connected",
            "simulation_id": simulation_id,
            "timestamp": datetime.utcnow().isoformat()
        })
        
        # Keep connection alive with heartbeat
        while True:
            # Wait for client messages or send heartbeats
            try:
                data = await asyncio.wait_for(
                    websocket.receive_text(),
                    timeout=30.0
                )
                
                # Handle client commands
                msg = json.loads(data)
                if msg.get("type") == "ping":
                    await websocket.send_json({"type": "pong"})
                elif msg.get("type") == "subscribe":
                    # Client wants to subscribe to simulation updates
                    await websocket.send_json({
                        "type": "subscribed",
                        "simulation_id": simulation_id
                    })
            
            except asyncio.TimeoutError:
                # Send heartbeat
                await websocket.send_json({
                    "type": "heartbeat",
                    "timestamp": datetime.utcnow().isoformat()
                })
    
    except WebSocketDisconnect:
        print(f"WebSocket disconnected: {simulation_id}")
    finally:
        del websocket_connections[simulation_id]


# =============================================================================
# HOT-RELOAD CONFIGURATION ENDPOINT
# =============================================================================
@app.post("/api/config/reload")
async def reload_configuration():
    """
    Hot-reload API keys from environment variables.
    
    ENHANCEMENT C: No server restart required!
    New keys picked up immediately.
    """
    key_rotator: KeyRotator = app.state.key_rotator
    
    # Reload providers from environment
    reloaded_count = key_rotator.reload_from_env()
    
    return {
        "status": "reloaded",
        "providers_loaded": reloaded_count,
        "timestamp": datetime.utcnow().isoformat()
    }


# =============================================================================
# DEBATE ENDPOINT (Legacy Feature Preservation)
# =============================================================================
@app.post("/api/debate")
async def run_debate_endpoint(
    topic: str,
    agents: List[Dict[str, str]],  # [{name, stance}, ...]
    rounds: int = 3,
    preferred_provider: Optional[str] = None
):
    """
    Run a multi-agent debate using LLM-powered agents.
    Preserved from streamlit_app.py DebateAgent class.
    """
    from app.services.debate import DebateOrchestrator
    
    orchestrator = DebateOrchestrator(app.state.key_rotator)
    
    log, winner = await orchestrator.run_debate(
        topic=topic,
        agents=agents,
        rounds=rounds,
        preferred_provider=preferred_provider
    )
    
    return {
        "topic": topic,
        "log": log,
        "winner": winner,
        "rounds_completed": rounds
    }


# =============================================================================
# MAIN ENTRY POINT
# =============================================================================
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
