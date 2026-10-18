import React, { useEffect, useState } from 'react';
import {
  Brain,
  Search,
  Bot,
  ArrowUpRight,
} from 'lucide-react';
import { api } from '../../lib/api';
import { Memory } from '../../types';

interface MemoryLibraryProps {
  projectId: string;
  onSelectGraphNode?: (nodeId: string) => void;
}

export const MemoryLibrary: React.FC<MemoryLibraryProps> = ({
  projectId,
  onSelectGraphNode,
}) => {
  const [memories, setMemories] = useState<Memory[]>([]);
  const [loading, setLoading] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedType, setSelectedType] = useState<string>('all');

  const fetchMemories = async () => {
    if (!projectId) return;
    setLoading(true);
    try {
      const data = await api.listMemories(projectId, searchQuery.trim() || undefined);
      setMemories(data);
    } catch (err) {
      console.error('Failed to list memories:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchMemories();
  }, [projectId]);

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    fetchMemories();
  };

  // Cognitive memory types supported in SwarmMind & FalkorDB
  const coreTypes = ['all', 'procedural', 'semantic', 'episodic', 'rule', 'fact', 'hypothesis', 'observation', 'summary'];

  const getCountForType = (type: string) => {
    if (type === 'all') return memories.length;
    return memories.filter((m) => m.memory_type.toLowerCase() === type.toLowerCase()).length;
  };

  const filteredMemories = memories.filter((m) => {
    if (selectedType === 'all') return true;
    return m.memory_type.toLowerCase() === selectedType.toLowerCase();
  });

  const getTypeBadgeStyle = (type: string) => {
    switch (type.toLowerCase()) {
      case 'procedural':
        return 'bg-indigo-500/10 text-indigo-400 border-indigo-500/30';
      case 'semantic':
        return 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30';
      case 'episodic':
        return 'bg-purple-500/10 text-purple-400 border-purple-500/30';
      case 'fact':
        return 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30';
      case 'rule':
        return 'bg-cyan-500/10 text-cyan-400 border-cyan-500/30';
      case 'summary':
        return 'bg-fuchsia-500/10 text-fuchsia-400 border-fuchsia-500/30';
      case 'observation':
        return 'bg-blue-500/10 text-blue-400 border-blue-500/30';
      case 'hypothesis':
        return 'bg-amber-500/10 text-amber-400 border-amber-500/30';
      default:
        return 'bg-slate-500/10 text-slate-400 border-slate-500/30';
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-xl font-bold text-white flex items-center gap-2">
            <Brain className="w-6 h-6 text-indigo-400" />
            Shared Memory Knowledge Base
          </h2>
          <p className="text-xs text-slate-400 mt-1">
            Persisted multi-agent semantic graph memories with confidence scoring & provenance.
          </p>
        </div>

        {/* Search Bar */}
        <form onSubmit={handleSearchSubmit} className="relative w-full sm:w-80">
          <input
            type="text"
            placeholder="Search claims, facts, tags..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full pl-9 pr-4 py-2 bg-slate-900 border border-slate-800 rounded-xl text-xs text-slate-100 placeholder-slate-500 focus:border-indigo-500 outline-none transition"
          />
          <Search className="w-4 h-4 text-slate-500 absolute left-3 top-2.5" />
        </form>
      </div>

      {/* Filter Tabs */}
      <div className="flex flex-wrap items-center gap-1.5 border-b border-slate-800 pb-3">
        {coreTypes.map((t) => {
          const count = getCountForType(t);
          const isSelected = selectedType === t;
          return (
            <button
              key={t}
              onClick={() => setSelectedType(t)}
              className={`px-3 py-1.5 rounded-lg text-xs font-mono capitalize transition flex items-center gap-1.5 ${
                isSelected
                  ? 'bg-indigo-600 text-white font-medium shadow-md'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-slate-900'
              }`}
            >
              <span>{t}</span>
              <span
                className={`text-[10px] px-1.5 py-0.2 rounded-full ${
                  isSelected
                    ? 'bg-indigo-800 text-indigo-200'
                    : count > 0
                    ? 'bg-slate-800 text-indigo-400 font-semibold'
                    : 'text-slate-600'
                }`}
              >
                {count}
              </span>
            </button>
          );
        })}
        <span className="text-xs text-slate-500 font-mono ml-auto hidden sm:inline">
          {filteredMemories.length} shown
        </span>
      </div>

      {/* Memory Cards Grid */}
      {loading ? (
        <div className="p-16 text-center text-slate-500">Loading graph memories...</div>
      ) : filteredMemories.length === 0 ? (
        <div className="p-16 text-center rounded-2xl border border-dashed border-slate-800 bg-slate-900/30 space-y-2">
          <Brain className="w-8 h-8 text-slate-600 mx-auto" />
          <p className="text-sm text-slate-400">No memories match your query</p>
          <p className="text-xs text-slate-600">Try selecting another filter or searching for a different keyword.</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {filteredMemories.map((m) => {
            const confidencePct = Math.round(m.confidence * 100);
            return (
              <div
                key={m.id}
                className="p-5 rounded-2xl border border-slate-800 bg-slate-900/60 hover:border-slate-700 transition flex flex-col justify-between space-y-4 shadow-lg group"
              >
                <div className="space-y-3">
                  <div className="flex items-center justify-between">
                    <span
                      className={`px-2.5 py-0.5 rounded-full text-[10px] font-semibold border ${getTypeBadgeStyle(
                        m.memory_type
                      )}`}
                    >
                      {m.memory_type}
                    </span>

                    <div className="flex items-center space-x-1.5 text-[11px] font-mono text-slate-400">
                      <span>Confidence</span>
                      <span className="text-emerald-400 font-bold">{confidencePct}%</span>
                    </div>
                  </div>

                  <p className="text-xs text-slate-200 leading-relaxed font-sans">
                    {m.content}
                  </p>

                  {m.instruction && (
                    <div className="p-2.5 rounded-xl bg-indigo-950/40 border border-indigo-500/20 text-[11px] font-mono text-indigo-300">
                      <span className="font-bold uppercase tracking-wider text-[9px] text-indigo-400 block mb-0.5">
                        Reinforced Policy:
                      </span>
                      {m.instruction}
                    </div>
                  )}
                </div>

                <div className="space-y-3 pt-3 border-t border-slate-800/80">
                  {/* Tags */}
                  {m.tags && m.tags.length > 0 && (
                    <div className="flex flex-wrap gap-1">
                      {m.tags.map((tag) => (
                        <span
                          key={tag}
                          className="px-2 py-0.5 rounded text-[10px] font-mono bg-slate-950 text-slate-400 border border-slate-800"
                        >
                          #{tag}
                        </span>
                      ))}
                    </div>
                  )}

                  <div className="flex items-center justify-between text-[11px] text-slate-500">
                    <div className="flex items-center space-x-1.5">
                      <Bot className="w-3.5 h-3.5 text-indigo-400" />
                      <span className="capitalize">{m.agent_role || 'Agent'}</span>
                    </div>

                    {onSelectGraphNode && (
                      <button
                        onClick={() => onSelectGraphNode(m.id)}
                        className="text-indigo-400 hover:text-indigo-300 font-medium flex items-center gap-0.5 opacity-0 group-hover:opacity-100 transition"
                      >
                        Inspect
                        <ArrowUpRight className="w-3 h-3" />
                      </button>
                    )}
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
};
