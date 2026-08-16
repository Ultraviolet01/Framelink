import React, { useState, useEffect } from 'react';
import { AlertTriangle, ShieldAlert, CheckCircle2, ArrowRightLeft, Sparkles, RefreshCw } from 'lucide-react';

export default function ConflictDetector({ client, onSelectConflictNodes }) {
  const [conflicts, setConflicts] = useState([]);
  const [isDetecting, setIsDetecting] = useState(false);
  const [resolvedIds, setResolvedIds] = useState(new Set());

  const runConflictDetection = async () => {
    setIsExecuting(true);
    setIsDetecting(true);
    try {
      const cypherQuery = `MATCH (c1:Claim)-[r:CONTRADICTS|REFUTES]-(c2:Claim) RETURN c1, r, c2`;
      const res = await client.executeCypher(cypherQuery);
      setConflicts(res.conflicts || []);
    } catch (err) {
      console.error(err);
    } finally {
      setIsDetecting(false);
    }
  };

  useEffect(() => {
    runConflictDetection();
  }, []);

  const handleResolveConflict = (conflictId) => {
    setResolvedIds(prev => new Set([...prev, conflictId]));
  };

  return (
    <div className="w-full glass-panel p-5 space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between border-b border-slate-800 pb-3">
        <div className="flex items-center gap-2">
          <ShieldAlert className="w-5 h-5 text-rose-400" />
          <div>
            <h3 className="text-sm font-semibold text-slate-100">HydraDB Real-Time Conflict Detector</h3>
            <p className="text-xs text-slate-400">
              Executes directional Cypher graph contradiction queries to flag incompatible enterprise facts
            </p>
          </div>
        </div>

        <button
          onClick={runConflictDetection}
          disabled={isDetecting}
          className="btn-secondary text-xs"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${isDetecting ? 'animate-spin' : ''}`} />
          Re-Run Conflict Scan
        </button>
      </div>

      {/* Conflict List */}
      {conflicts.length === 0 ? (
        <div className="text-center py-8 text-slate-500 text-xs">
          No active contradictions detected in the current HydraDB context graph.
        </div>
      ) : (
        <div className="space-y-3">
          {conflicts.map((cnf) => {
            const isResolved = resolvedIds.has(cnf.id);
            return (
              <div 
                key={cnf.id}
                className={`p-4 rounded-xl border transition-all ${
                  isResolved 
                    ? 'bg-slate-900/40 border-slate-800 opacity-60' 
                    : 'bg-rose-950/20 border-rose-900/50 hover:border-rose-500/50'
                }`}
              >
                <div className="flex items-center justify-between mb-3">
                  <div className="flex items-center gap-2">
                    <span className={`text-[10px] font-mono px-2 py-0.5 rounded font-bold uppercase ${
                      cnf.severity === 'CRITICAL' ? 'bg-rose-500/20 text-rose-300 border border-rose-500/40' : 'bg-amber-500/20 text-amber-300 border border-amber-500/40'
                    }`}>
                      {cnf.severity} SEVERITY CONFLICT
                    </span>
                    <span className="text-xs font-mono text-slate-400">Edge: {cnf.edge.type}</span>
                  </div>

                  {!isResolved ? (
                    <button
                      onClick={() => handleResolveConflict(cnf.id)}
                      className="text-xs bg-rose-500/10 hover:bg-rose-500/20 text-rose-300 border border-rose-500/30 px-3 py-1 rounded-lg transition-colors flex items-center gap-1"
                    >
                      <CheckCircle2 className="w-3.5 h-3.5" /> Mark Resolved
                    </button>
                  ) : (
                    <span className="text-xs text-emerald-400 font-medium flex items-center gap-1">
                      <CheckCircle2 className="w-3.5 h-3.5" /> Resolved
                    </span>
                  )}
                </div>

                {/* Contradicting Nodes Comparison */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-3 mb-3">
                  {/* Source Node */}
                  <div className="bg-slate-900/80 p-3 rounded-lg border border-slate-800">
                    <div className="text-[10px] font-mono text-indigo-400 mb-1">
                      Asserted Claim [{cnf.sourceNode.id}]:
                    </div>
                    <div className="text-xs font-semibold text-slate-200 mb-1">
                      {cnf.sourceNode.title || cnf.sourceNode.name}
                    </div>
                    <p className="text-[11px] text-slate-400 leading-normal">
                      {cnf.sourceNode.content || cnf.sourceNode.summary}
                    </p>
                  </div>

                  {/* Target Node */}
                  <div className="bg-slate-900/80 p-3 rounded-lg border border-slate-800">
                    <div className="text-[10px] font-mono text-rose-400 mb-1">
                      Contradictory Fact / Evidence [{cnf.targetNode.id}]:
                    </div>
                    <div className="text-xs font-semibold text-slate-200 mb-1">
                      {cnf.targetNode.title || cnf.targetNode.name}
                    </div>
                    <p className="text-[11px] text-slate-400 leading-normal">
                      {cnf.targetNode.content || cnf.targetNode.summary}
                    </p>
                  </div>
                </div>

                {/* Discrepancy Note */}
                <div className="bg-rose-900/20 border border-rose-800/40 p-2.5 rounded-lg flex items-start gap-2 text-xs text-rose-200">
                  <AlertTriangle className="w-4 h-4 text-rose-400 shrink-0 mt-0.5" />
                  <div>
                    <strong className="font-semibold">Factual Discrepancy: </strong>
                    {cnf.discrepancy}
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
