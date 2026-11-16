import WaveSurfer from 'wavesurfer.js';

// View policy, not audio-engine limits. Existing values outside fader travel expand it.
const FADER = { min: -60, max: 12, step: .1 };

export function createDesktop({ ui, audio, byId, node, button, label, trackColors, stage, notice,
  selectTrack, currentTrack, drawInspector, tickAtTime, timeChanges }) {
  let dock = 'mixer', sectionId = null, looping = false, wave = null;
  const source = () => ui.view?.source;
  const section = () => source()?.sections.find(s => s.id === sectionId) ?? source()?.sections[0];
  const matching = () => ui.rendition?.revision === ui.view?.revision;
  const secondsAt = tick => {
    let seconds = 0;
    const changes = timeChanges(source());
    for (let i = 0; i < changes.length; i++) {
      const end = Math.min(tick, changes[i+1]?.tick ?? source().length_ticks);
      if (end > changes[i].tick) seconds += (end - changes[i].tick) * 60 / source().ppq / changes[i].bpm;
      if (end === tick) break;
    }
    return seconds;
  };
  const seek = tick => {
    if (!matching()) return notice('This audio belongs to another revision. Render the displayed source to navigate its sections.');
    if (Number.isFinite(audio.duration)) audio.currentTime = Math.min(audio.duration, secondsAt(tick));
  };
  function showReview() {
    byId('review-panel').hidden = false;
    byId('toggle-review').setAttribute('aria-pressed', 'true');
  }
  function drawBrowser() {
    const root = byId('browser-content'); root.replaceChildren();
    if (!source()) return;
    const query = byId('browser-search').value.toLowerCase();
    const group = (title, items, make) => {
      root.append(node('h3', { text: title, classes: 'browser-heading' }));
      for (const item of items.filter(i => label(i.id).toLowerCase().includes(query))) root.append(make(item));
    };
    group('TRACKS', source().tracks, t => {
      const b = button(label(t.id), () => selectTrack(t), { classes: 'browser-item', attrs: { 'aria-pressed': ui.trackId === t.id } });
      b.style.setProperty('--track-color', trackColors[t.role.toLowerCase()] ?? '#91a6c0');
      b.append(node('span', {text: t.kind === 'samples' ? 'AUDIO' : 'MIDI', classes:'browser-kind'}));
      return b;
    });
    group('SONG SECTIONS', source().sections, s => button(label(s.id), () => selectSection(s.id), {
      classes:'browser-section', attrs:{'aria-pressed': section()?.id === s.id, title: s.mood}
    }));
    root.append(node('h3', {text:'DEVICES', classes:'browser-heading'}));
    root.append(button('Instruments & effects', () => {ui.inspector = 'plugins'; drawInspector();}, {classes:'browser-section'}));
  }
  function drawMixer() {
    const root = byId('mix-console'); root.replaceChildren();
    if (!source()) return;
    const readOnly = ui.view.revision !== ui.snapshot.project.revision;
    const add = (entity, kind, key, color, index) => {
      const title = label(entity.id ?? 'master');
      const strip = node('section', {classes:'channel-strip', attrs:{'aria-label':`${title} channel`}});
      strip.style.setProperty('--track-color', color);
      strip.classList.toggle('selected', entity.id === ui.trackId);
      const heading = key === 'track_id'
        ? button(title, () => selectTrack(entity), {classes:'channel-name'})
        : node('h3', {text:title, classes:'channel-name'});
      strip.append(node('span',{text:String(index).padStart(2,'0'),classes:'channel-number'}), heading);
      strip.append(node('p',{text:key==='track_id' ? `→ ${label(entity.bus)}` : 'BUS / OUTPUT',classes:'channel-route'}));
      const fader = node('audio-ui-fader', {attrs:{min:Math.min(FADER.min, entity.gain_db), max:Math.max(FADER.max, entity.gain_db),
        step:FADER.step, 'default-value':entity.gain_db, 'data-entity': entity.id ?? 'master'}});
      fader.value = entity.gain_db;
      fader.toggleAttribute('disabled', readOnly || ui.busy);
      const control = node('audio-ui-fader-control');
      const track = node('audio-ui-fader-track'); track.append(node('audio-ui-fader-indicator'));
      control.append(track, node('audio-ui-fader-thumb',{attrs:{'aria-label':`${title} source gain in dB`}}));
      fader.append(control);
      const readout = node('output', {text:`${entity.gain_db.toFixed(1)} dB`, classes:'gain-readout'});
      fader.addEventListener('input', e => {
        if (ui.busy || readOnly) return e.preventDefault();
        if (e.detail) readout.textContent = `${e.detail.value.toFixed(1)} dB`;
      });
      fader.addEventListener('change', e => {
        if (!e.detail || ui.busy || readOnly) return;
        const value = Math.round(e.detail.value * 10) / 10;
        // The committed source remains visible while the proposal is reviewed.
        fader.value = entity.gain_db;
        readout.textContent = `${entity.gain_db.toFixed(1)} dB`;
        if (value !== entity.gain_db) stage(key ? {kind, [key]:entity.id, value} : {kind,value}, `Set ${title} gain to ${value} dB`);
      });
      strip.append(fader, readout, node('span',{text:`${entity.inserts?.length ?? 0} inserts`,classes:'channel-route'}));
      root.append(strip);
    };
    source().tracks.forEach((t,i) => add(t,'set_track_gain','track_id',trackColors[t.role.toLowerCase()]??'#91a6c0',i+1));
    source().buses.forEach((b,i) => add(b,'set_bus_gain','bus_id','#a597d1',source().tracks.length+i+1));
    add(source().master,'set_master_gain',null,'#c7df8b',source().tracks.length+source().buses.length+1);
  }
  function drawPiano() {
    const root = byId('piano-editor'); root.replaceChildren();
    const track = currentTrack(), range = section();
    if (!track || !range) return;
    if (track.kind === 'samples') {
      root.append(node('div',{text:'Audio / sample track. Select a MIDI instrument to edit notes. Sample timing and velocity are available in the Events inspector.',classes:'editor-empty'})); return;
    }
    const ppq = source().ppq;
    const events = track.events.filter(e => e.start_tick >= range.start_tick && e.start_tick < range.end_tick);
    const notes = events.map(e => ({id:e.id,pitch:e.note,start:(e.start_tick-range.start_tick)/ppq,length:e.duration_ticks/ppq,velocity:e.velocity/127}));
    const pitches = events.map(e=>e.note);
    const low = Math.max(0, (pitches.length ? Math.min(...pitches) : 60)-2);
    const high = Math.min(127,Math.max(low+12,(pitches.length ? Math.max(...pitches) : 72)+2));
    const timeline = node('audio-ui-timeline',{attrs:{id:'note-timeline',duration:(range.end_tick-range.start_tick)/ppq,'snap-step':.25,'min-zoom':8,'max-zoom':240}});
    const roll = node('audio-ui-piano-roll',{attrs:{'min-pitch':low,'max-pitch':high,mode:'select'}});
    roll.toggleAttribute('disabled', track.protected || ui.view.revision !== ui.snapshot.project.revision);
    const keys = node('audio-ui-piano-roll-keys');
    const piano = node('audio-ui-piano', {attrs:{'aria-label':'Pitch reference (silent)'}}); piano.append(node('audio-ui-piano-keys')); keys.append(piano);
    const viewport = node('audio-ui-timeline-viewport');
    const ruler = node('audio-ui-timeline-ruler',{classes:'piano-ruler',attrs:{'aria-label':'Section beat position'}});
    for(let beat=0;beat<(range.end_tick-range.start_tick)/ppq;beat+=4) {
      ruler.append(node('audio-ui-timeline-mark',{text:beat+1,attrs:{value:beat}}));
    }
    viewport.append(ruler);
    const grid = node('audio-ui-piano-roll-grid',{attrs:{'aria-label':`${label(track.id)} notes`}});
    const noteList = node('audio-ui-piano-roll-notes');
    const template = node('template');
    // Maker templates supply a note's children; the library creates the note root.
    template.content.append(node('audio-ui-piano-roll-note-handle',{attrs:{edge:'end'}}));
    noteList.append(template);
    grid.append(node('audio-ui-piano-roll-rows'),noteList,node('audio-ui-timeline-playhead'));
    viewport.append(grid);
    const velocityLane = node('audio-ui-piano-roll-velocity-lane'); velocityLane.append(node('audio-ui-piano-roll-velocities'));
    viewport.append(velocityLane); roll.append(keys,viewport); timeline.append(roll);
    root.append(node('div',{text:`${label(track.id)} / ${label(range.id)} · ${events.length} notes · 1/16 grid · Drag / arrows to move · Shift + arrows to resize${track.protected ? ' · Protected' : ''}`,classes:'piano-info'}),timeline);
    roll.value = notes;
    if (ui.eventId && notes.some(n=>n.id===ui.eventId)) roll.selection=[ui.eventId];
    roll.addEventListener('noteselect', e => {
      ui.eventId = e.detail.selection[0] ?? null; drawInspector();
    });
    roll.addEventListener('input', e => {
      if (!e.detail) return;
      const unsupported = e.detail.value.length !== notes.length || e.detail.value.some(n => !events.some(v=>v.id===n.id));
      if (ui.busy || unsupported) {
        e.preventDefault();
        if (unsupported) notice('This editor supports moving, resizing and changing velocity of existing notes. Adding or deleting notes is not available yet.');
      }
    });
    roll.addEventListener('change', e => {
      if (!e.detail || ui.busy || track.protected || ui.view.revision !== ui.snapshot.project.revision) return;
      const operations = [];
      for (const n of e.detail.value) {
        const old = events.find(v=>v.id===n.id); if (!old) continue;
        const values = {start_tick:range.start_tick+Math.round(n.start*ppq),duration_ticks:Math.max(1,Math.round(n.length*ppq)),note:Math.round(n.pitch),velocity:Math.max(1,Math.round((n.velocity??1)*127))};
        const changes = Object.fromEntries(Object.entries(values).filter(([k,v])=>old[k]!==v));
        if (Object.keys(changes).length) operations.push({kind:'edit_event',track_id:track.id,event_id:n.id,changes});
      }
      roll.value = notes;
      if (operations.length) stage(operations,`Edit ${operations.length} notes on ${track.id}`);
    });
  }
  function draw() {
    if (!source()) return;
    if (!source().sections.some(s=>s.id===sectionId)) sectionId=source().sections[0]?.id;
    const picker = byId('piano-section'); picker.replaceChildren();
    for (const s of source().sections) picker.add(new Option(label(s.id),s.id));
    picker.value=sectionId;
    drawBrowser(); drawMixer(); if(dock==='piano') drawPiano(); sync();
  }
  function selectSection(id) {
    sectionId=id; byId('piano-section').value=id;
    drawBrowser(); if(dock==='piano') drawPiano();
    seek(section().start_tick); sync();
  }
  function sync() {
    if (!source()) return;
    const matches = matching();
    const state = byId('playback-state');
    state.textContent = !ui.rendition ? 'Choose a render' : matches ? 'Audio matches displayed source' : 'Audio differs from displayed source · render to update';
    state.classList.toggle('stale',!!ui.rendition&&!matches);
    byId('loop').disabled=!matches||!Number.isFinite(audio.duration);
    if (!matches) {
      byId('musical-position').textContent='—'; byId('tempo-display').textContent='— BPM';
      return;
    }
    const tick = tickAtTime(source(),audio.currentTime);
    const changes = timeChanges(source());
    const active = [...changes].reverse().find(c=>c.tick<=tick)??changes[0];
    byId('tempo-display').textContent=`${active.bpm} BPM · ${active.numerator}/${active.denominator}`;
    let bar=1, beat=1;
    // Meter runs, not tempo runs: a tempo change can occur inside a bar.
    const meters=changes.filter((c,i)=>!i||c.numerator!==changes[i-1].numerator||c.denominator!==changes[i-1].denominator);
    for(let i=0;i<meters.length;i++) {
      const c=meters[i], end=Math.min(tick,meters[i+1]?.tick??source().length_ticks);
      const beatTicks=source().ppq*4/c.denominator, barTicks=beatTicks*c.numerator;
      if(tick>=c.tick) {bar+=Math.floor((end-c.tick)/barTicks);beat=1+Math.floor(((end-c.tick)%barTicks)/beatTicks);}
      if(end===tick) break;
    }
    byId('musical-position').textContent=`${bar}.${beat}`;
    byId('arrangement-timeline').position=tick;
    const noteTimeline=byId('note-timeline');
    if(noteTimeline) noteTimeline.position=Math.max(0,(tick-section().start_tick)/source().ppq);
    if(looping&&!audio.paused&&section() && audio.currentTime >= secondsAt(section().end_tick)) audio.currentTime=secondsAt(section().start_tick);
  }
  function waveform(peaks,duration=audio.duration) {
    wave?.destroy(); wave=null;
    byId('waveform').hidden=!peaks?.length;
    if(!peaks?.length||!Number.isFinite(duration)||!duration) return;
    wave=WaveSurfer.create({container:byId('waveform'),media:audio,peaks:[Array.from(peaks)],duration,
      height:42,waveColor:'#607b83',progressColor:'#c7df8b',cursorColor:'#e9eef3',cursorWidth:1,
      barWidth:2,barGap:1,normalize:false,interact:true,hideScrollbar:true});
  }
  byId('browser-search').addEventListener('input',drawBrowser);
  byId('toggle-browser').addEventListener('click',()=>{
    const p=byId('browser-panel');p.hidden=!p.hidden;
    document.querySelector('.workspace').classList.toggle('browser-hidden',p.hidden);
    byId('toggle-browser').setAttribute('aria-pressed',String(!p.hidden));
  });
  byId('toggle-review').addEventListener('click',()=>{
    const p=byId('review-panel');p.hidden=!p.hidden;byId('toggle-review').setAttribute('aria-pressed',String(!p.hidden));
  });
  for(const b of document.querySelectorAll('[data-dock]')) b.addEventListener('click',()=>{
    dock=b.dataset.dock;
    for(const tab of document.querySelectorAll('[data-dock]'))tab.setAttribute('aria-pressed',String(tab===b));
    byId('mix-console').hidden=dock!=='mixer';byId('piano-editor').hidden=dock!=='piano';
    byId('piano-section-label').hidden=dock!=='piano';
    byId('dock-context').textContent=dock==='mixer'?'Source gains · stage changes, apply, then render':'Notes · stage edits, apply, then render';
    if(dock==='piano')drawPiano();
  });
  byId('piano-section').addEventListener('change',e=>selectSection(e.target.value));
  byId('arrangement-timeline').addEventListener('change',e=>{if(e.target===byId('arrangement-timeline'))seek(e.detail.value);});
  byId('stop').addEventListener('click',()=>{audio.pause();if(ui.loadedAudio)audio.currentTime=0;});
  byId('loop').addEventListener('click',()=>{
    looping=!looping;byId('loop').setAttribute('aria-pressed',String(looping));
    if(looping)seek(section().start_tick);
  });
  document.addEventListener('keydown',e=>{
    if(e.target.closest('input,select,textarea,button,[contenteditable="true"],audio-ui-piano-roll'))return;
    if(e.code==='Space'){e.preventDefault();if(!byId('play').disabled)byId('play').click();}
    if(e.code==='Home'){e.preventDefault();byId('stop').click();}
  });
  function setBusy() {
    for (const fader of document.querySelectorAll('audio-ui-fader')) {
      fader.toggleAttribute('disabled', ui.busy || ui.view?.revision !== ui.snapshot?.project.revision);
    }
  }
  return {draw,sync,waveform,selectSection,showReview,setBusy};
}
