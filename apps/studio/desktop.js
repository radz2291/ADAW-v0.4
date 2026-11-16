import WaveSurfer from 'wavesurfer.js';

// View policy, not audio-engine limits. Existing values outside fader travel expand it.
const FADER = { min: -60, max: 12, step: .1 };

export function createDesktop({ ui, audio, byId, node, button, label, trackColors, stage, notice,
  selectTrack, currentTrack, drawInspector, tickAtTime, timeChanges, liveMix, mixEntity }) {
  let dock = 'mixer', sectionId = null, looping = false, wave = null, snap=.25, drawMode=false, group=null;
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
    if (!matching()) return notice('Audition your latest edits before jumping to a section.');
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
      const b = button(label(t.id), () => selectTrack(t), { classes: 'browser-item', attrs: { 'aria-pressed': ui.trackId === t.id, title:label(t.id) } });
      b.style.setProperty('--track-color', trackColors[t.role.toLowerCase()] ?? '#91a6c0');
      b.append(node('span', {text: t.kind === 'samples' ? 'AUDIO' : 'MIDI', classes:'browser-kind'}));
      return b;
    });
    group('SONG SECTIONS', source().sections, s => button(label(s.id), () => selectSection(s.id), {
      classes:'browser-section', attrs:{'aria-pressed': section()?.id === s.id, title: `${label(s.id)} · ${s.mood}`}
    }));
    root.append(node('h3', {text:'DEVICES', classes:'browser-heading'}));
    root.append(button('Instruments & effects', () => {ui.inspector = 'plugins'; drawInspector();}, {classes:'browser-section'}));
  }
  let mixerUpdates = [];
  function syncMixer() { for (const update of mixerUpdates) update(); }
  function drawMixer() {
    mixerUpdates = [];
    const root = byId('mix-console'), scroll=root.scrollLeft; root.replaceChildren();
    if (!source()) return;
    const readOnly = ui.view.revision !== ui.snapshot.project.revision;
    const add = (entity, kind, key, color, index) => {
      const shown = mixEntity(entity,key), toggles = [];
      let pan;
      const title = label(entity.id ?? 'master');
      const strip = node('section', {classes:'channel-strip', attrs:{'aria-label':`${title} channel`}});
      strip.style.setProperty('--track-color', color);
      strip.classList.toggle('selected', entity.id === ui.trackId);
      const heading = key === 'track_id'
        ? button(title, () => selectTrack(entity), {classes:'channel-name',attrs:{title}})
        : node('h3', {text:title, classes:'channel-name',attrs:{title}});
      strip.append(node('span',{text:String(index).padStart(2,'0'),classes:'channel-number'}), heading);
      strip.append(node('p',{text:key==='track_id' ? `→ ${label(entity.bus)}` : 'BUS / OUTPUT',classes:'channel-route'}));
      const fader = node('audio-ui-fader', {attrs:{min:Math.min(FADER.min, shown.gain_db), max:Math.max(FADER.max, shown.gain_db),
        step:FADER.step, 'default-value':shown.gain_db, 'data-entity': entity.id ?? 'master'}});
      fader.value = shown.gain_db;
      fader.toggleAttribute('disabled', readOnly);
      const control = node('audio-ui-fader-control');
      const track = node('audio-ui-fader-track'); track.append(node('audio-ui-fader-indicator'));
      control.append(track, node('audio-ui-fader-thumb',{attrs:{'aria-label':`${title} source gain in dB`}}));
      fader.append(control);
      const readout = node('input', {classes:'gain-readout',attrs:{type:'number',step:.1,'aria-label':`${title} gain in dB`}});
      readout.value=shown.gain_db; readout.disabled=readOnly;
      const commit=value=>{const op=key?{kind,[key]:entity.id,value}:{kind,value};liveMix(op);stage(op,`Adjust ${title} gain`);};
      readout.addEventListener('change',()=>{if(readout.checkValidity()&&Number.isFinite(readout.valueAsNumber))commit(readout.valueAsNumber);});
      const reset=button('0 dB',()=>commit(0),{disabled:readOnly,attrs:{title:`Reset ${title} gain`}});
      fader.addEventListener('input', e => {
        if (readOnly) return e.preventDefault();
        if (e.detail) { readout.value = e.detail.value.toFixed(1); liveMix(key ? {kind,[key]:entity.id,value:e.detail.value} : {kind,value:e.detail.value}); }
      });
      fader.addEventListener('change', e => {
        if (!e.detail || readOnly) return;
        const value = Math.round(e.detail.value * 10) / 10;
        readout.value = value;
        if (value !== shown.gain_db) stage(key ? {kind, [key]:entity.id, value} : {kind,value}, `Set ${title} gain to ${value} dB`);
      });
      if(key==='track_id') {
        const channelButtons=node('div',{classes:'channel-buttons'});
        for(const field of ['mute','solo']) {
          const toggle=button(field==='mute'?'M':'S',()=>{
            const op={kind:`set_track_${field}`,track_id:entity.id,value:!mixEntity(entity,key)[field]};
            liveMix(op);stage(op,`${field} ${title}`);
          },{disabled:readOnly,attrs:{'aria-label':`${field==='mute'?'Mute':'Solo'} ${title}`,'aria-pressed':!!shown[field],title:field==='mute'?'Mute (takes priority over Solo)':'Solo (multiple tracks can be soloed)'}});
          toggles.push([field,toggle]);channelButtons.append(toggle);
        }
        strip.append(channelButtons);
        pan=node('input',{attrs:{type:'range',min:-1,max:1,step:.01,'aria-label':`${title} pan`}});pan.value=shown.pan;pan.disabled=readOnly;
        pan.addEventListener('input',()=>liveMix({kind:'set_track_pan',track_id:entity.id,value:pan.valueAsNumber}));
        pan.addEventListener('change',()=>stage({kind:'set_track_pan',track_id:entity.id,value:pan.valueAsNumber},`Pan ${title}`));
        strip.append(pan,button('Center',()=>{const op={kind:'set_track_pan',track_id:entity.id,value:0};liveMix(op);stage(op,`Center ${title}`);},{disabled:readOnly,attrs:{title:'Reset pan to center'}}));
      }
      mixerUpdates.push(()=>{
        const current=mixEntity(entity,key);
        fader.value=current.gain_db;
        if(document.activeElement!==readout)readout.value=current.gain_db;
        if(pan && document.activeElement!==pan)pan.value=current.pan;
        for(const [field,toggle] of toggles)toggle.setAttribute('aria-pressed',String(!!current[field]));
      });
      strip.append(fader, readout, reset);
      root.append(strip);
    };
    source().tracks.forEach((t,i) => add(t,'set_track_gain','track_id',trackColors[t.role.toLowerCase()]??'#91a6c0',i+1));
    source().buses.forEach((b,i) => add(b,'set_bus_gain','bus_id','#a597d1',source().tracks.length+i+1));
    add(source().master,'set_master_gain',null,'#c7df8b',source().tracks.length+source().buses.length+1);
    root.scrollLeft=scroll;
  }
  function drawPiano() {
    const root = byId('piano-editor'); const oldScroll=root.querySelector('audio-ui-timeline-viewport')?.scrollLeft??0; root.replaceChildren();
    const track = currentTrack(), range = section();
    if (!track || !range) return;
    if (track.kind === 'samples') {
      root.append(node('div',{text:'Audio / sample track. Select a MIDI instrument to edit notes. Sample timing and velocity are available in the Notes inspector.',classes:'editor-empty'})); return;
    }
    const ppq = source().ppq;
    let events = track.events.filter(e => e.start_tick >= range.start_tick && e.start_tick < range.end_tick);
    const notes = events.map(e => ({id:e.id,pitch:e.note,start:(e.start_tick-range.start_tick)/ppq,length:e.duration_ticks/ppq,velocity:e.velocity/127}));
    const pitches = events.map(e=>e.note);
    const low = Math.max(0, (pitches.length ? Math.min(...pitches) : 60)-2);
    const high = Math.min(127,Math.max(low+12,(pitches.length ? Math.max(...pitches) : 72)+2));
    const timeline = node('audio-ui-timeline',{attrs:{id:'note-timeline',duration:(range.end_tick-range.start_tick)/ppq,'snap-step':snap,'min-zoom':8,'max-zoom':240}});
    const roll = node('audio-ui-piano-roll',{attrs:{'min-pitch':low,'max-pitch':high,mode:drawMode?'draw':'select'}});
    roll.createNoteId=()=>`note-${crypto.randomUUID()}`;
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
    const toolbar=node('div',{classes:'note-tools'});
    const unavailable=track.protected||ui.view.revision!==ui.snapshot.project.revision;
    toolbar.append(button(drawMode?'Draw notes ✓':'Draw notes',()=>{drawMode=!drawMode;drawPiano();},{disabled:unavailable,attrs:{'aria-pressed':drawMode,title:'Click empty space to add notes; double-click also adds in Select mode'}}));
    const snapPicker=node('select',{attrs:{'aria-label':'Note snap'}});
    for(const [text,value] of [['1/4',1],['1/8',.5],['1/16',.25],['1/32',.125],['Off',0]])snapPicker.add(new Option(text,String(value)));
    snapPicker.value=String(snap);snapPicker.addEventListener('change',()=>{snap=Number(snapPicker.value);timeline.setAttribute('snap-step',snap);});
    toolbar.append(node('span',{text:'Snap'}),snapPicker);
    const shortcut=(key,ctrl=false)=>{grid.focus();grid.dispatchEvent(new KeyboardEvent('keydown',{key,ctrlKey:ctrl,bubbles:true,cancelable:true}));};
    for(const [text,key,ctrl] of [['Delete','Delete',false],['Duplicate','d',true],['Copy','c',true],['Paste','v',true]])toolbar.append(button(text,()=>shortcut(key,ctrl),{disabled:unavailable}));
    toolbar.append(node('span',{text:track.protected?'Protected track':`${label(track.id)} · ${events.length} notes`,classes:'piano-info',attrs:{title:label(track.id)}}));
    root.append(toolbar,timeline);
    roll.value=notes;
    roll.selection=(ui.selection?.length?ui.selection:[ui.eventId]).filter(id=>notes.some(n=>n.id===id));
    viewport.scrollLeft=oldScroll;
    roll.addEventListener('noteselect', e => {
      ui.selection=[...e.detail.selection];ui.eventId=ui.selection[0]??null;drawInspector();
    });
    roll.addEventListener('change', e => {
      if(!e.detail||unavailable)return;
      const operations=[],additions=[];
      for(const n of e.detail.value) {
        const values={start_tick:range.start_tick+Math.round(n.start*ppq),duration_ticks:Math.max(1,Math.round(n.length*ppq)),note:Math.round(n.pitch),velocity:Math.max(1,Math.min(127,Math.round((n.velocity??1)*127)))};
        const old=events.find(v=>v.id===n.id);
        if(!old)additions.push({id:String(n.id),...values});
        else {const changes=Object.fromEntries(Object.entries(values).filter(([k,v])=>old[k]!==v));if(Object.keys(changes).length)operations.push({kind:'edit_event',track_id:track.id,event_id:n.id,changes});}
      }
      const deleted=events.filter(v=>!e.detail.value.some(n=>n.id===v.id)).map(v=>v.id);
      if(additions.length)operations.push({kind:'add_events',track_id:track.id,events:additions});
      if(deleted.length)operations.push({kind:'delete_events',track_id:track.id,event_ids:deleted});
      ui.selection=[...roll.selection];ui.eventId=ui.selection[0]??null;
      if(operations.length) {
        events=e.detail.value.map(n=>({id:n.id,start_tick:range.start_tick+Math.round(n.start*ppq),duration_ticks:Math.max(1,Math.round(n.length*ppq)),note:Math.round(n.pitch),velocity:Math.max(1,Math.min(127,Math.round((n.velocity??1)*127)))}));
        stage(operations,`Edit notes on ${label(track.id)}`);
      }
    });
  }
  function selectGroup(track, range, events) {
    group={trackId:track.id,ids:events.map(e=>e.id),start:range.start_tick,end:range.end_tick};
    selectSection(range.id);drawGroup();
  }
  function drawGroup() {
    const root=byId('group-tools');root.replaceChildren();
    const track=source()?.tracks.find(t=>t.id===group?.trackId);
    if(!track){root.append(node('span',{text:'Select a section clip to arrange it.'}));return;}
    const ids=group.ids.filter(id=>track.events.some(e=>e.id===id));
    const locked=track.protected||ui.view.revision!==ui.snapshot.project.revision;
    root.append(node('span',{text:`${label(track.id)} · ${ids.length} events${locked?' · Locked':''}`,attrs:{title:label(track.id)}}));
    const numeric=(name,value)=>{const input=node('input',{attrs:{type:'number',step:1,'aria-label':name,title:name}});input.value=value;input.disabled=locked;const wrap=node('label',{text:name.replace('Group ','').replace(' (beats)','').replace('Split at beat','Split at'),classes:'group-field'});wrap.append(input);root.append(wrap);return input;};
    const start=numeric('Group start (beats)',group.start/source().ppq+1),end=numeric('Group end (beats)',group.end/source().ppq+1);
    const common={track_id:track.id,event_ids:ids};
    const run=(op,reason)=>stage(op,reason).then(()=>drawGroup());
    root.append(button('Move',()=>{
      const offset=Math.round((start.valueAsNumber-1)*source().ppq)-group.start;
      run({kind:'transform_events',...common,action:'move',offset_ticks:offset},'Move section group');
      group.start+=offset;group.end+=offset;
    },{disabled:locked}),button('Duplicate',()=>{
      const new_ids=Object.fromEntries(ids.map(id=>[id,`event-${crypto.randomUUID()}`]));
      run({kind:'duplicate_events',...common,new_ids,offset_ticks:Math.round((start.valueAsNumber-1)*source().ppq)-group.start||group.end-group.start},'Duplicate section group');
    },{disabled:locked}));
    const split=numeric('Split at beat',(group.start+group.end)/2/source().ppq+1);
    root.append(button('Split',()=>{
      const tick=Math.round((split.valueAsNumber-1)*source().ppq);
      const new_ids=Object.fromEntries(track.events.filter(e=>ids.includes(e.id)&&e.start_tick<tick&&e.start_tick+e.duration_ticks>tick).map(e=>[e.id,`event-${crypto.randomUUID()}`]));
      run({kind:'transform_events',...common,action:'split',tick,new_ids},'Split notes at beat');
      group.ids.push(...Object.values(new_ids));
    },{disabled:locked}),button('Trim',()=>run({kind:'transform_events',...common,action:'trim',start_tick:Math.round((start.valueAsNumber-1)*source().ppq),end_tick:Math.round((end.valueAsNumber-1)*source().ppq)},'Trim section group'),{disabled:locked}));
    if(track.kind==='samples')root.append(node('span',{text:'Sample groups: end trim only; split/front trim unavailable.',classes:'small'}));
  }

  function draw() {
    if (!source()) return;
    if (!source().sections.some(s=>s.id===sectionId)) sectionId=source().sections[0]?.id;
    const picker = byId('piano-section'); picker.replaceChildren();
    for (const s of source().sections) picker.add(new Option(label(s.id),s.id));
    picker.value=sectionId;
    drawBrowser(); drawMixer(); drawGroup(); if(dock==='piano') drawPiano(); sync();
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
    if(ui.audioLoading) {
      state.textContent='Loading mix…';state.classList.remove('stale');
      byId('loop').disabled=true;byId('musical-position').textContent='—';byId('tempo-display').textContent='— BPM';return;
    }
    state.textContent = !ui.rendition ? 'Ready to audition' : matches ? 'Latest mix' : 'Edits to hear · Audition';
    state.classList.toggle('stale',!!ui.rendition&&!matches);
    byId('loop').disabled=!matches||!Number.isFinite(audio.duration);
    byId('loop').title=`Loop ${label(section()?.id)} (${((section()?.end_tick-section()?.start_tick)/source().ppq).toFixed(0)} beats)`;
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
  byId('toggle-review').addEventListener('click',()=>{
    const p=byId('review-panel');p.hidden=!p.hidden;byId('toggle-review').setAttribute('aria-pressed',String(!p.hidden));
  });
  for(const b of document.querySelectorAll('[data-dock]')) b.addEventListener('click',()=>{
    dock=b.dataset.dock;
    for(const tab of document.querySelectorAll('[data-dock]'))tab.setAttribute('aria-pressed',String(tab===b));
    byId('mix-console').hidden=dock!=='mixer';byId('piano-editor').hidden=dock!=='piano';
    byId('piano-section-label').hidden=dock!=='piano';
    byId('dock-context').textContent=dock==='mixer'?'Adjust your mix · Audition for the finished sound':'Double-click to add · Drag to move · Audition to hear';
    if(dock==='piano')drawPiano();
  });
  byId('piano-section').addEventListener('change',e=>selectSection(e.target.value));
  byId('arrangement-timeline').addEventListener('change',e=>{if(e.target===byId('arrangement-timeline'))seek(e.detail.value);});
  byId('stop').addEventListener('click',()=>{ui.resumeOnLoad=false;audio.pause();if(ui.loadedAudio)audio.currentTime=0;});
  byId('loop').addEventListener('click',()=>{
    looping=!looping;byId('loop').setAttribute('aria-pressed',String(looping));
    if(looping)seek(section().start_tick);
  });
  document.addEventListener('keydown',e=>{
    if(e.target.closest('input,select,textarea,[contenteditable="true"]')||byId('help-dialog').open)return;
    const roll=byId('piano-editor').querySelector('audio-ui-piano-roll');
    if(e.key==='Escape') {
      group=null;ui.selection=[];ui.eventId=null;
      if(roll){roll.selection=[];roll.querySelector('audio-ui-piano-roll-grid')?.focus({preventScroll:true});}
      drawGroup();drawInspector();e.preventDefault();e.stopImmediatePropagation();
    }
    if(['Delete','Backspace'].includes(e.key)&&roll&&!roll.selection.length) {
      e.preventDefault();e.stopImmediatePropagation();
    }
  },true);
  document.addEventListener('keydown',e=>{
    if(e.target.closest('input,select,textarea,button,[contenteditable="true"],audio-ui-piano-roll'))return;
    if(e.code==='Space'){e.preventDefault();if(!byId('play').disabled)byId('play').click();}
    if(e.code==='Home'){e.preventDefault();byId('stop').click();}
  });
  function setBusy() {
    for (const fader of document.querySelectorAll('audio-ui-fader')) {
      fader.toggleAttribute('disabled', ui.view?.revision !== ui.snapshot?.project.revision);
    }
  }
  return {draw,sync,syncMixer,waveform,selectSection,selectGroup,showReview,setBusy};
}
