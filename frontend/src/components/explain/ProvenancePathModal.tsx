import React, { useEffect, useState } from 'react';
import {
  X,
  Sparkles,
  ShieldAlert,
  ArrowRight,
  BookOpen,
  Network,
  Layers,
} from 'lucide-react';
import { api } from '../../lib/api';
import { ExplanationResponse } from '../../types';

interface ProvenancePathModalProps {
  runId: string;
  nodeId?: string;
  recommendationTitle?: string;
  onClose: () => void;
}

export const ProvenancePathModal: React.FC<ProvenancePathModalProps> = ({
  runId,
  nodeId,
  recommendationTitle,
  onClose,
}) => {
  const [data, setData] = useState<ExplanationResponse | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    api.explainDecision(runId, { nodeId, recommendationTitle })
      .then(setData)
      .catch((err) => {
        console.error('Failed to load explanation:', err);
      })
      .finally(() => setLoading(false));
  }, [runId, nodeId, recommendationTitle]);

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-sm animate-in fade-in duration-200">
      <div className="relative w-full max-w-3xl max-h-[85vh] bg-slate-900 border border-indigo-500/30 rounded-2xl shadow-2xl overflow-hidden flex flex-col">
        {/* Modal Header */}
        <div className="px-6 py-4 border-b border-slate-800 bg-slate-950/60 flex items-center justify-between">
          <div className="flex items-center space-x-2.5">
            <div className="p-1.5 rounded-lg bg-indigo-500/10 text-indigo-400 border border-indigo-500/20">
              <Network className="w-5 h-5" />
            </div>
            <div>
              <span className="text-[10px] font-mono uppercase text-indigo-400 font-semibold tracking-wider">
                Graph-Grounded Explainability & Provenance
              </span>
              <h3 className="text-base font-bold text-white leading-snug">
                {recommendationTitle || data?.target_title || 'Decision Provenance Chain'}
              </h3>
            </div>
          </div>

          <button
            onClick={onClose}
            className="text-slate-400 hover:text-white p-1 rounded-lg hover:bg-slate-800 transition"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Modal Content */}
        <div className="p-6 overflow-y-auto space-y-6 text-xs text-slate-300">
          {loading ? (
            <div className="p-16 text-center text-slate-500 flex flex-col items-center justify-center gap-2">
              <Sparkles className="w-6 h-6 text-indigo-400 animate-spin" />
              <span>Tracing multi-hop Cypher provenance chain...</span>
            </div>
          ) : !data ? (
            <div className="p-12 text-center text-slate-500">
              Could not retrieve graph provenance for this decision.
            </div>
          ) : (
            <>
              {/* Narrative Summary */}
              <div className="p-4 rounded-xl border border-indigo-500/20 bg-indigo-950/20 space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-semibold text-indigo-300 flex items-center gap-1.5">
                    <Sparkles className="w-4 h-4 text-indigo-400" />
                    Autonomous Reasoning Rationale
                  </span>
                  <span className="font-mono text-emerald-400 font-bold">
                    {data.confidence_assessment}
                  </span>
                </div>
                <p className="text-slate-200 leading-relaxed font-sans text-xs">
                  {data.narrative_explanation}
                </p>
              </div>

              {/* Visual Provenance Flow Pipeline */}
              <div className="p-4 rounded-xl border border-slate-800 bg-slate-950/80 space-y-3">
                <h4 className="text-[11px] font-mono uppercase tracking-wider text-slate-400 flex items-center gap-1.5">
                  <Layers className="w-3.5 h-3.5 text-indigo-400" />
                  Multi-Hop Provenance Traversal Path
                </h4>
                <div className="flex flex-wrap items-center gap-2 text-xs font-mono">
                  <span className="px-2.5 py-1 rounded-lg bg-slate-900 border border-slate-800 text-slate-300">
                    Primary Sources (2)
                  </span>
                  <ArrowRight className="w-3 h-3 text-slate-600" />
                  <span className="px-2.5 py-1 rounded-lg bg-emerald-950/40 border border-emerald-500/30 text-emerald-300">
                    Researcher (Claims)
                  </span>
                  <ArrowRight className="w-3 h-3 text-slate-600" />
                  <span className="px-2.5 py-1 rounded-lg bg-rose-950/40 border border-rose-500/30 text-rose-300">
                    Critic (Dispute Preserved)
                  </span>
                  <ArrowRight className="w-3 h-3 text-slate-600" />
                  <span className="px-2.5 py-1 rounded-lg bg-cyan-950/40 border border-cyan-500/30 text-cyan-300">
                    Planner (GTM Recommendation)
                  </span>
                </div>
              </div>

              {/* Step-by-Step Chain */}
              <div className="space-y-3">
                <h4 className="text-[11px] font-mono uppercase tracking-wider text-slate-400">
                  Step-by-Step Graph Inferences ({data.steps.length})
                </h4>

                <div className="space-y-2.5">
                  {data.steps.map((step) => (
                    <div
                      key={step.step_number}
                      className="p-3.5 rounded-xl bg-slate-950 border border-slate-800/80 flex items-start gap-3"
                    >
                      <span className="w-5 h-5 rounded-full bg-indigo-500/10 text-indigo-400 border border-indigo-500/30 flex items-center justify-center font-mono text-[10px] shrink-0 mt-0.5 font-bold">
                        {step.step_number}
                      </span>

                      <div className="space-y-1 flex-1">
                        <div className="flex items-center justify-between">
                          <span className="px-2 py-0.5 rounded text-[10px] font-mono uppercase bg-slate-900 text-indigo-300 border border-slate-800">
                            {step.agent_role}
                          </span>
                          <span className="text-[10px] font-mono text-slate-500">
                            Confidence: <strong className="text-emerald-400">{Math.round(step.confidence * 100)}%</strong>
                          </span>
                        </div>

                        <p className="font-semibold text-slate-200 text-xs">{step.action}</p>
                        <p className="text-slate-300 text-xs leading-relaxed">{step.finding}</p>

                        {step.source_citation && (
                          <div className="pt-1 flex items-center gap-1.5 text-[11px] text-indigo-400">
                            <BookOpen className="w-3 h-3" />
                            <span className="font-mono">Cited: {step.source_citation}</span>
                          </div>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              {/* Preserved Contradictions Considered */}
              {data.contradictions && data.contradictions.length > 0 && (
                <div className="p-4 rounded-xl border border-rose-500/30 bg-rose-950/20 space-y-2">
                  <div className="flex items-center gap-1.5 text-rose-300 font-semibold text-xs">
                    <ShieldAlert className="w-4 h-4 text-rose-400" />
                    <span>Contradictions Evaluated & Mitigated</span>
                  </div>
                  {data.contradictions.map((c, idx) => (
                    <div key={idx} className="p-3 rounded-lg bg-slate-950/80 border border-rose-900/60 space-y-1 text-xs">
                      <p className="text-rose-200 font-medium">
                        {c.dispute_reason || c.notes}
                      </p>
                      {c.recommendation && (
                        <p className="text-[11px] text-slate-300">
                          <strong className="text-indigo-300">Swarm Resolution: </strong>
                          {c.recommendation}
                        </p>
                      )}
                    </div>
                  ))}
                </div>
              )}

              {/* Sources Cited */}
              {data.sources && data.sources.length > 0 && (
                <div className="p-4 rounded-xl border border-slate-800 bg-slate-950/60 space-y-2">
                  <h4 className="text-[11px] font-mono uppercase tracking-wider text-slate-400">
                    Primary Sources Grounding This Decision
                  </h4>
                  <ul className="space-y-1 text-xs">
                    {data.sources.map((s, idx) => (
                      <li key={idx} className="flex items-center justify-between text-slate-300 font-mono text-[11px]">
                        <span>• {s.title}</span>
                        <span className="text-indigo-400 truncate max-w-xs">{s.uri}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </>
          )}
        </div>
      </div>
    </div>
  );
};
