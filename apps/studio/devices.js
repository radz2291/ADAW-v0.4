// Device controls are views of service catalogs; only typed operations persist edits.
export function drawDevices({ target, ui, track, readOnly, node, button, label, stage }) {
  const paragraph = text => node('p', { text, classes: 'small' });
  if (!track) {
    target.append(paragraph('Select a track to see its instrument and effects.'));
    return;
  }
  const source = ui.view.source;
  const bus = source.buses.find(item => item.id === track.bus);
  const catalogs = ui.snapshot.plugins ?? [];
  const currentCatalog = predicate => readOnly ? null : catalogs.find(predicate);
  const finite = value => typeof value === 'number' && Number.isFinite(value);
  let controlIndex = 0;
  target.append(node('h3', { text: label(track.id), classes: 'entity-title' }),
    paragraph(`Instrument → track effects → ${label(track.bus)} → Master`));

  function device(title, catalog, operation, fallback) {
    const panel = node('details', { classes: 'control-block stack', attrs: { open: '' } });
    panel.append(node('summary', { text: title }));
    if (!catalog || catalog.error || !operation) {
      panel.append(paragraph(catalog?.error?.message ?? fallback));
      target.append(panel);
      return;
    }
    const parameters = catalog.parameters ?? [];
    if (!parameters.length) {
      panel.append(paragraph('This device has no exposed controls.'));
      target.append(panel);
      return;
    }
    const faust = catalog.kind === 'faust';
    const selectId = `device-parameter-${++controlIndex}`;
    const picker = node('select', { attrs: { id: selectId, 'aria-label': `${title} parameter` } });
    for (const [index, parameter] of parameters.entries()) {
      const name = faust ? (parameter.label || parameter.name.split('/').at(-1)) : parameter.name;
      picker.add(new Option(name, index));
    }
    const pickerLabel = node('label', { text: 'Parameter', classes: 'control-label', attrs: { for: selectId } });
    pickerLabel.append(picker);
    const controls = node('div', { classes: 'stack' });
    const renderParameter = () => {
      controls.replaceChildren();
      const parameter = parameters[Number(picker.value)];
      if (!parameter) return;
      const binding = faust ? parameter.binding : String(parameter.index);
      const name = faust ? (parameter.label || parameter.name.split('/').at(-1)) : parameter.name;
      const minimum = faust ? parameter.min : 0;
      const maximum = faust ? parameter.max : 1;
      const unavailable = readOnly || parameter.editable === false || !finite(minimum) || !finite(maximum);
      const inputId = `${selectId}-value`;
      const input = node('input', { attrs: { id: inputId, type: 'number', step: 'any', min: minimum,
        max: maximum, required: '', placeholder: 'Enter value', 'aria-label': `${title} ${name} value` } });
      if (finite(parameter.value)) input.value = parameter.value;
      input.disabled = unavailable;
      const slider = node('input', { attrs: { type: 'range', min: minimum, max: maximum,
        step: faust ? (parameter.step > 0 ? parameter.step : 'any')
          : parameter.isBoolean ? 1 : parameter.isDiscrete && parameter.numSteps > 1 ? 1 / (parameter.numSteps - 1) : 'any',
        'aria-label': `${title} ${name} slider` } });
      slider.style.width = '100%';
      slider.disabled = unavailable;
      slider.hidden = !finite(parameter.value);
      if (finite(parameter.value)) slider.value = parameter.value;
      slider.addEventListener('input', () => { input.value = slider.value; });
      input.addEventListener('input', () => {
        slider.hidden = !finite(input.valueAsNumber);
        if (!slider.hidden) slider.value = input.value;
      });
      const form = node('form', { classes: 'control-row' });
      const save = button('Save', () => {}, { disabled: unavailable || ui.busy,
        attrs: { 'data-project-action': '', 'data-unavailable': unavailable,
          'aria-label': `Save ${title} ${name}` } });
      save.type = 'submit';
      form.append(node('label', { text: name, attrs: { for: inputId } }), input, save);
      form.addEventListener('submit', event => {
        event.preventDefault();
        if (unavailable || ui.busy || !input.reportValidity()) return;
        const value = input.valueAsNumber;
        if (value === parameter.value) return;
        stage(operation(binding, value), `Set ${title} · ${name}`);
      });
      const range = faust ? `${minimum}–${maximum}` : '0–1 normalized';
      const status = parameter.value_source === 'opaque_state'
        ? 'Saved plugin state · enter a value to override.'
        : parameter.value_source === 'module_default' ? 'Device default' : 'Saved value';
      controls.append(paragraph(`${status} · ${range}`), slider, form);
      if (parameter.editable === false) controls.append(paragraph('This parameter is read-only.'));
    };
    picker.addEventListener('change', renderParameter);
    panel.append(pickerLabel, controls);
    renderParameter();
    target.append(panel);
  }

  const instrumentCatalog = currentCatalog(entry => entry.track_id === track.id && entry.insert_index === undefined);
  device(track.kind === 'samples' ? 'Sampler' : track.kind === 'vst' ? 'VST instrument' : 'Faust instrument',
    instrumentCatalog,
    track.kind === 'samples' ? null : (binding, value) => ({ kind: 'set_instrument_parameter', track_id: track.id, binding, value }),
    track.kind === 'samples' ? 'Sample playback · edit timing and velocity in Notes.'
      : readOnly ? 'Earlier version · controls are read-only.' : 'Control catalog unavailable.');

  target.append(node('h3', { text: 'Track effects', classes: 'control-block entity-title' }));
  if (!track.inserts.length) target.append(paragraph('No track effects.'));
  track.inserts.forEach((insert, index) => device(
    `${index + 1}. ${insert.registry_id ? 'VST effect' : 'Faust effect'}`, null, null,
    'Track effect parameters are view-only.'));
  target.append(node('h3', { text: `${label(track.bus)} bus`, classes: 'control-block entity-title' }));
  if (!bus?.inserts.length) target.append(paragraph('No bus effects.'));
  bus?.inserts.forEach((insert, index) => device(
    `${label(bus.id)} ${index + 1}. ${insert.registry_id ? 'VST effect' : 'Faust effect'}`,
    currentCatalog(entry => entry.bus_id === bus.id && entry.insert_index === index),
    (binding, value) => ({ kind: 'set_bus_insert_parameter', bus_id: bus.id, insert_index: index, binding, value }),
    readOnly ? 'Earlier version · controls are read-only.' : 'Control catalog unavailable.'));
  target.append(paragraph('Device order and bypass are view-only. Use the mixer for track, bus and master levels.'));
}
