import WaveSurfer from 'wavesurfer.js';
import { createChannelControls } from './channels.js';
import { soundIdentity } from './monitor.js';


export function createDesktop({ ui, audio, byId, node, button, label, trackColors, stage, notice,
  selectTrack, currentTrack, drawInspector, tickAtTime, timeChanges, liveMix, mixEntity }) {
  let dock = localStorage.getItem('adaw.studio.dock.v1') || 'piano', sectionId = null, looping = false, wave = null, snap=.25, drawMode=false, group=null;
  let trackWaves=null;
  function drawTrackWaveforms() {
    for(const old of document.querySelectorAll('.track-waveform'))old.remove();
    for(const lane of document.querySelectorAll('.has-waveform'))lane.classList.remove('has-waveform');
    if(!source()||trackWaves?.key!==soundIdentity(source()))return;
    for(const [id,peaks]of Object.entries(trackWaves.tracks)) {
      const lane=document.querySelector(`.timeline-row[data-track-id="${CSS.escape(id)}"] .lane`);if(!lane)continue;
      const svg=document.createElementNS('http://www.w3.org/2000/svg','svg');
      svg.setAttribute('class','track-waveform');svg.setAttribute('viewBox',`0 0 ${peaks.length} 100`);
      svg.setAttribute('preserveAspectRatio','none');svg.setAttribute('aria-hidden','true');
      const path=document.createElementNS('http://www.w3.org/2000/svg','path');
      path.setAttribute('d',peaks.map((value,i)=>`M${i},${50-Math.min(1,value)*45}V${50+Math.min(1,value)*45}`).join(''));
      path.setAttribute('stroke','currentColor');path.setAttribute('stroke-width','1');svg.append(path);lane.append(svg);
      lane.classList.add('has-waveform');
    }
  }
  function setTrackWaveforms(value){trackWaves=value;drawTrackWaveforms();}
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
    root.append(button('Instruments & effects', () => selectDock('devices'), {classes:'browser-section'}));
  }
  let mixerUpdates=[],railUpdates=[];
  function syncMixer(){for(const update of [...mixerUpdates,...railUpdates])update();}
  const controls=(entity,kind,key,compact=false)=>createChannelControls({entity,kind,key,compact,
    title:label(entity.id??'master'),readOnly:ui.view.revision!==ui.snapshot.project.revision,node,button,stage,liveMix,mixEntity});
  function beginTrackHeaders(){railUpdates=[];}
  function trackHeader(track,trackButton) {
    const root=node('div',{classes:'track-strip-header'}),heading=node('div',{classes:'track-heading'});
    heading.append(trackButton);root.append(heading);
    const parts=controls(track,'set_track_gain','track_id',true),tools=node('div',{classes:'track-header-controls'});
    const devices=button('Devices',()=>{selectTrack(track);selectDock('devices');},{classes:'track-devices',attrs:{title:`${label(track.id)} instrument and effects`}});
    heading.append(parts.toggles);tools.append(parts.fader,parts.number,parts.pan,devices);root.append(tools);railUpdates.push(parts.sync);
    return root;
  }
  function drawMixer() {
    mixerUpdates=[];const root=byId('mix-console'),scroll=root.scrollLeft;root.replaceChildren();
    if(!source())return;
    const add=(entity,kind,key,color,index)=>{
      const title=label(entity.id??'master'),strip=node('section',{classes:'channel-strip',attrs:{'aria-label':`${title} channel`}});
      strip.style.setProperty('--track-color',color);strip.classList.toggle('selected',entity.id===ui.trackId);
      const heading=key==='track_id'?button(title,()=>selectTrack(entity),{classes:'channel-name',attrs:{title}}):node('h3',{text:title,classes:'channel-name',attrs:{title}});
      strip.append(node('span',{text:String(index).padStart(2,'0'),classes:'channel-number'}),heading,
        node('p',{text:key==='track_id'?`→ ${label(entity.bus)}`:'BUS / OUTPUT',classes:'channel-route'}));
      const parts=controls(entity,kind,key);
      if(parts.pan)strip.append(parts.toggles,parts.pan,parts.center);
      strip.append(parts.fader,parts.number,parts.reset);mixerUpdates.push(parts.sync);root.append(strip);
    };
    source().tracks.forEach((t,i)=>add(t,'set_track_gain','track_id',trackColors[t.role.toLowerCase()]??'#91a6c0',i+1));
    source().buses.forEach((b,i)=>add(b,'set_bus_gain','bus_id','#a597d1',source().tracks.length+i+1));
    add(source().master,'set_master_gain',null,'#c7df8b',source().tracks.length+source().buses.length+1);root.scrollLeft=scroll;
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
    // Keyboard transposition is limited by MIDI, not the current viewport.
    roll.addEventListener('keydown', e => {
      if(!['ArrowUp','ArrowDown'].includes(e.key)||e.target.closest('input,select,textarea'))return;
      const delta=(e.key==='ArrowUp'?1:-1)*(e.shiftKey?12:1);
      const selected=roll.value.filter(n=>roll.selection.includes(n.id));
      if(!selected.length)return;
      const targets=selected.map(n=>Math.max(0,Math.min(127,n.pitch+delta)));
      roll.setAttribute('min-pitch',Math.min(Number(roll.getAttribute('min-pitch')),Math.max(0,Math.min(...targets)-2)));
      roll.setAttribute('max-pitch',Math.max(Number(roll.getAttribute('max-pitch')),Math.min(127,Math.max(...targets)+2)));
    },true);
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
    drawBrowser(); drawMixer(); drawGroup(); byId('dock-context').textContent=dock==='devices'?'Instrument & effects':dock==='mixer'?'Mix console':label(currentTrack()?.id); if(dock==='piano') drawPiano(); sync();
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
  function closeReview() {
    byId('review-panel').hidden=true;
    byId('toggle-review').setAttribute('aria-pressed','false');
    byId('toggle-review').focus();
  }
  byId('close-review').addEventListener('click',closeReview);
  function selectDock(next) {
    dock=['piano','mixer','devices'].includes(next)?next:'piano';
    document.body.dataset.dockView=dock;
    localStorage.setItem('adaw.studio.dock.v1',dock);
    for(const tab of document.querySelectorAll('[data-dock]'))tab.setAttribute('aria-pressed',String(tab.dataset.dock===dock));
    byId('mix-console').hidden=dock!=='mixer';byId('piano-editor').hidden=dock!=='piano';
    byId('piano-section-label').hidden=dock!=='piano';
    byId('dock-context').textContent=dock==='devices'?'Instrument & effects':dock==='mixer'?'Mix console':currentTrack()?label(currentTrack().id):'Select a track';
    ui.inspector=dock==='devices'?'plugins':'edit';drawInspector();
    if(dock==='piano')drawPiano();
    document.dispatchEvent(new CustomEvent('studio:dockchange',{detail:{dock}}));
  }
  for(const b of document.querySelectorAll('[data-dock]'))b.addEventListener('click',()=>selectDock(b.dataset.dock));
  byId('piano-section').addEventListener('change',e=>selectSection(e.target.value));
  byId('arrangement-timeline').addEventListener('change',e=>{if(e.target===byId('arrangement-timeline'))seek(e.detail.value);});
  byId('stop').addEventListener('click',()=>{ui.resumeOnLoad=false;audio.pause();if(ui.loadedAudio)audio.currentTime=0;});
  byId('loop').addEventListener('click',()=>{
    looping=!looping;byId('loop').setAttribute('aria-pressed',String(looping));
    if(looping)seek(section().start_tick);
  });
  document.addEventListener('keydown',e=>{
    if(byId('help-dialog').open)return;
    if(e.key==='Escape'&&(!byId('review-panel').hidden||byId('playback-details').open)) {
      if(!byId('review-panel').hidden)closeReview();
      else {byId('playback-details').open=false;byId('playback-details').querySelector('summary').focus();}
      e.preventDefault();e.stopImmediatePropagation();return;
    }
    if(e.target.closest('input,select,textarea,[contenteditable="true"]'))return;
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
  selectDock(dock);
  return {draw,sync,syncMixer,setTrackWaveforms,drawTrackWaveforms,waveform,selectSection,selectGroup,selectDock,beginTrackHeaders,trackHeader,showReview,setBusy};
}
