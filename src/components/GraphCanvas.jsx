import React, { useRef, useEffect, useState } from 'react';
import { NODE_TYPES, RELATIONSHIP_TYPES } from '../hydradb/ontology.js';
import { ZoomIn, ZoomOut, RotateCcw, Info, AlertTriangle, ShieldCheck, Zap } from 'lucide-react';

export default function GraphCanvas({ nodes, edges, highlightedNodeIds = [], highlightedEdgeIds = [], onSelectNode }) {
  const canvasRef = useRef(null);
  const [zoom, setZoom] = useState(1);
  const [offset, setOffset] = useState({ x: 0, y: 0 });
  const [isDragging, setIsDragging] = useState(false);
  const [dragStart, setDragStart] = useState({ x: 0, y: 0 });
  const [selectedNode, setSelectedNode] = useState(null);
  const [draggedNode, setDraggedNode] = useState(null);

  // Position nodes in a clean force layout initial state
  const nodePositionsRef = useRef(new Map());

  useEffect(() => {
    const width = 800;
    const height = 600;
    const nodeMap = nodePositionsRef.current;

    // Initialize positions if not already initialized
    nodes.forEach((node, i) => {
      if (!nodeMap.has(node.id)) {
        const angle = (i / nodes.length) * 2 * Math.PI;
        const radius = 180 + (i % 3) * 60;
        nodeMap.set(node.id, {
          x: width / 2 + Math.cos(angle) * radius,
          y: height / 2 + Math.sin(angle) * radius,
          vx: 0,
          vy: 0
        });
      }
    });
  }, [nodes]);

  // Main Render Loop
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    let animationFrameId;

    const render = () => {
      ctx.clearRect(0, 0, canvas.width, canvas.height);
      ctx.save();
      
      // Apply pan & zoom
      ctx.translate(offset.x, offset.y);
      ctx.scale(zoom, zoom);

      const positions = nodePositionsRef.current;

      // 1. Draw Edges
      edges.forEach(edge => {
        const sourcePos = positions.get(edge.source);
        const targetPos = positions.get(edge.target);
        if (!sourcePos || !targetPos) return;

        const relType = RELATIONSHIP_TYPES[edge.type] || { color: '#94a3b8' };
        const isHighlighted = highlightedEdgeIds.includes(edge.id);
        const isConflict = edge.type === 'CONTRADICTS' || edge.type === 'REFUTES';

        ctx.beginPath();
        ctx.moveTo(sourcePos.x, sourcePos.y);
        ctx.lineTo(targetPos.x, targetPos.y);

        ctx.strokeStyle = isConflict ? '#ef4444' : isHighlighted ? '#6366f1' : relType.color;
        ctx.lineWidth = isConflict ? 3 : isHighlighted ? 3 : 1.5;
        if (isConflict) ctx.setLineDash([6, 4]);
        else ctx.setLineDash([]);

        ctx.stroke();

        // Draw Edge Label
        const midX = (sourcePos.x + targetPos.x) / 2;
        const midY = (sourcePos.y + targetPos.y) / 2;
        ctx.fillStyle = '#0f172a';
        ctx.fillRect(midX - 35, midY - 10, 70, 18);
        ctx.strokeStyle = isConflict ? '#ef4444' : '#334155';
        ctx.lineWidth = 1;
        ctx.strokeRect(midX - 35, midY - 10, 70, 18);

        ctx.fillStyle = isConflict ? '#fca5a5' : '#cbd5e1';
        ctx.font = '10px JetBrains Mono';
        ctx.textAlign = 'center';
        ctx.textBaseline = 'middle';
        ctx.fillText(edge.type, midX, midY);
      });

      // 2. Draw Nodes
      nodes.forEach(node => {
        const pos = positions.get(node.id);
        if (!pos) return;

        const ontology = NODE_TYPES[node.label] || { color: '#64748b' };
        const isSelected = selectedNode?.id === node.id;
        const isHighlighted = highlightedNodeIds.includes(node.id);
        const isContradicted = node.status === 'CONTRADICTED' || node.status === 'REFUTES';

        // Draw node pulse if contradicted or highlighted
        if (isContradicted || isHighlighted) {
          ctx.beginPath();
          ctx.arc(pos.x, pos.y, 28, 0, 2 * Math.PI);
          ctx.fillStyle = isContradicted ? 'rgba(239, 68, 68, 0.25)' : 'rgba(99, 102, 241, 0.25)';
          ctx.fill();
        }

        // Main circle
        ctx.beginPath();
        ctx.arc(pos.x, pos.y, 20, 0, 2 * Math.PI);
        ctx.fillStyle = ontology.color;
        ctx.fill();
        ctx.strokeStyle = isSelected ? '#ffffff' : isHighlighted ? '#6366f1' : 'rgba(255,255,255,0.3)';
        ctx.lineWidth = isSelected ? 3 : 2;
        ctx.stroke();

        // Node ID label
        ctx.fillStyle = '#ffffff';
        ctx.font = 'bold 11px Inter';
        ctx.textAlign = 'center';
        ctx.textBaseline = 'middle';
        ctx.fillText(node.id, pos.x, pos.y);

        // Subtitle text under node
        ctx.fillStyle = '#94a3b8';
        ctx.font = '11px Inter';
        const displayTitle = (node.title || node.name || '').substring(0, 18);
        ctx.fillText(displayTitle, pos.x, pos.y + 32);
      });

      ctx.restore();
      animationFrameId = requestAnimationFrame(render);
    };

    render();
    return () => cancelAnimationFrame(animationFrameId);
  }, [nodes, edges, zoom, offset, selectedNode, highlightedNodeIds, highlightedEdgeIds]);

  // Canvas Mouse Interactions (Pan, Zoom, Select)
  const handleMouseDown = (e) => {
    const rect = canvasRef.current.getBoundingClientRect();
    const mouseX = (e.clientX - rect.left - offset.x) / zoom;
    const mouseY = (e.clientY - rect.top - offset.y) / zoom;

    const positions = nodePositionsRef.current;
    let clickedNode = null;

    nodes.forEach(node => {
      const pos = positions.get(node.id);
      if (pos) {
        const dist = Math.hypot(pos.x - mouseX, pos.y - mouseY);
        if (dist <= 22) clickedNode = node;
      }
    });

    if (clickedNode) {
      setSelectedNode(clickedNode);
      setDraggedNode(clickedNode.id);
      if (onSelectNode) onSelectNode(clickedNode);
    } else {
      setIsDragging(true);
      setDragStart({ x: e.clientX - offset.x, y: e.clientY - offset.y });
    }
  };

  const handleMouseMove = (e) => {
    if (draggedNode) {
      const rect = canvasRef.current.getBoundingClientRect();
      const mouseX = (e.clientX - rect.left - offset.x) / zoom;
      const mouseY = (e.clientY - rect.top - offset.y) / zoom;
      const pos = nodePositionsRef.current.get(draggedNode);
      if (pos) {
        pos.x = mouseX;
        pos.y = mouseY;
      }
    } else if (isDragging) {
      setOffset({
        x: e.clientX - dragStart.x,
        y: e.clientY - dragStart.y
      });
    }
  };

  const handleMouseUp = () => {
    setIsDragging(false);
    setDraggedNode(null);
  };

  const handleWheel = (e) => {
    e.preventDefault();
    const zoomFactor = e.deltaY < 0 ? 1.1 : 0.9;
    setZoom(prev => Math.min(Math.max(prev * zoomFactor, 0.4), 3.0));
  };

  const resetView = () => {
    setZoom(1);
    setOffset({ x: 0, y: 0 });
  };

  return (
    <div className="relative w-full h-[600px] glass-panel overflow-hidden flex flex-col">
      {/* Top Toolbar */}
      <div className="absolute top-4 left-4 right-4 z-10 flex items-center justify-between pointer-events-none">
        <div className="flex items-center gap-2 bg-slate-900/80 backdrop-blur-md px-3 py-1.5 rounded-lg border border-slate-700/60 pointer-events-auto">
          <Zap className="w-4 h-4 text-indigo-400" />
          <span className="text-xs font-semibold text-slate-200">HydraDB Canvas Substrate</span>
          <span className="text-[10px] bg-indigo-500/20 text-indigo-300 px-2 py-0.5 rounded font-mono">
            {nodes.length} Nodes • {edges.length} Edges
          </span>
        </div>

        <div className="flex items-center gap-2 bg-slate-900/80 backdrop-blur-md p-1 rounded-lg border border-slate-700/60 pointer-events-auto">
          <button 
            onClick={() => setZoom(z => Math.min(z * 1.2, 3))}
            className="p-1.5 hover:bg-slate-800 rounded text-slate-300 transition-colors"
            title="Zoom In"
          >
            <ZoomIn className="w-4 h-4" />
          </button>
          <button 
            onClick={() => setZoom(z => Math.max(z / 1.2, 0.4))}
            className="p-1.5 hover:bg-slate-800 rounded text-slate-300 transition-colors"
            title="Zoom Out"
          >
            <ZoomOut className="w-4 h-4" />
          </button>
          <button 
            onClick={resetView}
            className="p-1.5 hover:bg-slate-800 rounded text-slate-300 transition-colors"
            title="Reset Pan & Zoom"
          >
            <RotateCcw className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Canvas */}
      <canvas
        ref={canvasRef}
        width={900}
        height={600}
        onMouseDown={handleMouseDown}
        onMouseMove={handleMouseMove}
        onMouseUp={handleMouseUp}
        onWheel={handleWheel}
        className="w-full h-full cursor-grab active:cursor-grabbing"
      />

      {/* Bottom Legend */}
      <div className="absolute bottom-4 left-4 z-10 flex items-center gap-3 bg-slate-900/80 backdrop-blur-md px-3 py-2 rounded-lg border border-slate-700/60 text-xs">
        <span className="text-slate-400 font-medium">Ontology:</span>
        {Object.entries(NODE_TYPES).map(([key, item]) => (
          <div key={key} className="flex items-center gap-1.5">
            <span className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: item.color }} />
            <span className="text-slate-300 text-[11px]">{item.label}</span>
          </div>
        ))}
      </div>

      {/* Node Inspector Drawer */}
      {selectedNode && (
        <div className="absolute bottom-4 right-4 z-20 w-80 glass-panel p-4 border border-slate-700/80 shadow-2xl animate-fade-in">
          <div className="flex items-center justify-between mb-2">
            <div className="flex items-center gap-2">
              <span 
                className="w-3 h-3 rounded-full" 
                style={{ backgroundColor: NODE_TYPES[selectedNode.label]?.color || '#6366f1' }}
              />
              <span className="text-xs font-mono font-bold text-slate-400">{selectedNode.id}</span>
              <span className="text-xs bg-slate-800 text-slate-300 px-2 py-0.5 rounded font-semibold">
                {selectedNode.label}
              </span>
            </div>
            <button 
              onClick={() => setSelectedNode(null)}
              className="text-slate-400 hover:text-white text-sm"
            >
              ✕
            </button>
          </div>

          <h4 className="text-sm font-semibold text-slate-100 mb-1">
            {selectedNode.title || selectedNode.name}
          </h4>
          <p className="text-xs text-slate-400 mb-3 leading-relaxed">
            {selectedNode.content || selectedNode.summary || selectedNode.description || 'No detailed content provided.'}
          </p>

          <div className="space-y-1.5 text-xs text-slate-300 border-t border-slate-800 pt-2 font-mono">
            {selectedNode.confidenceScore !== undefined && (
              <div className="flex justify-between">
                <span className="text-slate-400">Confidence Score:</span>
                <span className={selectedNode.confidenceScore > 0.7 ? 'text-emerald-400' : 'text-rose-400'}>
                  {(selectedNode.confidenceScore * 100).toFixed(0)}%
                </span>
              </div>
            )}
            {selectedNode.status && (
              <div className="flex justify-between">
                <span className="text-slate-400">Status:</span>
                <span className="text-indigo-400 font-bold">{selectedNode.status}</span>
              </div>
            )}
            {selectedNode.publisher && (
              <div className="flex justify-between">
                <span className="text-slate-400">Publisher:</span>
                <span>{selectedNode.publisher}</span>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
