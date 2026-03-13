import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Download, Plus, Trash2, Monitor, Apple, Terminal, Loader2, CheckCircle } from 'lucide-react'
import {
  getRetention,
  updateRetention,
  getPatterns,
  createPattern,
  deletePattern,
  type PatternCreate,
} from '../api/client'

const CATEGORIES = [
  'PII',
  'CREDENTIALS',
  'SECRETS',
  'SOURCE_CODE',
  'FINANCIAL',
  'HEALTH',
  'CUSTOM',
] as const

export default function SettingsPage() {
  const queryClient = useQueryClient()
  const [activeTab, setActiveTab] = useState<'windows' | 'mac' | 'linux'>('mac')
  const [retentionInput, setRetentionInput] = useState<number | null>(null)
  const [retentionSaved, setRetentionSaved] = useState(false)

  // Pattern form state
  const [patternName, setPatternName] = useState('')
  const [patternCategory, setPatternCategory] = useState<string>('CUSTOM')
  const [patternRegex, setPatternRegex] = useState('')

  // --- Retention ---
  const { data: retentionData, isLoading: retentionLoading } = useQuery({
    queryKey: ['retention'],
    queryFn: getRetention,
  })

  const retentionDays = retentionInput ?? retentionData?.retention_days ?? 90

  const retentionMutation = useMutation({
    mutationFn: (days: number) => updateRetention(days),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['retention'] })
      setRetentionSaved(true)
      setTimeout(() => setRetentionSaved(false), 2000)
    },
  })

  // --- Patterns ---
  const { data: patterns = [], isLoading: patternsLoading } = useQuery({
    queryKey: ['patterns'],
    queryFn: getPatterns,
  })

  const createMutation = useMutation({
    mutationFn: (p: PatternCreate) => createPattern(p),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['patterns'] })
      setPatternName('')
      setPatternRegex('')
      setPatternCategory('CUSTOM')
    },
  })

  const deleteMutation = useMutation({
    mutationFn: (id: string) => deletePattern(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['patterns'] })
    },
  })

  function handleAddPattern() {
    const name = patternName.trim()
    const regex = patternRegex.trim()
    if (!name || !regex) return

    createMutation.mutate({
      name,
      category: patternCategory,
      pattern: regex,
      is_regex: true,
      severity: 'medium',
      enabled: true,
    })
  }

  const instructions: Record<string, string> = {
    windows: `1. Download the CA certificate below
2. Open certmgr.msc (Certificate Manager)
3. Navigate to Trusted Root Certification Authorities > Certificates
4. Right-click > All Tasks > Import
5. Select the downloaded certificate file
6. Configure proxy settings in Settings > Network & Internet > Proxy
7. Set HTTP/HTTPS proxy to your AIGateway server address`,
    mac: `1. Download the CA certificate below
2. Open Keychain Access
3. Drag the certificate file into the System keychain
4. Double-click the certificate and set Trust > Always Trust
5. Configure proxy in System Preferences > Network > Advanced > Proxies
6. Enable Web Proxy (HTTP) and Secure Web Proxy (HTTPS)
7. Set the proxy server to your AIGateway address`,
    linux: `1. Download the CA certificate below
2. Copy to /usr/local/share/ca-certificates/aigateway.crt
3. Run: sudo update-ca-certificates
4. Configure proxy environment variables:
   export HTTP_PROXY=http://<aigateway-host>:8080
   export HTTPS_PROXY=http://<aigateway-host>:8080
5. For persistent config, add to /etc/environment`,
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-white mb-1">Configurações</h1>
        <p className="text-sm text-slate-400">System settings and installation guide</p>
      </div>

      {/* Log Retention */}
      <div className="bg-slate-800/50 border border-slate-700/50 rounded-xl p-5">
        <h2 className="text-base font-semibold text-white mb-4">Log Retention</h2>
        <div className="flex items-center gap-4">
          <label className="text-sm text-slate-400">Retain logs for</label>
          {retentionLoading ? (
            <Loader2 className="w-4 h-4 text-slate-400 animate-spin" />
          ) : (
            <input
              type="number"
              min={1}
              max={365}
              value={retentionDays}
              onChange={(e) => setRetentionInput(Number(e.target.value))}
              className="w-24 bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-white text-sm focus:outline-none focus:border-indigo-500"
            />
          )}
          <span className="text-sm text-slate-400">days</span>
          <button
            onClick={() => retentionMutation.mutate(retentionDays)}
            disabled={retentionMutation.isPending}
            className="ml-4 px-4 py-2 text-sm bg-indigo-600 hover:bg-indigo-700 disabled:opacity-50 text-white rounded-lg transition-colors flex items-center gap-2"
          >
            {retentionMutation.isPending && <Loader2 className="w-4 h-4 animate-spin" />}
            {retentionSaved ? (
              <>
                <CheckCircle className="w-4 h-4" />
                Saved
              </>
            ) : (
              'Save'
            )}
          </button>
        </div>
        {retentionMutation.isError && (
          <p className="text-sm text-red-400 mt-2">Failed to update retention settings.</p>
        )}
      </div>

      {/* Custom Patterns */}
      <div className="bg-slate-800/50 border border-slate-700/50 rounded-xl p-5">
        <h2 className="text-base font-semibold text-white mb-4">Custom Detection Patterns</h2>
        <p className="text-sm text-slate-400 mb-3">
          Add custom regex patterns for detecting sensitive data in AI traffic.
        </p>

        {/* Add pattern form */}
        <div className="grid grid-cols-[1fr_auto_1fr_auto] gap-2 mb-4">
          <input
            type="text"
            value={patternName}
            onChange={(e) => setPatternName(e.target.value)}
            placeholder="Pattern name"
            className="bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-white text-sm focus:outline-none focus:border-indigo-500"
          />
          <select
            value={patternCategory}
            onChange={(e) => setPatternCategory(e.target.value)}
            className="bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-white text-sm focus:outline-none focus:border-indigo-500"
          >
            {CATEGORIES.map((cat) => (
              <option key={cat} value={cat}>
                {cat}
              </option>
            ))}
          </select>
          <input
            type="text"
            value={patternRegex}
            onChange={(e) => setPatternRegex(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleAddPattern()}
            placeholder="e.g. \b[A-Z]{2}\d{6,8}\b"
            className="bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-white text-sm font-mono focus:outline-none focus:border-indigo-500"
          />
          <button
            onClick={handleAddPattern}
            disabled={createMutation.isPending}
            className="flex items-center gap-1 px-4 py-2 text-sm bg-indigo-600 hover:bg-indigo-700 disabled:opacity-50 text-white rounded-lg transition-colors"
          >
            {createMutation.isPending ? (
              <Loader2 className="w-4 h-4 animate-spin" />
            ) : (
              <Plus className="w-4 h-4" />
            )}
            Add
          </button>
        </div>

        {createMutation.isError && (
          <p className="text-sm text-red-400 mb-3">Failed to create pattern.</p>
        )}

        {/* Patterns list */}
        {patternsLoading ? (
          <div className="flex items-center gap-2 text-sm text-slate-400">
            <Loader2 className="w-4 h-4 animate-spin" />
            Loading patterns...
          </div>
        ) : patterns.length === 0 ? (
          <p className="text-sm text-slate-500">No custom patterns configured.</p>
        ) : (
          <div className="overflow-hidden rounded-lg border border-slate-700/50">
            <table className="w-full text-sm">
              <thead>
                <tr className="bg-slate-900/50 text-slate-400">
                  <th className="text-left px-3 py-2 font-medium">Name</th>
                  <th className="text-left px-3 py-2 font-medium">Category</th>
                  <th className="text-left px-3 py-2 font-medium">Pattern</th>
                  <th className="w-10 px-3 py-2" />
                </tr>
              </thead>
              <tbody>
                {patterns.map((p) => (
                  <tr
                    key={p.id}
                    className="border-t border-slate-700/50 hover:bg-slate-800/40"
                  >
                    <td className="px-3 py-2 text-white">{p.name}</td>
                    <td className="px-3 py-2">
                      <span className="inline-block px-2 py-0.5 text-xs rounded-full bg-indigo-600/20 text-indigo-300">
                        {p.category}
                      </span>
                    </td>
                    <td className="px-3 py-2">
                      <code className="text-indigo-400 font-mono text-xs">{p.pattern}</code>
                    </td>
                    <td className="px-3 py-2">
                      <button
                        onClick={() => deleteMutation.mutate(p.id)}
                        disabled={deleteMutation.isPending}
                        className="text-slate-400 hover:text-red-400 transition-colors disabled:opacity-50"
                      >
                        <Trash2 className="w-4 h-4" />
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {deleteMutation.isError && (
          <p className="text-sm text-red-400 mt-2">Failed to delete pattern.</p>
        )}
      </div>

      {/* CA Certificate */}
      <div className="bg-slate-800/50 border border-slate-700/50 rounded-xl p-5">
        <h2 className="text-base font-semibold text-white mb-4">CA Certificate</h2>
        <p className="text-sm text-slate-400 mb-4">
          Download the CA certificate to install on client machines for HTTPS interception.
        </p>
        <a
          href="/api/certificate/ca.pem"
          download
          className="inline-flex items-center gap-2 px-4 py-2 text-sm bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg transition-colors"
        >
          <Download className="w-4 h-4" />
          Download CA Certificate
        </a>
      </div>

      {/* Installation Instructions */}
      <div className="bg-slate-800/50 border border-slate-700/50 rounded-xl p-5">
        <h2 className="text-base font-semibold text-white mb-4">Installation Instructions</h2>

        <div className="flex gap-2 mb-4">
          <button
            onClick={() => setActiveTab('windows')}
            className={`flex items-center gap-2 px-4 py-2 text-sm rounded-lg transition-colors ${
              activeTab === 'windows'
                ? 'bg-indigo-600 text-white'
                : 'bg-slate-700 text-slate-300 hover:bg-slate-600'
            }`}
          >
            <Monitor className="w-4 h-4" />
            Windows
          </button>
          <button
            onClick={() => setActiveTab('mac')}
            className={`flex items-center gap-2 px-4 py-2 text-sm rounded-lg transition-colors ${
              activeTab === 'mac'
                ? 'bg-indigo-600 text-white'
                : 'bg-slate-700 text-slate-300 hover:bg-slate-600'
            }`}
          >
            <Apple className="w-4 h-4" />
            macOS
          </button>
          <button
            onClick={() => setActiveTab('linux')}
            className={`flex items-center gap-2 px-4 py-2 text-sm rounded-lg transition-colors ${
              activeTab === 'linux'
                ? 'bg-indigo-600 text-white'
                : 'bg-slate-700 text-slate-300 hover:bg-slate-600'
            }`}
          >
            <Terminal className="w-4 h-4" />
            Linux
          </button>
        </div>

        <pre className="bg-slate-900 border border-slate-700/50 rounded-lg p-4 text-sm text-slate-300 whitespace-pre-wrap font-mono">
          {instructions[activeTab]}
        </pre>
      </div>
    </div>
  )
}
