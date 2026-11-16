// Workspace preferences only. These never change musical source or history.
export function setupLayout() {
  const key = 'adaw.studio.layout.v2';
  const get = id => document.getElementById(id);
  const workspace = document.querySelector('.workspace');
  const divider = get('pane-divider'), dialog = get('help-dialog');
  const defaults = () => ({browser: false, inspector: false, arrangementHeight: null});
  let preferences = defaults(), drag = null, helpTrigger = null;
  try {
    const saved = JSON.parse(localStorage.getItem(key) ?? 'null');
    if (saved && typeof saved === 'object') {
      for (const panel of ['browser', 'inspector']) if (typeof saved[panel] === 'boolean') preferences[panel] = saved[panel];
      if (Number.isFinite(saved.arrangementHeight)) preferences.arrangementHeight = saved.arrangementHeight;
    }
  } catch { /* A denied or damaged preference store must not prevent playback. */ }
  const save = () => { try { localStorage.setItem(key, JSON.stringify(preferences)); } catch {} };
  const available = () => {
    const h=selector=>document.querySelector(selector)?.getBoundingClientRect().height??0;
    return Math.max(280,innerHeight-h('.topbar')-h('.transport')-h('.arrangement>.panel-heading')-
      h('#group-tools')-h('#pane-divider')-h('.dock-heading')-20);
  };
  const limits = () => ({min:120,max:Math.max(180,available()-120)});
  const height = () => Math.round(Math.max(limits().min,Math.min(limits().max,
    preferences.arrangementHeight??available()*.5)));
  function render() {
    for (const panel of ['browser', 'inspector']) {
      const container = get(`${panel}-panel`), toggle = get(`toggle-${panel}`);
      const dock=document.body.dataset.dockView??'piano';
      if(container)container.hidden=panel==='browser'?!preferences.browser:dock==='devices'?false:dock==='mixer'||!preferences.inspector;
      if(panel==='inspector')toggle.hidden=dock!=='piano';
      workspace?.classList.toggle(`${panel}-hidden`, !preferences[panel]);
      toggle?.setAttribute('aria-pressed', String(preferences[panel]));
      toggle?.setAttribute('aria-expanded', String(preferences[panel]));
      toggle?.setAttribute('aria-controls', `${panel}-panel`);
    }
    document.documentElement.style.setProperty('--arrangement-height', `${height()}px`);
    if (divider) {
      divider.setAttribute('aria-valuemin', String(limits().min));
      divider.setAttribute('aria-valuemax', String(limits().max));
      divider.setAttribute('aria-valuenow', String(height()));
      divider.setAttribute('aria-valuetext', `Arrangement height ${height()} pixels`);
    }
  }
  for (const panel of ['browser', 'inspector']) get(`toggle-${panel}`)?.addEventListener('click', () => {
    preferences[panel] = !preferences[panel]; render(); save();
  });
  if (divider) {
    divider.tabIndex = 0;
    divider.setAttribute('role', 'separator');
    divider.setAttribute('aria-orientation', 'horizontal');
    divider.setAttribute('aria-label', 'Resize arrangement and editor panes');
    divider.title = 'Drag to resize arrangement · Arrow keys: 20 px · Shift: 60 px · Home: reset';
    divider.addEventListener('pointerdown', event => {
      if (event.button !== 0) return;
      drag = {startY: event.clientY, height: height(), previous: preferences.arrangementHeight};
      divider.setPointerCapture(event.pointerId); divider.focus();
      divider.classList.add('resizing'); event.preventDefault();
    });
    divider.addEventListener('pointermove', event => {
      if (!drag) return;
      preferences.arrangementHeight = Math.max(limits().min, Math.min(limits().max,
        drag.height + event.clientY - drag.startY)); render();
    });
    const finish = () => { if (drag) { drag = null; divider.classList.remove('resizing'); save(); } };
    divider.addEventListener('pointerup', finish);
    divider.addEventListener('lostpointercapture', finish);
    divider.addEventListener('pointercancel', () => {
      if (drag) { preferences.arrangementHeight = drag.previous; drag = null; render(); }
      divider.classList.remove('resizing');
    });
    divider.addEventListener('keydown', event => {
      if (!['ArrowUp', 'ArrowDown', 'Home', 'Escape'].includes(event.key)) return;
      event.preventDefault(); event.stopPropagation();
      if (event.key === 'Escape') {
        if (drag) { preferences.arrangementHeight = drag.previous; drag = null; divider.classList.remove('resizing'); }
      } else if (event.key === 'Home') preferences.arrangementHeight = null;
      else preferences.arrangementHeight = Math.max(limits().min, Math.min(limits().max,
        height() + (event.key === 'ArrowDown' ? 1 : -1) * (event.shiftKey ? 60 : 20)));
      render(); save();
    });
  }
  get('reset-layout')?.addEventListener('click', () => { preferences = defaults(); render(); save(); });
  get('help')?.addEventListener('click', () => { helpTrigger = document.activeElement; dialog?.showModal(); });
  get('close-help')?.addEventListener('click', () => dialog?.close());
  dialog?.addEventListener('close', () => helpTrigger?.focus());
  // Native dialog handles Escape and focus containment. Stop Studio shortcuts.
  dialog?.addEventListener('keydown', event => event.stopPropagation());
  window.addEventListener('resize', render);
  document.addEventListener('studio:dockchange',render);
  let resizeFrame;
  const observer=new ResizeObserver(()=>{cancelAnimationFrame(resizeFrame);resizeFrame=requestAnimationFrame(render);});
  for(const selector of ['.topbar','.transport','.arrangement>.panel-heading','#group-tools','.dock-heading']) {
    const item=document.querySelector(selector);if(item)observer.observe(item);
  }
  render();
  return {reset() { preferences = defaults(); render(); save(); }, get preferences() { return {...preferences}; }};
}
