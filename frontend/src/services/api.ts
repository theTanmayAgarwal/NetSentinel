import axios from "axios";

const baseURL = import.meta.env.VITE_API_BASE_URL ?? "/api";

export const api = axios.create({ baseURL, timeout: 20000 });

// System Health
export interface HealthResponse {
  status: string;
  app: string;
  version: string;
  env: string;
  timestamp: string;
}

export async function getHealth(): Promise<HealthResponse> {
  const { data } = await api.get<HealthResponse>("/health");
  return data;
}

// Audits & Upload
export interface FindingEvidence {
  source_line: string;
  line_number: number | null;
  device?: string;
  vendor?: string;
}

export interface RemediationInfo {
  control_id: string;
  vendor: string;
  commands: string[];
  explanation: string;
  validation_status: string;
  predicted_result: string;
}

export interface Finding {
  id?: number;
  control_id: string;
  title: string;
  category: string;
  framework: string;
  status: string; // PASS | FAIL | WARNING | CRITICAL
  severity: string; // HIGH | MEDIUM | LOW | CRITICAL
  observed: string;
  expected: string;
  rationale?: string;
  explanation?: string;
  vendor?: string;
  hostname?: string;
  evidence: FindingEvidence[];
  remediation?: RemediationInfo;
  nist_mapping?: string;
  disa_stig_mapping?: string;
  iso_mapping?: string;
}

export interface AuditSummary {
  score: number;
  passed: number;
  failed: number;
  warnings: number;
  unmapped?: number;
  critical: number;
  total: number;
}

export interface AuditReport {
  id?: number;
  audit_id?: number;
  filename: string;
  vendor: string;
  platform?: string;
  os_version?: string;
  confidence?: number;
  hostname: string;
  summary: AuditSummary;
  predicted_after: {
    score: number;
    passed: number;
    failed: number;
    warnings: number;
    critical: number;
    remediated_controls: RemediationInfo[];
    delta: number;
  };
  findings: Finding[];
  model: Record<string, any>;
  unknown_lines: string[];
  reused_mappings?: any[];
  created_at?: string;
}

export async function uploadAuditText(filename: string, configText: string): Promise<AuditReport> {
  const { data } = await api.post<AuditReport>("/audits/text", {
    filename,
    config_text: configText,
    actor: "administrator",
  });
  return data;
}

export async function uploadAuditFile(file: File): Promise<AuditReport> {
  const formData = new FormData();
  formData.append("file", file);
  formData.append("actor", "administrator");
  const { data } = await api.post<AuditReport>("/audits/upload", formData, {
    headers: { "Content-Type": "multipart/form-data" },
  });
  return data;
}

export async function getAudits(): Promise<any[]> {
  const { data } = await api.get<any[]>("/audits");
  return data;
}

export async function getAudit(id: number): Promise<AuditReport> {
  const { data } = await api.get<AuditReport>(`/audits/${id}`);
  return data;
}

// Devices
export async function getDevices(): Promise<any[]> {
  const { data } = await api.get<any[]>("/devices");
  return data;
}

export async function getDeviceDetail(id: number): Promise<any> {
  const { data } = await api.get<any>(`/devices/${id}`);
  return data;
}

// Findings
export async function getFindings(params?: { vendor?: string; severity?: string; status?: string; limit?: number }): Promise<Finding[]> {
  const { data } = await api.get<Finding[]>("/findings", { params });
  return data;
}

// Training & Adaptive Learning
export interface ClassifyResponse {
  status: "classified" | "unknown";
  confidence: number;
  confidence_threshold: number;
  source_line: string;
  vendor?: string;
  top_matches: any[];
  suggested?: {
    category: string;
    parameter: string;
    expected_value: string;
    control_id?: string;
    vendor?: string;
  };
}

export async function classifyUnknownLine(line: string, vendor?: string): Promise<ClassifyResponse> {
  const { data } = await api.post<ClassifyResponse>("/training/classify", { line, vendor });
  return data;
}

export interface AIProposalResponse {
  property: string;
  value: any;
  unit: string | null;
  confidence: number;
  reason: string;
  pattern: string;
}

export async function aiProposeMapping(line: string, context?: string, vendor?: string): Promise<AIProposalResponse> {
  const { data } = await api.post<AIProposalResponse>("/training/ai-propose", { line, context, vendor });
  return data;
}

export interface TeachExemplarPayload {
  raw_text: string;
  category: string;
  parameter: string;
  expected_value: string;
  control_id?: string;
  vendor?: string;
  platform?: string;
  os_version?: string;
}

export async function teachExemplar(payload: TeachExemplarPayload): Promise<any> {
  const { data } = await api.post<any>("/training/mappings", payload);
  return data;
}

export async function getMappings(status?: string): Promise<any[]> {
  const { data } = await api.get<any[]>("/mappings", { params: { status } });
  return data;
}

export async function getExemplars(status?: string): Promise<any[]> {
  return getMappings(status);
}

export async function updateMapping(id: number, updates: Record<string, any>): Promise<any> {
  const { data } = await api.patch<any>(`/mappings/${id}`, updates);
  return data;
}

export async function approveExemplar(id: number, approved: boolean): Promise<any> {
  const { data } = await api.patch<any>(`/mappings/${id}`, { status: approved ? "ACTIVE" : "REJECTED", reviewer: "administrator" });
  return data;
}

export async function correctMapping(id: number, parameter?: string, expected_value?: string, extra?: Record<string, any>): Promise<any> {
  const { data } = await api.patch<any>(`/mappings/${id}`, {
    security_property: parameter,
    value: expected_value,
    status: "ACTIVE",
    reviewer: "administrator",
    ...(extra || {})
  });
  return data;
}

export async function revalidateMapping(id: number): Promise<any> {
  const { data } = await api.patch<any>(`/mappings/${id}`, { status: "ACTIVE", reviewer: "administrator" });
  return data;
}

export async function revokeMapping(id: number): Promise<any> {
  const { data } = await api.patch<any>(`/mappings/${id}`, { status: "REVOKED", reviewer: "administrator" });
  return data;
}

export async function rejectMapping(id: number): Promise<any> {
  const { data } = await api.patch<any>(`/mappings/${id}`, { status: "REJECTED", reviewer: "administrator" });
  return data;
}



export interface TGRResult {
  tgr_percentage: number;
  total_held_out: number;
  correctly_classified: number;
  evaluation_details: any[];
}

export async function getTGR(): Promise<TGRResult> {
  const { data } = await api.get<TGRResult>("/training/tgr");
  return data;
}

