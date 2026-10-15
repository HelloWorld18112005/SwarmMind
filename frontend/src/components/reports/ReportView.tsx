import React, { useEffect, useState } from 'react';
import {
  FileText,
  Download,
  CheckCircle2,
  ShieldAlert,
  TrendingUp,
  Sparkles,
} from 'lucide-react';
import { api } from '../../lib/api';
import { Report, Run } from '../../types';
import { ProvenancePathModal } from '../explain/ProvenancePathModal';

interface ReportViewProps {
  projectId: string;
  activeRunId?: string;
}

export const ReportView: React.FC<ReportViewProps> = ({ projectId, activeRunId }) => {
  const [runs, setRuns] = useState<Run[]>([]);
  const [selectedRunId, setSelectedRunId] = useState<string>(activeRunId || '');
  const [report, setReport] = useState<Report | null>(null);
  const [loading, setLoading] = useState(false);
  const [exporting, setExporting] = useState(false);
  const [explainTarget, setExplainTarget] = useState<string | null>(null);

  // Fetch runs for project
  useEffect(() => {
    if (!projectId) return;
    api.listRuns(projectId).then((data) => {
      setRuns(data);
      if (data.length > 0 && !selectedRunId) {
        setSelectedRunId(data[0].id);
      }
    }).catch(console.error);
  }, [projectId]);

  // Fetch report when run selected
  useEffect(() => {
    if (!selectedRunId) return;
    setLoading(true);
    api.getReport(selectedRunId)
      .then(setReport)
      .catch((err) => {
        console.warn('No synthesized report found yet for run:', selectedRunId, err);
        setReport(null);
      })
      .finally(() => setLoading(false));
  }, [selectedRunId]);

  const handleExportMarkdown = async () => {
    if (!selectedRunId) return;
    setExporting(true);
    try {
      const markdown = await api.exportReportMarkdown(selectedRunId);
      const blob = new Blob([markdown], { type: 'text/markdown;charset=utf-8' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `SwarmMind_Report_${selectedRunId}.md`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    } catch (err: any) {
      alert(`Export failed: ${err.message}`);
    } finally {
      setExporting(false);
    }
  };

  return (
    <div className="space-y-6 max-w-5xl mx-auto">
      {/* Provenance Explainability Modal */}
      {explainTarget && selectedRunId && (
        <ProvenancePathModal
          runId={selectedRunId}
          recommendationTitle={explainTarget}
          onClose={() => setExplainTarget(null)}
        />
      )}

      {/* Top Header & Actions */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 border-b border-slate-800 pb-5">
        <div>
          <h2 className="text-2xl font-bold text-white flex items-center gap-2.5">
            <FileText className="w-6 h-6 text-indigo-400" />
            Executive Synthesis & Audit Report
          </h2>
          <p className="text-xs text-slate-400 mt-1">
            Ground-truth strategic intelligence synthesized from multi-agent graph deliberation.
          </p>
        </div>

        <div className="flex items-center gap-3">
          {/* Run Selector */}
          {runs.length > 0 && (
            <select
              value={selectedRunId}
              onChange={(e) => setSelectedRunId(e.target.value)}
              className="px-3 py-2 rounded-xl bg-slate-900 border border-slate-800 text-xs text-slate-200 outline-none font-mono"
            >
              {runs.map((r) => (
                <option key={r.id} value={r.id}>
                  {r.id} ({r.status})
                </option>
              ))}
            </select>
          )}

          {/* Export Markdown Button */}
          <button
            onClick={handleExportMarkdown}
            disabled={!report || exporting}
            className="inline-flex items-center space-x-2 px-4 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 text-white font-medium text-xs transition shadow-lg shadow-indigo-600/25"
          >
            <Download className="w-4 h-4" />
            <span>{exporting ? 'Exporting...' : 'Export as Markdown'}</span>
          </button>
        </div>
      </div>

      {loading ? (
        <div className="p-20 text-center text-slate-500">Loading synthesized report...</div>
      ) : !report ? (
        <div className="p-16 text-center rounded-2xl border border-dashed border-slate-800 bg-slate-900/30 space-y-3">
          <FileText className="w-10 h-10 text-slate-600 mx-auto" />
          <h3 className="text-sm font-semibold text-slate-300">No Report Generated Yet</h3>
          <p className="text-xs text-slate-500 max-w-md mx-auto">
            Launch an investigation from the Workspace or click "Seed Demo Data" above to load the Socratic AI Tutoring evaluation report.
          </p>
        </div>
      ) : (
        <div className="space-y-6 animate-in fade-in duration-300">
          {/* Executive Summary Card */}
          <div className="relative overflow-hidden rounded-2xl border border-indigo-500/30 bg-gradient-to-br from-indigo-950/40 via-slate-900/80 to-slate-900/60 p-6 shadow-xl space-y-4">
            <div className="flex items-center justify-between">
              <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-indigo-500/20 text-indigo-300 border border-indigo-500/40">
                Decision Recommendation
              </span>
              <button
                onClick={() => setExplainTarget(report.title)}
                className="inline-flex items-center gap-1.5 px-3 py-1 rounded-lg bg-indigo-600/30 hover:bg-indigo-600/40 border border-indigo-500/40 text-indigo-300 text-xs font-mono transition"
              >
                <Sparkles className="w-3.5 h-3.5 text-indigo-400" />
                <span>Trace Provenance</span>
              </button>
            </div>

            <h1 className="text-2xl font-bold text-white tracking-tight leading-snug">
              {report.title}
            </h1>

            <p className="text-sm text-slate-200 leading-relaxed font-sans">
              {report.executive_summary}
            </p>

            <div className="pt-2 border-t border-indigo-500/20 flex items-center justify-between text-xs text-indigo-300 font-mono">
              <span>Confidence Assessment:</span>
              <span className="font-bold text-emerald-400">{report.confidence_assessment}</span>
            </div>
          </div>

          {/* Preserved Contradictions & Market Divergence */}
          {report.unresolved_conflicts && report.unresolved_conflicts.length > 0 && (
            <div className="rounded-2xl border border-rose-500/40 bg-rose-950/20 p-6 space-y-4 shadow-xl">
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-2 text-rose-400">
                  <ShieldAlert className="w-5 h-5" />
                  <h3 className="font-bold text-base text-rose-200">
                    Preserved Market Contradictions ({report.unresolved_conflicts.length})
                  </h3>
                </div>
                <span className="text-xs font-mono text-rose-400/80 bg-rose-500/10 px-2.5 py-1 rounded border border-rose-500/30">
                  Unresolved in Graph
                </span>
              </div>

              <p className="text-xs text-rose-300/90 leading-relaxed">
                SwarmMind does not silently overwrite or average contradictory facts. The Critic agent explicitly preserved the following divergence:
              </p>

              <div className="space-y-3">
                {report.unresolved_conflicts.map((conflict, idx) => (
                  <div
                    key={idx}
                    className="p-4 rounded-xl bg-slate-950/80 border border-rose-500/30 space-y-3 text-xs"
                  >
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                      <div className="p-3 rounded-lg bg-slate-900 border border-slate-800 space-y-1">
                        <span className="text-[10px] font-mono text-slate-400 uppercase">Finding A</span>
                        <p className="text-slate-200 font-medium">{conflict.claim_a_text}</p>
                      </div>
                      <div className="p-3 rounded-lg bg-slate-900 border border-slate-800 space-y-1">
                        <span className="text-[10px] font-mono text-slate-400 uppercase">Finding B</span>
                        <p className="text-slate-200 font-medium">{conflict.claim_b_text}</p>
                      </div>
                    </div>

                    <div className="pt-2 border-t border-slate-900 text-xs text-slate-300 flex items-center justify-between">
                      <div>
                        <span className="font-semibold text-rose-300">Dispute Rationale: </span>
                        {conflict.notes || conflict.dispute_reason}
                      </div>
                      <button
                        onClick={() => setExplainTarget(conflict.claim_a_text)}
                        className="text-indigo-400 hover:text-indigo-300 font-mono text-[11px] underline ml-3 shrink-0"
                      >
                        Explain Dispute
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Key Findings */}
          <div className="rounded-2xl border border-slate-800 bg-slate-900/60 p-6 space-y-4 shadow-xl">
            <h3 className="font-bold text-base text-white flex items-center gap-2">
              <CheckCircle2 className="w-5 h-5 text-emerald-400" />
              Verified Key Findings
            </h3>

            <div className="space-y-2.5">
              {report.findings.map((finding, idx) => (
                <div
                  key={idx}
                  className="p-3.5 rounded-xl bg-slate-950 border border-slate-800/80 flex items-start justify-between gap-3 text-xs group"
                >
                  <div className="flex items-start gap-3 flex-1">
                    <span className="w-5 h-5 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/30 flex items-center justify-center font-mono text-[10px] shrink-0 mt-0.5">
                      {idx + 1}
                    </span>
                    <p className="text-slate-200 leading-relaxed font-sans">{finding}</p>
                  </div>

                  <button
                    onClick={() => setExplainTarget(finding)}
                    className="opacity-0 group-hover:opacity-100 transition px-2 py-1 rounded bg-slate-900 border border-slate-800 text-indigo-400 hover:text-indigo-300 font-mono text-[10px] shrink-0"
                  >
                    Trace
                  </button>
                </div>
              ))}
            </div>
          </div>

          {/* Actionable Recommendations */}
          {report.recommendations && report.recommendations.length > 0 && (
            <div className="rounded-2xl border border-slate-800 bg-slate-900/60 p-6 space-y-4 shadow-xl">
              <h3 className="font-bold text-base text-white flex items-center gap-2">
                <TrendingUp className="w-5 h-5 text-cyan-400" />
                Actionable Strategic Recommendations
              </h3>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {report.recommendations.map((rec, idx) => (
                  <div
                    key={idx}
                    className="p-4 rounded-xl bg-slate-950 border border-slate-800 flex flex-col justify-between space-y-3"
                  >
                    <div className="space-y-2">
                      <div className="flex items-center justify-between">
                        <span className="text-xs font-semibold text-white">{rec.title}</span>
                        <span className="px-2 py-0.5 rounded text-[10px] font-mono uppercase bg-cyan-500/10 text-cyan-400 border border-cyan-500/30">
                          {rec.priority}
                        </span>
                      </div>
                      <p className="text-xs text-slate-300 leading-relaxed">{rec.description}</p>
                    </div>

                    <div className="pt-2 border-t border-slate-900 flex items-center justify-between">
                      {rec.risks && rec.risks.length > 0 ? (
                        <span className="text-[10px] font-mono text-slate-500 uppercase">
                          {rec.risks.length} Risks Identified
                        </span>
                      ) : <span />}

                      <button
                        onClick={() => setExplainTarget(rec.title)}
                        className="inline-flex items-center gap-1 text-[11px] font-mono text-indigo-400 hover:text-indigo-300 font-medium"
                      >
                        <Sparkles className="w-3 h-3" />
                        <span>Trace Provenance</span>
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Evidence Sources Table */}
          {report.sources && report.sources.length > 0 && (
            <div className="rounded-2xl border border-slate-800 bg-slate-900/60 p-6 space-y-4 shadow-xl">
              <h3 className="font-bold text-base text-white">Sources & Evidence Provenance</h3>
              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs">
                  <thead className="border-b border-slate-800 text-slate-400 font-mono text-[11px]">
                    <tr>
                      <th className="py-2 px-3">Source Title</th>
                      <th className="py-2 px-3">Type</th>
                      <th className="py-2 px-3">URI / Citation</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800/60 font-sans">
                    {report.sources.map((src: any, sIdx) => (
                      <tr key={sIdx} className="hover:bg-slate-950/40">
                        <td className="py-2.5 px-3 font-medium text-slate-200">{src.title}</td>
                        <td className="py-2.5 px-3 font-mono text-slate-400 capitalize">{src.source_type}</td>
                        <td className="py-2.5 px-3 font-mono text-indigo-400 truncate max-w-xs">
                          {src.uri || 'Internal Document'}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};
