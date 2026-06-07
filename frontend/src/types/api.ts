/**
 * Type contracts mirroring the FastAPI Pydantic schemas.
 * Keep these in sync with `backend/app/schemas`.
 */

export interface FunctionRead {
  readonly id: number;
  readonly name: string;
  readonly order_index: number;
  readonly ast_node_count: number;
  readonly fingerprint_count: number;
}

export interface SubmissionSummary {
  readonly id: number;
  readonly name: string;
  readonly filename: string;
  readonly language: string;
  readonly ast_node_count: number;
  readonly function_count: number;
  readonly created_at: string;
}

export interface SubmissionRead {
  readonly id: number;
  readonly name: string;
  readonly filename: string;
  readonly language: string;
  readonly ast_node_count: number;
  readonly created_at: string;
  readonly functions: readonly FunctionRead[];
}

export interface SubmissionCreate {
  readonly name: string;
  readonly filename: string;
  readonly source_code: string;
}

export interface FunctionMatchRead {
  readonly function_a_id: number;
  readonly function_b_id: number;
  readonly similarity: number;
  readonly ted_similarity: number;
  readonly winnow_similarity: number;
}

export interface ComparisonRead {
  readonly id: number;
  readonly submission_a_id: number;
  readonly submission_b_id: number;
  readonly overall_score: number;
  readonly ted_score: number;
  readonly winnow_score: number;
  readonly callgraph_score: number;
  readonly status: string;
  readonly created_at: string;
  readonly matches: readonly FunctionMatchRead[];
}

export interface ComparisonRequest {
  readonly submission_a_id: number;
  readonly submission_b_id: number;
  readonly force?: boolean;
}

//Cohort analysis

export interface AnalysisCapabilities {
  readonly ai_reference_available: boolean;
  readonly default_reference_count: number;
  readonly max_reference_count: number;
}

export interface AnalysisRequest {
  readonly submission_ids?: readonly number[] | null;
  readonly use_ai_reference: boolean;
  readonly problem_description?: string | null;
  readonly reference_count: number;
}

export interface StudentPairResult {
  readonly submission_a_id: number;
  readonly submission_a_name: string;
  readonly submission_b_id: number;
  readonly submission_b_name: string;
  readonly overall_score: number;
  readonly ted_score: number;
  readonly winnow_score: number;
  readonly callgraph_score: number;
  readonly aligned_function_count: number;
}

export interface ReferenceSimilarityResult {
  readonly submission_id: number;
  readonly submission_name: string;
  readonly reference_label: string;
  readonly overall_score: number;
  readonly ted_score: number;
  readonly winnow_score: number;
  readonly callgraph_score: number;
}

export interface AiReferenceSolution {
  readonly label: string;
  readonly source_code: string;
}

export interface SubmissionReferenceSummary {
  readonly submission_id: number;
  readonly submission_name: string;
  readonly max_reference_score: number;
  readonly best_reference_label: string | null;
}

export interface ClusterMember {
  readonly submission_id: number;
  readonly name: string;
}

export interface SuspiciousCluster {
  readonly members: readonly ClusterMember[];
  readonly size: number;
  readonly average_similarity: number;
}

export interface AnalysisReport {
  readonly generated_at: string;
  readonly submission_count: number;
  readonly ai_reference_enabled: boolean;
  readonly ai_reference_count: number;
  readonly problem_description: string | null;
  readonly student_pairs: readonly StudentPairResult[];
  readonly highest_student_score: number;
  readonly clusters: readonly SuspiciousCluster[];
  readonly ai_references: readonly AiReferenceSolution[];
  readonly reference_results: readonly ReferenceSimilarityResult[];
  readonly reference_summaries: readonly SubmissionReferenceSummary[];
  readonly warnings: readonly string[];
}

//Saved score sets ("labs")

export interface SavedLabSummary {
  readonly id: number;
  readonly label: string;
  readonly created_at: string;
  readonly submission_count: number;
  readonly highest_student_score: number;
}

export interface SavedLabCreate {
  readonly label: string;
  readonly password: string;
  readonly report: AnalysisReport;
}
