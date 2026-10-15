import React, { useEffect, useState, useRef } from 'react';
import {
  Play,
  Clock,
  Terminal,
  Activity,
  Bot,
  ArrowRight,
  Sparkles,
} from 'lucide-react';
import { api } from '../../lib/api';
import { Project, Run, Task } from '../../types';

interface WorkspaceViewProps {
  project: Project;
  onNavigateToReport: () => void;
  onNavigateToGraph: () => void;
}

export const WorkspaceView: React.FC<WorkspaceViewProps> = ({
  project,
  onNavigateToReport,
  onNavigateToGraph,
}) => {
  const [runs, setRuns] = useState<Run[]>([]);
  const [activeRun, setActiveRun] = useState<Run | null>(null);
  const [tasks, setTasks] = useState<Task[]>([]);
  const [goal, setGoal] = useState('Evaluate strategic feasibility, TAM divergence, unit economics, and latency for AI Socratic Math Tutoring.');
  const [isLaunching, setIsLaunching] = useState(false);
  const [events, setEvents] = useState<any[]>([]);
  const eventLogRef = useRef<HTMLDivElement>(null);

  const fetchRuns = async () => {
    try {
      const runList = await api.listRuns(project.id);
      setRuns(runList);
      if (runList.length > 0 && !activeRun) {
        setActiveRun(runList[0]);
      }
    } catch (err) {
      console.error('Failed to list runs:', err);
    }
  };

  const fetchTasks = async (runId: string) => {
    try {
      const taskList = await api.listRunTasks(runId);
      setTasks(taskList);
    } catch (err) {
      console.error('Failed to list tasks:', err);
    }
  };

  useEffect(() => {
    fetchRuns();
  }, [project.id]);

  useEffect(() => {
    if (activeRun) {
      fetchTasks(activeRun.id);
    }
  }, [activeRun]);

  // Subscribe to live SSE events when active run is running
  useEffect(() => {
    if (!activeRun) return;

    const unsubscribe = api.subscribeRunEvents(activeRun.id, (event) => {
      setEvents((prev) => [...prev, event]);
      if (event.event_type === 'task_completed' || event.event_type === 'task_started') {
        fetchTasks(activeRun.id);
      }
      if (event.event_type === 'run_completed') {
        setActiveRun((prev) => (prev ? { ...prev, status: 'completed' } : null));
        fetchRuns();
      }
    });

    return () => {
      unsubscribe();
    };
  }, [activeRun?.id]);

  // Auto-scroll event log
  useEffect(() => {
    if (eventLogRef.current) {
      eventLogRef.current.scrollTop = eventLogRef.current.scrollHeight;
    }
  }, [events]);

  const handleLaunchInvestigation = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!goal.trim()) return;

    setIsLaunching(true);
    setEvents([]);
    try {
      const newRun = await api.createRun(project.id, goal.trim());
      setActiveRun(newRun);
      setRuns([newRun, ...runs]);
      await fetchTasks(newRun.id);
    } catch (err: any) {
      alert(`Launch error: ${err.message}`);
    } finally {
      setIsLaunching(false);
    }
  };

  const agentTeam = [
    { role: 'coordinator', color: 'text-blue-400 bg-blue-500/10 border-blue-500/30' },
    { role: 'researcher', color: 'text-emerald-400 bg-emerald-500/10 border-emerald-500/30' },
    { role: 'analyst', color: 'text-purple-400 bg-purple-500/10 border-purple-500/30' },
    { role: 'critic', color: 'text-rose-400 bg-rose-500/10 border-rose-500/30' },
    { role: 'planner', color: 'text-cyan-400 bg-cyan-500/10 border-cyan-500/30' },
    { role: 'synthesizer', color: 'text-amber-400 bg-amber-500/10 border-amber-500/30' },
  ];

  return (
    <div className="space-y-6">
      {/* Launch Goal Input */}
      <form
        onSubmit={handleLaunchInvestigation}
        className="p-5 rounded-2xl border border-indigo-500/30 bg-gradient-to-br from-indigo-950/30 via-slate-900/60 to-slate-900/40 space-y-3 shadow-xl"
      >
        <div className="flex items-center justify-between">
          <label className="text-xs font-semibold uppercase tracking-wider text-indigo-300 flex items-center gap-1.5">
            <Sparkles className="w-3.5 h-3.5 text-indigo-400" />
            Launch Autonomous Swarm Deliberation
          </label>
          <span className="text-[11px] font-mono text-slate-400">
            Project: <strong className="text-slate-200">{project.name}</strong>
          </span>
        </div>

        <div className="flex gap-3">
          <input
            type="text"
            value={goal}
            onChange={(e) => setGoal(e.target.value)}
            placeholder="Specify investigation goal for the 6-agent swarm..."
            className="flex-1 px-4 py-2.5 bg-slate-950 border border-slate-800 rounded-xl text-xs text-slate-100 placeholder-slate-500 focus:border-indigo-500 outline-none font-sans"
          />
          <button
            type="submit"
            disabled={isLaunching}
            className="inline-flex items-center space-x-2 px-5 py-2.5 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white font-medium text-xs transition shadow-lg shadow-indigo-600/30 disabled:opacity-50 shrink-0"
          >
            <Play className={`w-4 h-4 ${isLaunching ? 'animate-spin' : ''}`} />
            <span>{isLaunching ? 'Orchestrating...' : 'Launch Swarm'}</span>
          </button>
        </div>
      </form>

      {/* Active Run Banner & Controls */}
      {activeRun && (
        <div className="p-4 rounded-xl border border-slate-800 bg-slate-900/70 flex flex-wrap items-center justify-between gap-4">
          <div className="flex items-center space-x-3">
            <div className={`p-2 rounded-lg ${activeRun.status === 'completed' ? 'bg-emerald-500/10 text-emerald-400' : 'bg-indigo-500/10 text-indigo-400'}`}>
              <Activity className="w-5 h-5" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="font-mono text-xs font-bold text-slate-200">{activeRun.id}</span>
                <span className={`px-2 py-0.5 rounded text-[10px] font-mono uppercase ${
                  activeRun.status === 'completed'
                    ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/40'
                    : 'bg-amber-500/20 text-amber-300 border border-amber-500/40 animate-pulse'
                }`}>
                  {activeRun.status}
                </span>
              </div>
              <p className="text-xs text-slate-400 mt-0.5 max-w-xl truncate">{activeRun.goal}</p>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={onNavigateToGraph}
              className="px-3 py-1.5 rounded-lg border border-slate-700 bg-slate-800 hover:bg-slate-700 text-xs text-slate-200 transition"
            >
              Explore Graph
            </button>
            <button
              onClick={onNavigateToReport}
              className="px-3 py-1.5 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-xs font-medium text-white transition flex items-center gap-1"
            >
              View Report
              <ArrowRight className="w-3.5 h-3.5" />
            </button>
          </div>
        </div>
      )}

      {/* Agent Swarm Roster */}
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-2.5">
        {agentTeam.map((agent) => (
          <div
            key={agent.role}
            className={`p-3 rounded-xl border ${agent.color} flex flex-col justify-between space-y-1`}
          >
            <div className="flex items-center justify-between">
              <Bot className="w-3.5 h-3.5" />
              <span className="text-[10px] font-mono uppercase">Role</span>
            </div>
            <div className="font-semibold text-xs capitalize text-slate-100">{agent.role}</div>
          </div>
        ))}
      </div>

      {/* Two Column Layout: Tasks DAG & Live Terminal Feed */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Task DAG Execution Status */}
        <div className="p-5 rounded-2xl border border-slate-800 bg-slate-900/50 space-y-4">
          <div className="flex items-center justify-between border-b border-slate-800 pb-3">
            <h3 className="text-xs font-semibold uppercase tracking-wider text-slate-300 flex items-center gap-2">
              <Clock className="w-4 h-4 text-indigo-400" />
              Orchestrated Task Graph ({tasks.length})
            </h3>
            <span className="text-[11px] font-mono text-slate-500">
              Completed: {tasks.filter((t) => t.status === 'completed').length}/{tasks.length}
            </span>
          </div>

          {tasks.length === 0 ? (
            <div className="p-8 text-center text-xs text-slate-500">
              No tasks orchestrated yet for this run.
            </div>
          ) : (
            <div className="space-y-2.5">
              {tasks.map((task) => (
                <div
                  key={task.id}
                  className="p-3 rounded-xl bg-slate-950 border border-slate-800 flex items-start justify-between gap-3 text-xs"
                >
                  <div className="space-y-1 flex-1">
                    <div className="flex items-center gap-2">
                      <span className="font-semibold text-slate-200">{task.title}</span>
                      <span className="px-1.5 py-0.5 rounded text-[9px] font-mono uppercase bg-slate-900 text-indigo-300 border border-slate-800">
                        {task.assigned_role}
                      </span>
                    </div>
                    {task.dependencies && task.dependencies.length > 0 && (
                      <p className="text-[10px] text-slate-500 font-mono">
                        Depends on: {task.dependencies.join(', ')}
                      </p>
                    )}
                  </div>

                  <span
                    className={`px-2 py-0.5 rounded text-[10px] font-mono uppercase shrink-0 ${
                      task.status === 'completed'
                        ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/30'
                        : task.status === 'running'
                        ? 'bg-amber-500/10 text-amber-400 border border-amber-500/30 animate-pulse'
                        : 'bg-slate-900 text-slate-500 border border-slate-800'
                    }`}
                  >
                    {task.status}
                  </span>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Live SSE Event Stream Feed */}
        <div className="p-5 rounded-2xl border border-slate-800 bg-slate-950 flex flex-col space-y-3 font-mono">
          <div className="flex items-center justify-between border-b border-slate-800 pb-2">
            <div className="flex items-center space-x-2 text-xs font-semibold text-slate-300">
              <Terminal className="w-4 h-4 text-emerald-400" />
              <span>Real-Time SSE Event Stream</span>
            </div>
            <span className="flex items-center gap-1.5 text-[10px] text-emerald-400">
              <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
              Connected
            </span>
          </div>

          <div
            ref={eventLogRef}
            className="flex-1 h-80 overflow-y-auto space-y-2 text-[11px] pr-2 text-slate-300"
          >
            {events.length === 0 ? (
              <p className="text-slate-600 italic">Awaiting orchestration events...</p>
            ) : (
              events.map((ev, idx) => (
                <div key={idx} className="flex items-start gap-2 border-b border-slate-900 pb-1.5">
                  <span className="text-slate-500 shrink-0 font-mono text-[10px]">
                    {new Date(ev.timestamp || Date.now()).toLocaleTimeString()}
                  </span>
                  <span className="px-1 py-0.2 rounded text-[9px] uppercase bg-slate-900 text-indigo-400 border border-slate-800 shrink-0">
                    {ev.event_type}
                  </span>
                  <span className="break-words text-slate-300">
                    {ev.message || JSON.stringify(ev.payload || {})}
                  </span>
                </div>
              ))
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
