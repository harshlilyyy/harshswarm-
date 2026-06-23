'use client';

import { useState } from 'react';
import { Activity, Zap, Database, RefreshCw, CheckCircle, AlertTriangle, XCircle } from 'lucide-react';
import {
  useHealthCheck,
  useKeyStatus,
  useRunSimulation,
  useGenerate,
  useResetProvider,
  useReloadConfig,
} from '@/lib/api';

export default function Home() {
  const [agentInput, setAgentInput] = useState('Harsh, Jayant, Ahany, Priya, Rohan');
  const [rounds, setRounds] = useState(8);
  const [seed, setSeed] = useState(42);
  
  const health = useHealthCheck();
  const keyStatus = useKeyStatus();
  const runSim = useRunSimulation();
  const generate = useGenerate();
  const resetProvider = useResetProvider();
  const reloadConfig = useReloadConfig();
  
  const [latestResult, setLatestResult] = useState<any>(null);
  const [prompt, setPrompt] = useState('');
  const [generatedResponse, setGeneratedResponse] = useState('');

  const handleRunSimulation = async () => {
    const agentNames = agentInput.split(',').map((n) => n.trim()).filter(Boolean);
    try {
      const result = await runSim.mutateAsync({ agent_names: agentNames, rounds, seed });
      setLatestResult(result);
    } catch (error) {
      console.error('Simulation failed:', error);
    }
  };

  const handleGenerate = async () => {
    if (!prompt.trim()) return;
    try {
      const result = await generate.mutateAsync({ prompt: prompt.trim(), system: 'You are a helpful AI assistant.' });
      setGeneratedResponse(result.response);
    } catch (error) {
      console.error('Generation failed:', error);
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'healthy': return <CheckCircle className="w-4 h-4 text-green-500" />;
      case 'degraded': return <AlertTriangle className="w-4 h-4 text-yellow-500" />;
      case 'open': return <XCircle className="w-4 h-4 text-red-500" />;
      default: return <Activity className="w-4 h-4 text-gray-400" />;
    }
  };

  return (
    <main className="min-h-screen p-8">
      <header className="mb-12 text-center">
        <h1 className="text-6xl font-serif italic gradient-text mb-2">Nyx</h1>
        <p className="text-lg opacity-70">Decision Intelligence Simulator v2.0</p>
        <div className="mt-4 flex items-center justify-center gap-2">
          {health.isLoading ? (
            <RefreshCw className="w-4 h-4 animate-spin" />
          ) : health.isSuccess ? (
            <><Zap className="w-4 h-4 text-green-500" /><span className="text-sm">Backend Connected</span></>
          ) : (
            <><AlertTriangle className="w-4 h-4 text-red-500" /><span className="text-sm">Backend Unavailable</span></>
          )}
        </div>
      </header>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8 max-w-7xl mx-auto">
        <div className="space-y-6">
          <div className="glass-card">
            <h2 className="text-xl font-semibold mb-4 flex items-center gap-2">
              <Activity className="w-5 h-5" />Simulation Configuration
            </h2>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium mb-2">Agent Names</label>
                <input type="text" value={agentInput} onChange={(e) => setAgentInput(e.target.value)}
                  className="input-glass w-full text-left" placeholder="Comma-separated names" />
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium mb-2">Rounds</label>
                  <input type="number" value={rounds} onChange={(e) => setRounds(Number(e.target.value))}
                    className="input-glass w-full" min={1} max={50} />
                </div>
                <div>
                  <label className="block text-sm font-medium mb-2">Seed</label>
                  <input type="number" value={seed} onChange={(e) => setSeed(Number(e.target.value))}
                    className="input-glass w-full" />
                </div>
              </div>
              <button onClick={handleRunSimulation} disabled={runSim.isPending}
                className="btn-primary w-full mt-4 disabled:opacity-50">
                {runSim.isPending ? 'Running...' : '🚀 Run Simulation'}
              </button>
            </div>
          </div>

          <div className="glass-card">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-xl font-semibold flex items-center gap-2">
                <Zap className="w-5 h-5" />API Key Health
              </h2>
              <button onClick={() => reloadConfig.mutate()} className="text-sm text-purple-600 hover:text-purple-800"
                disabled={reloadConfig.isPending}>
                {reloadConfig.isPending ? 'Reloading...' : '↻ Reload'}
              </button>
            </div>
            <div className="space-y-2 max-h-64 overflow-y-auto">
              {keyStatus.isLoading ? (
                <div className="text-center py-4"><RefreshCw className="w-6 h-6 animate-spin mx-auto" /></div>
              ) : keyStatus.data?.providers.map((provider) => (
                <div key={provider.name} className="flex items-center justify-between p-2 bg-white/30 rounded-lg">
                  <div className="flex items-center gap-2">
                    {getStatusIcon(provider.status)}
                    <span className="font-medium">{provider.name}</span>
                  </div>
                  <div className="text-right">
                    <div className="text-xs opacity-70">{(provider.success_rate * 100).toFixed(0)}% success</div>
                    {provider.status === 'open' && (
                      <button onClick={() => resetProvider.mutate(provider.name)} className="text-xs text-red-600 hover:underline">Reset</button>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>

        <div className="lg:col-span-2 space-y-6">
          {latestResult && (
            <div className="glass-card">
              <h2 className="text-xl font-semibold mb-4">📊 Outcome Vector</h2>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <div className="bg-white/40 rounded-xl p-4 text-center">
                  <div className="text-2xl font-bold text-purple-600">{latestResult.outcome_vector.reputation_mean.toFixed(3)}</div>
                  <div className="text-xs opacity-70 mt-1">Reputation Mean</div>
                </div>
                <div className="bg-white/40 rounded-xl p-4 text-center">
                  <div className="text-2xl font-bold text-pink-600">{latestResult.outcome_vector.inequality.toFixed(3)}</div>
                  <div className="text-xs opacity-70 mt-1">Inequality</div>
                </div>
                <div className="bg-white/40 rounded-xl p-4 text-center">
                  <div className="text-2xl font-bold text-blue-600">{latestResult.outcome_vector.trust_proxy.toFixed(3)}</div>
                  <div className="text-xs opacity-70 mt-1">Trust Proxy</div>
                </div>
                <div className="bg-white/40 rounded-xl p-4 text-center">
                  <div className="text-2xl font-bold text-green-600">{latestResult.outcome_vector.centralization.toFixed(3)}</div>
                  <div className="text-xs opacity-70 mt-1">Centralization</div>
                </div>
              </div>
              <div className="mt-6">
                <h3 className="font-medium mb-3">Agent Final States</h3>
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
                  {latestResult.agents.map((agent: any) => (
                    <div key={agent.name} className="bg-white/30 rounded-lg p-3">
                      <div className="font-semibold mb-2">{agent.name}</div>
                      <div className="text-xs space-y-1">
                        <div className="flex justify-between">
                          <span>Mode:</span>
                          <span className={`mode-badge mode-${agent.state.mode}`}>{agent.state.mode}</span>
                        </div>
                        <div className="flex justify-between"><span>Self Worth:</span><span>{agent.state.self_worth.toFixed(2)}</span></div>
                        <div className="flex justify-between"><span>Anxiety:</span><span>{agent.state.anxiety.toFixed(2)}</span></div>
                        <div className="flex justify-between"><span>Reputation:</span><span>{agent.state.reputation.toFixed(2)}</span></div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}

          <div className="glass-card">
            <h2 className="text-xl font-semibold mb-4 flex items-center gap-2">
              <Database className="w-5 h-5" />LLM Generator (with Fallback)
            </h2>
            <div className="space-y-4">
              <textarea value={prompt} onChange={(e) => setPrompt(e.target.value)}
                className="input-glass w-full text-left h-24 resize-none" placeholder="Enter your prompt here..." />
              <button onClick={handleGenerate} disabled={generate.isPending || !prompt.trim()}
                className="btn-primary w-full disabled:opacity-50">
                {generate.isPending ? 'Generating...' : '✨ Generate'}
              </button>
              {generatedResponse && (
                <div className="mt-4 p-4 bg-white/40 rounded-xl">
                  <div className="text-sm font-medium mb-2">Response:</div>
                  <div className="text-base leading-relaxed">{generatedResponse}</div>
                </div>
              )}
            </div>
          </div>

          <div className="glass-card">
            <h2 className="text-xl font-semibold mb-4 flex items-center gap-2">
              <Activity className="w-5 h-5" />Live Console
            </h2>
            <div className="bg-black/5 rounded-xl p-4 h-48 overflow-y-auto font-mono text-sm">
              <div className="opacity-50">System ready. Waiting for simulation events...</div>
            </div>
          </div>
        </div>
      </div>
    </main>
  );
}
