import axios from 'axios'

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || '/api',
  headers: {
    'Content-Type': 'application/json',
  },
})

// --- Types (aligned with actual API responses) ---

export interface Stats {
  total_requests: number
  blocked: number
  anonymized: number
  allowed: number
  top_users: { user: string; count: number }[]
  top_categories: { category: string; count: number }[]
}

export interface TimelinePoint {
  hour: string
  total: number
  blocked: number
  anonymized: number
  allowed: number
}

export interface TopUser {
  user: string
  count: number
}

export interface TopCategory {
  category: string
  count: number
}

export interface LogEntry {
  id: string
  timestamp: string
  user_identifier: string | null
  source_ip: string | null
  ai_provider: string
  action_taken: string
  findings: Record<string, unknown> | null
  request_hash: string | null
  response_code: number | null
  processing_time_ms: number | null
}

export interface LogFilters {
  page?: number
  page_size?: number
  date_from?: string
  date_to?: string
  user?: string
  ai_provider?: string
  action?: string
}

export interface LogsResponse {
  items: LogEntry[]
  total: number
  page: number
  page_size: number
  pages: number
}

export interface Policy {
  id: string
  name: string
  description: string | null
  action: string
  ai_targets: string[] | null
  finding_categories: string[] | null
  priority: number
  enabled: boolean
  created_at: string
  updated_at: string
}

export interface PoliciesResponse {
  items: Policy[]
  total: number
  page: number
  page_size: number
  pages: number
}

export type PolicyCreate = Omit<Policy, 'id' | 'created_at' | 'updated_at'>

// --- Stats ---

export async function getStats(): Promise<Stats> {
  const { data } = await api.get('/stats/overview')
  return data
}

export async function getTimeline(): Promise<TimelinePoint[]> {
  const { data } = await api.get('/stats/timeline')
  return data
}

export async function getTopUsers(): Promise<TopUser[]> {
  const { data } = await api.get('/stats/top-users')
  return data
}

export async function getTopCategories(): Promise<TopCategory[]> {
  const { data } = await api.get('/stats/top-categories')
  return data
}

// --- Logs ---

export async function getLogs(filters: LogFilters = {}): Promise<LogsResponse> {
  const { data } = await api.get('/logs', { params: filters })
  return data
}

export async function getLogById(id: string): Promise<LogEntry> {
  const { data } = await api.get(`/logs/${id}`)
  return data
}

export async function exportLogs(filters: LogFilters = {}): Promise<Blob> {
  const { data } = await api.get('/logs/export', {
    params: filters,
    responseType: 'blob',
  })
  return data
}

// --- Policies ---

export async function getPolicies(): Promise<PoliciesResponse> {
  const { data } = await api.get('/policies')
  return data
}

export async function createPolicy(policyData: PolicyCreate): Promise<Policy> {
  const { data } = await api.post('/policies', policyData)
  return data
}

export async function updatePolicy(id: string, policyData: Partial<Policy>): Promise<Policy> {
  const { data } = await api.put(`/policies/${id}`, policyData)
  return data
}

export async function deletePolicy(id: string): Promise<void> {
  await api.delete(`/policies/${id}`)
}

export async function togglePolicy(id: string): Promise<Policy> {
  const { data } = await api.patch(`/policies/${id}/toggle`)
  return data
}

// --- Settings ---

export interface SensitivePattern {
  id: string
  name: string
  category: string
  pattern: string
  is_regex: boolean
  severity: string
  enabled: boolean
}

export interface PatternCreate {
  name: string
  category: string
  pattern: string
  is_regex: boolean
  severity: string
  enabled: boolean
}

export async function getRetention(): Promise<{ retention_days: number }> {
  const { data } = await api.get('/settings/retention')
  return data
}

export async function updateRetention(days: number): Promise<{ retention_days: number }> {
  const { data } = await api.put('/settings/retention', { retention_days: days })
  return data
}

export async function getPatterns(): Promise<SensitivePattern[]> {
  const { data } = await api.get('/settings/patterns')
  return data
}

export async function createPattern(pattern: PatternCreate): Promise<SensitivePattern> {
  const { data } = await api.post('/settings/patterns', pattern)
  return data
}

export async function deletePattern(id: string): Promise<void> {
  await api.delete(`/settings/patterns/${id}`)
}

api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('token')
      localStorage.removeItem('username')
      window.location.href = '/login'
    }
    return Promise.reject(error)
  }
)

export default api
