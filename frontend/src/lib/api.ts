/**
 * NYX API Client
 * 
 * React Query hooks for calling the FastAPI backend.
 * Handles all HTTP communication with proper error handling.
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';

const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000';

// =============================================================================
// TYPES
// =============================================================================

export interface SimulationRequest {
  agent_names: string[];
  rounds?: number;
  seed?: number;
}

export interface SimulationResult {
  simulation_id: string;
  state_history: Record<string, any>[];
  outcome_vector: {
    reputation_mean: number;
    inequality: number;
    trust_proxy: number;
    centralization: number;
  };
  agents: Array<{
    name: string;
    state: Record<string, any>;
    history_length: number;
  }>;
  influence_matrix: Record<string, Record<string, number>>;
  seed: number;
}

export interface ProviderHealth {
  name: string;
  configured: boolean;
  status: 'healthy' | 'degraded' | 'open' | 'half_open';
  success_rate: number;
  total_calls: number;
  weight: number;
  consecutive_failures: number;
}

export interface KeyStatusResponse {
  providers: ProviderHealth[];
  active_provider: string | null;
  rotation_strategy: string;
}

export interface GenerateRequest {
  prompt: string;
  system?: string;
  preferred_provider?: string;
}

export interface GenerateResponse {
  response: string;
  provider: string;
  timestamp: string;
}

// =============================================================================
// HELPER FUNCTIONS
// =============================================================================

async function fetchAPI<T>(endpoint: string, options?: RequestInit): Promise<T> {
  const response = await fetch(`${BACKEND_URL}${endpoint}`, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...options?.headers,
    },
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Unknown error' }));
    throw new Error(error.detail || `HTTP ${response.status}`);
  }

  return response.json();
}

// =============================================================================
// REACT QUERY HOOKS
// =============================================================================

/**
 * Health check - is the backend running?
 */
export function useHealthCheck() {
  return useQuery({
    queryKey: ['health'],
    queryFn: () => fetchAPI<{ status: string; timestamp: string }>('/health'),
    refetchInterval: 30000, // Check every 30 seconds
    retry: 2,
  });
}

/**
 * Key Status Dashboard - shows health of all API providers
 */
export function useKeyStatus() {
  return useQuery({
    queryKey: ['keyStatus'],
    queryFn: () => fetchAPI<KeyStatusResponse>('/api/keys/status'),
    refetchInterval: 10000, // Refresh every 10 seconds
  });
}

/**
 * Run a simulation
 */
export function useRunSimulation() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (request: SimulationRequest) =>
      fetchAPI<SimulationResult>('/api/simulate', {
        method: 'POST',
        body: JSON.stringify(request),
      }),
    onSuccess: () => {
      // Invalidate key status to update call counts
      queryClient.invalidateQueries({ queryKey: ['keyStatus'] });
    },
  });
}

/**
 * Get a specific simulation result by ID
 */
export function useSimulation(simulationId?: string) {
  return useQuery({
    queryKey: ['simulation', simulationId],
    queryFn: () => fetchAPI<SimulationResult>(`/api/simulate/${simulationId}`),
    enabled: !!simulationId,
  });
}

/**
 * Run Black Swan analysis
 */
export function useBlackSwanAnalysis() {
  return useMutation({
    mutationFn: (request: SimulationRequest) =>
      fetchAPI('/api/analyze/black-swan', {
        method: 'POST',
        body: JSON.stringify(request),
      }),
  });
}

/**
 * Run Counterfactual analysis
 */
export function useCounterfactual() {
  return useMutation({
    mutationFn: (request: SimulationRequest & { intervention?: string }) =>
      fetchAPI('/api/analyze/counterfactual', {
        method: 'POST',
        body: JSON.stringify(request),
      }),
  });
}

/**
 * Run Multi-Trial analysis
 */
export function useMultiTrial() {
  return useMutation({
    mutationFn: (request: SimulationRequest & { trials?: number }) =>
      fetchAPI('/api/analyze/multi-trial', {
        method: 'POST',
        body: JSON.stringify(request),
      }),
  });
}

/**
 * Generate text with LLM fallback
 */
export function useGenerate() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (request: GenerateRequest) =>
      fetchAPI<GenerateResponse>('/api/generate', {
        method: 'POST',
        body: JSON.stringify(request),
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['keyStatus'] });
    },
  });
}

/**
 * Reset a provider's circuit breaker
 */
export function useResetProvider() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (providerName: string) =>
      fetchAPI(`/api/keys/reset/${providerName}`, {
        method: 'POST',
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['keyStatus'] });
    },
  });
}

/**
 * Hot-reload configuration
 */
export function useReloadConfig() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: () => fetchAPI('/api/config/reload', { method: 'POST' }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['keyStatus'] });
    },
  });
}

/**
 * WebSocket hook for real-time simulation streaming
 */
export function useSimulationWebSocket(simulationId: string | null) {
  const [messages, setMessages] = useState<any[]>([]);
  const [isConnected, setIsConnected] = useState(false);

  useEffect(() => {
    if (!simulationId) return;

    const ws = new WebSocket(`ws://${BACKEND_URL.replace('http://', '')}/ws/simulation/${simulationId}`);

    ws.onopen = () => {
      setIsConnected(true);
      console.log('WebSocket connected');
    };

    ws.onmessage = (event) => {
      const message = JSON.parse(event.data);
      setMessages((prev) => [...prev, message]);
    };

    ws.onclose = () => {
      setIsConnected(false);
      console.log('WebSocket disconnected');
    };

    ws.onerror = (error) => {
      console.error('WebSocket error:', error);
    };

    // Send heartbeat every 30 seconds
    const heartbeat = setInterval(() => {
      if (ws.readyState === WebSocket.OPEN) {
        ws.send(JSON.stringify({ type: 'ping' }));
      }
    }, 30000);

    return () => {
      clearInterval(heartbeat);
      ws.close();
    };
  }, [simulationId]);

  return { messages, isConnected };
}
