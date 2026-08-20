const { chromium } = require('playwright')
const BASE = 'http://localhost:5173'
;(async () => {
  const browser = await chromium.launch()
  const page = await browser.newPage({ viewport: { width: 1440, height: 900 } })

  // Écran 05 — après challenge 20u (blocs remplis + chip)
  await page.goto(BASE + '/explication', { waitUntil: 'networkidle' })
  await page.waitForTimeout(3000)
  await page.getByRole('button', { name: /Et si on envoyait 20 unités/i }).first().click()
  await page.waitForTimeout(3000)
  await page.screenshot({ path: '/home/user/shots/05-explication-challenge-20u.png' })

  // Écran 01 — mode sombre (toggle) + particules sur simulation 30
  await page.goto(BASE + '/simulation', { waitUntil: 'networkidle' })
  await page.waitForTimeout(2500)
  const slider = page.locator('input[type=range]')
  await slider.evaluate((el) => {
    const setter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set
    setter.call(el, '30')
    el.dispatchEvent(new Event('input', { bubbles: true }))
  })
  await page.waitForTimeout(2500)
  await page.screenshot({ path: '/home/user/shots/04-simulation-particules.png' })

  console.log('captures finales OK')
  await browser.close()
})().catch(e => { console.error('FATAL', e); process.exit(1) })
