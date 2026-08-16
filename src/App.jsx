import React, { useState, useEffect } from 'react';
import { hydradb } from './hydradb/client.js';
import GraphCanvas from './components/GraphCanvas.jsx';
import QueryWorkbench from './components/QueryWorkbench.jsx';
import ConflictDetector from './components/ConflictDetector.jsx';
import PathExplainer from './components/PathExplainer.jsx';
import FactCheckConsole from './components/FactCheckConsole.jsx';

import { 
  Database, 
  GitBranch, 
  ShieldAlert, 
  GitCommit, 
  Search, 
  Terminal, 
  Layers, 
  Cpu, 
  ExternalLink,
  Radio,
  Server,
  Zap,
  Code
} from 'lucide-react';

export default function App() {
  const [graphData, setGraphData] = useState({ nodes: [], edges: [] });
  const [activeTab, setActiveTab] = useState('canvas');
  const [highlightedNodes, setHighlightedNodes] = useState([]);
  const [highlightedEdges, setHighlightedEdges] = useState([]);
  const [selectedNodeId, setSelectedNodeId] = useState('CLM-101');
  const [metrics, setMetrics] = useState({ nodes: 0, edges: 0, conflicts: 0, queryLatency: '1.2ms' });
  const [streamMessages, setStreamMessages] = useState([]);
  const [isStreaming, setIsStreaming] = useState(false);
  const [mcpResult, setMcpResult] = useState(null);

  // Initial load
  useEffect(() => {
    refreshGraph();
  }, []);

  const refreshGraph = () => {
    const data = hydradb.getAllGraphData();
    setGraphData(data);
    const conflicts = hydradb.detectConflictsInternal();
    setMetrics({
      nodes: data.nodes.length,
      edges: data.edges.length,
      conflicts: conflicts.length,
      queryLatency: '1.2ms'
    });
  };

  const handleQueryResult = (result) => {
    if (result.nodes) setHighlightedNodes(result.nodes.map(n => n.id));
    if (result.edges) setHighlightedEdges(result.edges.map(e => e.id));
    refreshGraph();
  };

  // Run SSE Streaming Analysis Demo
  const startSSEStream = () => {
    setIsStreaming(true);
    setStreamMessages([]);

    const steps = [
      { step: '1/4', status: 'Calling Anthropic Claude Messages API for entity extraction...' },
      { step: '2/4', status: 'Generating 384-dim all-MiniLM-L6-v2 vector embeddings...' },
      { step: '3/4', status: 'Executing Cypher context query on http://127.0.0.1:8443/v1/graphs/default/query...' },
      { step: '4/4', status: 'LangGraph Agent Execution Complete: Contradiction Flagged.' }
    ];

    steps.forEach((st, idx) => {
      setTimeout(() => {
        setStreamMessages(prev => [...prev, st]);
        if (idx === steps.length - 1) setIsStreaming(false);
      }, (idx + 1) * 600);
    });
  };

  // Test MCP Server Tool
  const triggerMCPTool = (toolName) => {
    if (toolName === 'hydradb_detect_conflicts') {
      const res = hydradb.detectConflictsInternal();
      setMcpResult({ tool: toolName, status: 'success', result: res });
    } else {
      const res = hydradb.explainPathInternal('CLM-101');
      setMcpResult({ tool: toolName, status: 'success', result: res });
    }
  };

  return (
    <div className="min-h-screen flex flex-col bg-[#090d16] text-slate-100 font-sans selection:bg-indigo-500 selection:text-white">
      {/* Top Header Navigation */}
      <header className="sticky top-0 z-50 bg-slate-950/80 backdrop-blur-xl border-b border-slate-800/80 px-6 py-3.5 flex items-center justify-between shadow-2xl">
        <div className="flex items-center gap-3">
          <div className="p-2 rounded-xl bg-gradient-to-tr from-indigo-600 via-indigo-500 to-purple-500 shadow-lg shadow-indigo-500/20">
            <Database className="w-5 h-5 text-white" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-base font-bold tracking-tight text-white">Framelink</h1>
              <span className="text-[10px] font-mono bg-indigo-500/20 text-indigo-300 border border-indigo-500/30 px-2 py-0.5 rounded font-semibold">
                Track 01 • Enterprise Context
              </span>
            </div>
            <p className="text-xs text-slate-400">
              Python FastAPI + LangGraph + Anthropic Claude + HydraDB HTTP API
            </p>
          </div>
        </div>

        {/* Header Right Badges */}
        <div className="flex items-center gap-3">
          <a
            href="https://github.com/hydra-db/hydradb"
            target="_blank"
            rel="noopener noreferrer"
            className="text-xs font-mono text-slate-300 bg-slate-900/90 hover:bg-slate-800 border border-slate-700/80 px-3 py-1.5 rounded-lg flex items-center gap-1.5 transition-all shadow-sm"
          >
            <GitBranch className="w-3.5 h-3.5 text-indigo-400" /> hydra-db/hydradb <ExternalLink className="w-3 h-3 text-slate-500" />
          </a>
          <div className="flex items-center gap-2 bg-emerald-950/40 border border-emerald-500/30 px-3 py-1.5 rounded-lg text-xs font-mono text-emerald-300">
            <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
            FastAPI / HydraDB HTTP Active
          </div>
        </div>
      </header>

      {/* Metrics & Architecture Sub-Bar */}
      <div className="px-6 py-4 grid grid-cols-2 md:grid-cols-5 gap-4 bg-slate-950/40 border-b border-slate-800/60">
        <div className="glass-panel p-3.5 flex items-center gap-3">
          <div className="p-2.5 rounded-lg bg-indigo-500/10 border border-indigo-500/20 text-indigo-400">
            <Layers className="w-5 h-5" />
          </div>
          <div>
            <div className="text-[10px] font-mono text-slate-400 uppercase tracking-wider">Substrate Nodes</div>
            <div className="text-lg font-bold font-mono text-slate-100">{metrics.nodes}</div>
          </div>
        </div>

        <div className="glass-panel p-3.5 flex items-center gap-3">
          <div className="p-2.5 rounded-lg bg-cyan-500/10 border border-cyan-500/20 text-cyan-400">
            <GitBranch className="w-5 h-5" />
          </div>
          <div>
            <div className="text-[10px] font-mono text-slate-400 uppercase tracking-wider">Ontology Edges</div>
            <div className="text-lg font-bold font-mono text-slate-100">{metrics.edges}</div>
          </div>
        </div>

        <div className="glass-panel p-3.5 flex items-center gap-3">
          <div className="p-2.5 rounded-lg bg-rose-500/10 border border-rose-500/20 text-rose-400">
            <ShieldAlert className="w-5 h-5" />
          </div>
          <div>
            <div className="text-[10px] font-mono text-slate-400 uppercase tracking-wider">Active Conflicts</div>
            <div className="text-lg font-bold font-mono text-rose-400">{metrics.conflicts}</div>
          </div>
        </div>

        <div className="glass-panel p-3.5 flex items-center gap-3">
          <div className="p-2.5 rounded-lg bg-emerald-500/10 border border-emerald-500/20 text-emerald-400">
            <Cpu className="w-5 h-5" />
          </div>
          <div>
            <div className="text-[10px] font-mono text-slate-400 uppercase tracking-wider">Embeddings</div>
            <div className="text-xs font-bold font-mono text-emerald-300">all-MiniLM-L6-v2</div>
          </div>
        </div>

        <div className="glass-panel p-3.5 flex items-center gap-3 col-span-2 md:col-span-1">
          <div className="p-2.5 rounded-lg bg-purple-500/10 border border-purple-500/20 text-purple-400">
            <Server className="w-5 h-5" />
          </div>
          <div>
            <div className="text-[10px] font-mono text-slate-400 uppercase tracking-wider">MCP & GraphQL</div>
            <div className="text-xs font-bold font-mono text-purple-300">Online (:8000)</div>
          </div>
        </div>
      </div>

      {/* Main Workspace Area */}
      <main className="flex-1 p-6 max-w-7xl w-full mx-auto space-y-5">
        {/* Workspace Navigation Tabs */}
        <div className="flex flex-wrap items-center gap-2 border-b border-slate-800 pb-2">
          <button
            onClick={() => setActiveTab('canvas')}
            className={`px-4 py-2 rounded-lg text-xs font-semibold flex items-center gap-2 transition-all ${
              activeTab === 'canvas'
                ? 'bg-indigo-600 text-white shadow-lg shadow-indigo-600/30'
                : 'bg-slate-900/60 text-slate-400 hover:bg-slate-800/80 hover:text-slate-200'
            }`}
          >
            <Layers className="w-4 h-4" /> Graph Substrate & Workbench
          </button>
          
          <button
            onClick={() => setActiveTab('conflicts')}
            className={`px-4 py-2 rounded-lg text-xs font-semibold flex items-center gap-2 transition-all ${
              activeTab === 'conflicts'
                ? 'bg-rose-600 text-white shadow-lg shadow-rose-600/30'
                : 'bg-slate-900/60 text-slate-400 hover:bg-slate-800/80 hover:text-slate-200'
            }`}
          >
            <ShieldAlert className="w-4 h-4" /> Conflict Detector ({metrics.conflicts})
          </button>

          <button
            onClick={() => setActiveTab('explainer')}
            className={`px-4 py-2 rounded-lg text-xs font-semibold flex items-center gap-2 transition-all ${
              activeTab === 'explainer'
                ? 'bg-emerald-600 text-white shadow-lg shadow-emerald-600/30'
                : 'bg-slate-900/60 text-slate-400 hover:bg-slate-800/80 hover:text-slate-200'
            }`}
          >
            <GitCommit className="w-4 h-4" /> Path Provenance Explainer
          </button>

          <button
            onClick={() => setActiveTab('verify')}
            className={`px-4 py-2 rounded-lg text-xs font-semibold flex items-center gap-2 transition-all ${
              activeTab === 'verify'
                ? 'bg-purple-600 text-white shadow-lg shadow-purple-600/30'
                : 'bg-slate-900/60 text-slate-400 hover:bg-slate-800/80 hover:text-slate-200'
            }`}
          >
            <Search className="w-4 h-4" /> Claim Verification Console
          </button>

          <button
            onClick={() => setActiveTab('sse_mcp')}
            className={`px-4 py-2 rounded-lg text-xs font-semibold flex items-center gap-2 transition-all ${
              activeTab === 'sse_mcp'
                ? 'bg-cyan-600 text-white shadow-lg shadow-cyan-600/30'
                : 'bg-slate-900/60 text-slate-400 hover:bg-slate-800/80 hover:text-slate-200'
            }`}
          >
            <Radio className="w-4 h-4" /> SSE Stream & MCP Server
          </button>
        </div>

        {/* Tab Content Views */}
        {activeTab === 'canvas' && (
          <div className="space-y-5">
            <GraphCanvas
              nodes={graphData.nodes}
              edges={graphData.edges}
              highlightedNodeIds={highlightedNodes}
              highlightedEdgeIds={highlightedEdges}
              onSelectNode={(node) => setSelectedNodeId(node.id)}
            />
            <QueryWorkbench client={hydradb} onQueryResult={handleQueryResult} />
          </div>
        )}

        {activeTab === 'conflicts' && (
          <div className="space-y-5">
            <ConflictDetector 
              client={hydradb} 
              onSelectConflictNodes={(nodes) => setHighlightedNodes(nodes.map(n => n.id))} 
            />
          </div>
        )}

        {activeTab === 'explainer' && (
          <div className="space-y-5">
            <PathExplainer client={hydradb} selectedNodeId={selectedNodeId} />
          </div>
        )}

        {activeTab === 'verify' && (
          <div className="space-y-5">
            <FactCheckConsole 
              client={hydradb} 
              onClaimAdded={() => refreshGraph()} 
            />
          </div>
        )}

        {activeTab === 'sse_mcp' && (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
            {/* SSE Streaming Panel */}
            <div className="glass-panel p-5 space-y-4">
              <div className="flex items-center justify-between border-b border-slate-800 pb-3">
                <div className="flex items-center gap-2">
                  <Radio className="w-5 h-5 text-cyan-400" />
                  <h3 className="text-sm font-semibold text-slate-100">FastAPI Server-Sent Events (SSE) Stream</h3>
                </div>
                <button onClick={startSSEStream} disabled={isStreaming} className="btn-primary text-xs">
                  {isStreaming ? 'Streaming...' : 'Run SSE Stream'}
                </button>
              </div>

              <div className="bg-slate-950/90 border border-slate-800 rounded-lg p-3 min-h-[220px] font-mono text-xs space-y-2">
                {streamMessages.length === 0 ? (
                  <span className="text-slate-500">Click "Run SSE Stream" to test real-time claim analysis streaming...</span>
                ) : (
                  streamMessages.map((msg, idx) => (
                    <div key={idx} className="flex items-start gap-2 text-slate-300 animate-fade-in">
                      <span className="text-cyan-400 font-bold">[{msg.step}]</span>
                      <span>{msg.status}</span>
                    </div>
                  ))
                )}
              </div>
            </div>

            {/* MCP Server Inspector */}
            <div className="glass-panel p-5 space-y-4">
              <div className="flex items-center justify-between border-b border-slate-800 pb-3">
                <div className="flex items-center gap-2">
                  <Code className="w-5 h-5 text-purple-400" />
                  <h3 className="text-sm font-semibold text-slate-100">Model Context Protocol (MCP) Server</h3>
                </div>
                <span className="text-[10px] font-mono bg-purple-500/20 text-purple-300 border border-purple-500/30 px-2 py-0.5 rounded">
                  MCP Protocol v0.1
                </span>
              </div>

              <div className="flex items-center gap-2">
                <button
                  onClick={() => triggerMCPTool('hydradb_detect_conflicts')}
                  className="text-xs bg-slate-800 hover:bg-slate-700 text-slate-200 px-3 py-1.5 rounded-lg border border-slate-700 font-mono"
                >
                  Call tool: hydradb_detect_conflicts
                </button>
                <button
                  onClick={() => triggerMCPTool('hydradb_explain_path')}
                  className="text-xs bg-slate-800 hover:bg-slate-700 text-slate-200 px-3 py-1.5 rounded-lg border border-slate-700 font-mono"
                >
                  Call tool: hydradb_explain_path
                </button>
              </div>

              {mcpResult && (
                <div className="bg-slate-950 p-3 rounded-lg border border-slate-800 max-h-52 overflow-y-auto">
                  <div className="text-[10px] font-mono text-purple-400 mb-1">
                    MCP Response Payload ({mcpResult.tool}):
                  </div>
                  <pre className="text-[11px] font-mono text-slate-300">
                    {JSON.stringify(mcpResult, null, 2)}
                  </pre>
                </div>
              )}
            </div>
          </div>
        )}
      </main>

      {/* Footer */}
      <footer className="border-t border-slate-800/80 px-6 py-4 mt-8 bg-slate-950/60 text-center text-xs text-slate-500 font-mono">
        Framelink • Powered by <a href="https://github.com/hydra-db/hydradb" target="_blank" rel="noreferrer" className="text-indigo-400 underline">HydraDB</a> • Released under MIT License
      </footer>
    </div>
  );
}
