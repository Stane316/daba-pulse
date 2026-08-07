import { ArrowLeft, ArrowRight, Moon, Sun } from 'lucide-react'
import { NavLink, useLocation, useNavigate } from 'react-router-dom'
import type { ReactNode } from 'react'
import { SCENES } from '../lib/scenes'
import { cn, SyntheticBadge } from './ui'
import { usePulse } from '../context/PulseContext'
import { useTheme } from '../context/ThemeContext'
import { formatFCFA } from '../lib/format'

export function TheaterShell({ children }: { children: ReactNode }) {
  const location = useLocation()
  const navigate = useNavigate()
  const { summary, selected } = usePulse()
  const { theme, toggle } = useTheme()

  const currentIndex = Math.max(
    0,
    SCENES.findIndex((s) =>
      s.path === '/'
        ? location.pathname === '/'
        : location.pathname.startsWith(s.path),
    ),
  )
  const current = SCENES[currentIndex] ?? SCENES[0]
  const prev = SCENES[currentIndex - 1]
  const next = SCENES[currentIndex + 1]

  return (
    <div className="relative min-h-screen overflow-x-hidden">
      {/* Atmospheric background */}
      <div className="pointer-events-none fixed inset-0 -z-10">
        <div className="absolute inset-0 bg-charcoal-deep" />
        <div
          className="absolute -left-32 top-0 h-[520px] w-[520px] rounded-full opacity-30 blur-3xl"
          style={{
            background:
              'radial-gradient(circle, rgba(36,79,89,0.55) 0%, transparent 70%)',
          }}
        />
        <div
          className="absolute -right-20 bottom-0 h-[480px] w-[480px] rounded-full opacity-25 blur-3xl"
          style={{
            background:
              'radial-gradient(circle, rgba(169,75,75,0.35) 0%, transparent 70%)',
          }}
        />
        <div
          className="absolute left-1/2 top-1/3 h-[300px] w-[600px] -translate-x-1/2 rounded-full opacity-20 blur-3xl"
          style={{
            background:
              'radial-gradient(circle, rgba(201,150,58,0.2) 0%, transparent 70%)',
          }}
        />
        {/* Organic flow lines */}
        <svg
          className="absolute inset-0 h-full w-full opacity-[0.07]"
          xmlns="http://www.w3.org/2000/svg"
        >
          <path
            d="M-20 200 C 200 100, 400 300, 700 180 S 1200 100, 1400 250"
            stroke="#D8C9AE"
            strokeWidth="1"
            fill="none"
          />
          <path
            d="M-40 420 C 250 520, 450 300, 800 400 S 1100 500, 1500 380"
            stroke="#244F59"
            strokeWidth="1.2"
            fill="none"
          />
        </svg>
      </div>

      {/* Top bar — not a generic SaaS navbar */}
      <header className="sticky top-0 z-40 border-b border-white/5 bg-charcoal-deep/80 backdrop-blur-md">
        <div className="mx-auto flex max-w-[1400px] items-center justify-between gap-4 px-5 py-3 md:px-8">
          <div className="flex items-center gap-4">
            <div className="flex items-center gap-2.5">
              <div className="flex h-8 w-8 items-center justify-center rounded-md border border-amber/30 bg-charcoal">
                <svg width="16" height="16" viewBox="0 0 32 32" fill="none">
                  <path
                    d="M8 22 L16 8 L24 22"
                    stroke="#C9963A"
                    strokeWidth="2.4"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                  />
                  <circle cx="16" cy="18" r="2.2" fill="#A94B4B" />
                </svg>
              </div>
              <div>
                <div className="text-sm font-semibold tracking-wide text-bone">
                  DabaPulse
                </div>
                <div className="text-[10px] uppercase tracking-[0.18em] text-mineral">
                  Decision Theater
                </div>
              </div>
            </div>
            <div className="hidden h-6 w-px bg-white/10 sm:block" />
            <SyntheticBadge />
            <button
              type="button"
              onClick={toggle}
              aria-label={theme === 'dark' ? 'Passer en mode clair' : 'Passer en mode sombre'}
              title={theme === 'dark' ? 'Mode clair' : 'Mode sombre'}
              className="inline-flex h-8 w-8 items-center justify-center rounded-full border border-white/10 bg-white/5 text-mineral transition hover:border-amber/30 hover:bg-white/10 hover:text-bone"
            >
              {theme === 'dark' ? <Sun size={14} /> : <Moon size={14} />}
            </button>
          </div>

          <div className="hidden items-center gap-6 md:flex">
            {summary && (
              <div className="text-right">
                <div className="text-[10px] uppercase tracking-[0.16em] text-mineral">
                  RaR total
                </div>
                <div className="num text-sm font-semibold text-risk-soft">
                  {formatFCFA(summary.revenue_at_risk_total, true)}
                </div>
              </div>
            )}
            {selected && (
              <div className="max-w-[200px] truncate text-right text-xs text-bone-dim">
                {selected.boutique?.nom ?? 'Réputation globale'}
                {selected.produit ? ` · ${selected.produit.nom}` : ''}
              </div>
            )}
          </div>
        </div>

        {/* Scene rail */}
        <nav className="mx-auto max-w-[1400px] overflow-x-auto px-5 md:px-8">
          <ol className="flex min-w-max items-stretch gap-1 pb-3">
            {SCENES.map((scene, i) => {
              const active = i === currentIndex
              const done = i < currentIndex
              return (
                <li key={scene.id} className="flex items-center">
                  <NavLink
                    to={scene.path}
                    className={cn(
                      'group flex items-center gap-2 rounded-full px-3 py-1.5 text-xs transition',
                      active && 'bg-white/8 text-bone',
                      !active && done && 'text-sand/80 hover:text-bone',
                      !active && !done && 'text-mineral hover:text-bone-dim',
                    )}
                  >
                    <span
                      className={cn(
                        'num flex h-5 w-5 items-center justify-center rounded-full text-[10px] font-semibold',
                        active && 'bg-amber text-charcoal',
                        done && !active && 'bg-sage/30 text-sage-light',
                        !active && !done && 'bg-white/5 text-mineral',
                      )}
                    >
                      {scene.index}
                    </span>
                    <span className="hidden sm:inline">{scene.label}</span>
                  </NavLink>
                  {i < SCENES.length - 1 && (
                    <span
                      className={cn(
                        'mx-1 h-px w-4 md:w-8',
                        i < currentIndex ? 'bg-sage/50' : 'bg-white/10',
                      )}
                    />
                  )}
                </li>
              )
            })}
          </ol>
        </nav>
      </header>

      {/* Main stage */}
      <main id="main-content" tabIndex={-1} className="mx-auto max-w-[1400px] px-5 py-8 outline-none md:px-8 md:py-10">
        {children}
      </main>

      {/* Bottom navigation — story progression */}
      <footer className="sticky bottom-0 z-30 border-t border-white/5 bg-charcoal-deep/90 backdrop-blur-md">
        <div className="mx-auto flex max-w-[1400px] items-center justify-between gap-4 px-5 py-3 md:px-8">
          <button
            type="button"
            disabled={!prev}
            onClick={() => prev && navigate(prev.path)}
            className="inline-flex items-center gap-2 rounded-full px-3 py-2 text-sm text-bone-dim transition hover:bg-white/5 hover:text-bone disabled:opacity-30"
          >
            <ArrowLeft size={16} />
            <span className="hidden sm:inline">{prev?.label ?? '—'}</span>
          </button>

          <div className="text-center">
            <div className="text-[10px] uppercase tracking-[0.2em] text-mineral">
              Scène {current.index} / {SCENES.length}
            </div>
            <div className="max-w-md truncate text-xs text-bone-dim">
              {current.question}
            </div>
          </div>

          <button
            type="button"
            disabled={!next}
            onClick={() => next && navigate(next.path)}
            className={cn(
              'inline-flex items-center gap-2 rounded-full px-4 py-2 text-sm font-medium transition',
              next
                ? 'bg-amber text-charcoal hover:bg-sand'
                : 'text-mineral opacity-30',
            )}
          >
            <span className="hidden sm:inline">{next?.label ?? 'Fin'}</span>
            <ArrowRight size={16} />
          </button>
        </div>
      </footer>
    </div>
  )
}
