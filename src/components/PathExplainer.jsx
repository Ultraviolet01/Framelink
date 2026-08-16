import React, { useState, useEffect } from 'react';
import { GitCommit, ArrowRight, ShieldCheck, HelpCircle, FileText, CheckCircle2 } from 'lucide-react';
import { NODE_TYPES } from '../hydradb/ontology.js';

export default function PathExplainer({ client, selectedNodeId = 'CLM-101' }) {
  const [targetClaimId, setTargetClaimId] = useState(selectedNodeId);
  const [explanationData, setExplanationData] = useState(null);
  const [isCalculating, setIsCalculating] = useState(false);

  const calculateExplanation = async (claimId = targetClaimId) => {
    setIsCalculating(true);
    try {
      const cypherQuery = `MATCH p = shortestPath((c:Claim {id: '${claimId}'})-[*..6]-(s:Source)) RETURN p`;
      const res = await client.executeCypher(cypherQuery);
      setExplanationData(res);
    } catch (err) {
      console.error('Path explanation error:', err);
    } finally {
      setIsCalculating(false);
    }
  };

  useEffect(() => {
    calculateExplanation(selectedNodeId);
  }, [selectedNodeId]);

  return (
    <div className="w-full glass-panel p-5 space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between border-b border-slate-800 pb-3">
        <div className="flex items-center gap-2">
          <GitCommit className="w-5 h-5 text-emerald-400" />
          <div>
            <h3 className="text-sm font-semibold text-slate-100">HydraDB Graph Path Explainer & Provenance</h3>
            <p className="text-xs text-slate-400">
              Generates step-by-step reasoning chains from claims back to ground-truth sources
            </p>
          </div>
        </div>

        {/* Claim Selector */}
        <div className="flex items-center gap-2">
          <select
            value={targetClaimId}
            onChange={(e) => {
              setTargetClaimId(e.target.value);
              calculateExplanation(e.target.value);
            }}
            className="bg-slate-900 border border-slate-700 text-xs font-mono text-slate-200 px-3 py-1.5 rounded-lg focus:outline-none focus:border-indigo-500"
          >
            <option value="CLM-101">CLM-101 (Acme Net-Zero)</option>
            <option value="CLM-102">CLM-102 (OmniTech Revenue)</option>
            <option value="CLM-103">CLM-103 (BioHealth FDA API)</option>
          </select>
        </div>
      </div>

      {/* Path Visual Breakdown */}
      {explanationData && explanationData.nodes.length > 0 && (
        <div className="space-y-4">
          {/* Path Steps Horizontal Chain */}
          <div className="bg-slate-950/80 p-4 rounded-xl border border-slate-800 overflow-x-auto">
            <div className="text-xs font-mono text-slate-400 mb-3 flex items-center justify-between">
              <span>Path Provenance Topology ({explanationData.nodes.length} Nodes Traverse Chain):</span>
              {explanationData.explanation?.aggregatedConfidence && (
                <span className="text-emerald-400 font-bold">
                  Overall Trust Score: {(explanationData.explanation.aggregatedConfidence * 100).toFixed(1)}%
                </span>
              )}
            </div>

            <div className="flex items-center gap-3 min-w-max">
              {explanationData.nodes.map((node, idx) => {
                const ontology = NODE_TYPES[node.label] || { color: '#6366f1' };
                const nextEdge = explanationData.edges[idx];

                return (
                  <React.Fragment key={node.id}>
                    <div className="bg-slate-900 border border-slate-800 p-3 rounded-lg w-52 flex flex-col gap-1.5 shadow-lg">
                      <div className="flex items-center justify-between">
                        <span className="text-[10px] font-mono font-bold px-2 py-0.5 rounded" style={{ backgroundColor: `${ontology.color}25`, color: ontology.color }}>
                          {node.label}
                        </span>
                        <span className="text-[10px] font-mono text-slate-500">{node.id}</span>
                      </div>
                      <div className="text-xs font-semibold text-slate-200 truncate">
                        {node.title || node.name}
                      </div>
                      <div className="text-[10px] text-slate-400 flex justify-between border-t border-slate-800/80 pt-1">
                        <span>Confidence:</span>
                        <span className="text-indigo-400 font-mono">
                          {((node.confidenceScore || 0.85) * 100).toFixed(0)}%
                        </span>
                      </div>
                    </div>

                    {nextEdge && (
                      <div className="flex flex-col items-center justify-center px-1">
                        <span className="text-[10px] font-mono text-slate-500 mb-1">
                          {nextEdge.type}
                        </span>
                        <ArrowRight className="w-4 h-4 text-indigo-400" />
                      </div>
                    )}
                  </React.Fragment>
                );
              })}
            </div>
          </div>

          {/* Detailed Reasoning Text */}
          <div className="bg-slate-900/60 p-4 rounded-xl border border-slate-800">
            <h4 className="text-xs font-mono font-semibold text-slate-300 mb-2 flex items-center gap-1.5">
              <FileText className="w-3.5 h-3.5 text-indigo-400" /> HydraDB Natural Language Explanation Stream:
            </h4>
            <pre className="text-xs font-mono text-slate-300 whitespace-pre-wrap leading-relaxed bg-slate-950 p-3 rounded-lg border border-slate-800">
              {explanationData.explanation}
            </pre>
          </div>
        </div>
      )}
    </div>
  );
}
