import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import {
  getPolicies,
  createPolicy,
  updatePolicy,
  deletePolicy,
  togglePolicy,
} from '../api/client'
import type { Policy, PolicyCreate } from '../api/client'
import { Plus, Pencil, Trash2 } from 'lucide-react'
import { clsx } from 'clsx'

const ACTIONS = ['BLOCK', 'ANONYMIZE', 'LOG_ONLY', 'ALLOW']
const AI_TARGETS = ['openai', 'anthropic', 'google', 'mistral', 'cohere', 'meta']
const FINDING_CATEGORIES = [
  'PII',
  'CREDENTIALS',
  'SECRETS',
  'SOURCE_CODE',
  'FINANCIAL',
  'HEALTH',
  'CUSTOM',
]

interface PolicyForm {
  name: string
  description: string
  action: string
  ai_targets: string[]
  finding_categories: string[]
  priority: number
  enabled: boolean
}

const emptyForm: PolicyForm = {
  name: '',
  description: '',
  action: 'BLOCK',
  ai_targets: [],
  finding_categories: [],
  priority: 0,
  enabled: true,
}

export default function PolicyEditor() {
  const queryClient = useQueryClient()
  const [modalOpen, setModalOpen] = useState(false)
  const [editingId, setEditingId] = useState<string | null>(null)
  const [form, setForm] = useState<PolicyForm>(emptyForm)

  const { data: policiesData } = useQuery({
    queryKey: ['policies'],
    queryFn: getPolicies,
  })
  const policies = policiesData?.items ?? []

  const createMut = useMutation({
    mutationFn: (data: PolicyCreate) => createPolicy(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['policies'] })
      closeModal()
    },
  })

  const updateMut = useMutation({
    mutationFn: ({ id, data }: { id: string; data: Partial<Policy> }) => updatePolicy(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['policies'] })
      closeModal()
    },
  })

  const deleteMut = useMutation({
    mutationFn: (id: string) => deletePolicy(id),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['policies'] }),
  })

  const toggleMut = useMutation({
    mutationFn: (id: string) => togglePolicy(id),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['policies'] }),
  })

  function closeModal() {
    setModalOpen(false)
    setEditingId(null)
    setForm(emptyForm)
  }

  function openCreate() {
    setForm(emptyForm)
    setEditingId(null)
    setModalOpen(true)
  }

  function openEdit(policy: Policy) {
    setForm({
      name: policy.name,
      description: policy.description ?? '',
      action: policy.action,
      ai_targets: policy.ai_targets ?? [],
      finding_categories: policy.finding_categories ?? [],
      priority: policy.priority,
      enabled: policy.enabled,
    })
    setEditingId(policy.id)
    setModalOpen(true)
  }

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    if (editingId) {
      updateMut.mutate({ id: editingId, data: form })
    } else {
      createMut.mutate(form)
    }
  }

  function toggleMulti(arr: string[], value: string): string[] {
    return arr.includes(value) ? arr.filter((v) => v !== value) : [...arr, value]
  }

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-lg font-semibold text-white">Policies</h2>
        <button
          onClick={openCreate}
          className="flex items-center gap-2 bg-indigo-600 hover:bg-indigo-700 text-white text-sm px-4 py-2 rounded-lg transition-colors"
        >
          <Plus className="w-4 h-4" />
          Nova Política
        </button>
      </div>

      {/* Table */}
      <div className="bg-slate-800/50 border border-slate-700/50 rounded-xl overflow-hidden">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-slate-700/50 text-slate-400 text-left">
              <th className="px-4 py-3 font-medium">Name</th>
              <th className="px-4 py-3 font-medium">Action</th>
              <th className="px-4 py-3 font-medium">Priority</th>
              <th className="px-4 py-3 font-medium">Enabled</th>
              <th className="px-4 py-3 font-medium text-right">Actions</th>
            </tr>
          </thead>
          <tbody>
            {policies.map((policy) => (
              <tr key={policy.id} className="border-b border-slate-700/30 hover:bg-slate-700/20">
                <td className="px-4 py-3 text-white">{policy.name}</td>
                <td className="px-4 py-3">
                  <span
                    className={clsx('text-xs px-2 py-1 rounded-full font-medium', {
                      'bg-red-500/10 text-red-400': policy.action === 'BLOCK',
                      'bg-yellow-500/10 text-yellow-400': policy.action === 'ANONYMIZE',
                      'bg-blue-500/10 text-blue-400': policy.action === 'LOG_ONLY',
                      'bg-emerald-500/10 text-emerald-400': policy.action === 'ALLOW',
                    })}
                  >
                    {policy.action}
                  </span>
                </td>
                <td className="px-4 py-3 text-slate-300">{policy.priority}</td>
                <td className="px-4 py-3">
                  <button
                    onClick={() => toggleMut.mutate(policy.id)}
                    className={clsx(
                      'w-10 h-5 rounded-full relative transition-colors',
                      policy.enabled ? 'bg-indigo-600' : 'bg-slate-600'
                    )}
                  >
                    <span
                      className={clsx(
                        'absolute top-0.5 w-4 h-4 bg-white rounded-full transition-transform',
                        policy.enabled ? 'left-5' : 'left-0.5'
                      )}
                    />
                  </button>
                </td>
                <td className="px-4 py-3 text-right space-x-2">
                  <button
                    onClick={() => openEdit(policy)}
                    className="text-slate-400 hover:text-white transition-colors"
                  >
                    <Pencil className="w-4 h-4 inline" />
                  </button>
                  <button
                    onClick={() => {
                      if (confirm('Delete this policy?')) deleteMut.mutate(policy.id)
                    }}
                    className="text-slate-400 hover:text-red-400 transition-colors"
                  >
                    <Trash2 className="w-4 h-4 inline" />
                  </button>
                </td>
              </tr>
            ))}
            {policies.length === 0 && (
              <tr>
                <td colSpan={5} className="px-4 py-8 text-center text-slate-500">
                  No policies configured yet.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      {/* Modal */}
      {modalOpen && (
        <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50">
          <form
            onSubmit={handleSubmit}
            className="bg-slate-800 border border-slate-700 rounded-xl p-6 w-full max-w-lg space-y-4 max-h-[90vh] overflow-y-auto"
          >
            <h3 className="text-lg font-semibold text-white">
              {editingId ? 'Edit Policy' : 'Nova Política'}
            </h3>

            <div>
              <label className="block text-sm text-slate-400 mb-1">Name</label>
              <input
                value={form.name}
                onChange={(e) => setForm({ ...form, name: e.target.value })}
                required
                className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-white text-sm focus:outline-none focus:border-indigo-500"
              />
            </div>

            <div>
              <label className="block text-sm text-slate-400 mb-1">Description</label>
              <textarea
                value={form.description}
                onChange={(e) => setForm({ ...form, description: e.target.value })}
                rows={2}
                className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-white text-sm focus:outline-none focus:border-indigo-500"
              />
            </div>

            <div>
              <label className="block text-sm text-slate-400 mb-1">Action</label>
              <select
                value={form.action}
                onChange={(e) => setForm({ ...form, action: e.target.value })}
                className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-white text-sm focus:outline-none focus:border-indigo-500"
              >
                {ACTIONS.map((a) => (
                  <option key={a} value={a}>
                    {a}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-sm text-slate-400 mb-1">AI Targets</label>
              <div className="flex flex-wrap gap-2">
                {AI_TARGETS.map((t) => (
                  <button
                    type="button"
                    key={t}
                    onClick={() => setForm({ ...form, ai_targets: toggleMulti(form.ai_targets, t) })}
                    className={clsx(
                      'text-xs px-3 py-1 rounded-full border transition-colors',
                      form.ai_targets.includes(t)
                        ? 'bg-indigo-600/20 border-indigo-500 text-indigo-400'
                        : 'border-slate-600 text-slate-400 hover:border-slate-500'
                    )}
                  >
                    {t}
                  </button>
                ))}
              </div>
            </div>

            <div>
              <label className="block text-sm text-slate-400 mb-1">Finding Categories</label>
              <div className="flex flex-wrap gap-2">
                {FINDING_CATEGORIES.map((c) => (
                  <button
                    type="button"
                    key={c}
                    onClick={() =>
                      setForm({ ...form, finding_categories: toggleMulti(form.finding_categories, c) })
                    }
                    className={clsx(
                      'text-xs px-3 py-1 rounded-full border transition-colors',
                      form.finding_categories.includes(c)
                        ? 'bg-indigo-600/20 border-indigo-500 text-indigo-400'
                        : 'border-slate-600 text-slate-400 hover:border-slate-500'
                    )}
                  >
                    {c}
                  </button>
                ))}
              </div>
            </div>

            <div className="flex gap-4">
              <div className="flex-1">
                <label className="block text-sm text-slate-400 mb-1">Priority</label>
                <input
                  type="number"
                  value={form.priority}
                  onChange={(e) => setForm({ ...form, priority: Number(e.target.value) })}
                  className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-white text-sm focus:outline-none focus:border-indigo-500"
                />
              </div>
              <div className="flex items-end pb-2">
                <label className="flex items-center gap-2 text-sm text-slate-400 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={form.enabled}
                    onChange={(e) => setForm({ ...form, enabled: e.target.checked })}
                    className="rounded"
                  />
                  Enabled
                </label>
              </div>
            </div>

            <div className="flex justify-end gap-3 pt-2">
              <button
                type="button"
                onClick={closeModal}
                className="px-4 py-2 text-sm text-slate-400 hover:text-white transition-colors"
              >
                Cancel
              </button>
              <button
                type="submit"
                className="px-4 py-2 text-sm bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg transition-colors"
              >
                {editingId ? 'Update' : 'Create'}
              </button>
            </div>
          </form>
        </div>
      )}
    </div>
  )
}
