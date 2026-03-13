import { useQuery } from '@tanstack/react-query'
import { getStats } from '../api/client'
import { ShieldOff, ShieldCheck, Eye, Activity } from 'lucide-react'
import { clsx } from 'clsx'

function pctChange(current: number, previous: number | undefined): string | null {
  if (previous === undefined || previous === 0) return null
  const pct = ((current - previous) / previous) * 100
  return pct >= 0 ? `+${pct.toFixed(1)}%` : `${pct.toFixed(1)}%`
}

interface CardProps {
  title: string
  value: number
  change: string | null
  icon: React.ReactNode
  color: string
  testId: string
}

function StatCard({ title, value, change, icon, color, testId }: CardProps) {
  return (
    <div
      data-testid={testId}
      className="bg-slate-800/50 border border-slate-700/50 rounded-xl p-5 flex items-start justify-between"
    >
      <div>
        <p className="text-sm text-slate-400 mb-1">{title}</p>
        <p className="text-2xl font-bold text-white">{value.toLocaleString()}</p>
        {change && (
          <p
            className={clsx(
              'text-xs mt-1 font-medium',
              change.startsWith('+') ? 'text-emerald-400' : 'text-red-400'
            )}
          >
            {change} vs. período anterior
          </p>
        )}
      </div>
      <div className={clsx('rounded-lg p-2.5', color)}>{icon}</div>
    </div>
  )
}

export default function StatsCards() {
  const { data } = useQuery({
    queryKey: ['stats'],
    queryFn: getStats,
    refetchInterval: 30_000,
  })

  const stats = data ?? { total_requests: 0, blocked: 0, anonymized: 0, allowed: 0 }

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
      <StatCard
        testId="total-requests-metric"
        title="Total Requests (24h)"
        value={stats.total_requests}
        change={pctChange(stats.total_requests, stats.total_requests_prev)}
        icon={<Activity className="w-5 h-5 text-blue-400" />}
        color="bg-blue-500/10"
      />
      <StatCard
        testId="blocked-requests-metric"
        title="Blocked"
        value={stats.blocked}
        change={pctChange(stats.blocked, stats.blocked_prev)}
        icon={<ShieldOff className="w-5 h-5 text-red-400" />}
        color="bg-red-500/10"
      />
      <StatCard
        testId="anonymized-metric"
        title="Anonymized"
        value={stats.anonymized}
        change={pctChange(stats.anonymized, stats.anonymized_prev)}
        icon={<Eye className="w-5 h-5 text-yellow-400" />}
        color="bg-yellow-500/10"
      />
      <StatCard
        testId="allowed-metric"
        title="Allowed"
        value={stats.allowed}
        change={pctChange(stats.allowed, stats.allowed_prev)}
        icon={<ShieldCheck className="w-5 h-5 text-emerald-400" />}
        color="bg-emerald-500/10"
      />
    </div>
  )
}
