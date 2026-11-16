const { chromium } = require('../../apps/studio/node_modules/playwright');
const fs=require('node:fs');
const crypto=require('node:crypto');
const out='evidence/evaluation/round-00';fs.mkdirSync(out,{recursive:true});
const result={date:new Date().toISOString(),checks:[],errors:[],remote:[]};
async function check(name,fn){try{result.checks.push({name,status:'PASS',detail:await fn()});}catch(e){result.checks.push({name,status:'FAIL',detail:e.message});}}
function ok(v,msg){if(!v)throw Error(msg);}
(async()=>{
 const browser=await chromium.launch({channel:'msedge',headless:true});
 result.browser=browser.version();
 const page=await browser.newPage({viewport:{width:1440,height:900}});
 page.on('pageerror',e=>result.errors.push(e.message));
 page.on('request',r=>{if(!r.url().startsWith('http://127.0.0.1:'))result.remote.push(r.url());});
 const state=async()=> (await(await fetch('http://127.0.0.1:8771/api/v1/state')).json()).data;
 await page.goto('http://127.0.0.1:8771');await page.locator('#play:not([disabled])').waitFor();
 await page.waitForFunction(()=>Number.isFinite(document.querySelector('#audio').duration));
 result.initial=await state();
 await check('Direct fader persistence',async()=>{const fader=page.locator('audio-ui-fader[data-entity="evaluation-midi"] input');await fader.focus();await fader.press('ArrowDown');await page.waitForTimeout(400);const after=await state();ok(after.project.revision!==result.initial.project.revision,'Gesture only staged; canonical revision unchanged');});
 await page.locator('#track-evaluation-midi').click();await page.locator('[data-dock=piano]').click();await page.locator('#piano-section').selectOption('intro');
 await check('Delete selected note',async()=>{const before=await state();const note=page.locator('audio-ui-piano-roll-note[note-id="eval-0"]');await note.click();await note.press('Delete');await page.waitForTimeout(300);ok((await state()).project.revision!==before.project.revision,'Delete rejected: '+await page.locator('#notice').textContent());});
 await check('Protected piano locked',async()=>{await page.locator('#track-evaluation-protected').click();ok(await page.locator('audio-ui-piano-roll').getAttribute('disabled')!==null,'not disabled');return 'Protected editor disabled';});
 await check('Tempo/meter section navigation',async()=>{await page.locator('.browser-section').filter({hasText:/^turn$/}).click();ok(await page.locator('#tempo-display').textContent()==='104 BPM · 3/4','wrong tempo/meter');ok(await page.locator('#musical-position').textContent()==='3.1','wrong bar');return await page.locator('#audio').evaluate(e=>e.currentTime);});
 await check('Space and Home',async()=>{await page.locator('body').click({position:{x:5,y:5}});await page.keyboard.press('Space');await page.waitForFunction(()=>!document.querySelector('#audio').paused);await page.keyboard.press('Home');ok(await page.locator('#audio').evaluate(e=>e.paused&&e.currentTime===0),'Home incorrect');});
 await check('Input typing transport isolation',async()=>{await page.locator('#browser-search').fill('');await page.locator('#browser-search').press('Space');ok(await page.locator('#audio').evaluate(e=>e.paused),'input starts playback');await page.locator('#browser-search').fill('');});
 for(const width of [1440,1280]){await page.setViewportSize({width,height:width===1440?900:720});await page.screenshot({path:`${out}/fixture-${width}.png`,fullPage:true});}
 await check('Missing everyday controls inventory',async()=>{result.buttons=await page.getByRole('button').allTextContents();result.controls=await page.locator('input,select').evaluateAll(es=>es.map(e=>({id:e.id,label:e.getAttribute('aria-label'),type:e.type})));return result.buttons;});
 const original=await(await fetch('http://127.0.0.1:8767/api/v1/state')).json();result.glassInitial=original.data.project.revision;
 await page.goto('http://127.0.0.1:8767');await page.locator('#play:not([disabled])').waitFor();
 await check('Full Glass navigation search zoom playback',async()=>{await page.locator('#browser-search').fill('808');ok(await page.locator('.browser-item').count()>0,'search empty');await page.locator('#browser-search').fill('');await page.locator('#zoom').selectOption('4');ok(await page.locator('#timeline-viewport').evaluate(e=>e.scrollWidth>e.clientWidth),'zoom not scrollable');await page.locator('#play').click();await page.waitForFunction(()=>document.querySelector('#audio').currentTime>.1);await page.locator('#stop').click();return await page.locator('#audio').evaluate(e=>({duration:e.duration,src:e.src}));});
 await page.screenshot({path:out+'/glass-desktop.png',fullPage:true});
 await check('390px overflow and local assets',async()=>{await page.setViewportSize({width:390,height:844});await page.screenshot({path:out+'/glass-narrow.png',fullPage:true});ok(await page.evaluate(()=>document.documentElement.scrollWidth)===390,'horizontal overflow');await page.locator('#play').scrollIntoViewIfNeeded();await page.locator('#play').click();await page.waitForFunction(()=>!document.querySelector('#audio').paused);await page.locator('#stop').click();ok(result.remote.length===0,'remote asset');});
 result.glassFinal=(await(await(await fetch('http://127.0.0.1:8767/api/v1/state')).json()).data).project.revision;
 await browser.close();fs.writeFileSync(out+'/browser.json',JSON.stringify(result,null,2));console.log(JSON.stringify({checks:result.checks,errors:result.errors}));
})().catch(e=>{result.fatal=e.stack;fs.writeFileSync(out+'/browser.json',JSON.stringify(result,null,2));console.error(e);process.exitCode=1;});
