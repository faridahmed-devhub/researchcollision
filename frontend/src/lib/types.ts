export interface User {
  id: string;
  email: string;
  name: string;
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
  user: User;
}

export interface Workspace {
  id: string;
  name: string;
  description: string | null;
  discovery_mode: string;
  created_at: string;
  updated_at: string;
}

export interface WorkspaceStats {
  papers_analyzed: number;
  researchers_analyzed: number;
  gaps: number;
  intersections: number;
  hypotheses: number;
  collaboration_opportunities: number;
  avg_confidence: number;
  active_jobs: number;
  topics: { name: string; count: number }[];
  timeline: { year: number | null; count: number }[];
  methods: { name: string; count: number }[];
  domains: { name: string; count: number }[];
  opportunity_scores: { name: string; score: number }[];
}

export interface ProviderStatus {
  llm_provider: string;
  llm_model: string;
  mock_mode: boolean;
  embedding_provider: string;
  literature_provider: string;
  app_env: string;
}

export interface Researcher {
  id: string;
  workspace_id: string | null;
  name: string;
  affiliation: string | null;
  homepage_url: string | null;
  bio: string | null;
  external_ids: Record<string, unknown>;
  is_synthetic: boolean;
  created_at: string;
}

export interface Paper {
  id: string;
  doi: string | null;
  title: string;
  abstract: string | null;
  publication_year: number | null;
  venue: string | null;
  source_provider: string;
  provider_id: string;
  source_url: string | null;
  citation_count: number;
  is_synthetic: boolean;
  created_at: string;
}

export type EvidenceStatus =
  | "VERIFIED"
  | "INFERRED"
  | "SPECULATIVE"
  | "UNKNOWN"
  | "UNVERIFIED";

export interface Evidence {
  id: string;
  claim: string;
  source_url: string | null;
  source_type: string;
  paper_id: string | null;
  source_title: string | null;
  evidence_text: string | null;
  confidence: number;
  status: EvidenceStatus;
  retrieved_at: string | null;
  created_at: string;
}

export interface Gap {
  id: string;
  workspace_id: string;
  description: string;
  gap_type: string;
  confidence: number;
  status: string;
  created_at: string;
}

export interface GapDetail extends Gap {
  evidence: Evidence[];
}

export interface ResearcherRef {
  id: string;
  name: string;
  affiliation?: string | null;
}

export interface Intersection {
  id: string;
  workspace_id: string;
  job_id: string | null;
  title: string;
  description: string;
  shared_problem: string | null;
  complementary_expertise: string | null;
  research_gap_id: string | null;
  gap_description: string | null;
  researcher_a_id: string;
  researcher_b_id: string;
  why_researcher_a: string | null;
  why_researcher_b: string | null;
  novelty_confidence: number;
  feasibility_confidence: number;
  discovery_mode: string;
  status: string;
  created_at: string;
}

export interface Hypothesis {
  id: string;
  workspace_id: string;
  intersection_id: string;
  label: string;
  research_question: string;
  hypothesis_text: string;
  motivation: string | null;
  method: string | null;
  dataset: string | null;
  baseline: string | null;
  metrics: string | null;
  expected_contribution: string | null;
  risks: string | null;
  confidence: number;
  created_at: string;
}

export interface Experiment {
  id: string;
  hypothesis_id: string;
  baseline: string | null;
  proposed_approach: string | null;
  dataset: string | null;
  dataset_status: string;
  training_setup: string | null;
  evaluation_setup: string | null;
  metrics: string | null;
  ablations: unknown[];
  expected_outcomes: string | null;
  failure_conditions: string | null;
}

export interface IntersectionDetail extends Intersection {
  researcher_a: ResearcherRef | null;
  researcher_b: ResearcherRef | null;
  evidence: Evidence[];
  hypotheses: Hypothesis[];
}

export interface HypothesisDetail extends Hypothesis {
  experiment: Experiment | null;
  intersection: Intersection | null;
  evidence: Evidence[];
}

export interface Collaboration {
  id: string;
  workspace_id: string;
  intersection_id: string | null;
  researcher_a_id: string;
  researcher_b_id: string;
  score: number;
  category: string;
  component_scores: Record<string, number>;
  rationale: string | null;
  created_at: string;
}

export interface DiscoveryJob {
  id: string;
  workspace_id: string;
  user_id: string;
  job_type: string;
  status: "PENDING" | "RUNNING" | "PAUSED" | "COMPLETED" | "FAILED" | "CANCELLED";
  progress: number;
  current_step: string | null;
  total_steps: number;
  error_message: string | null;
  config: Record<string, unknown>;
  result_summary: Record<string, unknown> | null;
  started_at: string | null;
  completed_at: string | null;
  attempt: number;
  created_at: string;
  updated_at: string;
}

export interface JobEvent {
  id: string;
  event_type: string;
  message: string | null;
  data: Record<string, unknown> | null;
  created_at: string;
}

export interface PaperEvidenceRef {
  evidence_id: string;
  claim: string;
  status: EvidenceStatus | string;
  source_title: string | null;
  source_url: string | null;
}

export interface PaperCitation {
  evidence_id: string;
  number: number;
  status: string;
  text: string;
}

export interface PaperDraft {
  report_id: string;
  job_id: string;
  workspace_id: string;
  title: string;
  abstract: string;
  introduction: string;
  related_work: string;
  research_gap: string;
  research_question: string;
  hypothesis: string;
  methodology: string;
  experiment_design: string;
  expected_results: string;
  expected_results_label: string;
  limitations: string[];
  conclusion: string;
  evidence: PaperEvidenceRef[];
  citations: PaperCitation[];
  draft_status: string;
  created_at: string;
}

export interface ProfileVersion {
  id: string;
  version: number;
  dna_json: Record<string, string[]>;
  created_at: string;
}

export interface ResearchProfile {
  id: string;
  workspace_id: string;
  researcher_id: string | null;
  name: string;
  source_type: string;
  current_version: number;
  created_at: string;
  updated_at: string;
}

export interface ProfileDetail extends ResearchProfile {
  dna: Record<string, string[]>;
  versions: ProfileVersion[];
}

export const DNA_FIELDS: { key: string; label: string }[] = [
  { key: "domains", label: "Domains" },
  { key: "research_problems", label: "Research Problems" },
  { key: "methods", label: "Methods" },
  { key: "datasets", label: "Datasets" },
  { key: "tools", label: "Tools" },
  { key: "research_questions", label: "Research Questions" },
  { key: "publications", label: "Publications" },
  { key: "technical_skills", label: "Technical Skills" },
  { key: "research_interests", label: "Research Interests" },
  { key: "emerging_interests", label: "Emerging Interests" },
  { key: "experience", label: "Experience" },
];
