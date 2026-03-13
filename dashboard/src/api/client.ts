import axios from 'axios'

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || '/api',
  headers: {
    'Content-Type': 'application/json',
  },
})

// --- Types ---

export interface Stats {
  total_requests: number
  blocked: number
  anonymized: number
  allowed: number
  total_requests_prev?: number
  blocked_prev?: number
  anonymized_prev?: number
  allowed_prev?: number
}

export interface TimelinePoint {
  timestamp: string
  total: number
  blocked: number
  anonymized: number
  allowed: number
}

export interface TopUser {
  user: string
  request_count: number
}

export interface TopCategory {
  category: string
  count: number
}

export interface LogEntry {
  id: string
  timestamp: string
  user: string
  ai_provider: string
  action: string
  findings_summary: string
  details?: Record<string, unknown>
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
}

export interface Policy {
  id: string
  name: string
  description: string
  action: string
  ai_targets: string[]
  finding_categories: string[]
  priority: number
  enabled: boolean
}

export type PolicyCreate = Omit<Policy, 'id'>

// --- Stats ---

export async function getStats(): Promise<Stats> {
  const { data } = await api.get('/stats')
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

export async function getPolicies(): Promise<Policy[]> {
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

export default api
