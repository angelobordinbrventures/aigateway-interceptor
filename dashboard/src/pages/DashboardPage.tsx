import { useQuery } from '@tanstack/react-query'
import StatsCards from '../components/StatsCards'
import TrafficMonitor from '../components/TrafficMonitor'
import AlertsPanel from '../components/AlertsPanel'
import { getTopUsers, getTopCategories } from '../api/client'

export default function DashboardPage() {
  const { data: topUsers = [] } = useQuery({
    queryKey: ['topUsers'],
    queryFn: getTopUsers,
    refetchInterval: 30_000,
  })

  const { data: topCategories = [] } = useQuery({
    queryKey: ['topCategories'],
    queryFn: getTopCategories,
    refetchInterval: 30_000,
  })

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-white mb-1">Dashboard</h1>
        <p className="text-sm text-slate-400">Real-time overview of AI traffic and security events</p>
      </div>

      <StatsCards />

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2">
          <TrafficMonitor />
        </div>
        <div className="lg:col-span-1">
          <AlertsPanel />
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Top Users */}
        <div className="bg-slate-800/50 border border-slate-700/50 rounded-xl p-5">
          <h2 className="text-base font-semibold text-white mb-4">Top Users</h2>
          <div className="space-y-2">
            {topUsers.length === 0 && (
              <p className="text-sm text-slate-500">No data yet.</p>
            )}
            {topUsers.map((u, i) => (
              <div key={u.user} className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <span className="text-xs text-slate-500 w-5">{i + 1}.</span>
                  <span className="text-sm text-slate-300">{u.user}</span>
                </div>
                <span className="text-sm font-medium text-white">
                  {u.request_count.toLocaleString()}
                </span>
              </div>
            ))}
          </div>
        </div>

        {/* Top Categories */}
        <div className="bg-slate-800/50 border border-slate-700/50 rounded-xl p-5">
          <h2 className="text-base font-semibold text-white mb-4">Top Finding Categories</h2>
          <div className="space-y-2">
            {topCategories.length === 0 && (
              <p className="text-sm text-slate-500">No data yet.</p>
            )}
            {topCategories.map((c, i) => (
              <div key={c.category} className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <span className="text-xs text-slate-500 w-5">{i + 1}.</span>
                  <span className="text-sm text-slate-300">{c.category}</span>
                </div>
                <span className="text-sm font-medium text-white">
                  {c.count.toLocaleString()}
                </span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}
