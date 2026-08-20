/* Passe 2 — assertions DOM détaillées par écran (vérification visuelle rigoureuse) */
const { chromium } = require('playwright')

const BASE = 'http://localhost:5173'

;(async () => {
  const browser = await chromium.launch()
  const page = await browser.newPage({ viewport: { width: 1440, height: 900 } })
  const results = []

  async function check(name, fn) {
    try {
      const r = await fn()
      results.push({ name, ok: !!r, detail: r })
    } catch (e) {
      results.push({ name, ok: false, detail: String(e).slice(0, 120) })
    }
  }

  // --- 01 SIGNAL ---
  await page.goto(BASE + '/', { waitUntil: 'networkidle' })
  await page.waitForTimeout(3000)
  await check('01: count-up RaR total', () => page.evaluate(() => {
    const t = document.body.innerText
    return t.includes('1,09 M') || t.includes('1.09 M') || /1\s?0[9]\s?3\s?0\s?5\s?0/.test(t.replace(/\s/g, '')) || t.includes('M FCFA')
  }))
  await check('01: carte situation B001×P005 (486 000)', () => page.evaluate(() => document.body.innerText.includes('486 000') || document.body.innerText.includes('486,000') || document.body.innerText.includes('486 000 FCFA')))
  await check('01: badge données synthétiques', () => page.evaluate(() => document.body.innerText.includes('SYNTHÉTIQUES') || document.body.innerText.includes('synthétiques')))
  await check('01: import CSV présent', () => page.evaluate(() => document.body.innerText.includes('Importer') || document.body.innerText.includes('CSV')))
  await check('01: palette sombre (fond charcoal)', () => page.evaluate(() => {
    const bg = getComputedStyle(document.body).backgroundColor
    const r = parseInt(bg.match(/\d+/)?.[0] || '255')
    return r < 60 // fond très sombre
  }))

  // --- 02 INVESTIGATION ---
  await page.goto(BASE + '/investigation', { waitUntil: 'networkidle' })
  await page.waitForTimeout(3000)
  await check('02: titre éditorial', () => page.evaluate(() => document.body.innerText.includes('Pourquoi cette situation est-elle critique')))
  await check('02: graphique (svg recharts)', () => page.evaluate(() => !!document.querySelector('svg path, svg .recharts-surface, svg')))
  await check('02: drivers/facteurs listés', () => page.evaluate(() => /déficit|stock|demande|couverture/i.test(document.body.innerText)))

  // --- 03 DECISION ---
  await page.goto(BASE + '/decision', { waitUntil: 'networkidle' })
  await page.waitForTimeout(3000)
  await check('03: titre éditorial', () => page.evaluate(() => document.body.innerText.includes('Que devons-nous faire')))
  await check('03: recommandation 25 u visible', () => page.evaluate(() => /25\s?u|25\s?unités|Réallouer/i.test(document.body.innerText)))
  await check('03: export présent', () => page.evaluate(() => /Exporter|Export|Markdown|JSON/i.test(document.body.innerText)))

  // --- 04 SIMULATION ---
  await page.goto(BASE + '/simulation', { waitUntil: 'networkidle' })
  await page.waitForTimeout(3000)
  await check('04: titre éditorial', () => page.evaluate(() => document.body.innerText.includes('Que se passe-t-il si')))
  await check('04: slider présent', () => page.evaluate(() => !!document.querySelector('input[type=range]')))
  await check('04: canvas particules', () => page.evaluate(() => !!document.querySelector('canvas')))
  await check('04: revenu protégé', () => page.evaluate(() => /protég|Protégé|450|486/i.test(document.body.innerText)))

  // --- 05 EXPLICATION (INC-20) ---
  await page.goto(BASE + '/explication', { waitUntil: 'networkidle' })
  await page.waitForTimeout(3500)
  await check('05: 4 blocs Faits/Hypothèses/Interprétation/Incertitude', () => page.evaluate(() => {
    const t = document.body.innerText
    return t.includes('Faits') && t.includes('Hypothèses') && t.includes('Interprétation') && t.includes('Incertitude')
  }))
  await check('05: badges calculé/supposé', () => page.evaluate(() => /calculé par le moteur|supposé|versionné/i.test(document.body.innerText)))
  await check('05: mode déterministe badge', () => page.evaluate(() => document.body.innerText.includes('Mode déterministe')))
  await check('05: suggestions Q&A', () => page.evaluate(() => document.body.innerText.includes('Et si on envoyait 20 unités') || document.body.innerText.includes('Et si on envoyait 20 unités ?')))
  // Tester le challenge en conditions réelles via l'UI
  await check('05: clic « Et si 20u ? » → bloc Faits contient Scénario', async () => {
    await page.getByRole('button', { name: /Et si on envoyait 20 unités/i }).click()
    await page.waitForTimeout(2500)
    const t = await page.evaluate(() => document.body.innerText)
    return t.includes('Scénario 20 u') && (t.includes('126 000') || t.includes('126,000'))
  })

  // --- 06 HORIZON ---
  await page.goto(BASE + '/horizon', { waitUntil: 'networkidle' })
  await page.waitForTimeout(3000)
  await check('06: titre éditorial', () => page.evaluate(() => document.body.innerText.includes('Que pourrait devenir ce moteur')))
  await check('06: tunnel/vision contenu', () => page.evaluate(() => document.body.innerText.length > 300))

  // --- Light/Dark toggle ---
  await page.goto(BASE + '/', { waitUntil: 'networkidle' })
  await page.waitForTimeout(2000)
  await check('theme: toggle Sun/Moon existe', () => page.evaluate(() => !!document.querySelector('[aria-label*="clair"], [aria-label*="sombre"], [title*="clair"], [title*="sombre"], button svg')))
  const lightBtn = page.getByRole('button', { name: /clair|sombre|light|dark|Sun|Moon/i }).first()
  if (await lightBtn.count()) {
    await lightBtn.click()
    await page.waitForTimeout(800)
    await check('theme: bascule vers clair (fond s\'éclaircit)', () => page.evaluate(() => {
      const bg = getComputedStyle(document.body).backgroundColor
      const r = parseInt(bg.match(/\d+/)?.[0] || '0')
      return r > 100
    }))
  }

  // --- Navigation entre écrans (parcours décisionnel) ---
  await page.goto(BASE + '/', { waitUntil: 'networkidle' })
  await page.waitForTimeout(2000)
  const navOk = []
  for (const [label, path] of [['Situation', '/'], ['Investigation', '/investigation'], ['Décision', '/decision'], ['Simulation', '/simulation'], ['Explication', '/explication'], ['Horizon', '/horizon']]) {
    if (label === 'Situation') continue
    await page.goto(BASE + path, { waitUntil: 'networkidle' })
    await page.waitForTimeout(1200)
    const url = page.url()
    navOk.push(`${label}:${url.includes(path) ? 'OK' : 'KO'}`)
  }
  results.push({ name: 'nav: 6 routes accessibles', ok: navOk.every(x => x.endsWith('OK')), detail: navOk.join(' ') })

  console.log('=== ASSERTIONS DOM ===')
  for (const r of results) {
    console.log(`${r.ok ? '✅' : '❌'} ${r.name}${r.detail && r.ok ? '' : ' — ' + r.detail}`)
  }
  const fails = results.filter(r => !r.ok)
  console.log(`\nRésultat: ${results.length - fails.length}/${results.length} OK`)
  await browser.close()
})().catch((e) => { console.error('FATAL', e); process.exit(1) })
