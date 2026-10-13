/* Optional real-browser regression: node tests/live_feed_browser.cjs <fixtures> <output>. */
const fs = require('node:fs');
const path = require('node:path');
const assert = require('node:assert/strict');
const {chromium} = require('playwright');
(async () => {
  const [fixtures, output] = process.argv.slice(2);
  fs.mkdirSync(output, {recursive:true});
  const html = fs.readFileSync(path.join(fixtures,'browser-preview.html'),'utf8');
  const original = JSON.parse(fs.readFileSync(path.join(fixtures,'browser-feed.json'),'utf8'));
  const browser = await chromium.launch({executablePath:process.env.PLAYWRIGHT_EXECUTABLE_PATH,headless:true,args:['--no-sandbox']});
  try {
    for (const width of [390,768,1440]) for (const colorScheme of ['light','dark']) {
      const context = await browser.newContext({viewport:{width,height:1100},colorScheme});
      const page = await context.newPage(); const errors=[]; page.on('pageerror',e=>errors.push(e.message));
      let feed = structuredClone(original); let requests=0;
      await page.route('**/*',route=> {
        if (route.request().url().includes('activity.json')) {requests++;return route.fulfill({contentType:'application/json',body:JSON.stringify(feed)});}
        return route.fulfill({contentType:'text/html',body:html});
      });
      await page.goto('https://preview.example/');
      await page.waitForFunction(()=>document.querySelector('[data-feed-freshness]').textContent.includes('checked'));
      assert.equal(await page.locator('.feed-task').count(),5);
      assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth),false);
      const first = page.locator('.feed-task').first();
      await first.locator('summary').click();
      assert.equal(await first.getAttribute('open'),'');
      const oldText = await first.locator('.feed-title').innerText();
      const oldId = await first.getAttribute('data-task');
      feed.tasks[0].title='A newer task title';feed.generated='2026-10-13T20:01:00Z';
      await page.evaluate(()=>document.dispatchEvent(new Event('visibilitychange')));
      await page.locator('[data-feed-new]').waitFor({state:'visible'});
      assert.equal(await first.locator('.feed-title').innerText(),oldText);
      assert.equal(await first.getAttribute('open'),'');
      await page.locator('[data-feed-new]').click();
      assert.equal(await page.locator('.feed-task').first().locator('.feed-title').innerText(),'A newer task title');
      assert.equal(await page.locator(`details[data-task="${oldId}"]`).getAttribute('open'),'');
      await page.locator('[data-feed-more]').click();
      assert.equal(await page.locator('.feed-task').count(),8);
      assert.equal(await page.locator(`details[data-task="${oldId}"]`).getAttribute('open'),'');
      // Unsafe response must leave the last good snapshot visible.
      feed.tasks[0].events[0].url='javascript:alert(1)';
      await page.evaluate(()=>document.dispatchEvent(new Event('visibilitychange')));
      await page.waitForFunction(()=>document.querySelector('[data-feed-notice]').textContent.includes('unavailable'));
      assert.equal(await page.locator('.feed-task').count(),8);
      assert.deepEqual(errors,[]);
      assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth),false);
      await page.locator('#live-feed-heading').scrollIntoViewIfNeeded();
      await page.screenshot({path:path.join(output,`feed-${width}-${colorScheme}.png`)});
      assert(requests>=3);
      await context.close();
    }
    const context=await browser.newContext({javaScriptEnabled:false});const page=await context.newPage();
    await page.route('**/*',r=>r.fulfill({contentType:'text/html',body:html}));await page.goto('https://preview.example/');
    assert.equal(await page.locator('.feed-task').count(),5);assert(await page.locator('.feed-task a').first().getAttribute('href'));await context.close();
    console.log('PASS: six viewport/theme cases; grouped history, buffered updates, Show more, unsafe-feed fallback, no overflow/errors; no-JS snapshot.');
  } finally {await browser.close();}
})().catch(e=>{console.error(e);process.exit(1);});
