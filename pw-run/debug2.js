const { chromium } = require('playwright')
const BASE = 'http://localhost:5173'
;(async () => {
  const browser = await chromium.launch()
  const page = await browser.newPage({ viewport: { width: 1440, height: 900 } })

  // reduced-motion ?
  console.log('prefers-reduced-motion:', await page.evaluate(() => matchMedia('(prefers-reduced-motion: reduce)').matches))

  // SIMULATION — scroll pour déclencher le canvas
  await page.goto(BASE + '/simulation', { waitUntil: 'networkidle' })
  await page.waitForTimeout(2500)
  console.log('canvas avant scroll:', await page.evaluate(() => document.querySelectorAll('canvas').length))
  await page.evaluate(() => window.scrollTo(0, 600))
  await page.waitForTimeout(2500)
  console.log('canvas après scroll:', await page.evaluate(() => document.querySelectorAll('canvas').length))

  // EXPLICATION — chip intention
  await page.goto(BASE + '/explication', { waitUntil: 'networkidle' })
  await page.waitForTimeout(3000)
  await page.getByRole('button', { name: /Et si on envoyait 20 unités/i }).first().click()
  await page.waitForTimeout(2500)
  const t = await page.evaluate(() => document.body.innerText)
  console.log('contient "Intention détectée":', t.includes('Intention détectée'))
  console.log('contient "Comparer des scénarios":', t.includes('Comparer des scénarios'))
  console.log('contexte intention:', (t.match(/.{0,30}Intention.{0,60}/g) || []).slice(0, 2))

  await browser.close()
})().catch(e => { console.error('FATAL', e); process.exit(1) })
