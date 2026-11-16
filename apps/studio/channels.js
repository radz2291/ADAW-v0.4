// Shared channel controls for the arrangement rail and console. Both write the
// same typed operations; the compact rail is hidden while the console is open.
const FADER = {min:-60,max:12,step:.1}; // Versioned view travel, not DSP limits.
export function createChannelControls({entity,kind,key,title,readOnly,compact=false,
  node,button,stage,liveMix,mixEntity}) {
  const shown=()=>mixEntity(entity,key), initial=shown();
  const operation=value=>key?{kind,[key]:entity.id,value}:{kind,value};
  const commit=value=>{const op=operation(value);liveMix(op);return stage(op,`Adjust ${title} gain`);};
  const fader=node('audio-ui-fader',{attrs:{min:Math.min(FADER.min,initial.gain_db),max:Math.max(FADER.max,initial.gain_db),
    step:FADER.step,'default-value':0,orientation:compact?'horizontal':'vertical','data-entity':entity.id??'master'}});
  fader.value=initial.gain_db;fader.toggleAttribute('disabled',readOnly);
  const control=node('audio-ui-fader-control'),track=node('audio-ui-fader-track');
  track.append(node('audio-ui-fader-indicator'));
  control.append(track,node('audio-ui-fader-thumb',{attrs:{'aria-label':`${title} source gain in dB`}}));fader.append(control);
  const number=node('input',{classes:'gain-readout',attrs:{type:'number',step:.1,'aria-label':`${title} gain in dB`,title:'Gain · dB'}});
  number.value=initial.gain_db;number.disabled=readOnly;
  number.addEventListener('change',()=>{if(number.checkValidity()&&Number.isFinite(number.valueAsNumber))commit(number.valueAsNumber);});
  number.addEventListener('keydown',event=>{if(event.key==='Enter'){event.preventDefault();number.blur();}});
  fader.addEventListener('input',event=>{
    if(readOnly)return event.preventDefault();
    if(event.detail){number.value=event.detail.value.toFixed(1);liveMix(operation(event.detail.value));}
  });
  fader.addEventListener('change',event=>{
    if(readOnly||!event.detail)return;
    const value=Math.round(event.detail.value*10)/10;number.value=value;
    stage(operation(value),`Adjust ${title} gain`);
  });
  const reset=button('0 dB',()=>commit(0),{disabled:readOnly,attrs:{title:`Reset ${title} gain`}});
  const toggles=node('div',{classes:'channel-buttons'}),switches=[];
  let pan=null,center=null;
  if(key==='track_id') {
    for(const field of ['mute','solo']) {
      const toggle=button(field==='mute'?'M':'S',()=>{
        const op={kind:`set_track_${field}`,track_id:entity.id,value:!shown()[field]};liveMix(op);stage(op,`${field} ${title}`);
      },{disabled:readOnly,attrs:{'aria-label':`${field==='mute'?'Mute':'Solo'} ${title}`,'aria-pressed':!!initial[field],title:field==='mute'?'Mute · takes priority over Solo':'Solo · multiple tracks can play together'}});
      switches.push([field,toggle]);toggles.append(toggle);
    }
    const panCommit=value=>{const op={kind:'set_track_pan',track_id:entity.id,value};liveMix(op);stage(op,`Pan ${title}`);};
    pan=node('input',{classes:'pan-control',attrs:{type:'range',min:-1,max:1,step:.01,'aria-label':`${title} pan`,title:'Pan · double-click to center'}});
    pan.value=initial.pan;pan.disabled=readOnly;
    pan.addEventListener('input',()=>liveMix({kind:'set_track_pan',track_id:entity.id,value:pan.valueAsNumber}));
    pan.addEventListener('change',()=>panCommit(pan.valueAsNumber));
    pan.addEventListener('dblclick',()=>{if(!readOnly)panCommit(0);});
    center=button('Center',()=>panCommit(0),{disabled:readOnly,attrs:{title:'Reset pan to center'}});
  }
  function sync() {
    const current=shown();
    fader.setAttribute('min',Math.min(FADER.min,current.gain_db));fader.setAttribute('max',Math.max(FADER.max,current.gain_db));
    fader.value=current.gain_db;
    if(document.activeElement!==number)number.value=current.gain_db;
    if(pan&&document.activeElement!==pan)pan.value=current.pan;
    for(const [field,toggle]of switches)toggle.setAttribute('aria-pressed',String(!!current[field]));
  }
  return {fader,number,reset,toggles,pan,center,sync};
}
