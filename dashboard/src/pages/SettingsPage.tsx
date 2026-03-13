import { useState } from 'react'
import { Download, Plus, X, Monitor, Apple, Terminal } from 'lucide-react'

export default function SettingsPage() {
  const [retentionDays, setRetentionDays] = useState(90)
  const [patterns, setPatterns] = useState<string[]>([])
  const [newPattern, setNewPattern] = useState('')
  const [activeTab, setActiveTab] = useState<'windows' | 'mac' | 'linux'>('mac')

  function addPattern() {
    const trimmed = newPattern.trim()
    if (trimmed && !patterns.includes(trimmed)) {
      setPatterns([...patterns, trimmed])
      setNewPattern('')
    }
  }

  function removePattern(p: string) {
    setPatterns(patterns.filter((v) => v !== p))
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
          <input
            type="number"
            min={1}
            max={365}
            value={retentionDays}
            onChange={(e) => setRetentionDays(Number(e.target.value))}
            className="w-24 bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-white text-sm focus:outline-none focus:border-indigo-500"
          />
          <span className="text-sm text-slate-400">days</span>
          <button className="ml-4 px-4 py-2 text-sm bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg transition-colors">
            Save
          </button>
        </div>
      </div>

      {/* Custom Patterns */}
      <div className="bg-slate-800/50 border border-slate-700/50 rounded-xl p-5">
        <h2 className="text-base font-semibold text-white mb-4">Custom Detection Patterns</h2>
        <p className="text-sm text-slate-400 mb-3">
          Add custom regex patterns for detecting sensitive data in AI traffic.
        </p>
        <div className="flex gap-2 mb-4">
          <input
            type="text"
            value={newPattern}
            onChange={(e) => setNewPattern(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && addPattern()}
            placeholder="e.g. \b[A-Z]{2}\d{6,8}\b"
            className="flex-1 bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-white text-sm font-mono focus:outline-none focus:border-indigo-500"
          />
          <button
            onClick={addPattern}
            className="flex items-center gap-1 px-4 py-2 text-sm bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg transition-colors"
          >
            <Plus className="w-4 h-4" />
            Add
          </button>
        </div>
        <div className="space-y-2">
          {patterns.length === 0 && (
            <p className="text-sm text-slate-500">No custom patterns configured.</p>
          )}
          {patterns.map((p) => (
            <div
              key={p}
              className="flex items-center justify-between bg-slate-900/50 border border-slate-700/50 rounded-lg px-3 py-2"
            >
              <code className="text-sm text-indigo-400 font-mono">{p}</code>
              <button
                onClick={() => removePattern(p)}
                className="text-slate-400 hover:text-red-400 transition-colors"
              >
                <X className="w-4 h-4" />
              </button>
            </div>
          ))}
        </div>
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
