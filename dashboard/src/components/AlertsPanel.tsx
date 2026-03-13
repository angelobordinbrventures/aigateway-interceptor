import { useQuery } from '@tanstack/react-query'
import { getLogs } from '../api/client'
import type { LogEntry } from '../api/client'
import { clsx } from 'clsx'

function actionColor(action: string) {
  switch (action.toUpperCase()) {
    case 'BLOCKED':
      return 'bg-red-500/10 text-red-400 border-red-500/20'
    case 'ANONYMIZED':
      return 'bg-yellow-500/10 text-yellow-400 border-yellow-500/20'
    case 'ALLOWED':
      return 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20'
    default:
      return 'bg-slate-500/10 text-slate-400 border-slate-500/20'
  }
}

export default function AlertsPanel() {
  const { data } = useQuery({
    queryKey: ['alerts'],
    queryFn: () => getLogs({ page_size: 10, action: 'BLOCKED' }),
    refetchInterval: 30_000,
  })

  const alerts: LogEntry[] = data?.items ?? []

  return (
    <div
      data-testid="alerts-panel"
      className="bg-slate-800/50 border border-slate-700/50 rounded-xl p-5 h-full"
    >
      <h2 className="text-base font-semibold text-white mb-4">Recent Alerts</h2>
      <div className="space-y-2 overflow-y-auto max-h-[300px]">
        {alerts.length === 0 && (
          <p className="text-sm text-slate-500">No recent alerts.</p>
        )}
        {alerts.map((alert) => (
          <div
            key={alert.id}
            className="border border-slate-700/50 rounded-lg p-3 space-y-1"
          >
            <div className="flex items-center justify-between">
              <span className="text-xs text-slate-400">
                {new Date(alert.timestamp).toLocaleString()}
              </span>
              <span
                className={clsx(
                  'text-xs px-2 py-0.5 rounded-full border font-medium',
                  actionColor(alert.action_taken)
                )}
              >
                {alert.action_taken}
              </span>
            </div>
            <div className="flex items-center justify-between text-sm">
              <span className="text-slate-300 truncate">{alert.user_identifier ?? 'Unknown'}</span>
              <span className="text-slate-500 text-xs">{alert.ai_provider}</span>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
