import { useEffect, useState } from 'react';
import {
  BrainCircuit,
  Database,
  Network,
  RefreshCw,
  Sparkles,
  Layers,
  FileText,
  Brain,
  CheckCircle2,
  Trash2,
} from 'lucide-react';
import { api } from './lib/api';
import { HealthResponse, Project } from './types';
import { WorkspaceView } from './components/workspace/WorkspaceView';
import { GraphExplorer } from './components/graph/GraphExplorer';
import { MemoryLibrary } from './components/memory/MemoryLibrary';
import { ReportView } from './components/reports/ReportView';

export default function App() {
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [projects, setProjects] = useState<Project[]>([]);
  const [activeProject, setActiveProject] = useState<Project | null>(null);
  const [activeTab, setActiveTab] = useState<'workspace' | 'graph' | 'memory' | 'report'>('workspace');
  const [loading, setLoading] = useState(true);
  const [seeding, setSeeding] = useState(false);
  const [toastMessage, setToastMessage] = useState<string | null>(null);

  const showToast = (msg: string) => {
    setToastMessage(msg);
    setTimeout(() => setToastMessage(null), 4000);
  };

  const fetchData = async () => {
    setLoading(true);
    try {
      const [healthData, projectsData] = await Promise.all([
        api.getHealth().catch(() => null),
        api.listProjects().catch(() => []),
      ]);
      setHealth(healthData);
      setProjects(projectsData);

      if (projectsData.length > 0 && !activeProject) {
        const demoProj = projectsData.find((p) => p.id === 'proj-apexai-audit') || projectsData.find((p) => p.id === 'proj-ai-tutoring') || projectsData[0];
        setActiveProject(demoProj);
      }
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const handleSeedScenario = async (scenario: string = 'all') => {
    setSeeding(true);
    try {
      await api.seedDemo(scenario);
      if (scenario === 'incident') {
        showToast('Loaded Production Incident & Architecture Investigation (2 sequential runs, contradiction, turns & procedural rules)!');
      } else if (scenario === 'venture_audit' || scenario === 'ai_tutoring') {
        showToast('Loaded ApexAI Acquisition Due Diligence graph (6 agents, 6 tasks, 4 sources, 4 claims, and GPL/uptime contradictions)!');
      } else {
        showToast('Loaded hackathon demo scenarios into isolated FalkorDB tenant graphs!');
      }
      await fetchData();
    } catch (err: any) {
      alert(`Seeding failed: ${err.message}`);
    } finally {
      setSeeding(false);
    }
  };

  const handleClearData = async () => {
    if (!window.confirm('Clear all workspace graphs and start completely fresh?')) return;
    setLoading(true);
    try {
      await api.clearDemo();
      setProjects([]);
      setActiveProject(null);
      showToast('All workspace data and graphs have been reset.');
      await fetchData();
    } catch (err: any) {
      alert(`Clear failed: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col font-sans">
      {/* Toast Notification */}
      {toastMessage && (
        <div className="fixed top-5 right-5 z-50 bg-indigo-600 text-white px-4 py-2.5 rounded-xl shadow-2xl border border-indigo-400 text-xs flex items-center gap-2 animate-in slide-in-from-top duration-200">
          <CheckCircle2 className="w-4 h-4 text-emerald-300" />
          <span>{toastMessage}</span>
        </div>
      )}

      {/* Global Header */}
      <header className="border-b border-slate-800/80 bg-slate-900/60 backdrop-blur sticky top-0 z-50 px-6 py-3.5">
        <div className="max-w-7xl mx-auto flex items-center justify-between gap-4">
          <div className="flex items-center space-x-3">
            <div className="p-2 rounded-xl bg-gradient-to-tr from-indigo-600 to-violet-500 shadow-lg shadow-indigo-500/25">
              <BrainCircuit className="w-6 h-6 text-white" />
            </div>
            <div>
              <div className="flex items-center space-x-2">
                <span className="font-bold text-xl tracking-tight bg-gradient-to-r from-white via-slate-200 to-indigo-300 bg-clip-text text-transparent">
                  SwarmMind
                </span>
                <span className="text-xs px-2 py-0.5 rounded-full font-mono bg-indigo-500/10 border border-indigo-500/30 text-indigo-400">
                  FalkorDB Hackathon
                </span>
              </div>
              <p className="text-[11px] text-slate-400">Auditable Graph-Grounded Multi-Agent Collaboration</p>
            </div>
          </div>

          {/* Project Selector & Actions */}
          <div className="flex items-center space-x-3">
            {projects.length > 0 && (
              <div className="flex items-center space-x-2 bg-slate-900/90 px-3 py-1.5 rounded-xl border border-indigo-500/30 text-xs shadow-inner">
                <Layers className="w-3.5 h-3.5 text-indigo-400" />
                <div className="flex flex-col">
                  <div className="flex items-center gap-1.5">
                    <span className="text-[10px] uppercase font-bold text-indigo-300 tracking-wider">Tenant / Workspace Graph:</span>
                    <span className="text-[10px] font-mono text-emerald-400 bg-emerald-950/60 px-1.5 py-0.2 rounded border border-emerald-800/80">
                      swarmmind:{activeProject?.id || 'default'}
                    </span>
                  </div>
                  <select
                    value={activeProject?.id || ''}
                    onChange={(e) => {
                      const found = projects.find((p) => p.id === e.target.value);
                      if (found) setActiveProject(found);
                    }}
                    className="bg-transparent text-slate-200 font-medium outline-none cursor-pointer text-xs"
                  >
                    {projects.map((p) => (
                      <option key={p.id} value={p.id} className="bg-slate-900 text-slate-200">
                        {p.name}
                      </option>
                    ))}
                  </select>
                </div>
              </div>
            )}

            {/* Scenario Quick-Seed Dropdown */}
            <div className="flex items-center space-x-1.5 bg-slate-900/90 px-3 py-1.5 rounded-xl border border-indigo-500/30 hover:border-indigo-500/60 transition">
              <Sparkles className={`w-3.5 h-3.5 text-indigo-400 ${seeding ? 'animate-spin' : ''}`} />
              <select
                disabled={seeding}
                onChange={(e) => {
                  if (e.target.value === '__CLEAR__') {
                    handleClearData();
                  } else if (e.target.value) {
                    handleSeedScenario(e.target.value);
                  }
                  e.target.value = '';
                }}
                defaultValue=""
                className="bg-transparent text-indigo-300 font-medium text-xs outline-none cursor-pointer"
                title="Select a hackathon demo scenario to seed"
              >
                <option value="" disabled className="bg-slate-900 text-slate-400">
                  {seeding ? 'Seeding demo...' : '⚡ Seed Demo Scenario...'}
                </option>
                <option value="incident" className="bg-slate-900 text-slate-200">
                  ⚡ Outage & Remediation (2 Runs, Procedural Penalty, Turns)
                </option>
                <option value="ai_tutoring" className="bg-slate-900 text-slate-200">
                  💼 ApexAI M&A Due Diligence ($45M Escrow, Contradiction, PageRank)
                </option>
                <option value="all" className="bg-slate-900 text-slate-200">
                  ✨ Seed Both Scenarios
                </option>
                <option value="__CLEAR__" className="bg-slate-900 text-rose-400 font-medium">
                  🗑️ Clear / Reset All Workspaces
                </option>
              </select>
            </div>

            <div className="flex items-center space-x-2 px-3 py-1.5 rounded-xl border border-slate-800 bg-slate-900 text-xs">
              <Database className="w-3.5 h-3.5 text-indigo-400" />
              <span className="text-slate-400">Backend:</span>
              <span className="font-mono font-medium text-emerald-400 uppercase">
                {health?.graph_backend || 'local'}
              </span>
              <span className={`w-2 h-2 rounded-full ${health ? 'bg-emerald-500' : 'bg-amber-500 animate-pulse'}`} />
            </div>

            <button
              onClick={handleClearData}
              disabled={loading}
              className="p-2 rounded-xl border border-slate-800 hover:border-rose-500/50 bg-slate-900 hover:bg-rose-950/30 text-slate-400 hover:text-rose-300 transition"
              title="Clear all workspace data and reset graphs"
            >
              <Trash2 className="w-4 h-4" />
            </button>

            <button
              onClick={fetchData}
              disabled={loading}
              className="p-2 rounded-xl border border-slate-800 hover:border-slate-700 bg-slate-900 hover:bg-slate-800 text-slate-300 transition"
              title="Refresh status"
            >
              <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin text-indigo-400' : ''}`} />
            </button>
          </div>
        </div>
      </header>

      {/* Main Tab Navigation */}
      <div className="border-b border-slate-800 bg-slate-900/40 px-6">
        <div className="max-w-7xl mx-auto flex items-center space-x-6 text-xs font-medium">
          <button
            onClick={() => setActiveTab('workspace')}
            className={`py-3.5 border-b-2 flex items-center space-x-2 transition ${
              activeTab === 'workspace'
                ? 'border-indigo-500 text-indigo-400 font-semibold'
                : 'border-transparent text-slate-400 hover:text-slate-200'
            }`}
          >
            <Layers className="w-4 h-4" />
            <span>Swarm Workspace</span>
          </button>

          <button
            onClick={() => setActiveTab('graph')}
            className={`py-3.5 border-b-2 flex items-center space-x-2 transition ${
              activeTab === 'graph'
                ? 'border-indigo-500 text-indigo-400 font-semibold'
                : 'border-transparent text-slate-400 hover:text-slate-200'
            }`}
          >
            <Network className="w-4 h-4" />
            <span>Graph Explorer</span>
          </button>

          <button
            onClick={() => setActiveTab('memory')}
            className={`py-3.5 border-b-2 flex items-center space-x-2 transition ${
              activeTab === 'memory'
                ? 'border-indigo-500 text-indigo-400 font-semibold'
                : 'border-transparent text-slate-400 hover:text-slate-200'
            }`}
          >
            <Brain className="w-4 h-4" />
            <span>Shared Memories</span>
          </button>

          <button
            onClick={() => setActiveTab('report')}
            className={`py-3.5 border-b-2 flex items-center space-x-2 transition ${
              activeTab === 'report'
                ? 'border-indigo-500 text-indigo-400 font-semibold'
                : 'border-transparent text-slate-400 hover:text-slate-200'
            }`}
          >
            <FileText className="w-4 h-4" />
            <span>Executive Report</span>
          </button>
        </div>
      </div>

      {/* Main Content Area */}
      <main className="max-w-7xl mx-auto w-full px-6 py-8 flex-1">
        {!activeProject ? (
          <div className="p-16 text-center rounded-2xl border border-dashed border-slate-800 bg-slate-900/30 space-y-3">
            <Network className="w-10 h-10 text-slate-600 mx-auto" />
            <h3 className="text-sm font-semibold text-slate-300">No Active Workspace</h3>
            <p className="text-xs text-slate-500">
              Click "Seed Demo Data" above to initialize the demo workspace or create a project.
            </p>
          </div>
        ) : (
          <>
            {activeTab === 'workspace' && (
              <WorkspaceView
                project={activeProject}
                onNavigateToReport={() => setActiveTab('report')}
                onNavigateToGraph={() => setActiveTab('graph')}
              />
            )}

            {activeTab === 'graph' && (
              <GraphExplorer projectId={activeProject.id} />
            )}

            {activeTab === 'memory' && (
              <MemoryLibrary
                projectId={activeProject.id}
                onSelectGraphNode={() => {
                  setActiveTab('graph');
                }}
              />
            )}

            {activeTab === 'report' && (
              <ReportView projectId={activeProject.id} />
            )}
          </>
        )}
      </main>

      {/* Footer */}
      <footer className="border-t border-slate-800/80 bg-slate-900/40 py-6 px-6 text-center text-xs text-slate-500">
        <div className="max-w-7xl mx-auto flex flex-col sm:flex-row items-center justify-between gap-2">
          <span>SwarmMind • Built for FalkorDB Graph Hacks 2026</span>
          <span className="font-mono">FalkorDB Cloud Ready • Graph-Grounded Multi-Agent Collaboration</span>
        </div>
      </footer>
    </div>
  );
}
