/* Vérification visuelle des 6 écrans DabaPulse — Playwright */
const { chromium } = require('playwright')

const BASE = 'http://localhost:5173'
const ROUTES = [
  { path: '/', name: '01-signal-situation' },
  { path: '/investigation', name: '02-investigation' },
  { path: '/decision', name: '03-decision' },
  { path: '/simulation', name: '04-simulation' },
  { path: '/explication', name: '05-explication' },
  { path: '/horizon', name: '06-horizon' },
]

;(async () => {
  const browser = await chromium.launch()
  const page = await browser.newPage({ viewport: { width: 1440, height: 900 } })
  const errors = []
  page.on('console', (msg) => {
    if (msg.type() === 'error') errors.push(`[console] ${msg.text().slice(0, 200)}`)
  })
  page.on('pageerror', (err) => errors.push(`[pageerror] ${String(err).slice(0, 200)}`))

  const report = []
  for (const route of ROUTES) {
    const url = BASE + route.path
    let ok = true
    let note = ''
    try {
      const resp = await page.goto(url, { waitUntil: 'networkidle', timeout: 30000 })
      if (!resp || resp.status() >= 400) {
        ok = false
        note = `HTTP ${resp ? resp.status() : 'ERR'}`
      } else {
        // attendre le rendu (count-up, skeletons, data)
        await page.waitForTimeout(3500)
        const h = await page.evaluate(() => document.querySelector('h1, h2')?.textContent?.trim()?.slice(0, 80) ?? '(pas de titre)')
        const text = await page.evaluate(() => document.body.innerText.slice(0, 220).replace(/\n+/g, ' · '))
        note = `h1/h2: ${h}`
        const path = `shots/${route.name}.png`
        await page.screenshot({ path, fullPage: false })
        report.push({ route: route.path, ok, note, text })
      }
    } catch (e) {
      ok = false
      note = String(e).slice(0, 160)
      report.push({ route: route.path, ok, note, text: '' })
    }
  }

  console.log('=== RAPPORT VISUEL ===')
  for (const r of report) {
    console.log(`${r.ok ? '✅' : '❌'} ${r.route} — ${r.note}`)
    if (r.ok) console.log(`   contenu: ${r.text}`)
  }
  console.log('=== ERREURS CONSOLE ===')
  console.log(errors.length ? errors.slice(0, 10).join('\n') : 'aucune erreur console')
  await browser.close()
})().catch((e) => { console.error('FATAL', e); process.exit(1) })
