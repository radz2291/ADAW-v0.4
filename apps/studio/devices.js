// Device cards display service catalogs. Every gesture uses the typed edit service.
const VISIBLE_CONTROLS = 6; // View policy only; all catalog controls remain available.
const finite = value => typeof value === 'number' && Number.isFinite(value);
const format = value => finite(value) ? Number(value.toPrecision(6)).toString() : '';

export function drawDevices({ target, ui, track, readOnly, node, label, stage }) {
  const note = text => node('p', { text, classes: 'device-note' });
  if (!track) {
    target.append(node('div', { text: 'Select a track to shape its sound.', classes: 'device-empty' }));
    return;
  }
  const source = ui.view.source;
  const bus = source.buses.find(item => item.id === track.bus);
  const catalogs = ui.snapshot.plugins ?? [];
  const currentCatalog = predicate => readOnly ? null : catalogs.find(predicate);
  const rack = node('div', { classes: 'device-rack', attrs: { 'aria-label': `${label(track.id)} device chain` } });
  const route = node('div', { classes: 'device-route' });
  route.append(node('strong', { text: label(track.id) }),
    node('span', { text: '→', attrs: { 'aria-hidden': 'true' } }),
    node('span', { text: `${label(track.bus)} bus` }),
    node('span', { text: '→', attrs: { 'aria-hidden': 'true' } }), node('span', { text: 'Master' }));
  target.append(route, rack);
  let deviceIndex = 0, controlIndex = 0;

  function parameterControl(parameter, catalog, accessibleTitle, operation) {
    const faust = catalog.kind === 'faust';
    const binding = faust ? parameter.binding : String(parameter.index);
    const name = faust ? (parameter.label || parameter.name.split('/').at(-1)) : parameter.name;
    const minimum = faust ? parameter.min : 0;
    const maximum = faust ? parameter.max : 1;
    const validRange = finite(minimum) && finite(maximum) && minimum < maximum;
    const unavailable = readOnly || parameter.editable === false || !validRange;
    const known = finite(parameter.value);
    const tile = node('div', { classes: 'device-control' });
    const id = `device-control-${++controlIndex}`;
    const caption = node('label', { text: name, classes: 'device-control-name', attrs: { for: id, title: name } });
    const precision = node('input', { classes: 'device-control-value', attrs: { id, type: 'number', step: 'any',
      min: minimum, max: maximum, required: '', placeholder: 'Set value', 'aria-label': `${accessibleTitle} ${name} value`,
      title: `${format(minimum)}–${format(maximum)}${faust ? '' : ' normalized'} · Enter or leave the field to save` } });
    precision.disabled = unavailable;
    precision.value = format(parameter.value);
    let knob, pending = 0, lastIntent = parameter.value;
    const restore = () => {
      const latest = ui.snapshot.plugins?.find(row => ['track_id', 'bus_id', 'insert_index', 'module_sha256', 'registry_id']
        .every(key => row[key] === catalog[key]));
      const saved = latest?.parameters?.find(item => (faust ? item.binding : String(item.index)) === binding);
      const value = saved ? saved.value : parameter.value;
      precision.value = format(value);
      if (knob && finite(value)) knob.value = value;
      lastIntent = value;
    };
    const commit = value => {
      if (unavailable || !finite(value) || value < minimum || value > maximum || value === lastIntent) return;
      lastIntent = value;
      const gesture = ++pending;
      // Successful saves redraw from the new snapshot. A failed control returns
      // to its saved value; the main save UI owns the error and retry action.
      Promise.resolve(stage(operation(binding, value), `Set ${accessibleTitle} · ${name}`))
        .then(() => { if (tile.isConnected && gesture === pending) restore(); })
        .catch(() => { if (tile.isConnected && gesture === pending) restore(); });
    };
    if (known && validRange) {
      const step = faust ? (parameter.step > 0 ? parameter.step : (maximum - minimum) / 1000)
        : parameter.isBoolean ? 1 : parameter.isDiscrete && parameter.numSteps > 1 ? 1 / (parameter.numSteps - 1) : .001;
      knob = node('audio-ui-knob', { classes: 'device-knob', attrs: { min: minimum, max: maximum, step,
        'large-step': Math.min(maximum - minimum, step * 10), 'default-value': parameter.value,
        'drag-mode': 'vertical', title: 'Drag up or down · Shift for precision · double-click returns to the saved value' } });
      knob.toggleAttribute('disabled', unavailable);
      const surface = node('audio-ui-knob-control');
      surface.append(node('audio-ui-knob-track', { attrs: { 'stroke-width': 3 } }),
        node('audio-ui-knob-indicator', { attrs: { 'stroke-width': 3 } }),
        node('audio-ui-knob-thumb', { attrs: { 'aria-label': `${accessibleTitle} ${name} slider` } }));
      knob.append(surface);
      knob.value = parameter.value;
      knob.addEventListener('input', event => {
        if (!event.detail || unavailable) return;
        precision.value = format(event.detail.value);
      });
      knob.addEventListener('change', event => { if (event.detail) commit(event.detail.value); });
      tile.append(knob);
    } else {
      tile.append(node('div', { text: known ? format(parameter.value) : '—', classes: 'device-control-unknown',
        attrs: { title: known ? 'Fixed device value' : 'Current value is stored inside the saved plugin state' } }));
    }
    precision.addEventListener('change', () => {
      if (precision.reportValidity()) commit(precision.valueAsNumber);
    });
    precision.addEventListener('keydown', event => {
      if (event.key === 'Enter') {
        event.preventDefault();
        if (precision.reportValidity()) commit(precision.valueAsNumber);
      } else if (event.key === 'Escape') {
        event.preventDefault(); restore(); precision.blur();
      }
    });
    tile.append(caption, precision);
    if (!known) tile.append(node('span', { text: 'Saved state', classes: 'device-control-hint' }));
    if (parameter.editable === false) tile.append(node('span', { text: 'Read only', classes: 'device-control-hint' }));
    return tile;
  }

  function device(title, accessibleTitle, subtitle, catalog, operation, fallback) {
    const parameters = catalog?.parameters ?? [];
    const panel = node('section', { classes: 'device-card', attrs: { 'aria-label': `${accessibleTitle} device` } });
    panel.style.setProperty('--device-columns', Math.max(2, Math.min(3, parameters.length)));
    const heading = node('header', { classes: 'device-card-header' });
    const titles = node('div');
    titles.append(node('h3', { text: title }), node('span', { text: subtitle, classes: 'device-card-subtitle' }));
    heading.append(node('span', { text: String(++deviceIndex).padStart(2, '0'), classes: 'device-order', attrs: { 'aria-label': `Device ${deviceIndex}` } }), titles);
    panel.append(heading);
    if (!catalog || catalog.error || !operation) {
      panel.classList.add('device-card-readonly');
      panel.append(note(catalog?.error ? 'Controls unavailable. Your saved sound is unchanged.' : fallback));
      if (catalog?.error) panel.title = catalog.error.message;
      rack.append(panel);
      return;
    }
    if (!parameters.length) {
      panel.append(note('No adjustable controls.'));
    } else {
      const controls = node('div', { classes: 'device-controls' });
      for (const parameter of parameters.slice(0, VISIBLE_CONTROLS)) controls.append(parameterControl(parameter, catalog, accessibleTitle, operation));
      panel.append(controls);
      if (parameters.length > VISIBLE_CONTROLS) {
        const more = node('details', { classes: 'device-more' });
        more.append(node('summary', { text: `${parameters.length - VISIBLE_CONTROLS} more controls` }));
        const extra = node('div', { classes: 'device-controls' });
        more.append(extra);
        let populated = false;
        more.addEventListener('toggle', () => {
          if (!more.open || populated) return;
          populated = true;
          for (const parameter of parameters.slice(VISIBLE_CONTROLS)) extra.append(parameterControl(parameter, catalog, accessibleTitle, operation));
        });
        panel.append(more);
      }
    }
    rack.append(panel);
  }

  const instrumentCatalog = currentCatalog(entry => entry.track_id === track.id && entry.insert_index === undefined);
  const instrumentLabel = track.kind === 'samples' ? 'Sampler' : track.kind === 'vst' ? 'VST instrument' : 'Faust instrument';
  device(track.kind === 'samples' ? 'Sampler' : 'Instrument', instrumentLabel, label(track.id), instrumentCatalog,
    track.kind === 'samples' ? null : (binding, value) => ({ kind: 'set_instrument_parameter', track_id: track.id, binding, value }),
    track.kind === 'samples' ? 'Sample playback. Timing and velocity are in Notes.'
      : readOnly ? 'Earlier version · read only.' : 'Controls unavailable.');

  track.inserts.forEach((insert, index) => device('Track effect', `${index + 1}. ${insert.registry_id ? 'VST effect' : 'Faust effect'}`,
    `${label(track.id)} · insert ${index + 1}`, null, null, 'Read only · this effect remains active.'));
  bus?.inserts.forEach((insert, index) => device('Bus effect', `${label(bus.id)} ${index + 1}. ${insert.registry_id ? 'VST effect' : 'Faust effect'}`,
    `${label(bus.id)} · insert ${index + 1}`, currentCatalog(entry => entry.bus_id === bus.id && entry.insert_index === index),
    (binding, value) => ({ kind: 'set_bus_insert_parameter', bus_id: bus.id, insert_index: index, binding, value }),
    readOnly ? 'Earlier version · read only.' : 'Controls unavailable.'));
  const destination = node('div', { classes: 'device-destination' });
  destination.append(node('span', { text: 'OUTPUT', classes: 'device-card-subtitle' }),
    node('strong', { text: `${label(track.bus)} bus` }), node('span', { text: '→ Master' }));
  rack.append(destination);
}
