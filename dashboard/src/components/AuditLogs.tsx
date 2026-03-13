import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { getLogs, exportLogs } from '../api/client'
import type { LogFilters, LogEntry } from '../api/client'
import { Download, ChevronDown, ChevronUp } from 'lucide-react'
import { clsx } from 'clsx'

const AI_PROVIDERS = ['', 'openai', 'anthropic', 'google', 'mistral', 'cohere', 'groq', 'deepseek']
const ACTIONS_FILTER = ['', 'BLOCKED', 'ANONYMIZED', 'ALLOWED', 'LOG_ONLY']

export default function AuditLogs() {
  const [filters, setFilters] = useState<LogFilters>({ page: 1, page_size: 20 })
  const [expandedId, setExpandedId] = useState<string | null>(null)

  const { data } = useQuery({
    queryKey: ['logs', filters],
    queryFn: () => getLogs(filters),
  })

  const logs = data?.items ?? []
  const total = data?.total ?? 0
  const totalPages = Math.max(1, data?.pages ?? 1)

  async function handleExport() {
    try {
      const blob = await exportLogs(filters)
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = 'audit-logs.csv'
      a.click()
      URL.revokeObjectURL(url)
    } catch {
      // silently fail
    }
  }

  function actionBadge(action: string) {
    const colors: Record<string, string> = {
      BLOCKED: 'bg-red-500/10 text-red-400',
      ANONYMIZED: 'bg-yellow-500/10 text-yellow-400',
      ALLOWED: 'bg-emerald-500/10 text-emerald-400',
      LOG_ONLY: 'bg-blue-500/10 text-blue-400',
    }
    return colors[action.toUpperCase()] ?? 'bg-slate-500/10 text-slate-400'
  }

  function findingsSummary(log: LogEntry): string {
    if (!log.findings) return '-'
    if (typeof log.findings === 'object') {
      const cats = (log.findings as Record<string, unknown>).categories
      if (Array.isArray(cats)) return cats.join(', ')
    }
    return JSON.stringify(log.findings).slice(0, 60)
  }

  return (
    <div>
      {/* Filters */}
      <div className="flex flex-wrap gap-3 mb-4">
        <input
          type="date"
          value={filters.date_from ?? ''}
          onChange={(e) => setFilters({ ...filters, date_from: e.target.value || undefined, page: 1 })}
          className="bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-white text-sm focus:outline-none focus:border-indigo-500"
          placeholder="From"
        />
        <input
          type="date"
          value={filters.date_to ?? ''}
          onChange={(e) => setFilters({ ...filters, date_to: e.target.value || undefined, page: 1 })}
          className="bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-white text-sm focus:outline-none focus:border-indigo-500"
          placeholder="To"
        />
        <input
          type="text"
          value={filters.user ?? ''}
          onChange={(e) => setFilters({ ...filters, user: e.target.value || undefined, page: 1 })}
          placeholder="Search user..."
          className="bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-white text-sm focus:outline-none focus:border-indigo-500"
        />
        <select
          value={filters.ai_provider ?? ''}
          onChange={(e) => setFilters({ ...filters, ai_provider: e.target.value || undefined, page: 1 })}
          className="bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-white text-sm focus:outline-none focus:border-indigo-500"
        >
          <option value="">All Providers</option>
          {AI_PROVIDERS.filter(Boolean).map((p) => (
            <option key={p} value={p}>{p}</option>
          ))}
        </select>
        <select
          value={filters.action ?? ''}
          onChange={(e) => setFilters({ ...filters, action: e.target.value || undefined, page: 1 })}
          aria-label="Filtrar por ação"
          className="bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-white text-sm focus:outline-none focus:border-indigo-500"
        >
          <option value="">All Actions</option>
          {ACTIONS_FILTER.filter(Boolean).map((a) => (
            <option key={a} value={a}>{a}</option>
          ))}
        </select>
        <button
          onClick={handleExport}
          className="flex items-center gap-2 bg-slate-700 hover:bg-slate-600 text-white text-sm px-4 py-2 rounded-lg transition-colors ml-auto"
        >
          <Download className="w-4 h-4" />
          Export CSV
        </button>
      </div>

      {/* Table */}
      <div
        data-testid="logs-table"
        className="bg-slate-800/50 border border-slate-700/50 rounded-xl overflow-hidden"
      >
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-slate-700/50 text-slate-400 text-left">
              <th className="px-4 py-3 font-medium w-8"></th>
              <th className="px-4 py-3 font-medium">Timestamp</th>
              <th className="px-4 py-3 font-medium">User</th>
              <th className="px-4 py-3 font-medium">AI Provider</th>
              <th className="px-4 py-3 font-medium">Action</th>
              <th className="px-4 py-3 font-medium">Findings</th>
            </tr>
          </thead>
          <tbody>
            {logs.map((log: LogEntry) => (
              <tr
                key={log.id}
                onClick={() => setExpandedId(expandedId === log.id ? null : log.id)}
                className="border-b border-slate-700/30 hover:bg-slate-700/20 cursor-pointer"
              >
                <td className="px-4 py-3 text-slate-400">
                  {expandedId === log.id ? (
                    <ChevronUp className="w-4 h-4" />
                  ) : (
                    <ChevronDown className="w-4 h-4" />
                  )}
                </td>
                <td className="px-4 py-3 text-slate-300 whitespace-nowrap">
                  {new Date(log.timestamp).toLocaleString()}
                </td>
                <td className="px-4 py-3 text-white">{log.user_identifier ?? 'Unknown'}</td>
                <td className="px-4 py-3 text-slate-300">{log.ai_provider}</td>
                <td className="px-4 py-3">
                  <span className={clsx('text-xs px-2 py-1 rounded-full font-medium', actionBadge(log.action_taken))}>
                    {log.action_taken}
                  </span>
                </td>
                <td className="px-4 py-3 text-slate-400 truncate max-w-[200px]">
                  {findingsSummary(log)}
                </td>
              </tr>
            ))}
            {expandedId && logs.find(l => l.id === expandedId) && (
              <tr key={`${expandedId}-detail`} className="border-b border-slate-700/30">
                <td colSpan={6} className="px-6 py-4 bg-slate-900/50">
                  <pre className="text-xs text-slate-300 whitespace-pre-wrap overflow-x-auto">
                    {JSON.stringify(logs.find(l => l.id === expandedId), null, 2)}
                  </pre>
                </td>
              </tr>
            )}
            {logs.length === 0 && (
              <tr>
                <td colSpan={6} className="px-4 py-8 text-center text-slate-500">
                  No log entries found.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      {/* Pagination */}
      <div className="flex items-center justify-between mt-4">
        <p className="text-sm text-slate-400">
          {total} total entries - Page {filters.page} of {totalPages}
        </p>
        <div className="flex gap-2">
          <button
            disabled={filters.page === 1}
            onClick={() => setFilters({ ...filters, page: (filters.page ?? 1) - 1 })}
            className="px-3 py-1.5 text-sm bg-slate-700 hover:bg-slate-600 disabled:opacity-50 disabled:cursor-not-allowed text-white rounded-lg transition-colors"
          >
            Previous
          </button>
          <button
            disabled={(filters.page ?? 1) >= totalPages}
            onClick={() => setFilters({ ...filters, page: (filters.page ?? 1) + 1 })}
            className="px-3 py-1.5 text-sm bg-slate-700 hover:bg-slate-600 disabled:opacity-50 disabled:cursor-not-allowed text-white rounded-lg transition-colors"
          >
            Next
          </button>
        </div>
      </div>
    </div>
  )
}
