import React, { useCallback, useEffect, useState } from 'react';
import {
  ReactFlow,
  Background,
  Controls,
  MiniMap,
  useNodesState,
  useEdgesState,
  MarkerType,
  Edge,
  Node,
} from '@xyflow/react';
import {
  Network,
  RefreshCw,
  AlertTriangle,
} from 'lucide-react';
import { api } from '../../lib/api';
import { GraphData, GraphNode } from '../../types';
import { CustomNode } from './CustomNode';
import { NodeInspector } from './NodeInspector';

const nodeTypes: any = {
  custom: CustomNode,
};

interface GraphExplorerProps {
  projectId: string;
}

export const GraphExplorer: React.FC<GraphExplorerProps> = ({ projectId }) => {
  const [graphData, setGraphData] = useState<GraphData | null>(null);
  const [loading, setLoading] = useState(false);
  const [filterLabel, setFilterLabel] = useState<string>('ALL');
  const [disputesOnly, setDisputesOnly] = useState<boolean>(false);
  const [selectedNode, setSelectedNode] = useState<GraphNode | null>(null);

  const [nodes, setNodes, onNodesChange] = useNodesState<Node>([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState<Edge>([]);

  const loadGraph = useCallback(async () => {
    if (!projectId) return;
    setLoading(true);
    try {
      const data = await api.getProjectGraph(projectId);
      setGraphData(data);
    } catch (err) {
      console.error('Failed to load project graph:', err);
    } finally {
      setLoading(false);
    }
  }, [projectId]);

  useEffect(() => {
    loadGraph();
  }, [loadGraph]);

  // Compute graph layout and contradiction links
  useEffect(() => {
    if (!graphData) return;

    const contradictedNodeIds = new Set<string>();
    graphData.edges.forEach((e) => {
      if (e.relationship === 'CONTRADICTS') {
        contradictedNodeIds.add(e.source);
        contradictedNodeIds.add(e.target);
      }
    });

    // Filter nodes
    let filteredNodes = graphData.nodes;
    if (disputesOnly) {
      filteredNodes = filteredNodes.filter((n) => contradictedNodeIds.has(n.id));
    } else if (filterLabel !== 'ALL') {
      filteredNodes = filteredNodes.filter((n) => n.label.toUpperCase() === filterLabel.toUpperCase());
    }

    const filteredNodeIds = new Set(filteredNodes.map((n) => n.id));

    // Layout by node label layers
    const layerOrder: Record<string, number> = {
      Project: 0,
      Run: 1,
      Agent: 2,
      Task: 3,
      Memory: 4,
      Claim: 4,
      Source: 5,
    };

    const layerCounts: Record<number, number> = {};

    const flowNodes: Node[] = filteredNodes.map((n) => {
      const layer = layerOrder[n.label] ?? 3;
      const indexInLayer = layerCounts[layer] || 0;
      layerCounts[layer] = indexInLayer + 1;

      const x = 50 + layer * 320;
      const y = 80 + indexInLayer * 140;

      return {
        id: n.id,
        type: 'custom',
        position: { x, y },
        data: {
          id: n.id,
          label: n.label,
          title: n.title,
          properties: n.properties,
          hasContradiction: contradictedNodeIds.has(n.id),
        },
      };
    });

    // Edges
    const flowEdges: Edge[] = graphData.edges
      .filter((e) => filteredNodeIds.has(e.source) && filteredNodeIds.has(e.target))
      .map((e) => {
        const isContradiction = e.relationship === 'CONTRADICTS';
        const isSupport = e.relationship === 'SUPPORTS';

        return {
          id: e.id,
          source: e.source,
          target: e.target,
          label: e.relationship,
          animated: isContradiction,
          style: {
            stroke: isContradiction ? '#f43f5e' : isSupport ? '#10b981' : '#64748b',
            strokeWidth: isContradiction ? 2.5 : isSupport ? 2 : 1.5,
            strokeDasharray: isContradiction ? '5 5' : undefined,
          },
          labelStyle: {
            fill: isContradiction ? '#fb7185' : isSupport ? '#34d399' : '#94a3b8',
            fontWeight: 600,
            fontSize: 10,
          },
          labelBgStyle: {
            fill: '#090d16',
            fillOpacity: 0.85,
          },
          markerEnd: {
            type: MarkerType.ArrowClosed,
            color: isContradiction ? '#f43f5e' : isSupport ? '#10b981' : '#64748b',
          },
        };
      });

    setNodes(flowNodes);
    setEdges(flowEdges);
  }, [graphData, filterLabel, disputesOnly, setNodes, setEdges]);

  const onNodeClick = useCallback(
    (_: React.MouseEvent, node: Node) => {
      if (!graphData) return;
      const found = graphData.nodes.find((n) => n.id === node.id);
      if (found) setSelectedNode(found);
    },
    [graphData]
  );

  const filterOptions = ['ALL', 'CLAIM', 'MEMORY', 'TASK', 'AGENT', 'SOURCE'];

  return (
    <div className="relative w-full h-[760px] bg-slate-950 rounded-2xl border border-slate-800/80 overflow-hidden shadow-2xl flex flex-col">
      {/* Top Filter Bar */}
      <div className="px-5 py-3 border-b border-slate-800 bg-slate-900/70 backdrop-blur flex flex-wrap items-center justify-between gap-3 z-10">
        <div className="flex items-center space-x-2">
          <Network className="w-5 h-5 text-indigo-400" />
          <span className="font-semibold text-sm text-slate-100">FalkorDB Knowledge Graph</span>
          <span className="text-xs text-slate-500 font-mono">
            ({nodes.length} nodes • {edges.length} edges)
          </span>
        </div>

        <div className="flex items-center gap-2">
          {/* Label Filter Pills */}
          <div className="flex items-center bg-slate-950 p-1 rounded-lg border border-slate-800 text-xs">
            {filterOptions.map((opt) => (
              <button
                key={opt}
                onClick={() => {
                  setFilterLabel(opt);
                  setDisputesOnly(false);
                }}
                className={`px-2.5 py-1 rounded-md transition font-mono ${
                  filterLabel === opt && !disputesOnly
                    ? 'bg-indigo-600 text-white font-medium shadow'
                    : 'text-slate-400 hover:text-slate-200'
                }`}
              >
                {opt}
              </button>
            ))}
          </div>

          {/* Disputes Only Toggle */}
          <button
            onClick={() => setDisputesOnly(!disputesOnly)}
            className={`flex items-center space-x-1.5 px-3 py-1.5 rounded-lg border text-xs font-medium transition ${
              disputesOnly
                ? 'bg-rose-500/20 text-rose-300 border-rose-500/50 shadow-lg shadow-rose-500/10'
                : 'bg-slate-900 text-slate-400 border-slate-800 hover:text-rose-400'
            }`}
          >
            <AlertTriangle className={`w-3.5 h-3.5 ${disputesOnly ? 'text-rose-400' : ''}`} />
            <span>Contradictions Only</span>
          </button>

          {/* Refresh Button */}
          <button
            onClick={loadGraph}
            disabled={loading}
            className="p-1.5 rounded-lg border border-slate-800 bg-slate-900 hover:bg-slate-800 text-slate-400 hover:text-white transition"
            title="Refresh graph from FalkorDB"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin text-indigo-400' : ''}`} />
          </button>
        </div>
      </div>

      {/* React Flow Canvas */}
      <div className="flex-1 w-full h-full relative">
        <ReactFlow
          nodes={nodes}
          edges={edges}
          onNodesChange={onNodesChange}
          onEdgesChange={onEdgesChange}
          onNodeClick={onNodeClick}
          nodeTypes={nodeTypes}
          fitView
          fitViewOptions={{ padding: 0.2 }}
          minZoom={0.2}
          maxZoom={1.5}
        >
          <Background color="#1e293b" gap={24} size={1} />
          <Controls className="!bg-slate-900 !border-slate-800 !text-slate-200 fill-slate-200" />
          <MiniMap
            nodeColor={(node: any) => {
              if (node.data?.hasContradiction) return '#f43f5e';
              switch (node.data?.label) {
                case 'Agent': return '#06b6d4';
                case 'Task': return '#3b82f6';
                case 'Memory': return '#f59e0b';
                case 'Claim': return '#10b981';
                case 'Source': return '#64748b';
                default: return '#6366f1';
              }
            }}
            maskColor="rgba(2, 6, 23, 0.75)"
            className="!bg-slate-950 !border-slate-800"
          />
        </ReactFlow>

        {/* Node Inspector Drawer */}
        <NodeInspector
          node={selectedNode}
          edges={graphData?.edges || []}
          allNodes={graphData?.nodes || []}
          onClose={() => setSelectedNode(null)}
          onSelectNode={(id) => {
            const found = graphData?.nodes.find((n) => n.id === id);
            if (found) setSelectedNode(found);
          }}
        />
      </div>
    </div>
  );
};
