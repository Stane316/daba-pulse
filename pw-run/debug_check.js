/* Debug ciblé des 6 assertions en échec */
const { chromium } = require('playwright')
const BASE = 'http://localhost:5173'

;(async () => {
  const browser = await chromium.launch()
  const page = await browser.newPage({ viewport: { width: 1440, height: 900 } })

  // 1) SIGNAL — format du RaR carte + fond
  await page.goto(BASE + '/', { waitUntil: 'networkidle' })
  await page.waitForTimeout(3500)
  console.log('--- SIGNAL ---')
  console.log('body bg:', await page.evaluate(() => getComputedStyle(document.body).backgroundColor))
  console.log('html bg:', await page.evaluate(() => getComputedStyle(document.documentElement).backgroundColor))
  console.log('classe html:', await page.evaluate(() => document.documentElement.className))
  console.log('contient 486:', await page.evaluate(() => document.body.innerText.includes('486')))
  console.log('contient 486000:', await page.evaluate(() => document.body.innerText.includes('486000')))
  console.log('contient 486 000:', await page.evaluate(() => document.body.innerText.includes('486 000')))
  const m = await page.evaluate(() => document.body.innerText.match(/.{0,40}486.{0,40}/g))
  console.log('contexte 486:', m ? m.slice(0, 3) : 'absent')

  // 4) SIMULATION — canvas
  await page.goto(BASE + '/simulation', { waitUntil: 'networkidle' })
  await page.waitForTimeout(4000)
  console.log('\n--- SIMULATION ---')
  console.log('canvas count:', await page.evaluate(() => document.querySelectorAll('canvas').length))
  console.log('canvas visible:', await page.evaluate(() => {
    const c = document.querySelector('canvas')
    if (!c) return 'pas de canvas'
    const r = c.getBoundingClientRect()
    return `rect=${r.width}x${r.height} display=${getComputedStyle(c).display}`
  }))

  // 5) EXPLICATION — blocs + clic
  await page.goto(BASE + '/explication', { waitUntil: 'networkidle' })
  await page.waitForTimeout(3500)
  console.log('\n--- EXPLICATION ---')
  console.log('titre blocs (innerText brut):', await page.evaluate(() => {
    const t = document.body.innerText
    const i1 = t.indexOf('FAITS'); const i2 = t.indexOf('HYPOTHÈSES'); const i3 = t.indexOf('INTERPRÉTATION'); const i4 = t.indexOf('INCERTITUDE')
    return `FAITS@${i1} HYPOTH@${i2} INTERP@${i3} INCERT@${i4}`
  }))
  const btn = page.getByRole('button', { name: /Et si on envoyait 20 unités/i })
  console.log('boutons 20u trouvés:', await btn.count())
  if (await btn.count()) {
    await btn.first().click()
    await page.waitForTimeout(3000)
    const t = await page.evaluate(() => document.body.innerText)
    console.log('après clic — contient "Scénario":', t.includes('Scénario'))
    console.log('après clic — contexte 126:', (t.match(/.{0,50}126.{0,50}/g) || []).slice(0, 2))
    console.log('après clic — intention détectée:', (t.match(/Intention détectée[^\n]*/g) || [])[0] || 'absent')
  }

  // 6) THEME
  await page.goto(BASE + '/', { waitUntil: 'networkidle' })
  await page.waitForTimeout(2000)
  console.log('\n--- THEME ---')
  const btns = await page.evaluate(() => Array.from(document.querySelectorAll('button')).map(b => ({ t: b.textContent.trim().slice(0, 20), a: b.getAttribute('aria-label'), title: b.getAttribute('title') })))
  console.log('boutons:', JSON.stringify(btns.slice(0, 12), null, 1))
  const toggles = page.locator('button').filter({ has: page.locator('svg') })
  console.log('boutons avec svg:', await toggles.count())

  await browser.close()
})().catch((e) => { console.error('FATAL', e); process.exit(1) })
