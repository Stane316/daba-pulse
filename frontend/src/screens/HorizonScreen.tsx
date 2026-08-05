import { Panel, SceneQuestion } from '../components/ui'

const PHASES = [
  {
    phase: 'Aujourd\'hui',
    title: 'Protect Revenue',
    items: [
      'Smart Distribution',
      'Revenue-at-Risk',
      'Decision Engine',
      'What-if Simulation',
      'Visibility & Reputation',
    ],
    tone: 'now' as const,
  },
  {
    phase: 'Demain',
    title: 'Grow Revenue',
    items: [
      'Demand Intelligence',
      'Product Intelligence',
      'Customer Intelligence',
      'Partnership Intelligence',
      'Growth & Conversion',
    ],
    tone: 'next' as const,
  },
  {
    phase: 'Horizon',
    title: 'Business Twin',
    items: [
      'Executive Copilot',
      'Growth Memory',
      'Business Twin',
      'Mémoire des décisions',
      'Apprentissage continu',
    ],
    tone: 'far' as const,
  },
]

const ECOSYSTEM = [
  {
    name: 'Ferme Expérience',
    desc: 'Transformer la ferme en destination pédagogique — chaque visiteur devient client et ambassadeur.',
  },
  {
    name: 'Media Partnership',
    desc: 'Mesurer quel partenariat radio/TV apporte le meilleur retour sur investissement.',
  },
  {
    name: 'DABA Academy',
    desc: 'Formations élevage, provende, biogaz — nouveaux revenus pédagogiques.',
  },
  {
    name: 'DABA Club',
    desc: 'Fidélité et lifetime value : points, cadeaux, visites VIP.',
  },
  {
    name: 'QR Code Marketing',
    desc: 'Pont produit physique → écosystème digital : origine, recettes, conseils.',
  },
]

export function HorizonScreen() {
  return (
    <div>
      <SceneQuestion
        index={6}
        question="Que pourrait devenir ce moteur demain ?"
        eyebrow="Growth Horizon"
      />

      <section className="animate-fade-up mb-12 overflow-hidden rounded-3xl border border-white/5 bg-gradient-to-br from-charcoal via-petrol/20 to-charcoal p-8 md:p-12">
        <div className="grid items-center gap-8 md:grid-cols-2">
          <div>
            <div className="text-[11px] uppercase tracking-[0.22em] text-sage-light">
              Aujourd'hui
            </div>
            <h2 className="font-display mt-2 text-4xl text-bone md:text-5xl">
              Protect Revenue
            </h2>
            <p className="mt-4 text-sm leading-relaxed text-bone-dim">
              Le MVP démontre une chaîne complète : signal → risque → valeur →
              décision → simulation → impact. C'est la preuve que DABA peut
              protéger son revenu avant de le perdre.
            </p>
          </div>
          <div className="text-right md:text-left">
            <div className="text-[11px] uppercase tracking-[0.22em] text-amber">
              Demain
            </div>
            <h2 className="font-display mt-2 text-4xl text-amber md:text-5xl">
              Grow Revenue
            </h2>
            <p className="mt-4 text-sm leading-relaxed text-bone-dim">
              Le même moteur s'étend progressivement à la demande, aux produits,
              aux clients, aux partenariats et à la conversion — jusqu'au
              Business Twin.
            </p>
          </div>
        </div>

        <div className="mt-10 flex items-center gap-3">
          <div className="h-1 flex-1 rounded-full bg-sage/50" />
          <div className="text-[10px] uppercase tracking-[0.2em] text-mineral">
            évolution
          </div>
          <div className="h-1 flex-1 rounded-full bg-gradient-to-r from-amber/50 to-amber" />
        </div>
      </section>

      <div className="mb-10 grid gap-4 md:grid-cols-3">
        {PHASES.map((p, i) => (
          <Panel
            key={p.title}
            delay={i + 1}
            className={
              p.tone === 'now'
                ? 'border-sage/30'
                : p.tone === 'next'
                  ? 'border-amber/20'
                  : 'border-plum/30'
            }
          >
            <div className="text-[10px] uppercase tracking-[0.2em] text-mineral">
              {p.phase}
            </div>
            <h3 className="font-display mt-2 text-2xl text-bone">{p.title}</h3>
            <ul className="mt-4 space-y-2">
              {p.items.map((item) => (
                <li
                  key={item}
                  className="flex items-center gap-2 text-sm text-bone-dim"
                >
                  <span
                    className={`h-1.5 w-1.5 rounded-full ${
                      p.tone === 'now'
                        ? 'bg-sage'
                        : p.tone === 'next'
                          ? 'bg-amber'
                          : 'bg-plum'
                    }`}
                  />
                  {item}
                </li>
              ))}
            </ul>
            {p.tone !== 'now' && (
              <div className="mt-4 text-[10px] uppercase tracking-[0.14em] text-mineral">
                Vision — non livré dans le MVP
              </div>
            )}
          </Panel>
        ))}
      </div>

      <div className="mb-4">
        <h3 className="font-display text-2xl text-bone">
          Revenue Growth Ecosystem
        </h3>
        <p className="mt-2 max-w-2xl text-sm text-mineral">
          Extensions stratégiques post-MVP. Aucune de ces briques n'est présentée
          comme livrée aujourd'hui — elles illustrent comment le moteur pourra
          créer de nouvelles sources de revenu.
        </p>
      </div>

      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
        {ECOSYSTEM.map((e, i) => (
          <Panel key={e.name} delay={Math.min(i + 1, 5)} className="!p-4">
            <div className="text-sm font-semibold text-sand">{e.name}</div>
            <p className="mt-2 text-xs leading-relaxed text-bone-dim">{e.desc}</p>
          </Panel>
        ))}
      </div>

      <section className="animate-fade-up delay-3 mt-12 rounded-3xl border border-white/5 bg-charcoal/60 p-8 text-center md:p-12">
        <div className="text-[11px] uppercase tracking-[0.22em] text-mineral">
          La chaîne à retenir
        </div>
        <p className="font-display mx-auto mt-4 max-w-3xl text-2xl leading-snug text-bone md:text-3xl">
          Risque <span className="text-mineral">→</span> Argent{' '}
          <span className="text-mineral">→</span> Décision{' '}
          <span className="text-mineral">→</span> Impact
        </p>
        <p className="mx-auto mt-6 max-w-xl text-sm text-bone-dim">
          Un dashboard montre le problème. DabaPulse estime ce qu'il peut coûter
          et aide à décider quoi faire.
        </p>
        <div className="mt-8 text-xs text-mineral">
          DabaPulse — From business signals to better decisions.
        </div>
      </section>
    </div>
  )
}
