/* Real browser gestures against a disposable Faust project. No mocked HTTP. */
const assert = require('node:assert/strict');
const { mkdirSync } = require('node:fs');
const { execFileSync } = require('node:child_process');
const { chromium } = require('playwright');

async function main() {
  const [origin, root, python, output = '../../.local/desktop-qa'] = process.argv.slice(2);
  assert.equal(new URL(origin).hostname, '127.0.0.1');
  const inspect = () => JSON.parse(execFileSync(python, ['-m','app','--root',root,'--timeout','30','project-inspect'],
    {cwd:'../..',encoding:'utf8',timeout:30000})).data;
  const guarded = inspect();
  assert.equal(guarded.source.title, 'Desktop UI fixture', 'Only run on a disposable fixture');
  const served=(await(await fetch(origin+'/api/v1/state')).json()).data.project;
  assert.equal(served.revision,guarded.revision,'Server must serve the supplied disposable fixture');
  assert.equal(served.last_playable_rendition,guarded.last_playable_rendition,'Fixture rendition identity must agree');
  // Give the stock fixture a real exposed bus control for the Devices gesture.
  // This setup is guarded above and persists only through ProjectService.
  execFileSync(python,['-c',[
    'from app.project import ProjectService', 'import sys', 'service=ProjectService(sys.argv[1])',
    'revision,source=service.source()', 'assert source["title"]=="Desktop UI fixture"',
    'if not source["buses"][0]["inserts"]:',
    '    module=service.import_file("fixtures/saturation.dsp","faust","Disposable desktop device-control test",30)',
    '    service.edit(dict(command_id="desktop-device-fixture",base_revision=revision,reason="Prepare disposable device control",operations=[dict(kind="append_bus_insert",bus_id="music",insert=dict(module_sha256=module["sha256"],parameters={}))]))',
    '    service.render_project(60)',
  ].join('\n'),root],{cwd:'../..',encoding:'utf8',timeout:90000});
  const initial=inspect();
  mkdirSync(output,{recursive:true});
  const browser = await chromium.launch({channel:'msedge',headless:true});
  try {
    const page = await browser.newPage({viewport:{width:1440,height:1000}});
    const saveGesture = async (gesture, endpoint = 'edit') => {
      const response = page.waitForResponse(r => new URL(r.url()).pathname === `/api/v1/${endpoint}` && r.request().method() === 'POST');
      await gesture();
      const result = await (await response).json();
      assert.equal(result.ok, true, JSON.stringify(result.error));
      await page.waitForFunction(()=>document.getElementById('save-state').textContent === 'Saved');
      return inspect();
    };
    const errors=[], remote=[];
    page.on('pageerror',e=>errors.push(e.message));
    page.on('console',m=>{if(m.type()==='error')errors.push(m.text());});
    page.on('request',r=>{if(new URL(r.url()).origin!==origin)remote.push(r.url());});
    await page.goto(origin);
    await page.locator('#play:not([disabled])').waitFor();
    await page.waitForFunction(()=>Number.isFinite(document.getElementById('audio').duration));
    assert.equal(await page.locator('[data-dock=piano]').getAttribute('aria-pressed'),'true');
    assert.equal(await page.locator('#browser-panel').isVisible(),false);
    await page.locator('[data-dock=mixer]').click();
    await page.waitForFunction(()=>document.querySelector('#mix-console audio-ui-fader input:not([disabled])'));
    assert.equal(await page.locator('#mix-console audio-ui-fader').count(),4);
    await page.locator('#zoom').selectOption('4');
    assert.ok(await page.locator('#timeline-viewport').evaluate(e=>e.scrollWidth>e.clientWidth));
    await page.locator('#zoom').selectOption('1');
    await page.locator('#toggle-browser').click();
    await page.locator('#browser-search').fill('tone');
    assert.equal(await page.locator('.browser-item').count(),1);
    await page.locator('#browser-search').fill('');
    await page.locator('.browser-section').filter({hasText:/^turn$/}).click();
    await page.waitForFunction(()=>document.getElementById('tempo-display').textContent==='104 BPM · 3/4');
    assert.ok(Math.abs(await page.locator('#audio').evaluate(e=>e.currentTime) - (2+240/104))<.02);
    assert.equal(await page.locator('#musical-position').textContent(),'3.1');
    await page.locator('#loop').click();
    await page.locator('#play').click();
    await page.waitForFunction(()=>document.getElementById('audio').currentTime>4.4);
    await page.waitForFunction(()=>document.getElementById('audio').currentTime<4.4,{},{timeout:6000});
    await page.locator('#stop').click();
    await page.locator('#loop').click();
    await page.locator('body').click({position:{x:5,y:5}});
    await page.keyboard.press('Space');
    await page.waitForFunction(()=>!document.getElementById('audio').paused);
    await page.keyboard.press('Home');
    assert.equal(await page.locator('#audio').evaluate(e=>e.paused),true);

    const fader=page.locator('#mix-console audio-ui-fader[data-entity=tone] input');
    await fader.focus();await saveGesture(()=>fader.press('ArrowDown'));
    assert.ok(Math.abs(inspect().source.tracks[0].gain_db-(initial.source.tracks[0].gain_db-.1))<1e-9);
    assert.match(await page.locator('#playback-state').textContent(),/Edits to hear/);
    assert.equal(await page.locator('#loop').isDisabled(),true);

    await page.locator('#track-tone').click();await page.locator('[data-dock=piano]').click();
    await page.locator('#piano-section').selectOption('intro');
    const beforeNote=inspect();
    const note=page.locator('audio-ui-piano-roll-note[note-id=n0]');
    await note.click();await saveGesture(()=>note.press('ArrowUp'));
    assert.equal(inspect().source.tracks[0].events[0].note,beforeNote.source.tracks[0].events[0].note+1);
    const beforeResize=inspect();
    const handle=page.locator('audio-ui-piano-roll-note[note-id=n0] audio-ui-piano-roll-note-handle');
    const rect=await handle.boundingBox();
    const gridWidth=await page.locator('audio-ui-piano-roll-grid').evaluate(e=>e.clientWidth);
    await saveGesture(async()=>{
      await page.mouse.move(rect.x+rect.width/2,rect.y+rect.height/2);
      await page.mouse.down();await page.mouse.move(rect.x+rect.width/2+gridWidth/16,rect.y+rect.height/2,{steps:6});await page.mouse.up();
    });
    const resized=inspect();
    assert.equal(resized.source.tracks[0].events[0].duration_ticks,beforeResize.source.tracks[0].events[0].duration_ticks+240);
    const grid=page.locator('audio-ui-piano-roll-grid');
    const created=await saveGesture(()=>grid.dblclick({position:{x:gridWidth*.7,y:10}}));
    const createdNote=created.source.tracks[0].events.find(e=>!resized.source.tracks[0].events.some(old=>old.id===e.id));
    assert.ok(createdNote, 'Double-click creates a committed note with a distinct ID');
    assert.equal(created.source.tracks[0].events.length,resized.source.tracks[0].events.length+1);
    assert.equal(createdNote.start_tick%240,0,'New note follows the 1/16 snap');
    await page.locator('#audition').click();
    await page.waitForFunction(()=>document.getElementById('audition-state').textContent==='Ready', {}, {timeout:60000});
    const preview=inspect();
    const previewRendition=await (await fetch(origin+'/api/v1/renditions/'+preview.last_playable_rendition)).json();
    assert.equal(previewRendition.data.revision,created.revision,'Audition renders the directly edited source');
    const added=page.locator(`audio-ui-piano-roll-note[note-id="${createdNote.id}"]`);
    await added.click();
    const deleted=await saveGesture(()=>added.press('Delete'));
    assert.ok(!deleted.source.tracks[0].events.some(e=>e.id===createdNote.id));
    assert.equal(deleted.source.tracks[0].events.length,resized.source.tracks[0].events.length);
    const undone=await saveGesture(()=>page.locator('#undo').click(),'undo');
    assert.deepEqual(undone.source.tracks[0].events.find(e=>e.id===createdNote.id),createdNote);
    const redone=await saveGesture(()=>page.locator('#redo').click(),'redo');
    assert.ok(!redone.source.tracks[0].events.some(e=>e.id===createdNote.id));
    assert.equal(await page.locator('audio-ui-piano-roll-note').count(),4);
    await page.screenshot({path:output+'/piano.png',fullPage:true});
    await page.locator('#track-protected').click();
    assert.equal(await page.locator('audio-ui-piano-roll').getAttribute('disabled'),'');
    const protectedHead=inspect().revision;
    await page.locator('audio-ui-piano-roll-grid').dblclick();await page.keyboard.press('ArrowUp');
    assert.equal(inspect().revision,protectedHead);

    await page.locator('#track-tone').click();
    await page.locator('[data-dock=devices]').click();
    const drive=page.getByRole('spinbutton',{name:'music 1. Faust effect drive value',exact:true});
    const deviceState=(await(await fetch(origin+'/api/v1/state')).json()).data;
    const driveBinding=deviceState.plugins.find(row=>row.bus_id==='music'&&row.insert_index===0).parameters.find(p=>p.label==='drive').binding;
    await drive.fill('1.25');
    const deviceEdit=await saveGesture(()=>drive.press('Enter'));
    assert.equal(deviceEdit.source.buses.find(bus=>bus.id==='music').inserts[0].parameters[driveBinding],1.25);
    assert.ok(await page.locator('#inspector-content audio-ui-knob').count()>0,'Device cards use native controls');
    await page.screenshot({path:output+'/devices.png',fullPage:true});

    // A historical view must lock every source fader, not only inspector inputs.
    await page.locator('#toggle-review').click();
    await page.getByRole('button',{name:'View source',exact:true}).last().click();
    await page.locator('#back-head').waitFor();
    assert.equal(await page.locator('#mix-console audio-ui-fader:not([disabled])').count(),0);
    await page.locator('#back-head').click();
    const finalAudio=page.waitForResponse(r=>new URL(r.url()).pathname==='/api/v1/render' && r.request().method()==='POST', {timeout:60000});
    await page.locator('#audition').click();
    assert.equal((await (await finalAudio).json()).ok,true);
    await page.waitForFunction(()=>document.getElementById('audition-state').textContent==='Ready', {}, {timeout:60000});
    await page.waitForFunction(()=>!document.getElementById('loop').disabled);
    const result=inspect();
    assert.notEqual(result.last_playable_rendition,initial.last_playable_rendition);
    const r=await (await fetch(origin+'/api/v1/renditions/'+result.last_playable_rendition)).json();
    assert.equal(r.data.revision,result.revision);
    await page.locator('#play').click();await page.waitForFunction(()=>document.getElementById('audio').currentTime>.1);
    await page.locator('#stop').click();
    await page.locator('#playback-details > summary').click();
    await page.locator('#ab-a').click();await page.waitForFunction(()=>document.getElementById('playback-state').classList.contains('stale'));
    await page.locator('#ab-b').click();await page.waitForFunction(()=>!document.getElementById('playback-state').classList.contains('stale'));
    await page.locator('[data-dock=mixer]').click();
    await page.screenshot({path:output+'/desktop.png',fullPage:true});
    await page.setViewportSize({width:390,height:844});
    assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth),390);
    await page.screenshot({path:output+'/narrow.png',fullPage:true});
    assert.deepEqual(errors,[]);assert.deepEqual(remote,[]);
    console.log(JSON.stringify({status:'PASS',browser:'Edge headless',sourceRevision:initial.revision,
      finalRevision:result.revision,rendition:result.last_playable_rendition,checks:[
        'Piano default and browser disclosure','library elements loaded','local assets only','zoom and browser filter','tempo/meter seek',
        'section loop playback','transport shortcuts','fader gesture -> direct save -> CLI',
        'note keyboard edit -> direct save -> CLI','pointer note resize','pointer note creation and snapped stable ID',
        'one-click audition matches edited source','direct deletion','undo restores deleted note','redo deletes again',
        'protected track lock','Devices dock numeric direct commit','native device knob cards','historical revision lock',
        'real Faust rerender/playback','A/B stale audio identity','390px overflow','no browser/CSP errors']}));
  } finally {await browser.close();}
}
main().catch(e=>{console.error(e);process.exitCode=1;});
