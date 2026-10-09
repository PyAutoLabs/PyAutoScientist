const {test} = require('node:test');
const assert = require('node:assert/strict');
const vm = require('node:vm');
const fs = require('node:fs');
const script = fs.readFileSync(require('node:path').join(__dirname, '../scripts/overview.js'), 'utf8');
new vm.Script(script);
const ctx = vm.createContext({ URL, Date: class extends Date { static now() { return Date.parse('2026-10-09T12:00:00Z'); } } });
vm.runInContext(script.split('// ---- browser startup ----')[0], ctx);
function run(expr, vars = {}) { Object.assign(ctx, vars); return vm.runInContext(expr, ctx); }
function feed(overrides={}) { return { schema_version:1, organ:'mind',repo:'PyAutoMind',status:'green',headline:'2 active · 1 awaiting review',updated:'2026-10-09T10:00:00Z',pages_url:'https://example.test/PyAutoMind/',items:[],...overrides }; }
const organ = { key:'mind',url:'https://example.test/PyAutoMind/' };
function rows(d, st={}) {return run('summaries(organ, observation(st))', {organ,st:{feed:d,...st}});}
test('a decision outranks a failure and active work has its own row; hard cap three', () => {
 const result=rows(feed({items:[{severity:'red',text:'Failure'}, {severity:'yellow',text:'Choice',requires_human_decision:true,decision:'Choose a release date'}, {severity:'info',state:'active',text:'Implementing the dashboard'}]}));
 assert.equal(result.length,3);assert.equal(result[0].text,'Choose a release date');assert.equal(result[1].label,'In progress');
});
test('quiet, non-green, unavailable, expired and future evidence remain distinct', () => {
 assert.equal(rows(feed())[0].text,'No action reported');
 assert.equal(rows(feed({status:'red'}))[0].text,'Review failing status');
 assert.equal(rows(null)[0].text,'Unavailable');
 const expired=rows(feed({valid_until:'2026-10-09T10:01:00Z'}));assert.equal(expired[0].label,'Evidence');
 const future=rows(feed({updated:'2099-01-01T00:00:00Z'}));assert.equal(future[0].label,'Evidence');
 const cached=rows(null,{lastGood:feed(),error:'offline'});assert.equal(cached[1].label,'Last known');
});
test('active or healthy items are not reclassified as failures from their colour', () => {
 const result=rows(feed({items:[{severity:'red',state:'active',text:'A run in progress'}]}));
 assert.equal(result[0].text,'No action reported');assert.equal(result[1].label,'In progress');
});
test('ordinary headlines and feed timestamps never become completion history', () => {
 const result=rows(feed());assert.ok(result.every(r=>!r.label.includes('Latest')));
 assert.ok(result.every(r=>!r.text.includes('2026-10-09')));
 const release=run('summaries(hands, observation({feed:d}))',{hands:{key:'hands',url:'https://example.test/'},d:feed({headline:'2026.10.7.1 · 2d ago'})});
 assert.equal(release.at(-1).label,'Latest release');assert.equal(release.at(-1).text,'2026.10.7.1 · 2d ago');
 const failed=run('summaries(hands, observation({feed:d}))',{d:feed({status:'red',headline:'Build failed'})});
 assert.equal(failed.at(-1).label,'Releases');
});
test('summary links escape HTML, reject active URLs and stay concise', () => {
 const html=run('summaryHtml(rows)',{rows:[{label:'<script>',text:'<img src=x onerror=alert(1)> '+('word '.repeat(40)),url:'javascript:alert(1)'}]});
 assert.ok(!html.includes('<script>'));assert.ok(!html.includes('<img'));assert.ok(!html.includes('javascript:'));
 assert.ok(run('concise(text)',{text:'word '.repeat(40)}).split(' ').length<=12);
});
test('feed identity, impossible dates and malformed action metadata are rejected', () => {
 assert.equal(run('validate(d, identity)',{d:feed(),identity:{organ:'Mind',repo:'PyAutoMind'}}),null);
 assert.ok(run('validate(d, identity)',{d:feed({repo:'PyAutoHeart'})}));
 assert.ok(run('validate(d)',{d:feed({updated:'2026-02-30T12:00:00Z'})}));
 assert.ok(run('validate(d)',{d:feed({items:[{severity:'info',text:'text',actions:[{id:'x',kind:'link',label:'x',target:'javascript:alert(1)'}]}]})}));
});
