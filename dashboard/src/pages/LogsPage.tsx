import AuditLogs from '../components/AuditLogs'

export default function LogsPage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-white mb-1">Audit Logs</h1>
        <p className="text-sm text-slate-400">Browse and export all intercepted AI traffic logs</p>
      </div>
      <AuditLogs />
    </div>
  )
}
