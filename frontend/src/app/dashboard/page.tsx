'use client';

import React, { useState, useEffect } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Canvas } from '@react-three/fiber';
import { OrbitControls, Sphere, MeshDistortMaterial, Text } from '@react-three/drei';
import { Activity, Zap, Database, RefreshCw, Play, Pause, Rewind, FastForward, Box, Users, TrendingUp } from 'lucide-react';
import {
  useHealthCheck,
  useKeyStatus,
  useRunSimulation,
  useGenerate,
  useResetProvider,
  useReloadConfig,
  useSimulationWebSocket,
} from '@/lib/api';
import TimeScrubber from '@/components/TimeScrubber';

// =============================================================================
// TYPES
// =============================================================================

interface AgentState {
  name: string;
  mode: string;
  self_worth: number;
  anxiety: number;
  reputation: number;
}

interface SimulationTick {
  tick: number;
  agent: string;
  provider: string;
  response?: string;
  latency?: number;
  state?: AgentState;
}

// =============================================================================
// 3D AGENT AVATAR COMPONENT (Feature #5: The Holodeck)
// =============================================================================

function AgentAvatar({ agent, position, color }: { agent: string; position: [number, number, number]; color: string }) {
  return (
    <group position={position}>
      <Sphere args={[0.3, 32, 32]}>
        <MeshDistortMaterial
          color={color}
          attach="material"
          distort={0.4}
          speed={2}
          roughness={0.2}
          metalness={0.8}
        />
      </Sphere>
      <Text
        position={[0, -0.5, 0]}
        fontSize={0.15}
        color="white"
        anchorX="center"
        anchorY="middle"
      >
        {agent}
      </Text>
    </group>
  );
}

// =============================================================================
// AGENT TERRAIN COMPONENT
// =============================================================================

function AgentTerrain({ agents, ticks }: { agents: any[]; ticks: SimulationTick[] }) {
  // Color mapping based on provider (Feature #5: Colored halos)
  const providerColors: Record<string, string> = {
    Groq: '#22c55e',      // Green
    SambaNova: '#3b82f6', // Blue
    Cerebras: '#8b5cf6',  // Purple
    Google: '#f59e0b',    // Amber
    Mistral: '#ef4444',   // Red
    Cohere: '#06b6d4',    // Cyan
    OpenRouter: '#ec4899',// Pink
    HuggingFace: '#6366f1',// Indigo
  };

  // Get latest state for each agent
  const agentStates = new Map<string, AgentState>();
  if (agents && agents.length > 0) {
    agents.forEach((agent) => {
      agentStates.set(agent.name, agent.state);
    });
  }

  // Position agents in a circle
  const radius = 2;
  const positions = agentStates.size > 0
    ? Array.from(agentStates.entries()).map(([name], index) => {
        const angle = (index / agentStates.size) * Math.PI * 2;
        return [
          name,
          [Math.cos(angle) * radius, 0, Math.sin(angle) * radius] as [number, number, number]
        ];
      })
    : [];

  return (
    <>
      {positions.map(([name, pos]) => {
        const state = agentStates.get(name as string);
        // Determine color based on last used provider
        const lastTick = ticks.find(t => t.agent === name);
        const color = lastTick ? providerColors[lastTick.provider] || '#64748b' : '#64748b';
        
        return (
          <AgentAvatar
            key={name as string}
            agent={name as string}
            position={pos as [number, number, number]}
            color={color}
          />
        );
      })}
      
      {/* Central hub */}
      <Sphere args={[0.5, 32, 32]} position={[0, 0, 0]}>
        <MeshDistortMaterial
          color="#ffffff"
          attach="material"
          distort={0.2}
          speed={1}
          roughness={0.1}
          wireframe
        />
      </Sphere>
    </>
  );
}

// =============================================================================
// MAIN DASHBOARD PAGE
// =============================================================================

export default function DashboardPage() {
  const [agentInput, setAgentInput] = useState('Harsh, Jayant, Ahany, Priya, Rohan');
  const [rounds, setRounds] = useState(8);
  const [seed, setSeed] = useState(42);
  const [currentSimId, setCurrentSimId] = useState<string | null>(null);
  const [ticks, setTicks] = useState<SimulationTick[]>([]);
  const [isPlaying, setIsPlaying] = useState(true);
  
  const queryClient = useQueryClient();
  
  // Data fetching hooks
  const health = useHealthCheck();
  const keyStatus = useKeyStatus();
  const runSim = useRunSimulation();
  const generate = useGenerate();
  const resetProvider = useResetProvider();
  const reloadConfig = useReloadConfig();
  
  // WebSocket for real-time ticks
  const { messages, isConnected } = useSimulationWebSocket(currentSimId);
  
  // Update ticks from WebSocket messages
  useEffect(() => {
    if (messages && messages.length > 0) {
      const lastMsg = messages[messages.length - 1];
      if (lastMsg.type === 'tick' && lastMsg.data) {
        setTicks(prev => [...prev.slice(-99), lastMsg.data]);
      }
    }
  }, [messages]);
  
  const [latestResult, setLatestResult] = useState<any>(null);
  const [prompt, setPrompt] = useState('');
  const [generatedResponse, setGeneratedResponse] = useState('');

  const handleRunSimulation = async () => {
    const agentNames = agentInput.split(',').map((n) => n.trim()).filter(Boolean);
    try {
      const result = await runSim.mutateAsync({ agent_names: agentNames, rounds, seed });
      setLatestResult(result);
      setCurrentSimId(result.simulation_id);
      setTicks([]); // Reset ticks for new simulation
      setIsPlaying(true);
    } catch (error) {
      console.error('Simulation failed:', error);
    }
  };

  const handleGenerate = async () => {
    if (!prompt.trim()) return;
    try {
      const result = await generate.mutateAsync({ 
        prompt: prompt.trim(), 
        system: 'You are a helpful AI assistant.' 
      });
      setGeneratedResponse(result.response);
    } catch (error) {
      console.error('Generation failed:', error);
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'healthy': return <Activity className="w-4 h-4 text-green-500" />;
      case 'degraded': return <Activity className="w-4 h-4 text-yellow-500" />;
      case 'open': return <Activity className="w-4 h-4 text-red-500" />;
      default: return <Activity className="w-4 h-4 text-gray-400" />;
    }
  };

  // Calculate cost estimates (Feature #8: Cost Cockpit)
  const totalCalls = keyStatus.data?.providers.reduce((sum, p) => sum + p.total_calls, 0) || 0;
  const estimatedCost = totalCalls * 0.002; // Rough estimate: $0.002 per call

  return (
    <main className="min-h-screen bg-slate-950 text-slate-100 p-6">
      {/* Header */}
      <header className="mb-8 flex items-center justify-between">
        <div>
          <h1 className="text-4xl font-bold bg-gradient-to-r from-indigo-400 to-cyan-400 bg-clip-text text-transparent">
            NYX Phoenix Command
          </h1>
          <p className="text-slate-400 mt-1">Multi-Agent Simulation Engine v2.0</p>
        </div>
        
        <div className="flex items-center gap-4">
          {health.isLoading ? (
            <RefreshCw className="w-5 h-5 animate-spin text-indigo-400" />
          ) : health.isSuccess ? (
            <div className="flex items-center gap-2 px-3 py-1.5 bg-green-500/10 border border-green-500/30 rounded-full">
              <Zap className="w-4 h-4 text-green-500" />
              <span className="text-sm font-medium text-green-500">Backend Online</span>
            </div>
          ) : (
            <div className="flex items-center gap-2 px-3 py-1.5 bg-red-500/10 border border-red-500/30 rounded-full">
              <Activity className="w-4 h-4 text-red-500" />
              <span className="text-sm font-medium text-red-500">Offline</span>
            </div>
          )}
          
          {isConnected && (
            <div className="flex items-center gap-2 px-3 py-1.5 bg-blue-500/10 border border-blue-500/30 rounded-full">
              <div className="w-2 h-2 bg-blue-500 rounded-full animate-pulse" />
              <span className="text-sm font-medium text-blue-500">Live</span>
            </div>
          )}
        </div>
      </header>

      {/* Main Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        
        {/* Left Column: Controls (3 cols) */}
        <div className="lg:col-span-3 space-y-4">
          {/* Simulation Config */}
          <div className="bg-slate-900/50 backdrop-blur border border-slate-800 rounded-xl p-4">
            <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
              <Users className="w-5 h-5 text-indigo-400" />
              Configuration
            </h2>
            
            <div className="space-y-3">
              <div>
                <label className="block text-xs font-medium text-slate-400 mb-1">Agents</label>
                <input
                  type="text"
                  value={agentInput}
                  onChange={(e) => setAgentInput(e.target.value)}
                  className="w-full bg-slate-800/50 border border-slate-700 rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-indigo-500"
                  placeholder="Comma-separated names"
                />
              </div>
              
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-medium text-slate-400 mb-1">Rounds</label>
                  <input
                    type="number"
                    value={rounds}
                    onChange={(e) => setRounds(Number(e.target.value))}
                    className="w-full bg-slate-800/50 border border-slate-700 rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-indigo-500"
                    min={1}
                    max={50}
                  />
                </div>
                <div>
                  <label className="block text-xs font-medium text-slate-400 mb-1">Seed</label>
                  <input
                    type="number"
                    value={seed}
                    onChange={(e) => setSeed(Number(e.target.value))}
                    className="w-full bg-slate-800/50 border border-slate-700 rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-indigo-500"
                  />
                </div>
              </div>
              
              <button
                onClick={handleRunSimulation}
                disabled={runSim.isPending}
                className="w-full bg-indigo-600 hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed text-white font-medium py-2.5 rounded-lg transition-colors flex items-center justify-center gap-2"
              >
                {runSim.isPending ? (
                  <RefreshCw className="w-4 h-4 animate-spin" />
                ) : (
                  <Play className="w-4 h-4" />
                )}
                {runSim.isPending ? 'Running...' : 'Start Simulation'}
              </button>
            </div>
          </div>

          {/* Key Health Dashboard */}
          <div className="bg-slate-900/50 backdrop-blur border border-slate-800 rounded-xl p-4">
            <div className="flex items-center justify-between mb-3">
              <h2 className="text-lg font-semibold flex items-center gap-2">
                <Zap className="w-5 h-5 text-yellow-400" />
                API Keys
              </h2>
              <button
                onClick={() => reloadConfig.mutate()}
                disabled={reloadConfig.isPending}
                className="text-xs text-indigo-400 hover:text-indigo-300 disabled:opacity-50"
              >
                {reloadConfig.isPending ? '...' : '↻ Reload'}
              </button>
            </div>
            
            <div className="space-y-2 max-h-64 overflow-y-auto">
              {keyStatus.isLoading ? (
                <div className="text-center py-4">
                  <RefreshCw className="w-5 h-5 animate-spin mx-auto text-slate-500" />
                </div>
              ) : keyStatus.data?.providers.map((provider) => (
                <div
                  key={provider.name}
                  className="flex items-center justify-between p-2.5 bg-slate-800/50 rounded-lg border border-slate-700/50"
                >
                  <div className="flex items-center gap-2">
                    {getStatusIcon(provider.status)}
                    <span className="text-sm font-medium">{provider.name}</span>
                  </div>
                  <div className="text-right">
                    <div className="text-xs text-slate-400">
                      {(provider.success_rate * 100).toFixed(0)}% success
                    </div>
                    {provider.status === 'open' && (
                      <button
                        onClick={() => resetProvider.mutate(provider.name)}
                        className="text-xs text-red-400 hover:text-red-300 hover:underline"
                      >
                        Reset
                      </button>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Cost Cockpit (Feature #8) */}
          <div className="bg-slate-900/50 backdrop-blur border border-slate-800 rounded-xl p-4">
            <h2 className="text-lg font-semibold mb-3 flex items-center gap-2">
              <TrendingUp className="w-5 h-5 text-green-400" />
              Usage & Costs
            </h2>
            
            <div className="space-y-3">
              <div className="flex justify-between items-center">
                <span className="text-sm text-slate-400">Total Calls</span>
                <span className="text-sm font-semibold">{totalCalls}</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-sm text-slate-400">Est. Cost</span>
                <span className="text-sm font-semibold text-green-400">${estimatedCost.toFixed(4)}</span>
              </div>
              <div className="pt-2 border-t border-slate-700">
                <div className="text-xs text-slate-500">
                  Based on avg $0.002/call
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Center Column: Holodeck & Live Feed (6 cols) */}
        <div className="lg:col-span-6 space-y-4">
          {/* Feature #5: The Holodeck (3D Agent Terrain) */}
          <div className="bg-slate-900/50 backdrop-blur border border-slate-800 rounded-xl p-4 h-[400px]">
            <div className="flex items-center justify-between mb-3">
              <h2 className="text-lg font-semibold flex items-center gap-2">
                <Box className="w-5 h-5 text-purple-400" />
                Agent Terrain (Holodeck)
              </h2>
              <div className="text-xs text-slate-400">
                {latestResult?.agents?.length || 0} agents active
              </div>
            </div>
            
            <div className="h-[320px] rounded-lg overflow-hidden bg-slate-950/50">
              <Canvas camera={{ position: [0, 3, 5], fov: 60 }}>
                <ambientLight intensity={0.5} />
                <directionalLight position={[10, 10, 5]} intensity={1} />
                <pointLight position={[-10, -10, -5]} intensity={0.5} color="#6366f1" />
                
                <AgentTerrain 
                  agents={latestResult?.agents || []}
                  ticks={ticks}
                />
                
                <OrbitControls 
                  enableZoom={true}
                  enablePan={true}
                  autoRotate={true}
                  autoRotateSpeed={0.5}
                />
              </Canvas>
            </div>
            
            <div className="mt-2 flex items-center justify-center gap-4 text-xs text-slate-500">
              <div className="flex items-center gap-1">
                <div className="w-3 h-3 rounded-full bg-green-500" />
                <span>Groq</span>
              </div>
              <div className="flex items-center gap-1">
                <div className="w-3 h-3 rounded-full bg-blue-500" />
                <span>SambaNova</span>
              </div>
              <div className="flex items-center gap-1">
                <div className="w-3 h-3 rounded-full bg-purple-500" />
                <span>Cerebras</span>
              </div>
              <div className="flex items-center gap-1">
                <div className="w-3 h-3 rounded-full bg-amber-500" />
                <span>Google</span>
              </div>
            </div>
          </div>

          {/* Time Scrubber (Feature #6) */}
          {ticks.length > 0 && (
            <TimeScrubber
              ticks={ticks}
              isPlaying={isPlaying}
              onPlayPause={() => setIsPlaying(!isPlaying)}
            />
          )}

          {/* Live Console Feed */}
          <div className="bg-slate-900/50 backdrop-blur border border-slate-800 rounded-xl p-4">
            <div className="flex items-center justify-between mb-3">
              <h2 className="text-lg font-semibold flex items-center gap-2">
                <Database className="w-5 h-5 text-cyan-400" />
                Live Simulation Feed
              </h2>
              <span className="text-xs text-slate-400">
                {ticks.length} ticks recorded
              </span>
            </div>
            
            <div className="bg-black/50 rounded-lg p-3 h-[200px] overflow-y-auto font-mono text-xs space-y-1">
              {ticks.length === 0 ? (
                <div className="text-slate-500 text-center py-8">
                  Waiting for simulation to start...
                </div>
              ) : (
                ticks.slice(-20).reverse().map((tick, idx) => (
                  <div
                    key={idx}
                    className="flex items-center justify-between py-1.5 border-b border-slate-800/50 last:border-0"
                  >
                    <span className="text-slate-500">Tick {tick.tick}</span>
                    <span className="text-indigo-400 font-medium">{tick.agent}</span>
                    <span className="text-emerald-400 text-xs">{tick.provider}</span>
                    {tick.latency && (
                      <span className="text-slate-400 text-xs">{tick.latency.toFixed(0)}ms</span>
                    )}
                  </div>
                ))
              )}
            </div>
          </div>
        </div>

        {/* Right Column: Results & LLM (3 cols) */}
        <div className="lg:col-span-3 space-y-4">
          {/* Outcome Vector */}
          {latestResult && (
            <div className="bg-slate-900/50 backdrop-blur border border-slate-800 rounded-xl p-4">
              <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
                <Activity className="w-5 h-5 text-pink-400" />
                Outcome Vector
              </h2>
              
              <div className="space-y-3">
                <div className="bg-slate-800/50 rounded-lg p-3">
                  <div className="text-2xl font-bold text-purple-400">
                    {latestResult.outcome_vector.reputation_mean.toFixed(3)}
                  </div>
                  <div className="text-xs text-slate-400 mt-1">Reputation Mean</div>
                </div>
                
                <div className="bg-slate-800/50 rounded-lg p-3">
                  <div className="text-2xl font-bold text-pink-400">
                    {latestResult.outcome_vector.inequality.toFixed(3)}
                  </div>
                  <div className="text-xs text-slate-400 mt-1">Inequality</div>
                </div>
                
                <div className="bg-slate-800/50 rounded-lg p-3">
                  <div className="text-2xl font-bold text-blue-400">
                    {latestResult.outcome_vector.trust_proxy.toFixed(3)}
                  </div>
                  <div className="text-xs text-slate-400 mt-1">Trust Proxy</div>
                </div>
                
                <div className="bg-slate-800/50 rounded-lg p-3">
                  <div className="text-2xl font-bold text-green-400">
                    {latestResult.outcome_vector.centralization.toFixed(3)}
                  </div>
                  <div className="text-xs text-slate-400 mt-1">Centralization</div>
                </div>
              </div>
              
              {/* Agent States */}
              <div className="mt-4 pt-4 border-t border-slate-700">
                <h3 className="text-sm font-medium mb-2">Agent States</h3>
                <div className="space-y-2 max-h-48 overflow-y-auto">
                  {latestResult.agents.map((agent: any) => (
                    <div key={agent.name} className="bg-slate-800/30 rounded-lg p-2 text-xs">
                      <div className="font-medium text-slate-300 mb-1">{agent.name}</div>
                      <div className="grid grid-cols-2 gap-x-2 gap-y-1 text-slate-400">
                        <div>Mode: <span className={`mode-badge mode-${agent.state.mode}`}>{agent.state.mode}</span></div>
                        <div>Worth: {agent.state.self_worth.toFixed(2)}</div>
                        <div>Anxiety: {agent.state.anxiety.toFixed(2)}</div>
                        <div>Rep: {agent.state.reputation.toFixed(2)}</div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}

          {/* LLM Generator */}
          <div className="bg-slate-900/50 backdrop-blur border border-slate-800 rounded-xl p-4">
            <h2 className="text-lg font-semibold mb-3 flex items-center gap-2">
              <Zap className="w-5 h-5 text-amber-400" />
              Quick Generate
            </h2>
            
            <div className="space-y-3">
              <textarea
                value={prompt}
                onChange={(e) => setPrompt(e.target.value)}
                className="w-full bg-slate-800/50 border border-slate-700 rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-indigo-500 resize-none h-24"
                placeholder="Enter your prompt..."
              />
              
              <button
                onClick={handleGenerate}
                disabled={generate.isPending || !prompt.trim()}
                className="w-full bg-amber-600 hover:bg-amber-700 disabled:opacity-50 disabled:cursor-not-allowed text-white font-medium py-2.5 rounded-lg transition-colors"
              >
                {generate.isPending ? 'Generating...' : '✨ Generate'}
              </button>
              
              {generatedResponse && (
                <div className="bg-slate-800/50 rounded-lg p-3 text-sm leading-relaxed">
                  <div className="text-xs text-slate-400 mb-1">Response:</div>
                  {generatedResponse}
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </main>
  );
}
