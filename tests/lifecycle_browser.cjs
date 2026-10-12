// NODE_PATH=<playwright modules> node tests/lifecycle_browser.cjs <HTML> <evidence-dir>
const {chromium} = require('playwright');
const {pathToFileURL} = require('node:url');
const path = require('node:path');
const fs = require('node:fs');
const assert = require('node:assert/strict');
(async () => {
 const browser = await chromium.launch({headless:true, channel:'chromium'});
 const evidence = path.resolve(process.argv[3]); fs.mkdirSync(evidence,{recursive:true});
 try {
  for (const width of [390,1440]) for(const colorScheme of ['light','dark']) {
   const ctx=await browser.newContext({viewport:{width,height:1100},colorScheme});
   const requests=[];
   await ctx.route('https://**/*', route=>{requests.push(route.request().url());return route.fulfill({status:503,body:'{}'});});
   await ctx.addInitScript(()=>{
    const feed={schema_version:1,organ:'mind',repo:'ResearchPlans',status:'green',headline:'CACHED MUST NOT APPEAR',items:[],updated:new Date().toISOString(),pages_url:'https://example.invalid/plans/'};
    const key='scientist:last-good:'+JSON.stringify(['https://github.com/Research/Mira','mind','ResearchPlans','https://example.invalid/plans/']);
    localStorage.setItem(key,JSON.stringify({feed}));
   });
   const page=await ctx.newPage(); const errors=[]; page.on('pageerror',e=>errors.push(e.message));
   await page.goto(pathToFileURL(path.resolve(process.argv[2])).href);
   await page.waitForFunction(()=>!refreshing);
   assert.equal(await page.locator('#board-mind .organ-status').textContent(),'Paused');
   assert((await page.locator('#setup-broca').textContent()).includes('Setup incomplete'));
   assert((await page.locator('#board-heart .organ-status').textContent()).startsWith('Connected'));
   await page.locator('#board-mind summary').click();
   await page.locator('#board-mind a').focus();
   await page.evaluate(async()=>{await refresh();document.dispatchEvent(new Event('visibilitychange'));});
   await page.waitForFunction(()=>!refreshing);
   assert.equal(await page.locator('#board-mind').getAttribute('open'),'');
   assert(await page.locator('#board-mind a').evaluate(el=>el===document.activeElement));
   assert(!await page.locator('body').innerText().then(t=>t.includes('CACHED MUST NOT APPEAR')));
   assert(requests.length>0 && requests.every(url=>url.startsWith('https://example.invalid/checks/')));
   await page.locator('#setup-broca summary').click();
   await page.locator('.organ-catalogue > summary').click();
   assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),true);
   assert.deepEqual(errors,[]);
   await page.screenshot({path:path.join(evidence,`${width}-${colorScheme}.png`),fullPage:true});
   await ctx.close();
  }
  const ctx=await browser.newContext({javaScriptEnabled:false});
  const page=await ctx.newPage(); await page.goto(pathToFileURL(path.resolve(process.argv[2])).href);
  assert((await page.locator('#board-mind').textContent()).includes('Paused'));
  assert((await page.locator('#setup-broca').textContent()).includes('Setup incomplete'));
  await ctx.close();
  console.log('PASS: four browser layouts plus no-JS; pause/cache/refresh/focus/network checks');
 } finally {await browser.close();}
})().catch(e=>{console.error(e);process.exit(1);});
