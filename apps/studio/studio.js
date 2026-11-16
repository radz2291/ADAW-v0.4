import '@audio-ui/elements/timeline';
import '@audio-ui/elements/piano-roll';
import '@audio-ui/elements/fader';
import { createDesktop } from './desktop.js';
const byId = (id) => document.getElementById(id);
const audio = byId("audio");
const ui = {
  snapshot: null,
  view: null,
  trackId: null,
  eventId: null,
  inspector: "edit",
  proposal: null,
  busy: false,
  slot: "a",
  rendition: null,
  loadedAudio: null,
  audioRequest: 0,
  waveRequest: null,
  measurements: new Map(),
};
let sessionToken;

async function api(path, body) {
  const options = { cache: "no-store" };
  if (body !== undefined) {
    if (!sessionToken) sessionToken = (await api("/session")).token;
    options.method = "POST";
    options.headers = {
      "Content-Type": "application/json",
      "X-ADAW-Client": "studio",
      "X-ADAW-Token": sessionToken,
    };
    options.body = JSON.stringify(body);
  }
  const response = await fetch(`/api/v1${path}`, options);
  const result = await response.json();
  if (!response.ok || !result.ok) {
    if (response.status === 403) sessionToken = undefined;
    const error = new Error(result.error?.message ?? "Project service request failed.");
    error.code = result.error?.code;
    error.details = result.error?.details;
    throw error;
  }
  return result.data;
}

const idPath = (id) => encodeURIComponent(id);
const short = (id) => String(id ?? "").replace(/^(rev|rendition)-/, "").slice(0, 9);
const label = (text) => String(text ?? "").replaceAll("_", " ");
const playSource = (id) => `/api/v1/renditions/${idPath(id)}/audio`;
const finite = (value) => typeof value === "number" && Number.isFinite(value);

function node(tag, { text, classes, attrs } = {}) {
  const element = document.createElement(tag);
  if (text !== undefined) element.textContent = text;
  if (classes) element.className = classes;
  for (const [name, value] of Object.entries(attrs ?? {})) element.setAttribute(name, value);
  return element;
}

function button(text, onClick, options = {}) {
  const element = node("button", { text, classes: options.classes, attrs: { type: "button", ...options.attrs } });
  element.disabled = Boolean(options.disabled);
  element.addEventListener("click", onClick);
  return element;
}

const paragraph = (text, classes = "small") => node("p", { text, classes });
const detail = (title, value) => {
  const result = node("details", { classes: "detail" });
  result.append(node("summary", { text: title }), node("pre", { text: JSON.stringify(value, null, 2) }));
  return result;
};

function notice(message, isError = false, diagnostics) {
  const region = byId("notice");
  region.replaceChildren(paragraph(message, ""));
  if (diagnostics && Object.keys(diagnostics).length) region.append(detail("Service details", diagnostics));
  region.classList.toggle("error", isError);
  region.hidden = !message;
}

async function action(work, pending = "") {
  if (ui.busy) return;
  ui.busy = true;
  if (pending) notice(pending);
  updateBusy();
  try {
    await work();
  } catch (error) {
    notice(error.code ? `${error.code} · ${error.message}` : error.message, true, error.details);
  } finally {
    ui.busy = false;
    updateBusy();
  }
}

function updateBusy() {
  byId("render-head").disabled = !ui.snapshot || ui.busy;
  byId("refresh").disabled = ui.busy;
  byId("measure").disabled = !ui.rendition || ui.busy;
  for (const item of document.querySelectorAll("[data-project-action]")) {
    item.disabled = ui.busy || item.dataset.unavailable === "true";
  }
  desktop.setBusy();
}

function projectAction(text, callback, unavailable = false, classes = "") {
  return button(text, callback, {
    classes,
    disabled: ui.busy || unavailable,
    attrs: { "data-project-action": "", "data-unavailable": unavailable },
  });
}

const trackColors = {
  percussion: "#86bbf3",
  transition: "#b2adfa",
  bass: "#f4b783",
  harmony_texture: "#7fcbb1",
  lead: "#d3e58a",
};

function currentTrack() {
  return ui.view?.source.tracks.find((track) => track.id === ui.trackId);
}

function selectedEvent() {
  return currentTrack()?.events.find((event) => event.id === ui.eventId);
}

function selectTrack(track, eventId = null, focusId = null) {
  ui.trackId = track.id;
  ui.eventId = eventId;
  if (eventId) ui.inspector = "edit";
  drawTimeline();
  drawInspector();
  desktop.draw();
  if (focusId) document.getElementById(focusId)?.focus({ preventScroll: true });
}

function markTime(element, start, duration, length) {
  element.style.left = `${100 * start / length}%`;
  if (duration !== undefined) element.style.width = `${100 * duration / length}%`;
}

function timeChanges(source) {
  return source.time_map ?? [{ tick: 0, bpm: source.tempo, numerator: 4, denominator: 4 }];
}

function barPositions(source) {
  const meters = timeChanges(source).filter((item, index, items) => {
    const previous = items[index - 1];
    return !previous || item.numerator !== previous.numerator || item.denominator !== previous.denominator;
  });
  return meters.map((meter, index) => {
    const end = meters[index + 1]?.tick ?? source.length_ticks;
    return { ...meter, end, barTicks: source.ppq * 4 * meter.numerator / meter.denominator };
  });
}

function tickAtTime(source, seconds) {
  const changes = timeChanges(source);
  for (let index = 0; index < changes.length; index++) {
    const change = changes[index];
    const end = changes[index + 1]?.tick ?? source.length_ticks;
    const ticksPerSecond = source.ppq * change.bpm / 60;
    const duration = (end - change.tick) / ticksPerSecond;
    // Browser media time is rounded; match the engine's nearest-sample boundaries.
    if (seconds < duration - .5 / source.sample_rate) return change.tick + Math.max(0, seconds) * ticksPerSecond;
    seconds -= duration;
  }
  return source.length_ticks;
}

function drawTimeline() {
  const timeline = byId("timeline");
  const source = ui.view?.source;
  if (!source) return;
  const length = source.length_ticks;
  const zoom = Number(byId("zoom").value);
  const root = byId('arrangement-timeline');
  root.setAttribute('duration', length);
  root.setAttribute('snap-step', source.ppq / 4);
  const headerWidth = parseFloat(getComputedStyle(document.documentElement).getPropertyValue('--track-width'));
  const available = Math.max(160, byId('timeline-viewport').clientWidth - headerWidth);
  root.zoom = zoom === 1 ? null : available * zoom / length;
  timeline.style.width = '100%';
  const meters = barPositions(source);
  const rows = [];
  const addRow = (name, classes = "") => {
    const row = node("audio-ui-timeline-track", { classes: `timeline-row ${classes}` });
    const caption = node("audio-ui-timeline-track-header", { classes: "track-label" });
    caption.append(name);
    const lane = node(classes === "ruler-row" ? "audio-ui-timeline-ruler" : "audio-ui-timeline-lane", { classes: "lane" });
    for (const meter of meters) {
      const grid = node("div", { classes: "bar-grid", attrs: { "aria-hidden": "true" } });
      markTime(grid, meter.tick, meter.end - meter.tick, length);
      grid.style.setProperty("--bar-width", `${100 * meter.barTicks / (meter.end - meter.tick)}%`);
      lane.append(grid);
    }
    row.append(caption, lane);
    rows.push(row);
    return lane;
  };
  const ruler = addRow("Bar", "ruler-row");
  const barCount = meters.reduce((total, meter) => total + Math.ceil((meter.end - meter.tick) / meter.barTicks), 0);
  const stride = Math.max(1, Math.ceil(barCount / (12 * zoom)));
  let barNumber = 1;
  let lastLabelTick = -Infinity;
  for (const meter of meters) {
    const count = Math.ceil((meter.end - meter.tick) / meter.barTicks);
    for (let index = 0; index < count; index += stride) {
      const tick = meter.tick + index * meter.barTicks;
      if ((tick - lastLabelTick) / length * available * zoom < 30) continue;
      lastLabelTick = tick;
      const number = node("audio-ui-timeline-mark", { text: barNumber + index, classes: "ruler", attrs: { value: meter.tick + index * meter.barTicks } });
      markTime(number, meter.tick + index * meter.barTicks, undefined, length);
      ruler.append(number);
    }
    barNumber += count;
  }
  if (source.time_map) {
    const timeLane = addRow("Tempo / meter", "section-row");
    const changes = timeChanges(source);
    changes.forEach((change, index) => {
      const text = `${change.bpm} BPM · ${change.numerator}/${change.denominator}`;
      const marker = node("span", { text, classes: "section-marker time-marker", attrs: { title: text } });
      const end = changes[index + 1]?.tick ?? length;
      markTime(marker, change.tick, end - change.tick, length);
      timeLane.append(marker);
    });
  }
  const sections = addRow("Sections", "section-row");
  for (const section of source.sections) {
    const sectionLabel = label(section.id);
    const marker = button(sectionLabel, () => desktop.selectSection(section.id), {
      classes: "section-marker",
      attrs: { title: `${sectionLabel} · ${section.mood} · Swing ${Math.round(section.swing * 100)}%` },
    });
    markTime(marker, section.start_tick, section.end_tick - section.start_tick, length);
    sections.append(marker);
  }
  for (const track of source.tracks) {
    const trackFocus = `track-${track.id}`;
    const trackButton = button(label(track.id), () => selectTrack(track, null, trackFocus), {
      attrs: { id: trackFocus, "aria-pressed": track.id === ui.trackId, title: `${label(track.role)} · ${label(track.bus)}` },
    });
    const lane = addRow(trackButton);
    lane.parentElement.dataset.trackId = track.id;
    lane.parentElement.classList.toggle('selected-track', track.id === ui.trackId);
    for (const section of source.sections) {
      const events = track.events.filter(e => e.start_tick >= section.start_tick && e.start_tick < section.end_tick);
      if (!events.length) continue;
      const clip = button(label(section.id), () => { selectTrack(track); desktop.selectSection(section.id); }, {classes: 'section-clip', attrs: {title: `${label(track.id)} · ${label(section.id)} · ${events.length} events`}});
      markTime(clip, section.start_tick, section.end_tick-section.start_tick, length);
      lane.append(clip);
    }
    lane.style.setProperty("--track-color", trackColors[track.role.toLowerCase()] ?? "#a0bcc3");
    for (const event of track.events) {
      const eventFocus = `event-${event.id}`;
      const eventLabel = `${label(track.id)} · tick ${event.start_tick}`;
      const marker = button("", () => selectTrack(track, event.id, eventFocus), {
        classes: "event-block",
        attrs: {
          id: eventFocus, "aria-label": eventLabel, title: eventLabel,
          tabindex: "-1", "aria-pressed": event.id === ui.eventId,
        },
      });
      markTime(marker, event.start_tick, event.duration_ticks, length);
      marker.style.top = track.kind === "samples" ? "24%" : `${19 + (11 - event.note % 12) * 4}%`;
      marker.style.height = track.kind === "samples" ? "52%" : "22%";
      lane.append(marker);
    }
  }
  timeline.replaceChildren(...rows, node("div", { classes: "playhead", attrs: { id: "playhead", hidden: "", "aria-hidden": "true" } }));
  updateTransport();
}

function numberInput(id, value, options) {
  const input = node("input", { attrs: { type: "number", id, required: "", ...options } });
  if (finite(value)) input.value = value;
  return input;
}

function controlLabel(text, control) {
  const wrapper = node("label", { classes: "control-label" });
  wrapper.append(text, control);
  return wrapper;
}

function controlForm(name, input, operation, reason, unavailable) {
  const form = node("form", { classes: "control-row" });
  form.append(node("label", { text: name, attrs: { for: input.id } }), input);
  input.disabled = unavailable;
  const submit = projectAction("Stage", () => {}, unavailable);
  submit.type = "submit";
  form.append(submit);
  form.addEventListener("submit", (event) => {
    event.preventDefault();
    if (!unavailable && input.reportValidity()) stage(operation(input.valueAsNumber), reason);
  });
  return form;
}

function editEvent(target, track, readOnly) {
  if (!track) {
    target.append(paragraph("Select a track to inspect its events."));
    return;
  }
  target.append(paragraph(`${label(track.id)} · ${track.events.length} events`));
  if (!track.events.length) return;
  const eventPicker = node("select", { attrs: { id: "event-select" } });
  eventPicker.add(new Option("Choose an event", ""));
  for (const event of track.events) eventPicker.add(new Option(`${event.start_tick} ticks · MIDI ${event.note} · ${event.id}`, event.id));
  eventPicker.value = ui.eventId ?? "";
  eventPicker.addEventListener("change", () => selectTrack(track, eventPicker.value || null, "event-select"));
  target.append(controlLabel("Event", eventPicker));
  const event = selectedEvent();
  if (!event) return;
  const unavailable = readOnly || track.protected;
  if (track.protected) target.append(paragraph("Protected track. Event editing is locked."));
  const form = node("form", { classes: "stack" });
  const fields = node("div", { classes: "fields" });
  const entries = [
    ["start_tick", "Start (ticks)", 0, ui.view.source.length_ticks - 1],
    ["duration_ticks", "Length (ticks)", 1, ui.view.source.length_ticks],
    ["note", "MIDI note", 0, 127],
    ["velocity", "Velocity", 1, 127],
  ];
  const inputs = new Map();
  for (const [key, fieldLabel, min, max] of entries) {
    if (key === "note" && track.kind === "samples") continue;
    const input = numberInput(`edit-${key}`, event[key], { min, max, step: 1 });
    input.disabled = unavailable;
    fields.append(controlLabel(fieldLabel, input));
    inputs.set(key, input);
  }
  const submit = projectAction("Stage event edit", () => {}, unavailable, "primary");
  submit.type = "submit";
  form.append(fields, submit);
  form.addEventListener("submit", (submission) => {
    submission.preventDefault();
    if (unavailable) return;
    const changes = {};
    for (const [key, input] of inputs) {
      if (input.valueAsNumber !== event[key]) changes[key] = input.valueAsNumber;
    }
    if (!Object.keys(changes).length) return notice("Change an event field before staging.");
    stage({ kind: "edit_event", track_id: track.id, event_id: event.id, changes }, `Edit ${event.id} on ${track.id}`);
  });
  target.append(form);
}

function mixer(target, source, readOnly) {
  const addGain = (title, id, gain, kind, key) => {
    const input = numberInput(`gain-${kind}-${id}`, gain, { step: "any", "aria-label": `${title} gain in dB` });
    const operation = (value) => key ? { kind, [key]: id, value } : { kind, value };
    target.append(controlForm(`${title} · dB`, input, operation, `Adjust ${title} gain`, readOnly));
  };
  target.append(node("h3", { text: "Tracks", classes: "entity-title" }));
  for (const track of source.tracks) addGain(label(track.id), track.id, track.gain_db, "set_track_gain", "track_id");
  const busHeading = node("h3", { text: "Buses and master", classes: "control-block entity-title" });
  target.append(busHeading);
  for (const bus of source.buses) addGain(label(bus.id), bus.id, bus.gain_db, "set_bus_gain", "bus_id");
  addGain("Master", "master", source.master.gain_db, "set_master_gain");
}

function plugins(target, readOnly) {
  const entries = ui.snapshot.plugins ?? [];
  if (!entries.length) return target.append(paragraph("This project has no cataloged plugin controls."));
  for (const entry of entries) {
    const group = node("section", { classes: "control-block stack" });
    const isInstrument = Boolean(entry.track_id);
    const title = isInstrument ? label(entry.track_id) : `${label(entry.bus_id)} · insert ${entry.insert_index + 1}`;
    group.append(node("h3", { text: title }));
    if (entry.error) {
      group.append(paragraph(entry.error.message ?? "Plugin catalog unavailable."));
      target.append(group);
      continue;
    }
    const selector = node("select");
    const controls = entry.parameters ?? [];
    for (const parameter of controls) {
      selector.add(new Option(`${parameter.name} · #${parameter.index}`, parameter.index));
    }
    const bindingForm = node("div", { classes: "stack" });
    const showParameter = () => {
      bindingForm.replaceChildren();
      const parameter = controls.find((item) => String(item.index) === selector.value);
      if (!parameter) return;
      const id = `binding-${entry.track_id ?? entry.bus_id}-${entry.insert_index ?? "instrument"}`;
      const input = numberInput(id, parameter.value, { min: 0, max: 1, step: "any", placeholder: "0–1" });
      const disabled = readOnly || parameter.editable === false;
      const operation = (value) => isInstrument
        ? { kind: "set_instrument_parameter", track_id: entry.track_id, binding: String(parameter.index), value }
        : { kind: "set_bus_insert_parameter", bus_id: entry.bus_id, insert_index: entry.insert_index, binding: String(parameter.index), value };
      bindingForm.append(
        paragraph(finite(parameter.value) ? "Stored normalized value" : "Value comes from the saved plugin state"),
        controlForm("Normalized", input, operation, `Set ${title} · ${parameter.name}`, disabled),
      );
    };
    group.append(controlLabel("Parameter", selector), bindingForm);
    selector.addEventListener("change", showParameter);
    showParameter();
    target.append(group);
  }
}

function drawInspector() {
  const target = byId("inspector-content");
  target.replaceChildren();
  if (!ui.view) return;
  const readOnly = ui.view.revision !== ui.snapshot.project.revision;
  byId("inspector-context").textContent = readOnly ? "Preview · read-only" : "Project head";
  for (const tab of document.querySelectorAll("[data-view]")) tab.setAttribute("aria-pressed", tab.dataset.view === ui.inspector);
  if (ui.inspector === "edit") editEvent(target, currentTrack(), readOnly);
  if (ui.inspector === "mix") mixer(target, ui.view.source, readOnly);
  if (ui.inspector === "plugins") {
    if (readOnly) target.append(paragraph("View the project head to inspect current plugin bindings."));
    else plugins(target, false);
  }
}

function drawProject() {
  const { project } = ui.snapshot;
  const source = ui.view.source;
  const headView = ui.view.revision === project.revision;
  byId("project-title").textContent = source.title;
  const tempo = source.time_map?.length > 1 ? "Tempo map" : `${source.tempo} BPM`;
  byId("project-context").textContent = `${tempo} · ${source.sample_rate / 1000} kHz · Head ${short(project.revision)}`;
  byId("timeline-context").textContent = headView
    ? `${source.sections.length} sections · ${source.tracks.length} tracks`
    : `Viewing ${ui.view.revision.startsWith("proposal:") ? ui.view.revision : short(ui.view.revision)}`;
  byId("back-head").hidden = headView;
  if (!currentTrack()) ui.trackId = source.tracks[0]?.id;
  if (!selectedEvent()) ui.eventId = null;
  drawTimeline();
  drawInspector();
  drawProposals();
  drawRevisions();
  drawRenditionSelectors();
  desktop.draw();
  updateBusy();
}

async function refresh({ viewHead = false } = {}) {
  const next = await api("/state");
  const wasHead = !ui.view || ui.view.revision === ui.snapshot?.project.revision;
  ui.snapshot = next;
  if (viewHead || wasHead) ui.view = next.project;
  drawProject();
  const chosen = byId(`rendition-${ui.slot}`).value;
  if (chosen !== ui.loadedAudio) await loadRendition();
}

function stage(operation, reason) {
  const baseRevision = ui.view.revision;
  return action(async () => {
    const command = {
      command_id: `studio-${crypto.randomUUID()}`,
      base_revision: baseRevision,
      reason,
      operations: Array.isArray(operation) ? operation : [operation],
    };
    await api("/proposals", command);
    await inspectProposal(command.command_id);
    await refresh();
    desktop.showReview();
    notice("Edit staged. Apply it below, then Render head to hear your change. The current audio remains playable.");
  }, "Staging project edit…");
}

async function inspectProposal(id, showSource = false) {
  const result = await api(`/proposals/${idPath(id)}`);
  ui.proposal = { id, ...result };
  if (showSource) {
    ui.view = { revision: `proposal:${id}`, source: result.source };
    drawProject();
  } else drawProposals();
}

function drawProposals() {
  const root = byId("proposals");
  const list = node("div", { classes: "record-list" });
  for (const item of [...(ui.snapshot.history.proposals ?? [])].reverse()) {
    const record = node("article", { classes: "record" });
    record.append(paragraph(item.id, ""));
    record.append(projectAction(item.applied_revision ? "Inspect applied proposal" : "Inspect proposal", () =>
      action(() => inspectProposal(item.id))));
    list.append(record);
  }
  root.replaceChildren(list);
  if (!list.childElementCount) root.append(paragraph("No proposals yet."));
  if (!ui.proposal) return;
  const { id, command, applied } = ui.proposal;
  const item = ui.snapshot.history.proposals.find((proposal) => proposal.id === id);
  const alreadyApplied = applied || item?.applied_revision;
  const body = node("div", { classes: "control-block stack" });
  body.append(
    node("h3", { text: command.reason }),
    paragraph(`Base ${short(command.base_revision)} · ${alreadyApplied ? "Applied" : "Pending"}`),
    detail("Source operations", command.operations),
  );
  const actions = node("div", { classes: "inline-actions" });
  actions.append(
    projectAction("View arrangement", () => action(() => inspectProposal(id, true))),
    projectAction("Render preview", () => render({ proposal_id: id })),
    projectAction("Apply", () => action(async () => {
      const result = await api("/apply", { proposal_id: id });
      await inspectProposal(id);
      await refresh({ viewHead: true });
      notice(result.rebased ? "Proposal applied on the current head." : `Project head is now ${short(result.revision)}.`);
    }, "Applying proposal…"), Boolean(alreadyApplied), "primary"),
  );
  body.append(actions);
  root.append(body);
}

function drawRevisions() {
  const root = byId("revisions");
  const list = node("div", { classes: "record-list" });
  for (const revision of [...(ui.snapshot.history.revisions ?? [])].reverse()) {
    const record = node("article", { classes: "record" });
    const isHead = revision.id === ui.snapshot.project.revision;
    record.append(paragraph(`${isHead ? "Head · " : ""}${short(revision.id)} · ${revision.reason ?? ""}`, ""));
    const buttons = node("div", { classes: "inline-actions" });
    buttons.append(
      projectAction("View source", () => action(async () => {
        ui.view = await api(`/revisions/${idPath(revision.id)}`);
        drawProject();
      })),
      projectAction("Render", () => render({ revision: revision.id })),
      projectAction("Undo edit", () => action(async () => {
        const result = await api("/undo", { revision: revision.id });
        await refresh({ viewHead: true });
        notice(`Undo recorded at ${short(result.revision)}.`);
      }, "Applying inverse edit…"), !revision.parent),
    );
    record.append(buttons);
    if (ui.view.revision === revision.id) record.append(detail("Source", ui.view.source));
    list.append(record);
  }
  root.replaceChildren(list);
}

function drawRenditionSelectors() {
  const { history, project } = ui.snapshot;
  const renditions = [...(history.renditions ?? [])].reverse();
  const addOptions = (id, fallback) => {
    const select = byId(id);
    const previous = select.value;
    select.replaceChildren(new Option("Choose a render", ""));
    for (const item of renditions) {
      const revision = item.revision.startsWith("proposal:") ? "Proposal" : `Rev ${short(item.revision)}`;
      select.add(new Option(`${revision} · ${short(item.id)}`, item.id));
    }
    select.value = renditions.some((item) => item.id === previous) ? previous : fallback ?? "";
  };
  addOptions("rendition-a", project.last_playable_rendition ?? renditions[0]?.id);
  addOptions("rendition-b", renditions.find((item) => item.id !== byId("rendition-a").value)?.id);
}

function render(body) {
  return action(async () => {
    const rendition = await api("/render", body);
    await refresh();
    byId("rendition-b").value = rendition.id;
    ui.slot = "b";
    await loadRendition();
    notice(`Rendition ${short(rendition.id)} is ready in comparison slot B.`);
  }, "Rendering audio in the worker…");
}

const timestamp = (seconds) => {
  const time = Math.max(0, Math.floor(seconds || 0));
  return `${Math.floor(time / 60)}:${String(time % 60).padStart(2, "0")}`;
};

function updateTransport() {
  const duration = finite(audio.duration) ? audio.duration : 0;
  const position = byId("position");
  position.max = duration;
  position.value = Math.min(audio.currentTime, duration);
  position.disabled = !duration;
  byId("play").disabled = !ui.loadedAudio;
  byId("play").textContent = audio.paused ? "Play" : "Pause";
  byId("time").textContent = `${timestamp(audio.currentTime)} / ${timestamp(duration)}`;
  desktop.sync();
  const playhead = byId("playhead");
  const lane = byId("timeline").querySelector(".lane");
  const renditionMatchesView = ui.rendition?.revision === ui.view?.revision;
  if (playhead && lane) {
    playhead.hidden = !duration || !renditionMatchesView;
    if (!playhead.hidden) {
      const source = ui.view.source;
      const progress = tickAtTime(source, audio.currentTime) / source.length_ticks;
      playhead.style.left = `${lane.offsetLeft + lane.clientWidth * progress}px`;
    }
  }
}

function drawWaveform(peaks) { desktop.waveform(peaks); }

async function loadWaveform(id, signal) {
  if (!window.AudioContext) return;
  const response = await fetch(playSource(id), { signal });
  if (!response.ok) return;
  const buffer = await response.arrayBuffer();
  if (signal.aborted) return;
  const decoder = new AudioContext();
  try {
    const sound = await decoder.decodeAudioData(buffer);
    if (signal.aborted) return;
    const peaks = new Float32Array(420);
    for (let channel = 0; channel < sound.numberOfChannels; channel++) {
      const samples = sound.getChannelData(channel);
      for (let index = 0; index < samples.length; index++) {
        const bin = Math.floor(index * peaks.length / samples.length);
        peaks[bin] = Math.max(peaks[bin], Math.abs(samples[index]));
      }
    }
    desktop.waveform(peaks, sound.duration);
  } finally {
    await decoder.close();
  }
}

async function loadRendition({ preserve = false } = {}) {
  const id = byId(`rendition-${ui.slot}`).value;
  for (const slot of ["a", "b"]) byId(`ab-${slot}`).setAttribute("aria-pressed", slot === ui.slot);
  const time = preserve ? audio.currentTime : 0;
  const resume = preserve && !audio.paused;
  const request = ++ui.audioRequest;
  ui.waveRequest?.abort();
  ui.rendition = null;
  ui.loadedAudio = id || null;
  drawWaveform();
  drawQuality();
  audio.pause();
  if (!id) {
    audio.removeAttribute("src");
    audio.load();
    byId("audio-context").textContent = "Choose a rendition to audition.";
    updateTransport();
    return;
  }
  byId("audio-context").textContent = `Loading ${short(id)}…`;
  audio.src = playSource(id);
  if (time) {
    audio.addEventListener("loadedmetadata", () => {
      if (request === ui.audioRequest) audio.currentTime = Math.min(time, audio.duration || time);
    }, { once: true });
  }
  if (resume) audio.play().catch(() => {});
  const rendition = await api(`/renditions/${idPath(id)}`);
  if (request !== ui.audioRequest) return;
  ui.rendition = rendition;
  byId("audio-context").textContent = `${rendition.revision.startsWith("proposal:") ? "Proposal preview" : `Revision ${short(rendition.revision)}`} · ${short(id)}`;
  drawQuality();
  updateTransport();
  if (Array.isArray(rendition.waveform)) drawWaveform(rendition.waveform);
  else {
    ui.waveRequest = new AbortController();
    loadWaveform(id, ui.waveRequest.signal).catch(() => {});
  }
}

function drawQuality() {
  const root = byId("quality");
  root.replaceChildren();
  updateBusy();
  if (!ui.rendition) {
    root.append(paragraph("Choose a rendition in the transport to inspect its evidence."));
    return;
  }
  const rendition = ui.rendition;
  const quality = ui.measurements.get(rendition.id) ?? rendition.quality;
  const readings = node("dl", { classes: "metrics" });
  const reviews = rendition.reviews ?? [];
  const format = (value, unit) => finite(value) ? `${value.toFixed(2)} ${unit}` : "—";
  const rows = [
    ["Profile result", quality?.status ?? "Analysis pending"],
    ["Integrated loudness", format(quality?.integrated_lufs, "LUFS")],
    ["Sample peak", format(quality?.sample_peak_dbfs, "dBFS")],
    ["Estimated true peak", format(quality?.true_peak?.dbfs, "dBFS")],
    ["Duration", format(quality?.duration_seconds, "s")],
    ["Listening", reviews.length ? "Review recorded on export" : label(rendition.listening ?? quality?.listening ?? "NOT_EVALUATED").toLowerCase()],
  ];
  for (const [name, reading] of rows) readings.append(node("dt", { text: name }), node("dd", { text: reading }));
  root.append(readings);
  if (quality) root.append(detail("Measurements and profile", quality));
  if (rendition.manifest) root.append(detail("Rendition manifest", rendition.manifest));
  if (reviews.length) root.append(detail("Owner listening records", reviews));
  const exports = (ui.snapshot.history.exports ?? []).filter((entry) => entry.rendition === rendition.id);
  if (exports.length) root.append(reviewForm(exports, rendition));
}

function reviewForm(exports, rendition) {
  const wrapper = node("details", { classes: "detail" });
  wrapper.append(node("summary", { text: "Record listening decision" }));
  const form = node("form", { classes: "stack control-block" });
  const owner = node("input", { attrs: { type: "text", required: "", autocomplete: "name" } });
  const decision = node("select");
  decision.add(new Option("Request changes", "CHANGES_REQUESTED"));
  decision.add(new Option("Approve", "APPROVED"));
  const notes = node("textarea", { attrs: { required: "", rows: 3 } });
  const exportPicker = node("select");
  for (const entry of exports) exportPicker.add(new Option(entry.id.slice(0, 20), entry.id));
  const exportPlayer = node("audio", { attrs: { controls: "", preload: "none", "aria-label": "Exact verified export playback" } });
  const updateExport = () => {
    exportPlayer.src = `/api/v1/exports/${idPath(exportPicker.value)}/audio`;
  };
  exportPicker.addEventListener("change", updateExport);
  updateExport();
  exportPlayer.addEventListener("play", () => audio.pause());
  const submit = projectAction("Record decision", () => {});
  submit.type = "submit";
  form.append(
    paragraph("Listen to the verified export before recording a decision."),
    controlLabel("Verified export", exportPicker),
    exportPlayer,
    controlLabel("Owner name", owner),
    controlLabel("Decision", decision),
    controlLabel("Listening notes", notes),
    submit,
  );
  form.addEventListener("submit", (event) => {
    event.preventDefault();
    action(async () => {
      await api("/reviews", {
        export_id: exportPicker.value, owner: owner.value, decision: decision.value, notes: notes.value,
      });
      const updated = await api(`/renditions/${idPath(rendition.id)}`);
      if (ui.rendition?.id === rendition.id) ui.rendition = updated;
      drawQuality();
      notice("Listening decision recorded against the verified export.");
    }, "Recording listening decision…");
  });
  wrapper.append(form);
  return wrapper;
}

async function selectSlot(slot) {
  if (slot === ui.slot) return;
  ui.slot = slot;
  try {
    await loadRendition({ preserve: true });
  } catch (error) {
    notice(error.message, true, error.details);
  }
}

for (const tab of document.querySelectorAll("[data-view]")) {
  tab.addEventListener("click", () => {
    ui.inspector = tab.dataset.view;
    drawInspector();
  });
}
byId("refresh").addEventListener("click", () => action(() => refresh({ viewHead: true }), "Refreshing project…"));
byId("render-head").addEventListener("click", () => render({ revision: ui.snapshot.project.revision }));
byId("back-head").addEventListener("click", () => {
  ui.view = ui.snapshot.project;
  drawProject();
});
byId("zoom").addEventListener("change", drawTimeline);
window.addEventListener("resize", updateTransport);
byId("play").addEventListener("click", () => {
  if (audio.paused) audio.play().catch((error) => notice(error.message, true));
  else audio.pause();
});
byId("position").addEventListener("input", (event) => { audio.currentTime = Number(event.target.value); });
audio.volume = Number(byId("volume").value);
byId("volume").addEventListener("input", (event) => { audio.volume = Number(event.target.value); });
for (const type of ["loadedmetadata", "durationchange", "play", "pause", "ended", "timeupdate"]) {
  audio.addEventListener(type, updateTransport);
}
audio.addEventListener("error", () => {
  if (ui.loadedAudio) notice("The selected rendition could not be played.", true);
});
for (const slot of ["a", "b"]) {
  byId(`ab-${slot}`).addEventListener("click", () => selectSlot(slot));
  byId(`rendition-${slot}`).addEventListener("change", async () => {
    if (ui.slot !== slot) return;
    try {
      await loadRendition({ preserve: true });
    } catch (error) {
      notice(error.message, true, error.details);
    }
  });
}
byId("measure").addEventListener("click", () => action(async () => {
  const renditionId = ui.rendition.id;
  ui.measurements.set(renditionId, await api("/analyze", { rendition_id: renditionId }));
  drawQuality();
  notice(`Measured rendition ${short(renditionId)}.`);
}, "Analyzing rendered audio…"));
const desktop = createDesktop({ ui, audio, byId, node, button, label, trackColors, stage, notice,
  selectTrack, currentTrack, drawInspector, tickAtTime, timeChanges });
action(async () => {
  await refresh({ viewHead: true });
  notice("");
}, "Opening project…");
