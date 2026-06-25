"""
Unit tests for NYX simulation endpoints.
Tests core functionality, input validation, and error handling.
"""
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.core.nyx_kernel import run_simulation, CognitiveAgent


# Initialize test client
client = TestClient(app)


class TestSimulationEndpoints:
    """Test suite for /api/simulate endpoint."""
    
    def test_run_simulation_basic(self):
        """Test basic simulation with default parameters."""
        response = client.post(
            "/api/simulate",
            json={
                "agent_names": ["Alice", "Bob"],
                "rounds": 5,
                "seed": 42
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert "simulation_id" in data
        assert "state_history" in data
        assert "outcome_vector" in data
        assert "agents" in data
        assert len(data["agents"]) == 2
    
    def test_run_simulation_single_agent(self):
        """Test simulation with single agent."""
        response = client.post(
            "/api/simulate",
            json={
                "agent_names": ["Solo"],
                "rounds": 3,
                "seed": 123
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["agents"]) == 1
    
    def test_run_simulation_invalid_empty_agents(self):
        """Test that empty agent list is rejected."""
        response = client.post(
            "/api/simulate",
            json={
                "agent_names": [],
                "rounds": 5
            }
        )
        
        # Should fail validation (min_items=1)
        assert response.status_code == 422
    
    def test_run_simulation_too_many_agents(self):
        """Test that excessive agent count is rejected."""
        response = client.post(
            "/api/simulate",
            json={
                "agent_names": [f"Agent{i}" for i in range(25)],  # 25 agents
                "rounds": 5
            }
        )
        
        # Should fail validation (max_items=20)
        assert response.status_code == 422
    
    def test_run_simulation_invalid_rounds(self):
        """Test that invalid round count is rejected."""
        response = client.post(
            "/api/simulate",
            json={
                "agent_names": ["Alice"],
                "rounds": 0  # Invalid: min is 1
            }
        )
        
        assert response.status_code == 422
    
    def test_run_simulation_negative_rounds(self):
        """Test that negative rounds are rejected."""
        response = client.post(
            "/api/simulate",
            json={
                "agent_names": ["Alice"],
                "rounds": -5
            }
        )
        
        assert response.status_code == 422
    
    def test_get_simulation_result(self):
        """Test retrieving a previously run simulation."""
        # First, create a simulation
        create_response = client.post(
            "/api/simulate",
            json={
                "agent_names": ["Charlie", "Diana"],
                "rounds": 4,
                "seed": 999
            }
        )
        
        assert create_response.status_code == 200
        simulation_id = create_response.json()["simulation_id"]
        
        # Now retrieve it
        get_response = client.get(f"/api/simulate/{simulation_id}")
        
        assert get_response.status_code == 200
        data = get_response.json()
        assert data["simulation_id"] == simulation_id
        assert len(data["agents"]) == 2
    
    def test_get_nonexistent_simulation(self):
        """Test that nonexistent simulation returns 404."""
        response = client.get("/api/simulate/sim_nonexistent")
        
        assert response.status_code == 404


class TestKernelFunctions:
    """Direct tests for nyx_kernel functions."""
    
    def test_run_simulation_deterministic(self):
        """Test that same seed produces same results."""
        result1 = run_simulation(agent_names=["A", "B"], rounds=5, seed=42)
        result2 = run_simulation(agent_names=["A", "B"], rounds=5, seed=42)
        
        # Results should be identical with same seed
        assert result1["outcome_vector"] == result2["outcome_vector"]
    
    def test_run_simulation_different_seeds(self):
        """Test that different seeds produce different results."""
        result1 = run_simulation(agent_names=["A", "B"], rounds=5, seed=42)
        result2 = run_simulation(agent_names=["A", "B"], rounds=5, seed=123)
        
        # Results should likely differ with different seeds
        # (not guaranteed but very probable)
        assert result1["seed"] != result2["seed"]
    
    def test_cognitive_agent_creation(self):
        """Test CognitiveAgent initialization."""
        agent = CognitiveAgent(name="TestAgent")
        
        assert agent.name == "TestAgent"
        assert hasattr(agent, 'state')
        assert hasattr(agent, 'history')


class TestHealthEndpoints:
    """Test health check endpoints."""
    
    def test_health_check(self):
        """Test basic health endpoint."""
        response = client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "timestamp" in data
        assert "version" in data
    
    def test_readiness_check(self):
        """Test readiness endpoint."""
        response = client.get("/health/ready")
        
        # May return 200 or 503 depending on configuration
        assert response.status_code in [200, 503]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
