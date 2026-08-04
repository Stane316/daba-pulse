import {
  Area,
  AreaChart,
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'

const tooltipStyle = {
  background: '#1F2523',
  border: '1px solid rgba(255,255,255,0.08)',
  borderRadius: 10,
  fontSize: 12,
  color: '#F1EBDD',
}

export function DemandStockBars({
  demande,
  stock,
  deficit,
}: {
  demande: number
  stock: number
  deficit: number
}) {
  const data = [
    { name: 'Demande', value: demande, fill: '#C9963A' },
    { name: 'Stock', value: stock, fill: '#244F59' },
    { name: 'Déficit', value: deficit, fill: '#A94B4B' },
  ]
  return (
    <div className="h-44 w-full">
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={data} barCategoryGap="28%">
          <CartesianGrid stroke="rgba(255,255,255,0.04)" vertical={false} />
          <XAxis
            dataKey="name"
            tick={{ fill: '#657A7D', fontSize: 11 }}
            axisLine={false}
            tickLine={false}
          />
          <YAxis
            tick={{ fill: '#657A7D', fontSize: 11 }}
            axisLine={false}
            tickLine={false}
            width={32}
          />
          <Tooltip
            cursor={{ fill: 'rgba(255,255,255,0.03)' }}
            contentStyle={tooltipStyle}
            formatter={(v) => [`${v} u.`, '']}
          />
          <Bar dataKey="value" radius={[6, 6, 0, 0]}>
            {data.map((d) => (
              <Cell key={d.name} fill={d.fill} />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  )
}

export function HistoryArea({
  data,
}: {
  data: { date: string; ventes: number; stock: number }[]
}) {
  if (!data?.length) {
    return (
      <div className="flex h-40 items-center justify-center text-xs text-mineral">
        Historique indisponible
      </div>
    )
  }
  const chartData = data.map((d) => ({
    ...d,
    label: d.date.slice(5),
  }))
  return (
    <div className="h-44 w-full">
      <ResponsiveContainer width="100%" height="100%">
        <AreaChart data={chartData}>
          <defs>
            <linearGradient id="gVentes" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor="#C9963A" stopOpacity={0.45} />
              <stop offset="100%" stopColor="#C9963A" stopOpacity={0} />
            </linearGradient>
            <linearGradient id="gStock" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor="#244F59" stopOpacity={0.45} />
              <stop offset="100%" stopColor="#244F59" stopOpacity={0} />
            </linearGradient>
          </defs>
          <CartesianGrid stroke="rgba(255,255,255,0.04)" vertical={false} />
          <XAxis
            dataKey="label"
            tick={{ fill: '#657A7D', fontSize: 10 }}
            axisLine={false}
            tickLine={false}
          />
          <YAxis
            tick={{ fill: '#657A7D', fontSize: 10 }}
            axisLine={false}
            tickLine={false}
            width={28}
          />
          <Tooltip contentStyle={tooltipStyle} />
          <Area
            type="monotone"
            dataKey="ventes"
            name="Ventes"
            stroke="#C9963A"
            fill="url(#gVentes)"
            strokeWidth={2}
          />
          <Area
            type="monotone"
            dataKey="stock"
            name="Stock"
            stroke="#2f6673"
            fill="url(#gStock)"
            strokeWidth={1.5}
          />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  )
}

export function RarComparisonBars({
  avant,
  apres,
}: {
  avant: number
  apres: number
}) {
  const max = Math.max(avant, apres, 1)
  return (
    <div className="space-y-4">
      <BarRow label="Avant" value={avant} max={max} color="#A94B4B" />
      <BarRow label="Après" value={apres} max={max} color="#4F7463" />
    </div>
  )
}

function BarRow({
  label,
  value,
  max,
  color,
}: {
  label: string
  value: number
  max: number
  color: string
}) {
  const pct = Math.max(2, (value / max) * 100)
  return (
    <div>
      <div className="mb-1.5 flex justify-between text-xs">
        <span className="text-mineral">{label}</span>
        <span className="num text-bone">
          {Math.round(value).toLocaleString('fr-FR')} FCFA
        </span>
      </div>
      <div className="h-3 overflow-hidden rounded-full bg-charcoal-soft">
        <div
          className="h-full origin-left rounded-full transition-all duration-700 ease-out"
          style={{
            width: `${pct}%`,
            background: color,
            animation: 'bar-grow 0.8s cubic-bezier(0.22,1,0.36,1) both',
          }}
        />
      </div>
    </div>
  )
}
