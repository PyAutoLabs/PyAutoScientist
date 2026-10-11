// Optional rendered-page check: NODE_PATH=<playwright modules> node
// tests/projects_browser.cjs <rendered fixture HTML> <evidence directory>
const { chromium } = require('playwright');
const { pathToFileURL } = require('node:url');
const path = require('node:path');
const fs = require('node:fs');
const assert = require('node:assert/strict');

(async () => {
  const browser = await chromium.launch({ headless: true, channel: "chromium" });
  const destination = pathToFileURL(path.resolve(process.argv[2])).href;
  const evidence = path.resolve(process.argv[3]);
  fs.mkdirSync(evidence, { recursive: true });
  let cases = 0;
  try {
    for (const width of [390, 768, 1440]) {
      for (const colorScheme of ['light', 'dark']) {
        const context = await browser.newContext({ viewport: { width, height: 1000 }, colorScheme });
        await context.route('https://**/*', route => route.fulfill({ status: 503, body: '{}' }));
        const page = await context.newPage();
        const errors = [];
        page.on('pageerror', error => errors.push(error.message));
        await page.goto(destination);
        await page.waitForFunction(() => !refreshing);
        assert.equal(await page.locator('.project-card').count(), 6);
        assert(await page.locator('#projects-heading').isVisible());
        assert(await page.locator('#dashboards-heading').isVisible());
        assert.equal(await page.locator('#dashboards details').first().getAttribute('id'), 'board-brain');
        for (const [name, resource] of [['Pulse', 'lens-profiling'], ['Insight', 'lens-inference'],
                                       ['Eyes', 'lens-visualization'], ['Heart', 'lens-tests'],
                                       ['Broca', 'lens-workspace']]) {
          const row = page.locator('#project-lens .summary-row').filter({ has: page.locator(`[data-resource="${resource}"]`) });
          assert.equal(await row.locator('dt a').textContent(), name);
          assert((await row.locator('dt a').getAttribute('href')).endsWith(`/PyAuto${name}/`));
        }
        assert.equal(await page.locator('[data-resource="broca-assistants"]').count(), 0);
        assert.equal(await page.locator('.project-card[open]').count(), 0);
        const summary = page.locator('#project-lens > summary');
        await summary.focus();
        await page.keyboard.press('Enter');
        assert.equal(await page.locator('#project-lens').getAttribute('open'), '');
        assert.equal(await page.evaluate(() => document.activeElement.parentElement.id), 'project-lens');
        // Feed refresh never rebuilds project disclosures or steals their focus.
        await page.evaluate(() => refresh());
        assert.equal(await page.locator('#project-lens').getAttribute('open'), '');
        assert.equal(await page.evaluate(() => document.activeElement.parentElement.id), 'project-lens');
        const grid = await page.locator('#projects .organ-grid').boundingBox();
        const card = await page.locator('#project-lens').boundingBox();
        assert(Math.abs(grid.width - card.width) < 2, 'expanded card spans full row');
        assert.equal(await page.locator('#project-reduce [data-resource$="assistant"]').count(), 0);
        assert(await page.locator('#project-lens [data-resource="array"]').count());
        assert(await page.locator('#project-galaxy [data-resource="array"]').count());
        await page.evaluate(() => document.querySelectorAll('details').forEach(d => { d.open = true; }));
        assert(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth), 'whole-page overflow');
        assert(await page.locator('#project-lens a').first().isVisible());
        assert.deepEqual(errors, []);
        await page.screenshot({ path: path.join(evidence, `projects-${width}-${colorScheme}.png`), fullPage: true });
        await context.close();
        cases++;
      }
    }
    const context = await browser.newContext({ javaScriptEnabled: false, viewport: { width: 390, height: 1000 } });
    const page = await context.newPage();
    await page.goto(destination);
    await page.locator('#project-fit > summary').click();
    assert(await page.locator('#project-fit a').first().isVisible());
    await context.close();
    console.log(`${cases} responsive/theme cases and no-JavaScript disclosure passed`);
  } finally {
    await browser.close();
  }
})().catch(error => { console.error(error); process.exitCode = 1; });
