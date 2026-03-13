import { NavLink, useNavigate } from 'react-router-dom'
import { LayoutDashboard, FileText, Shield, Settings, Zap, LogOut } from 'lucide-react'
import { clsx } from 'clsx'
import { useAuth } from '../contexts/AuthContext'

const navItems = [
  { to: '/', label: 'Dashboard', icon: LayoutDashboard },
  { to: '/logs', label: 'Logs', icon: FileText },
  { to: '/policies', label: 'Políticas', icon: Shield },
  { to: '/settings', label: 'Configurações', icon: Settings },
]

export default function Sidebar() {
  const { username, logout } = useAuth()
  const navigate = useNavigate()

  function handleLogout() {
    logout()
    navigate('/login')
  }

  return (
    <aside className="fixed left-0 top-0 h-screen w-64 bg-slate-900 border-r border-slate-700/50 flex flex-col z-50">
      <div className="flex items-center gap-3 px-6 py-5 border-b border-slate-700/50">
        <div className="bg-indigo-600 rounded-lg p-2">
          <Zap className="w-5 h-5 text-white" />
        </div>
        <span className="text-lg font-bold text-white tracking-tight">AIGateway</span>
      </div>

      <nav className="flex-1 px-3 py-4 space-y-1">
        {navItems.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            end={item.to === '/'}
            className={({ isActive }) =>
              clsx(
                'flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors',
                isActive
                  ? 'bg-indigo-600/20 text-indigo-400'
                  : 'text-slate-400 hover:text-white hover:bg-slate-800'
              )
            }
          >
            <item.icon className="w-5 h-5" />
            {item.label}
          </NavLink>
        ))}
      </nav>

      <div className="px-4 py-4 border-t border-slate-700/50 space-y-3">
        {username && (
          <p className="text-xs text-slate-400 truncate">Signed in as <span className="font-medium text-slate-300">{username}</span></p>
        )}
        <button
          onClick={handleLogout}
          className="flex items-center gap-2 w-full px-3 py-2 rounded-lg text-sm font-medium text-slate-400 hover:text-white hover:bg-slate-800 transition-colors"
        >
          <LogOut className="w-4 h-4" />
          Logout
        </button>
        <p className="text-xs text-slate-500">AIGateway Interceptor v1.0</p>
      </div>
    </aside>
  )
}
