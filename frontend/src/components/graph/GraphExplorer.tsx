import React, { useCallback, useEffect, useState } from 'react';
import {
  ReactFlow,
  ReactFlowProvider,
  Background,
  MiniMap,
  useNodesState,
  useEdgesState,
  useReactFlow,
  MarkerType,
  Edge,
  Node,
} from '@xyflow/react';
import '@xyflow/react/dist/style.css';
import {
  Network,
  RefreshCw,
  AlertTriangle,
  Maximize2,
  ZoomIn,
  ZoomOut,
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

// Inner canvas component that has access to useReactFlow hook
const FlowCanvas: React.FC<{
  nodes: Node[];
  edges: Edge[];
  onNodesChange: any;
  onEdgesChange: any;
  onNodeClick: any;
  graphData: GraphData | null;
  selectedNode: GraphNode | null;
  setSelectedNode: (n: GraphNode | null) => void;
  filterLabel: string;
  disputesOnly: boolean;
}> = ({
  nodes,
  edges,
  onNodesChange,
  onEdgesChange,
  onNodeClick,
  graphData,
  selectedNode,
  setSelectedNode,
  filterLabel,
  disputesOnly,
}) => {
  const { fitView, zoomIn, zoomOut } = useReactFlow();

  // Automatically fit and center view whenever nodes change or filter changes
  useEffect(() => {
    if (nodes.length > 0) {
      const timer = setTimeout(() => {
        fitView({ padding: 0.25, duration: 400 });
      }, 50);
      return () => clearTimeout(timer);
    }
  }, [nodes.length, filterLabel, disputesOnly, fitView]);

  return (
    <div className="flex-1 w-full h-full relative">
      <ReactFlow
        nodes={nodes}
        edges={edges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        onNodeClick={onNodeClick}
        nodeTypes={nodeTypes}
        fitView
        fitViewOptions={{ padding: 0.25 }}
        minZoom={0.1}
        maxZoom={2.5}
        zoomOnScroll={true}
        panOnScroll={false}
        panOnDrag={true}
        zoomOnPinch={true}
        nodesDraggable={true}
      >
        <Background color="#1e293b" gap={24} size={1} />
        
        {/* MiniMap in bottom-right so it doesn't block content */}
        <MiniMap
          position="bottom-right"
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
          className="!bg-slate-950 !border-slate-800 !rounded-xl !shadow-2xl"
          zoomable
          pannable
        />
      </ReactFlow>

      {/* Floating Canvas Quick Controls (Center / Fit View, Zoom) */}
      <div className="absolute top-4 right-4 z-10 flex items-center gap-1.5 bg-slate-900/90 border border-slate-800 p-1 rounded-xl shadow-xl backdrop-blur">
        <button
          onClick={() => fitView({ padding: 0.25, duration: 400 })}
          className="p-1.5 rounded-lg text-slate-300 hover:text-white hover:bg-slate-800 transition text-xs flex items-center gap-1"
          title="Center and fit all nodes in view"
        >
          <Maximize2 className="w-3.5 h-3.5" />
          <span className="text-[11px] font-mono">Fit View</span>
        </button>
        <div className="w-[1px] h-4 bg-slate-800" />
        <button
          onClick={() => zoomIn({ duration: 300 })}
          className="p-1.5 rounded-lg text-slate-300 hover:text-white hover:bg-slate-800 transition"
          title="Zoom in"
        >
          <ZoomIn className="w-3.5 h-3.5" />
        </button>
        <button
          onClick={() => zoomOut({ duration: 300 })}
          className="p-1.5 rounded-lg text-slate-300 hover:text-white hover:bg-slate-800 transition"
          title="Zoom out"
        >
          <ZoomOut className="w-3.5 h-3.5" />
        </button>
      </div>

      {/* Slide-over Node Inspector */}
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
  );
};

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

    // 1. Filter nodes
    let filteredNodes = graphData.nodes;
    if (disputesOnly) {
      filteredNodes = filteredNodes.filter((n) => contradictedNodeIds.has(n.id));
    } else if (filterLabel !== 'ALL') {
      filteredNodes = filteredNodes.filter((n) => n.label.toUpperCase() === filterLabel.toUpperCase());
    }

    const filteredNodeIds = new Set(filteredNodes.map((n) => n.id));

    // 2. Intelligent Adaptive Layout:
    let flowNodes: Node[] = [];

    if (filterLabel !== 'ALL' && !disputesOnly) {
      // Clean multi-column grid when viewing a single entity type (e.g. all Claims or all Memories)
      const cols = Math.min(3, Math.max(1, Math.ceil(Math.sqrt(filteredNodes.length))));
      flowNodes = filteredNodes.map((n, idx) => {
        const col = idx % cols;
        const row = Math.floor(idx / cols);
        const x = 80 + col * 300;
        const y = 80 + row * 150;

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
    } else {
      // Natural left-to-right DAG layering for full system view or disputes
      const layerOrder: Record<string, number> = {
        Project: 0,
        Run: 1,
        Agent: 2,
        Task: 3,
        Source: 3,
        Claim: 4,
        Memory: 5,
        Decision: 6,
      };

      // Compact active layers so there are no empty gaps
      const activeLayers = Array.from(new Set(filteredNodes.map((n) => layerOrder[n.label] ?? 3))).sort((a, b) => a - b);
      const layerColMap = new Map(activeLayers.map((l, idx) => [l, idx]));
      const layerCounts: Record<number, number> = {};

      flowNodes = filteredNodes.map((n) => {
        const layer = layerOrder[n.label] ?? 3;
        const col = layerColMap.get(layer) ?? 0;
        const indexInLayer = layerCounts[layer] || 0;
        layerCounts[layer] = indexInLayer + 1;

        const x = 60 + col * 340;
        const y = 60 + indexInLayer * 150;

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
    }

    // 3. Edges with styled arrows
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
            stroke: isContradiction ? '#f43f5e' : isSupport ? '#10b981' : '#6366f1',
            strokeWidth: isContradiction ? 2.5 : isSupport ? 2 : 1.5,
            strokeDasharray: isContradiction ? '5 5' : undefined,
          },
          labelStyle: {
            fill: isContradiction ? '#fb7185' : isSupport ? '#34d399' : '#818cf8',
            fontWeight: 700,
            fontSize: 10,
          },
          labelBgStyle: {
            fill: '#090d16',
            fillOpacity: 0.9,
          },
          markerEnd: {
            type: MarkerType.ArrowClosed,
            color: isContradiction ? '#f43f5e' : isSupport ? '#10b981' : '#6366f1',
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
      {/* Top Filter & Toolbar */}
      <div className="px-5 py-3 border-b border-slate-800 bg-slate-900/70 backdrop-blur flex flex-wrap items-center justify-between gap-3 z-10">
        <div className="flex items-center space-x-2">
          <Network className="w-5 h-5 text-indigo-400" />
          <span className="font-semibold text-sm text-slate-100">FalkorDB Knowledge Graph</span>
          <span className="text-xs text-slate-400 font-mono bg-slate-800/60 px-2 py-0.5 rounded border border-slate-700/60">
            {nodes.length} nodes • {edges.length} edges
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
                    ? 'bg-indigo-600 text-white font-semibold shadow'
                    : 'text-slate-400 hover:text-slate-200'
                }`}
              >
                {opt}
              </button>
            ))}
          </div>

          {/* Contradictions Only Toggle */}
          <button
            onClick={() => setDisputesOnly(!disputesOnly)}
            className={`flex items-center space-x-1.5 px-3 py-1.5 rounded-lg border text-xs font-semibold transition ${
              disputesOnly
                ? 'bg-rose-500/20 text-rose-300 border-rose-500/50 shadow-lg shadow-rose-500/10'
                : 'bg-slate-900 text-slate-400 border-slate-800 hover:text-rose-400'
            }`}
          >
            <AlertTriangle className={`w-3.5 h-3.5 ${disputesOnly ? 'text-rose-400 animate-pulse' : ''}`} />
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

      {/* React Flow Provider Wrapper */}
      <ReactFlowProvider>
        <FlowCanvas
          nodes={nodes}
          edges={edges}
          onNodesChange={onNodesChange}
          onEdgesChange={onEdgesChange}
          onNodeClick={onNodeClick}
          graphData={graphData}
          selectedNode={selectedNode}
          setSelectedNode={setSelectedNode}
          filterLabel={filterLabel}
          disputesOnly={disputesOnly}
        />
      </ReactFlowProvider>
    </div>
  );
};
