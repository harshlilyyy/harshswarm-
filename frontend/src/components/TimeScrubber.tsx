'use client';

import React, { useState, useRef, useEffect } from 'react';
import { Play, Pause, Rewind, FastForward } from 'lucide-react';

// =============================================================================
// TYPES
// =============================================================================

interface SimulationTick {
  tick: number;
  agent: string;
  provider: string;
  response?: string;
  latency?: number;
  state?: any;
}

interface TimeScrubberProps {
  ticks: SimulationTick[];
  isPlaying: boolean;
  onPlayPause: () => void;
}

// =============================================================================
// TIME SCRUBBER COMPONENT (Feature #6: The Time Machine)
// =============================================================================

/**
 * Feature #6: Deterministic Replay via Time Scrubber
 * 
 * This component provides a scrubber bar to navigate through simulation history.
 * Users can drag backwards and forwards in time to watch exactly how events occurred.
 * 
 * Key capabilities:
 * - Play/Pause simulation replay
 * - Jump to specific tick
 * - Visual progress indicator
 * - Current tick preview
 */
export default function TimeScrubber({ ticks, isPlaying, onPlayPause }: TimeScrubberProps) {
  const [currentTickIndex, setCurrentTickIndex] = useState(ticks.length - 1);
  const scrubberRef = useRef<HTMLDivElement>(null);
  const isDragging = useRef(false);

  // Update current tick when new ticks arrive
  useEffect(() => {
    if (isPlaying && ticks.length > 0) {
      setCurrentTickIndex(ticks.length - 1);
    }
  }, [ticks, isPlaying]);

  // Auto-play functionality
  useEffect(() => {
    if (!isPlaying || ticks.length === 0) return;

    const interval = setInterval(() => {
      setCurrentTickIndex(prev => {
        if (prev >= ticks.length - 1) {
          return ticks.length - 1; // Stop at end
        }
        return prev + 1;
      });
    }, 200); // 5 ticks per second playback speed

    return () => clearInterval(interval);
  }, [isPlaying, ticks.length]);

  const handleScrubberClick = (e: React.MouseEvent<HTMLDivElement>) => {
    if (!scrubberRef.current || ticks.length === 0) return;

    const rect = scrubberRef.current.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const width = rect.width;
    const percentage = Math.max(0, Math.min(1, x / width));
    const newIndex = Math.floor(percentage * (ticks.length - 1));
    
    setCurrentTickIndex(newIndex);
    setIsPlayingLocal(false);
  };

  const handleJumpToStart = () => {
    setCurrentTickIndex(0);
  };

  const handleJumpToEnd = () => {
    setCurrentTickIndex(ticks.length - 1);
  };

  const handleStepBack = () => {
    setCurrentTickIndex(prev => Math.max(0, prev - 1));
  };

  const handleStepForward = () => {
    setCurrentTickIndex(prev => Math.min(ticks.length - 1, prev + 1));
  };

  const setIsPlayingLocal = (playing: boolean) => {
    if (playing !== isPlaying) {
      onPlayPause();
    }
  };

  const currentTick = ticks[currentTickIndex];
  const progress = ticks.length > 0 ? ((currentTickIndex + 1) / ticks.length) * 100 : 0;

  return (
    <div className="bg-slate-900/50 backdrop-blur border border-slate-800 rounded-xl p-4">
      {/* Header with controls */}
      <div className="flex items-center justify-between mb-3">
        <h2 className="text-lg font-semibold flex items-center gap-2">
          <span className="text-indigo-400">⏱️</span>
          Time Machine
        </h2>
        
        <div className="flex items-center gap-2">
          <button
            onClick={handleJumpToStart}
            className="p-2 hover:bg-slate-800 rounded-lg transition-colors"
            title="Jump to start"
          >
            <Rewind className="w-4 h-4 text-slate-400" />
          </button>
          
          <button
            onClick={handleStepBack}
            className="p-2 hover:bg-slate-800 rounded-lg transition-colors"
            title="Previous tick"
          >
            <span className="text-slate-400 font-bold">◀</span>
          </button>
          
          <button
            onClick={() => setIsPlayingLocal(!isPlaying)}
            className="p-2 bg-indigo-600 hover:bg-indigo-700 rounded-lg transition-colors"
            title={isPlaying ? 'Pause' : 'Play'}
          >
            {isPlaying ? (
              <Pause className="w-4 h-4 text-white" />
            ) : (
              <Play className="w-4 h-4 text-white" />
            )}
          </button>
          
          <button
            onClick={handleStepForward}
            className="p-2 hover:bg-slate-800 rounded-lg transition-colors"
            title="Next tick"
          >
            <span className="text-slate-400 font-bold">▶</span>
          </button>
          
          <button
            onClick={handleJumpToEnd}
            className="p-2 hover:bg-slate-800 rounded-lg transition-colors"
            title="Jump to end"
          >
            <FastForward className="w-4 h-4 text-slate-400" />
          </button>
        </div>
      </div>

      {/* Progress info */}
      <div className="flex items-center justify-between mb-2 text-sm">
        <span className="text-slate-400">
          Tick {currentTickIndex + 1} of {ticks.length}
        </span>
        <span className="text-slate-400">
          {(progress).toFixed(1)}% complete
        </span>
      </div>

      {/* Scrubber bar */}
      <div
        ref={scrubberRef}
        onClick={handleScrubberClick}
        className="relative h-12 bg-slate-800 rounded-lg cursor-pointer overflow-hidden group"
      >
        {/* Background track */}
        <div className="absolute inset-0 bg-slate-800" />
        
        {/* Progress fill */}
        <div
          className="absolute top-0 left-0 h-full bg-gradient-to-r from-indigo-600 to-purple-600 transition-all duration-100"
          style={{ width: `${progress}%` }}
        />
        
        {/* Tick markers */}
        <div className="absolute inset-0 flex items-center justify-between px-2">
          {ticks.map((_, idx) => {
            const isCurrent = idx === currentTickIndex;
            const isMajor = idx % 5 === 0;
            
            return (
              <div
                key={idx}
                className={`
                  relative z-10 w-0.5 rounded-full transition-all
                  ${isMajor ? 'h-6 bg-slate-500' : 'h-3 bg-slate-600'}
                  ${isCurrent ? 'h-full bg-white shadow-lg shadow-white/50' : ''}
                  group-hover:h-4
                `}
              />
            );
          })}
        </div>
        
        {/* Hover indicator */}
        <div className="absolute inset-0 opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none">
          <div className="absolute top-1 right-2 text-xs text-white/70">
            Click to scrub
          </div>
        </div>
      </div>

      {/* Current tick preview */}
      {currentTick && (
        <div className="mt-3 p-3 bg-slate-800/50 rounded-lg border border-slate-700">
          <div className="flex items-center justify-between text-xs mb-2">
            <span className="text-indigo-400 font-medium">{currentTick.agent}</span>
            <span className="text-emerald-400">{currentTick.provider}</span>
            <span className="text-slate-500">Tick {currentTick.tick}</span>
          </div>
          
          {currentTick.response && (
            <div className="text-xs text-slate-300 line-clamp-2">
              {currentTick.response}
            </div>
          )}
          
          {currentTick.latency && (
            <div className="mt-1 text-xs text-slate-500">
              Latency: {currentTick.latency.toFixed(0)}ms
            </div>
          )}
        </div>
      )}

      {/* Playback speed hint */}
      <div className="mt-2 text-center text-xs text-slate-500">
        {isPlaying ? 'Playing at 5 ticks/sec' : 'Paused - Use controls to navigate'}
      </div>
    </div>
  );
}
