import React from 'react';
import {
  X,
  AlertTriangle,
  ArrowRight,
  ArrowLeft,
  Layers,
} from 'lucide-react';
import { GraphEdge, GraphNode } from '../../types';

interface NodeInspectorProps {
  node: GraphNode | null;
  edges: GraphEdge[];
  allNodes: GraphNode[];
  onClose: () => void;
  onSelectNode: (nodeId: string) => void;
}

export const NodeInspector: React.FC<NodeInspectorProps> = ({
  node,
  edges,
  allNodes,
  onClose,
  onSelectNode,
}) => {
  if (!node) return null;

  const outgoingEdges = edges.filter((e) => e.source === node.id);
  const incomingEdges = edges.filter((e) => e.target === node.id);

  const contradictionEdge = edges.find(
    (e) => (e.source === node.id || e.target === node.id) && e.relationship === 'CONTRADICTS'
  );

  const opposingNodeId = contradictionEdge
    ? contradictionEdge.source === node.id
      ? contradictionEdge.target
      : contradictionEdge.source
    : null;
  const opposingNode = opposingNodeId ? allNodes.find((n) => n.id === opposingNodeId) : null;

  const getNodeTitle = (id: string): string => {
    const found = allNodes.find((n) => n.id === id);
    if (!found) return id;
    const name = found.properties?.name;
    return String(found.title || name || id);
  };

  const getNodeLabel = (id: string): string => {
    const found = allNodes.find((n) => n.id === id);
    return found?.label || 'Node';
  };

  return (
    <div className="absolute right-0 top-0 bottom-0 w-96 bg-slate-900/95 border-l border-slate-800 shadow-2xl backdrop-blur p-5 flex flex-col z-20 overflow-y-auto space-y-5 animate-in slide-in-from-right duration-200">
      <div className="flex items-start justify-between border-b border-slate-800 pb-3">
        <div>
          <span className="px-2 py-0.5 rounded text-[10px] font-mono uppercase bg-indigo-500/10 text-indigo-400 border border-indigo-500/30">
            {node.label}
          </span>
          <h3 className="font-semibold text-slate-100 text-sm mt-1 leading-snug">
            {String(node.title || node.properties?.name || node.id)}
          </h3>
          <p className="text-[11px] font-mono text-slate-500 mt-0.5">{node.id}</p>
        </div>
        <button
          onClick={onClose}
          className="text-slate-400 hover:text-white p-1 rounded-lg hover:bg-slate-800 transition"
        >
          <X className="w-4 h-4" />
        </button>
      </div>

      {contradictionEdge && opposingNode && (
        <div className="p-3.5 rounded-xl border border-rose-500/40 bg-rose-950/30 space-y-2">
          <div className="flex items-center gap-1.5 text-rose-400 text-xs font-semibold">
            <AlertTriangle className="w-4 h-4" />
            <span>Preserved Graph Contradiction</span>
          </div>
          <p className="text-xs text-rose-200 leading-relaxed">
            {String(contradictionEdge.properties?.dispute_reason || contradictionEdge.properties?.notes || 'Direct evidentiary conflict detected by Critic agent.')}
          </p>
          <div className="pt-1.5 border-t border-rose-900/60 flex items-center justify-between text-[11px]">
            <span className="text-slate-400">Opposing Claim:</span>
            <button
              onClick={() => onSelectNode(opposingNode.id)}
              className="text-indigo-400 hover:text-indigo-300 font-medium underline flex items-center gap-1"
            >
              View Opposing Claim
              <ArrowRight className="w-3 h-3" />
            </button>
          </div>
        </div>
      )}

      <div className="space-y-2">
        <h4 className="text-xs font-semibold text-slate-400 uppercase tracking-wider flex items-center gap-1.5">
          <Layers className="w-3.5 h-3.5 text-indigo-400" />
          Properties & Metadata
        </h4>
        <div className="bg-slate-950/60 rounded-xl border border-slate-800/80 p-3 space-y-2 text-xs">
          {Object.entries(node.properties || {}).map(([key, val]) => {
            if (val === null || val === undefined || key === 'title') return null;
            return (
              <div key={key} className="flex flex-col border-b border-slate-900 pb-1.5 last:border-0 last:pb-0">
                <span className="text-slate-500 text-[10px] uppercase font-mono">{key}</span>
                <span className="text-slate-200 break-words font-mono text-[11px]">
                  {typeof val === 'object' ? JSON.stringify(val) : String(val)}
                </span>
              </div>
            );
          })}
        </div>
      </div>

      <div className="space-y-2">
        <h4 className="text-xs font-semibold text-slate-400 uppercase tracking-wider flex items-center gap-1.5">
          <ArrowRight className="w-3.5 h-3.5 text-emerald-400" />
          Outgoing Connections ({outgoingEdges.length})
        </h4>
        {outgoingEdges.length === 0 ? (
          <p className="text-xs text-slate-500 italic">No outgoing graph edges</p>
        ) : (
          <div className="space-y-1.5">
            {outgoingEdges.map((e) => (
              <div
                key={e.id}
                onClick={() => onSelectNode(e.target)}
                className="p-2 rounded-lg bg-slate-950 border border-slate-800/80 hover:border-indigo-500/50 cursor-pointer transition flex items-center justify-between text-xs"
              >
                <div className="flex items-center gap-1.5 overflow-hidden">
                  <span className="px-1.5 py-0.5 rounded text-[9px] font-mono uppercase bg-slate-800 text-indigo-300">
                    {e.relationship}
                  </span>
                  <span className="text-slate-300 truncate max-w-[170px]">
                    {getNodeTitle(e.target)}
                  </span>
                </div>
                <span className="text-[10px] text-slate-500 font-mono">[{getNodeLabel(e.target)}]</span>
              </div>
            ))}
          </div>
        )}
      </div>

      <div className="space-y-2">
        <h4 className="text-xs font-semibold text-slate-400 uppercase tracking-wider flex items-center gap-1.5">
          <ArrowLeft className="w-3.5 h-3.5 text-blue-400" />
          Incoming Connections ({incomingEdges.length})
        </h4>
        {incomingEdges.length === 0 ? (
          <p className="text-xs text-slate-500 italic">No incoming graph edges</p>
        ) : (
          <div className="space-y-1.5">
            {incomingEdges.map((e) => (
              <div
                key={e.id}
                onClick={() => onSelectNode(e.source)}
                className="p-2 rounded-lg bg-slate-950 border border-slate-800/80 hover:border-indigo-500/50 cursor-pointer transition flex items-center justify-between text-xs"
              >
                <div className="flex items-center gap-1.5 overflow-hidden">
                  <span className="px-1.5 py-0.5 rounded text-[9px] font-mono uppercase bg-slate-800 text-blue-300">
                    {e.relationship}
                  </span>
                  <span className="text-slate-300 truncate max-w-[170px]">
                    {getNodeTitle(e.source)}
                  </span>
                </div>
                <span className="text-[10px] text-slate-500 font-mono">[{getNodeLabel(e.source)}]</span>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};
