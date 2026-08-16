/**
 * VeritasGraph Enterprise — HydraDB Ontology Schema Definitions
 * Track 01: Enterprise Context / Fact-Checking Claim Ontology
 */

export const NODE_TYPES = {
  CLAIM: {
    label: 'Claim',
    color: '#8b5cf6', // Violet
    icon: 'FileText',
    description: 'Corporate assertion, ESG declaration, or financial metric statement'
  },
  ENTITY: {
    label: 'Entity',
    color: '#3b82f6', // Blue
    icon: 'Building2',
    description: 'Corporation, division, vendor, or regulatory body'
  },
  EVIDENCE: {
    label: 'Evidence',
    color: '#10b981', // Emerald
    icon: 'ShieldCheck',
    description: 'Third-party audit data, sensor logs, satellite measurement, or invoice'
  },
  SOURCE: {
    label: 'Source',
    color: '#f59e0b', // Amber
    icon: 'Globe',
    description: 'Root publishing authority, SEC filing, EPA registry, or whistle-blower document'
  },
  AUDIT_REPORT: {
    label: 'AuditReport',
    color: '#ec4899', // Pink
    icon: 'ClipboardCheck',
    description: 'Independent verification or compliance assessment report'
  },
  METRIC: {
    label: 'Metric',
    color: '#06b6d4', // Cyan
    icon: 'BarChart3',
    description: 'Quantifiable KPI measurement (e.g. Scope 1 CO2, Revenue $M)'
  }
};

export const RELATIONSHIP_TYPES = {
  SUPPORTS: {
    label: 'SUPPORTS',
    color: '#10b981',
    description: 'Target node provides supporting evidence or corroboration'
  },
  CONTRADICTS: {
    label: 'CONTRADICTS',
    color: '#ef4444',
    description: 'Direct factual contradiction or logical incompatibility'
  },
  CITES: {
    label: 'CITES',
    color: '#6366f1',
    description: 'Direct citation or reference to a source document'
  },
  REFUTES: {
    label: 'REFUTES',
    color: '#f97316',
    description: 'Official rebuttal or factual counter-evidence'
  },
  VERIFIED_BY: {
    label: 'VERIFIED_BY',
    color: '#14b8a6',
    description: 'Validation by accredited third-party auditor'
  },
  SUPERSEDES: {
    label: 'SUPERSEDES',
    color: '#a855f7',
    description: 'Temporal revision superseding prior statement'
  },
  ISSUED_BY: {
    label: 'ISSUED_BY',
    color: '#64748b',
    description: 'Entity authorship or issuance relation'
  }
};
