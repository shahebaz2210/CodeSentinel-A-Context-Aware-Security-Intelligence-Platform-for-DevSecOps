/** API client for CodeSentinel backend */

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

function getToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem("github_token");
}

async function apiFetch<T>(path: string, options?: RequestInit): Promise<T> {
  const token = getToken();
  const res = await fetch(`${API_URL}${path}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...(options?.headers || {}),
    },
  });
  if (!res.ok) {
    const err = await res.text();
    throw new Error(err || `API error: ${res.status}`);
  }
  return res.json() as Promise<T>;
}

// ── Auth ────────────────────────────────────────────────────
export function getGitHubLoginUrl(): string {
  return `${API_URL}/auth/github`;
}

// ── Repositories ─────────────────────────────────────────────
export function fetchGitHubRepos(): Promise<GitHubRepo[]> {
  return apiFetch<GitHubRepo[]>("/api/repos");
}

export function connectRepo(payload: ConnectRepoPayload): Promise<{ id: string; full_name: string; already_connected: boolean }> {
  return apiFetch("/api/repos/connect", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

// ── Scans ─────────────────────────────────────────────────────
export function createScan(repoId: string, scanType: "repo" | "pr" = "repo"): Promise<ScanCreated> {
  return apiFetch<ScanCreated>(`/api/scans?repo_id=${repoId}&scan_type=${scanType}`, { method: "POST" });
}

export function fetchScan(scanId: string): Promise<ScanStatus> {
  return apiFetch<ScanStatus>(`/api/scans/${scanId}`);
}

export function fetchScanFindings(scanId: string): Promise<FindingSummary[]> {
  return apiFetch<FindingSummary[]>(`/api/scans/${scanId}/findings`);
}

export function fetchRepoScans(repoId: string, page = 1): Promise<{ total: number; scans: ScanHistoryItem[] }> {
  return apiFetch(`/api/repos/${repoId}/scans?page=${page}&limit=20`);
}

export function fetchLatestScan(repoId: string): Promise<ScanStatus | null> {
  return apiFetch(`/api/repos/${repoId}/latest-scan`);
}

export function fetchRepoTrends(repoId: string): Promise<TrendItem[]> {
  return apiFetch(`/api/repos/${repoId}/trends`);
}

// ── Findings ──────────────────────────────────────────────────
export function fetchFinding(findingId: string): Promise<FindingDetail> {
  return apiFetch<FindingDetail>(`/api/findings/${findingId}`);
}

// ── Patch Validation ──────────────────────────────────────────
export function triggerValidation(findingId: string): Promise<{ task_id: string }> {
  return apiFetch(`/api/findings/${findingId}/validate`, { method: "POST" });
}

// ── Assistant ─────────────────────────────────────────────────
export function streamAssistantAnswer(
  question: string,
  scanId?: string,
  findingId?: string
): EventSource {
  const token = getToken();
  // SSE via POST — use fetch with ReadableStream
  return new EventSource(
    `${API_URL}/api/assistant/stream?question=${encodeURIComponent(question)}${scanId ? `&scan_id=${scanId}` : ""}${token ? `&token=${token}` : ""}`
  );
}

// ── Types ─────────────────────────────────────────────────────
export interface GitHubRepo {
  github_id: number;
  name: string;
  full_name: string;
  clone_url: string;
  private: boolean;
  default_branch: string;
  owner: string;
  language?: string;
  updated_at?: string;
}

export interface ConnectRepoPayload {
  github_id: number;
  name: string;
  full_name: string;
  clone_url: string;
  default_branch: string;
  owner_login: string;
  is_private: boolean;
}

export interface ScanCreated {
  scan_id: string;
  status: string;
  celery_task_id: string;
}

export interface ScanStatus {
  scan_id: string;
  repository_id: string;
  scan_type: string;
  status: "pending" | "running" | "completed" | "failed";
  security_score: number | null;
  gate_result: "pass" | "warning" | "block" | null;
  error_message?: string;
  started_at: string;
  completed_at?: string;
}

export interface FindingSummary {
  id: string;
  finding_type: string;
  tool: string;
  severity: "critical" | "high" | "medium" | "low" | "info";
  file_path: string;
  line_start: number | null;
  message: string;
  history_status: string | null;
  risk_score: number | null;
}

export interface FindingDetail extends FindingSummary {
  scan_id: string;
  line_end: number | null;
  code_snippet: string | null;
  root_cause: string | null;
  attack_scenario: string | null;
  ai_explanation: string | null;
  owasp_refs: string[];
  cwe_refs: string[];
  security_recommendations: string | null;
  suggested_fix: string | null;
  secure_coding_guidance: string | null;
  fix_explanation: string | null;
  validation_status: "not_run" | "pending" | "pass" | "fail" | null;
  is_true_positive: boolean | null;
  confidence: number | null;
}

export interface ScanHistoryItem {
  scan_id: string;
  scan_type: string;
  status: string;
  security_score: number | null;
  gate_result: string | null;
  started_at: string;
  completed_at?: string;
}

export interface TrendItem {
  scan_id: string;
  date: string;
  security_score: number | null;
  gate_result: string | null;
  new_findings: number;
  resolved_findings: number;
  recurring_findings: number;
  total_findings: number;
}
