/**
 * Enterprise Fact-Check Claims Custom Dataset
 * Track 01: Enterprise Context / Ontology
 * Disclosed in README per Hackathon FAQ
 */

export const INITIAL_NODES = [
  // Scene 1: Acme Corp ESG Net-Zero Claim & Contradiction Chain
  {
    id: 'CLM-101',
    label: 'Claim',
    title: 'Acme Corp Net-Zero Carbon FY2025',
    content: 'Acme Corporation has achieved 100% Net-Zero carbon emissions across all global manufacturing operations in FY2025.',
    entityId: 'ENT-01',
    status: 'CONTRADICTED',
    confidenceScore: 0.28,
    date: '2025-01-15',
    category: 'ESG Compliance'
  },
  {
    id: 'ENT-01',
    label: 'Entity',
    name: 'Acme Corporation Global',
    ticker: 'ACME',
    industry: 'Heavy Industrial Manufacturing',
    jurisdiction: 'United States'
  },
  {
    id: 'EVD-201',
    label: 'Evidence',
    title: 'GreenCert Audit Certificate #8849',
    summary: 'Third-party carbon offset certificate purchased from Amazon Rainforest Preservation Fund for 150,000 MT CO2e.',
    issuer: 'GreenCert Global LLC',
    confidenceScore: 0.91,
    verified: true
  },
  {
    id: 'EVD-202',
    label: 'Evidence',
    title: 'EPA Sentinel Satellite Methane Scan #TX-99',
    summary: 'Satellite imagery and ground sensors detected 42,000 MT un-offset methane flaring at Acme West Texas Refinery during Q3-Q4 2025.',
    issuer: 'US Environmental Protection Agency',
    confidenceScore: 0.99,
    verified: true
  },
  {
    id: 'SRC-301',
    label: 'Source',
    title: 'SEC Form 10-K FY2025 Annual Disclosure',
    url: 'https://sec.gov/edgar/data/acme-10k-2025',
    publisher: 'SEC EDGAR Database',
    isRoot: true
  },
  {
    id: 'SRC-302',
    label: 'Source',
    title: 'EPA Clean Air Enforcement Public Registry',
    url: 'https://epa.gov/enforcement/cases/acme-tx-2025',
    publisher: 'US Government Data Portal',
    isRoot: true
  },
  {
    id: 'AUD-401',
    label: 'AuditReport',
    title: '2025 Independent Forensic ESG Assessment',
    auditor: 'KPMG Sustainability Services',
    rating: 'QUALIFIED (WITH EXCEPTIONS)',
    date: '2025-02-01'
  },

  // Scene 2: OmniTech Q3 Revenue Revenue Inflation Claim & Contradiction Chain
  {
    id: 'CLM-102',
    label: 'Claim',
    title: 'OmniTech Q3 Cloud Revenue 45% YoY Growth',
    content: 'OmniTech Cloud Services generated $3.2B in revenue during Q3 2025, representing 45% year-over-year organic growth.',
    entityId: 'ENT-02',
    status: 'REFUTED',
    confidenceScore: 0.15,
    date: '2025-10-20',
    category: 'Financial Disclosures'
  },
  {
    id: 'ENT-02',
    label: 'Entity',
    name: 'OmniTech Solutions Inc.',
    ticker: 'OMNI',
    industry: 'Enterprise Software & Cloud',
    jurisdiction: 'Delaware, USA'
  },
  {
    id: 'EVD-203',
    label: 'Evidence',
    title: 'Q3 Earnings Presentation Slide Deck',
    summary: 'Internal deck presented to investors listing $3.2B cloud bookings.',
    issuer: 'OmniTech Investor Relations',
    confidenceScore: 0.60,
    verified: false
  },
  {
    id: 'EVD-204',
    label: 'Evidence',
    title: 'Short-Seller Accounting Audit Report (Hindenburg)',
    summary: 'Forensic bank ledger analysis revealed $850M in round-trip transactions with undisclosed shell company distributors in Singapore.',
    issuer: 'Apex Forensic Research',
    confidenceScore: 0.94,
    verified: true
  },
  {
    id: 'SRC-303',
    label: 'Source',
    title: 'Bank of America Escrow Wire Logs Q3',
    publisher: 'Financial Intelligence Unit',
    isRoot: true
  },

  // Scene 3: BioHealth Pharma FDA Ingredient Sourcing Claim
  {
    id: 'CLM-103',
    label: 'Claim',
    title: 'BioHealth 100% FDA-Approved API Sourcing',
    content: 'All active pharmaceutical ingredients (APIs) utilized in BioHealth CardiaGuard drug are 100% sourced from cGMP FDA-inspected facilities.',
    entityId: 'ENT-03',
    status: 'PARTIALLY_VALIDATED',
    confidenceScore: 0.62,
    date: '2025-06-10',
    category: 'Regulatory Compliance'
  },
  {
    id: 'ENT-03',
    label: 'Entity',
    name: 'BioHealth Dynamics Ltd.',
    ticker: 'BHD',
    industry: 'Biopharmaceuticals',
    jurisdiction: 'United Kingdom'
  },
  {
    id: 'EVD-205',
    label: 'Evidence',
    title: 'FDA Form 483 Warning Inspection Letter #2025-492',
    summary: 'FDA inspection cited uncertified sub-tier vendor Apex Fine Chem supplying 35% of bulk active powder.',
    issuer: 'US Food and Drug Administration',
    confidenceScore: 0.98,
    verified: true
  },
  {
    id: 'MTR-501',
    label: 'Metric',
    name: 'Uncertified Ingredient Ratio',
    value: '35.4%',
    unit: 'Percentage of total API mass',
    threshold: '0.0%'
  }
];

export const INITIAL_EDGES = [
  // Scene 1 Connections
  {
    id: 'EDG-01',
    source: 'CLM-101',
    target: 'ENT-01',
    type: 'ISSUED_BY',
    properties: { timestamp: '2025-01-15' }
  },
  {
    id: 'EDG-02',
    source: 'CLM-101',
    target: 'SRC-301',
    type: 'CITES',
    properties: { section: 'Item 7 - ESG Overview' }
  },
  {
    id: 'EDG-03',
    source: 'EVD-201',
    target: 'CLM-101',
    type: 'SUPPORTS',
    properties: { weight: 0.75, note: 'Valid offset purchase document' }
  },
  {
    id: 'EDG-04',
    source: 'EVD-202',
    target: 'CLM-101',
    type: 'CONTRADICTS',
    properties: { severity: 'HIGH', discrepancy: '42,000 MT un-offset flaring emissions' }
  },
  {
    id: 'EDG-05',
    source: 'EVD-202',
    target: 'SRC-302',
    type: 'CITES',
    properties: { datasetId: 'EPA-SAT-2025' }
  },
  {
    id: 'EDG-06',
    source: 'AUD-401',
    target: 'CLM-101',
    type: 'VERIFIED_BY',
    properties: { status: 'QUALIFIED' }
  },
  {
    id: 'EDG-07',
    source: 'AUD-401',
    target: 'EVD-202',
    type: 'CITES',
    properties: { weight: 0.95 }
  },

  // Scene 2 Connections
  {
    id: 'EDG-08',
    source: 'CLM-102',
    target: 'ENT-02',
    type: 'ISSUED_BY',
    properties: { timestamp: '2025-10-20' }
  },
  {
    id: 'EDG-09',
    source: 'EVD-203',
    target: 'CLM-102',
    type: 'SUPPORTS',
    properties: { weight: 0.40, note: 'Self-reported internal deck' }
  },
  {
    id: 'EDG-10',
    source: 'EVD-204',
    target: 'CLM-102',
    type: 'CONTRADICTS',
    properties: { severity: 'CRITICAL', discrepancy: '$850M round-trip fake revenue' }
  },
  {
    id: 'EDG-11',
    source: 'EVD-204',
    target: 'SRC-303',
    type: 'CITES',
    properties: { wireCount: 142 }
  },

  // Scene 3 Connections
  {
    id: 'EDG-12',
    source: 'CLM-103',
    target: 'ENT-03',
    type: 'ISSUED_BY',
    properties: { timestamp: '2025-06-10' }
  },
  {
    id: 'EDG-13',
    source: 'EVD-205',
    target: 'CLM-103',
    type: 'REFUTES',
    properties: { severity: 'HIGH', violation: 'Form 483 Citation' }
  },
  {
    id: 'EDG-14',
    source: 'EVD-205',
    target: 'MTR-501',
    type: 'CITES',
    properties: { metricName: 'Uncertified API Ratio' }
  }
];
