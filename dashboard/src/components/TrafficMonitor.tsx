import { useQuery } from '@tanstack/react-query'
import { getTimeline } from '../api/client'
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts'

export default function TrafficMonitor() {
  const { data: timeline } = useQuery({
    queryKey: ['timeline'],
    queryFn: getTimeline,
    refetchInterval: 30_000,
  })

  const chartData = (timeline ?? []).map((p) => ({
    ...p,
    time: new Date(p.hour).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
  }))

  return (
    <div
      data-testid="traffic-timeline-chart"
      className="bg-slate-800/50 border border-slate-700/50 rounded-xl p-5"
    >
      <h2 className="text-base font-semibold text-white mb-4">Traffic Monitor (Last 24h)</h2>
      <ResponsiveContainer width="100%" height={320}>
        <LineChart data={chartData}>
          <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
          <XAxis dataKey="time" stroke="#94a3b8" fontSize={12} />
          <YAxis stroke="#94a3b8" fontSize={12} />
          <Tooltip
            contentStyle={{
              backgroundColor: '#1e293b',
              border: '1px solid #334155',
              borderRadius: '8px',
              color: '#e2e8f0',
            }}
          />
          <Legend />
          <Line type="monotone" dataKey="total" stroke="#60a5fa" strokeWidth={2} dot={false} />
          <Line type="monotone" dataKey="blocked" stroke="#f87171" strokeWidth={2} dot={false} />
          <Line type="monotone" dataKey="anonymized" stroke="#fbbf24" strokeWidth={2} dot={false} />
          <Line type="monotone" dataKey="allowed" stroke="#34d399" strokeWidth={2} dot={false} />
        </LineChart>
      </ResponsiveContainer>
    </div>
  )
}
