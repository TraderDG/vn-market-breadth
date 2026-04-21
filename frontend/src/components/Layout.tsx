import { NavLink, Outlet, useNavigate } from 'react-router-dom'
import { useActiveSignals } from '../hooks/useQueries'
import { triggerRefresh } from '../api/breadth'
import { useState } from 'react'
import clsx from 'clsx'

const NAV = [
  { to: '/',          label: 'Overview',       icon: '◉' },
  { to: '/ad',        label: 'A/D Line',       icon: '〰' },
  { to: '/nh-nl',     label: 'NH-NL',          icon: '△▽' },
  { to: '/volume',    label: 'Volume',          icon: '▊' },
  { to: '/above-ma',  label: '% Above MA',     icon: '▲' },
  { to: '/signals',   label: 'Signals',         icon: '⚡' },
]

export default function Layout() {
  const { data: activeSignals } = useActiveSignals()
  const [refreshing, setRefreshing] = useState(false)
  const signalCount = activeSignals?.count ?? 0

  const handleRefresh = async () => {
    setRefreshing(true)
    try { await triggerRefresh() } catch {}
    setRefreshing(false)
  }

  return (
    <div className="flex h-screen overflow-hidden">
      {/* Sidebar */}
      <aside className="w-48 flex-shrink-0 bg-brand-surface border-r border-brand-border flex flex-col">
        {/* Logo */}
        <div className="px-4 py-4 border-b border-brand-border">
          <div className="text-brand-text font-bold text-sm">VN Market Breadth</div>
          <div className="text-brand-muted text-xs font-mono mt-0.5">26 Indicators</div>
        </div>

        {/* Nav */}
        <nav className="flex-1 px-2 py-3 space-y-0.5">
          {NAV.map(({ to, label, icon }) => (
            <NavLink
              key={to}
              to={to}
              end={to === '/'}
              className={({ isActive }) => clsx(
                'flex items-center gap-2.5 px-3 py-2 rounded-lg text-sm transition-colors',
                isActive
                  ? 'bg-brand-accent/15 text-brand-accent font-medium'
                  : 'text-brand-muted hover:text-brand-text hover:bg-brand-border/40'
              )}
            >
              <span className="font-mono text-xs w-5 text-center">{icon}</span>
              <span>{label}</span>
              {label === 'Signals' && signalCount > 0 && (
                <span className="ml-auto text-xs bg-brand-bear text-white rounded-full w-4 h-4 flex items-center justify-center font-mono">
                  {signalCount}
                </span>
              )}
            </NavLink>
          ))}
        </nav>

        {/* Refresh button */}
        <div className="px-2 py-3 border-t border-brand-border">
          <button
            onClick={handleRefresh}
            disabled={refreshing}
            className="w-full px-3 py-1.5 text-xs font-mono text-brand-muted hover:text-brand-text border border-brand-border rounded-lg transition-colors disabled:opacity-50"
          >
            {refreshing ? 'Refreshing...' : '↻ Refresh Data'}
          </button>
        </div>
      </aside>

      {/* Main content */}
      <main className="flex-1 overflow-y-auto p-5">
        <Outlet />
      </main>
    </div>
  )
}
