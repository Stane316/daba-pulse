const { chromium } = require('playwright')
const BASE = 'http://localhost:5173'
;(async () => {
  const browser = await chromium.launch()
  const page = await browser.newPage({ viewport: { width: 1440, height: 900 } })

  // SIMULATION — slider à 30 → déficit 0 → particules
  await page.goto(BASE + '/simulation', { waitUntil: 'networkidle' })
  await page.waitForTimeout(2500)
  console.log('canvas (reco 25u):', await page.evaluate(() => document.querySelectorAll('canvas').length))
  const slider = page.locator('input[type=range]')
  console.log('slider présent:', await slider.count())
  if (await slider.count()) {
    await slider.evaluate((el) => {
      const setter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set
      setter.call(el, '30')
      el.dispatchEvent(new Event('input', { bubbles: true }))
      el.dispatchEvent(new Event('change', { bubbles: true }))
    })
    await page.waitForTimeout(2500)
    console.log('canvas après slider=30:', await page.evaluate(() => document.querySelectorAll('canvas').length))
    const t = await page.evaluate(() => document.body.innerText)
    console.log('contient 486 000 / protégé:', /486|protégé/i.test(t))
  }

  // EXPLICATION — chip intention (casse insensible)
  await page.goto(BASE + '/explication', { waitUntil: 'networkidle' })
  await page.waitForTimeout(3000)
  await page.getByRole('button', { name: /Et si on envoyait 20 unités/i }).first().click()
  await page.waitForTimeout(2500)
  const t = await page.evaluate(() => document.body.innerText)
  console.log('INTENTION (uppercase trouvé):', t.toLowerCase().includes('intention détectée'))
  console.log('COMPARER (uppercase):', t.toLowerCase().includes('comparer des scénarios'))

  await browser.close()
})().catch(e => { console.error('FATAL', e); process.exit(1) })
