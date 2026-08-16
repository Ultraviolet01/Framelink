import React, { useState } from 'react';
import { Terminal, Play, Clock, Code, Database, FileCode, CheckCircle } from 'lucide-react';

const PRESET_QUERIES = [
  {
    name: 'Multi-Hop Claim Traversal',
    cypher: `MATCH p = (c:Claim {id: 'CLM-101'})-[r:SUPPORTS|CITES|VERIFIED_BY*1..4]->(target)
RETURN p, c, r, target
ORDER BY length(p) ASC`
  },
  {
    name: 'Enterprise Conflict Detection',
    cypher: `MATCH (c1:Claim)-[r:CONTRADICTS]-(c2:Claim)
OPTIONAL MATCH (c1)-[:CITES]->(s1:Source)
OPTIONAL MATCH (c2)-[:CITES]->(s2:Source)
RETURN c1, r, c2, s1, s2
ORDER BY r.severity DESC`
  },
  {
    name: 'Path Explanation & Provenance',
    cypher: `MATCH p = shortestPath((c:Claim {id: 'CLM-101'})-[*..6]-(s:Source {isRoot: true}))
RETURN p, [node in nodes(p) | node.confidenceScore] AS confidence_scores`
  },
  {
    name: 'All Evidence & Audits',
    cypher: `MATCH (e:Evidence)-[r:VERIFIED_BY|CITES]->(a:AuditReport)
RETURN e, r, a`
  }
];

export default function QueryWorkbench({ client, onQueryResult }) {
  const [cypherQuery, setCypherQuery] = useState(PRESET_QUERIES[0].cypher);
  const [isExecuting, setIsExecuting] = useState(false);
  const [lastResult, setLastResult] = useState(null);
  const [queryHistory, setQueryHistory] = useState([]);

  const handleRunQuery = async (queryToRun = cypherQuery) => {
    setIsExecuting(true);
    try {
      const res = await client.executeCypher(queryToRun);
      setLastResult(res);
      setQueryHistory(prev => [res, ...prev.slice(0, 4)]);
      if (onQueryResult) onQueryResult(res);
    } catch (err) {
      console.error('Cypher Query Execution Failed:', err);
    } finally {
      setIsExecuting(false);
    }
  };

  return (
    <div className="w-full glass-panel p-5 flex flex-col gap-4">
      {/* Header */}
      <div className="flex items-center justify-between border-b border-slate-800 pb-3">
        <div className="flex items-center gap-2">
          <Terminal className="w-5 h-5 text-indigo-400" />
          <h3 className="text-sm font-semibold text-slate-100">HydraDB Cypher Query Workbench</h3>
          <span className="text-[11px] bg-slate-800 text-slate-400 px-2 py-0.5 rounded font-mono">
            Protocol: Bolt 5.4 / HTTPS API
          </span>
        </div>
        
        <button
          onClick={() => handleRunQuery()}
          disabled={isExecuting}
          className="btn-primary text-xs"
        >
          <Play className="w-3.5 h-3.5 fill-current" />
          {isExecuting ? 'Executing...' : 'Run Cypher Query'}
        </button>
      </div>

      {/* Preset Query Chips */}
      <div className="flex items-center gap-2 overflow-x-auto pb-1">
        <span className="text-xs text-slate-400 flex items-center gap-1 shrink-0 font-medium">
          <FileCode className="w-3.5 h-3.5" /> Preset Queries:
        </span>
        {PRESET_QUERIES.map((preset, idx) => (
          <button
            key={idx}
            onClick={() => {
              setCypherQuery(preset.cypher);
              handleRunQuery(preset.cypher);
            }}
            className="text-xs bg-slate-800/80 hover:bg-slate-700/80 border border-slate-700/60 text-slate-300 px-2.5 py-1 rounded-md transition-colors shrink-0 font-mono"
          >
            {preset.name}
          </button>
        ))}
      </div>

      {/* Query Editor */}
      <div className="relative">
        <textarea
          value={cypherQuery}
          onChange={(e) => setCypherQuery(e.target.value)}
          rows={4}
          className="w-full bg-slate-950/90 border border-slate-700/80 rounded-lg p-3 text-xs font-mono text-indigo-300 focus:outline-none focus:border-indigo-500/80 leading-relaxed shadow-inner"
          placeholder="Enter Cypher query (MATCH ... RETURN ...)"
        />
        <div className="absolute bottom-3 right-3 text-[10px] text-slate-500 font-mono">
          HydraDB Query Engine v2026.1
        </div>
      </div>

      {/* Results Section */}
      {lastResult && (
        <div className="mt-2 space-y-3">
          <div className="flex items-center justify-between text-xs text-slate-400 font-mono bg-slate-900/60 p-2.5 rounded-lg border border-slate-800">
            <div className="flex items-center gap-3">
              <span className="flex items-center gap-1 text-emerald-400">
                <CheckCircle className="w-3.5 h-3.5" /> Query Succeeded
              </span>
              <span>• Nodes: <strong className="text-slate-200">{lastResult.nodes.length}</strong></span>
              <span>• Edges: <strong className="text-slate-200">{lastResult.edges.length}</strong></span>
              {lastResult.conflicts.length > 0 && (
                <span className="text-rose-400">• Conflicts: <strong>{lastResult.conflicts.length}</strong></span>
              )}
            </div>
            <div className="flex items-center gap-1 text-slate-500">
              <Clock className="w-3.5 h-3.5" /> {lastResult.executionTimeMs} ms
            </div>
          </div>

          {/* Json Response Tabs / View */}
          <div className="bg-slate-950/80 rounded-lg border border-slate-800 p-3 max-h-52 overflow-y-auto">
            <div className="text-[11px] font-mono text-slate-400 mb-2 border-b border-slate-800/80 pb-1">
              Raw Bolt Response Stream:
            </div>
            <pre className="text-[11px] font-mono text-slate-300 leading-normal">
              {JSON.stringify(lastResult.rawResult, null, 2)}
            </pre>
          </div>
        </div>
      )}
    </div>
  );
}
