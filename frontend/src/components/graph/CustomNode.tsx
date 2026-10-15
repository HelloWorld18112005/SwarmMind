import { memo } from 'react';
import { Handle, Position } from '@xyflow/react';
import {
  Folder,
  PlayCircle,
  Bot,
  CheckSquare,
  Brain,
  Scale,
  BookOpen,
  AlertTriangle,
  Tag,
} from 'lucide-react';

export interface CustomNodeData {
  id: string;
  label: string;
  title: string;
  properties?: Record<string, any>;
  hasContradiction?: boolean;
}

export const CustomNode = memo(({ data }: { data: CustomNodeData }) => {
  const { label, title, properties, hasContradiction } = data;

  const getStyle = () => {
    switch (label) {
      case 'Project':
        return {
          border: 'border-indigo-500/60',
          bg: 'bg-indigo-950/70',
          text: 'text-indigo-300',
          icon: <Folder className="w-3.5 h-3.5 text-indigo-400" />,
        };
      case 'Run':
        return {
          border: 'border-purple-500/60',
          bg: 'bg-purple-950/70',
          text: 'text-purple-300',
          icon: <PlayCircle className="w-3.5 h-3.5 text-purple-400" />,
        };
      case 'Agent':
        return {
          border: 'border-cyan-500/60',
          bg: 'bg-cyan-950/70',
          text: 'text-cyan-300',
          icon: <Bot className="w-3.5 h-3.5 text-cyan-400" />,
        };
      case 'Task':
        return {
          border: 'border-blue-500/60',
          bg: 'bg-blue-950/70',
          text: 'text-blue-300',
          icon: <CheckSquare className="w-3.5 h-3.5 text-blue-400" />,
        };
      case 'Memory':
        return {
          border: 'border-amber-500/60',
          bg: 'bg-amber-950/70',
          text: 'text-amber-300',
          icon: <Brain className="w-3.5 h-3.5 text-amber-400" />,
        };
      case 'Claim':
        return hasContradiction
          ? {
              border: 'border-rose-500 ring-2 ring-rose-500/50',
              bg: 'bg-rose-950/80',
              text: 'text-rose-200',
              icon: <AlertTriangle className="w-3.5 h-3.5 text-rose-400 animate-pulse" />,
            }
          : {
              border: 'border-emerald-500/60',
              bg: 'bg-emerald-950/70',
              text: 'text-emerald-300',
              icon: <Scale className="w-3.5 h-3.5 text-emerald-400" />,
            };
      case 'Source':
        return {
          border: 'border-slate-600',
          bg: 'bg-slate-900/90',
          text: 'text-slate-300',
          icon: <BookOpen className="w-3.5 h-3.5 text-slate-400" />,
        };
      default:
        return {
          border: 'border-slate-700',
          bg: 'bg-slate-900',
          text: 'text-slate-300',
          icon: <Tag className="w-3.5 h-3.5 text-slate-400" />,
        };
    }
  };

  const style = getStyle();
  const confidence = properties?.confidence !== undefined ? Math.round(Number(properties.confidence) * 100) : null;
  const role = properties?.role || properties?.assigned_role;

  return (
    <div
      className={`px-3 py-2.5 rounded-xl border ${style.border} ${style.bg} shadow-lg backdrop-blur min-w-[200px] max-w-[280px] text-xs transition-all hover:scale-105 hover:shadow-indigo-500/10 cursor-pointer`}
    >
      <Handle type="target" position={Position.Top} className="!w-2 !h-2 !bg-indigo-400 !border-slate-900" />

      <div className="flex items-center justify-between gap-1 mb-1.5">
        <div className="flex items-center gap-1.5">
          {style.icon}
          <span className={`font-semibold uppercase tracking-wider text-[10px] ${style.text}`}>
            {label}
          </span>
        </div>
        {hasContradiction && (
          <span className="px-1.5 py-0.5 rounded text-[9px] font-bold bg-rose-500/20 text-rose-400 border border-rose-500/40">
            DISPUTED
          </span>
        )}
        {confidence !== null && !hasContradiction && (
          <span className="px-1.5 py-0.5 rounded text-[9px] font-mono bg-slate-800 text-slate-300 border border-slate-700">
            {confidence}%
          </span>
        )}
      </div>

      <div className="font-medium text-slate-100 line-clamp-2 leading-snug">
        {String(title || properties?.name || properties?.id || 'Untitled Node')}
      </div>

      {role && (
        <div className="mt-1.5 pt-1 border-t border-slate-800/80 flex items-center justify-between text-[10px] text-slate-400">
          <span>Role</span>
          <span className="font-mono text-indigo-300 uppercase">{String(role)}</span>
        </div>
      )}

      <Handle type="source" position={Position.Bottom} className="!w-2 !h-2 !bg-indigo-400 !border-slate-900" />
    </div>
  );
});

CustomNode.displayName = 'CustomNode';
