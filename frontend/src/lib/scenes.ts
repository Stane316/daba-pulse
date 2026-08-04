import type { SceneMeta } from '../types'

export const SCENES: SceneMeta[] = [
  {
    id: 'situation',
    index: 1,
    label: 'Situation',
    question: 'Où le revenu est-il exposé maintenant ?',
    path: '/',
  },
  {
    id: 'investigation',
    index: 2,
    label: 'Investigation',
    question: 'Pourquoi cette situation est-elle critique ?',
    path: '/investigation',
  },
  {
    id: 'decision',
    index: 3,
    label: 'Décision',
    question: 'Que devons-nous faire ?',
    path: '/decision',
  },
  {
    id: 'simulation',
    index: 4,
    label: 'Simulation',
    question: "Que se passe-t-il si j'applique cette décision ?",
    path: '/simulation',
  },
  {
    id: 'explication',
    index: 5,
    label: 'Explication',
    question: 'Pourquoi cette décision est-elle recommandée ?',
    path: '/explication',
  },
  {
    id: 'horizon',
    index: 6,
    label: 'Horizon',
    question: 'Que pourrait devenir ce moteur demain ?',
    path: '/horizon',
  },
]
