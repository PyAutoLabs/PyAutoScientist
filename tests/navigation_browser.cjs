// NODE_PATH=<playwright modules> node tests/navigation_browser.cjs <fixtures> <evidence>
// Fixtures: CLI-rendered empty.html, connected.html and examples/lifecycle as lifecycle.html.
const {chromium} = require('playwright');
const fs = require('node:fs');
const path = require('node:path');
const http = require('node:http');
const assert = require('node:assert/strict');
(async () => {
 const fixtures = path.resolve(process.argv[2]), evidence = path.resolve(process.argv[3]);
 fs.mkdirSync(evidence,{recursive:true});
 const server = http.createServer((req,res)=>{
  const name = new URL(req.url,'http://localhost').pathname.slice(1);
  if (!['empty.html','connected.html','lifecycle.html'].includes(name)) {res.writeHead(404);res.end();return;}
  res.setHeader('Content-Type','text/html; charset=utf-8');res.end(fs.readFileSync(path.join(fixtures,name)));
 });
 await new Promise(resolve=>server.listen(0,'127.0.0.1',resolve));
 let browser;
 try {
  browser=await chromium.launch({headless:true,...(process.env.PLAYWRIGHT_EXECUTABLE_PATH ? {executablePath:process.env.PLAYWRIGHT_EXECUTABLE_PATH} : {channel:'chromium'})});
  const base=`http://127.0.0.1:${server.address().port}/`, results=[];
  for(const width of [390,768,820,1024,1440]) for(const colorScheme of ['light','dark']) {
   const ctx=await browser.newContext({viewport:{width,height:1000},colorScheme,permissions:['clipboard-read','clipboard-write']});
   const requests=[];
   await ctx.route('https://**/*',route=>{requests.push(route.request().url());return route.fulfill({status:200,contentType:'text/html',body:'<h1>Configured board</h1>'});});
   const page=await ctx.newPage(),errors=[];page.on('pageerror',e=>errors.push(e.message));
   for(const variant of ['empty','connected']) {
    await page.goto(base+variant+'.html');
    assert.equal(await page.locator('.instance-nav a').count(),15);
    assert.equal(await page.locator('#scientist').isVisible(),true);
    await page.locator('.organ-catalogue > summary').click();
    const original=await page.locator('.organ-catalogue textarea[aria-label="Add brain"]').inputValue();
    // Native keyboard link activation is the same navigation route as a pointer.
    await page.locator('.instance-nav a[href="#organ-brain"]').focus();await page.keyboard.press('Enter');
    await page.waitForFunction(()=>!document.getElementById('organ-brain').hidden);
    assert.equal(await page.locator('#scientist').isVisible(),false);
    assert.equal(await page.locator('#organ-brain textarea').inputValue(),original);
    assert.equal(await page.locator('#organ-brain h1').evaluate(el=>el===document.activeElement),true);
    await page.locator('#organ-brain button.copy').click();
    assert.equal(await page.evaluate(()=>navigator.clipboard.readText()),original);
    assert.equal(await page.locator('.instance-nav a[aria-current="page"]').getAttribute('href'),'#organ-brain');
    assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),true);
    if(variant==='connected') await page.screenshot({path:path.join(evidence,`brain-${width}-${colorScheme}.png`),fullPage:true});
    for(const href of await page.locator('.instance-nav a').evaluateAll(as=>as.map(a=>a.getAttribute('href')))) {
     await page.locator(`.instance-nav a[href="${href}"]`).click();
     await page.waitForFunction(href=>document.querySelector('.instance-nav [aria-current="page"]').getAttribute('href')===href,href);
    }
    await page.goto(base+variant+'.html#organ-brain');
    assert.equal(await page.locator('#organ-brain').isVisible(),true);
    await page.locator('.instance-nav a[href="#organ-mind"]').click();
    await page.goBack();await page.waitForFunction(()=>!document.getElementById('organ-brain').hidden);
    await page.goForward();await page.waitForFunction(()=>!document.getElementById('organ-mind').hidden);
    await page.locator('.instance-nav a[href="#scientist"]').click();
    await page.waitForFunction(()=>!document.getElementById('scientist').hidden);
    await page.evaluate(()=>new Promise(resolve=>requestAnimationFrame(()=>requestAnimationFrame(resolve))));
    assert(await page.evaluate(()=>document.querySelector('#scientist .hero').getBoundingClientRect().top >= document.querySelector('.instance-nav').getBoundingClientRect().bottom),'navigation must not cover the overview banner');
    if(variant==='connected') await page.screenshot({path:path.join(evidence,`overview-${width}-${colorScheme}.png`),fullPage:true});
   }
   assert.deepEqual(requests,[],'empty and disconnected project must not request any external URL');
   await page.goto(base+'lifecycle.html');await page.waitForFunction(()=>!refreshing);
   assert(requests.every(url=>url.startsWith('https://example.invalid/checks/state.json')));
   await page.locator('.instance-nav a[href="#organ-broca"]').click();
   assert.equal(await page.locator('#organ-broca textarea').inputValue(),await page.locator('#setup-broca textarea').inputValue());
   await page.locator('.instance-nav a[href="#organ-brain"]').click();
   await page.locator('.instance-nav a[href="#organ-mind"]').click();
   await page.frameLocator('#organ-mind iframe').locator('h1').waitFor();
   assert.equal(await page.locator('#organ-mind .organ-state').textContent(),'Paused');
   assert(requests.includes('https://example.invalid/plans/'));
   assert(!requests.some(url=>url.startsWith('https://example.invalid/plans/state.json')));
   await page.goBack();await page.waitForFunction(()=>!document.getElementById('organ-brain').hidden);
   await page.goForward();await page.waitForFunction(()=>!document.getElementById('organ-mind').hidden);
   await page.locator('.instance-nav a[href="#organ-heart"]').click();
   await page.frameLocator('#organ-heart iframe').locator('h1').waitFor();
   assert(requests.includes('https://example.invalid/checks/'));
   assert.deepEqual(errors,[]);
   results.push({width,colorScheme,variants:3,passed:true});await ctx.close();
  }
  const ctx=await browser.newContext({javaScriptEnabled:false});
  const page=await ctx.newPage();await page.goto(base+'empty.html#organ-brain');
  assert.equal(await page.locator('#organ-brain textarea').isVisible(),true);
  await ctx.close();
  fs.writeFileSync(path.join(evidence,'validation.json'),JSON.stringify(results,null,2));
  console.log('PASS: 30 browser cases, keyboard/copy/history, inactive network isolation, connected/paused routing, no-JS text.');
 } finally {if(browser)await browser.close();await new Promise(resolve=>server.close(resolve));}
})().catch(e=>{console.error(e);process.exitCode=1;});
