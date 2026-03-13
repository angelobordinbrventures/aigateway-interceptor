import PolicyEditor from '../components/PolicyEditor'

export default function PoliciesPage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-white mb-1">Políticas</h1>
        <p className="text-sm text-slate-400">Manage interception and DLP policies for AI traffic</p>
      </div>
      <PolicyEditor />
    </div>
  )
}
