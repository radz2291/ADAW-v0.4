// A replaceable playback aid. Native rendition stems are immutable; ProjectService
// remains the sole source authority. Never label this approximation as a master.
const dbGain = (db) => 10 ** (db / 20);
const db = (value) => value > 0 ? 20 * Math.log10(value) : -Infinity;
const stable = (value) => JSON.stringify(value, (_, v) => v && !Array.isArray(v) && typeof v === 'object'
  ? Object.fromEntries(Object.keys(v).sort().map(key => [key, v[key]])) : v);
function soundIdentity(source) {
  const copy = structuredClone(source);
  for (const track of copy.tracks) for (const key of ['gain_db', 'pan', 'mute', 'solo']) delete track[key];
  for (const bus of copy.buses) delete bus.gain_db;
  delete copy.master.gain_db;
  return stable(copy);
}

// Native graph sums every bus into master, including the recursively fed sends.
function busWeights(source) {
  const weights = new Map(source.buses.map(bus => [bus.id, dbGain(bus.gain_db)]));
  for (const bus of [...source.buses].reverse()) {
    for (const send of bus.send_from ?? []) {
      weights.set(send.bus, weights.get(send.bus) +
        dbGain(source.buses.find(candidate => candidate.id === send.bus).gain_db) *
        dbGain(send.gain_db) * weights.get(bus.id));
    }
  }
  return weights;
}

export function createMonitor({audio, onMeters = () => {}, onStatus = () => {}}) {
  let context, media, output, rendered, stemOutput, analysers, frame;
  let manifest = null, source = null, buffers = new Map(), voices = [], request = 0;
  let mode = 'render', ready = false, compatible = false, destroyed = false;
  let currentMeters = {left: -Infinity, right: -Infinity, leftPeak: 0, rightPeak: 0, clip: false, mode};
  const events = [];
  const state = (message) => onStatus({mode, ready, compatible, revision: manifest?.revision,
    renditionId: manifest?.rendition_id, message,
    limitations: manifest?.limitations ?? 'Audition once to prepare live monitoring.'});
  function ensureContext() {
    if (context) return;
    context = new AudioContext({latencyHint: 'interactive'});
    media = context.createMediaElementSource(audio);
    rendered = context.createGain(); stemOutput = context.createGain(); output = context.createGain();
    media.connect(rendered).connect(output); stemOutput.connect(output);
    output.channelCount = 2; output.channelCountMode = 'explicit'; output.connect(context.destination);
    const splitter = context.createChannelSplitter(2); output.connect(splitter);
    analysers = [0, 1].map(channel => {
      const analyser = context.createAnalyser(); analyser.fftSize = 2048;
      splitter.connect(analyser, channel); return analyser;
    });
    meters();
  }
  function meters() {
    if (destroyed) return;
    const peaks = [0, 0], rms = [0, 0];
    if (!audio.paused && !audio.ended && context.state === 'running') {
      analysers.forEach((analyser, channel) => {
        const samples = new Float32Array(analyser.fftSize);
        analyser.getFloatTimeDomainData(samples);
        let squares = 0;
        for (const sample of samples) { peaks[channel] = Math.max(peaks[channel], Math.abs(sample)); squares += sample * sample; }
        rms[channel] = Math.sqrt(squares / samples.length);
      });
    }
    currentMeters = {left: db(peaks[0]), right: db(peaks[1]), leftPeak: peaks[0], rightPeak: peaks[1],
      leftRms: rms[0], rightRms: rms[1], clip: peaks.some(peak => peak >= 1), mode, timestamp: performance.now()};
    onMeters(currentMeters);
    frame = requestAnimationFrame(meters);
  }
  function stopVoices() {
    for (const voice of voices) { try { voice.player.stop(); } catch {} voice.player.disconnect(); voice.splitter.disconnect(); voice.left.disconnect(); voice.right.disconnect(); voice.merger.disconnect(); }
    voices = [];
  }
  function applyLevels() {
    if (!context) return;
    const active = mode === 'monitor' && ready && compatible;
    const now = context.currentTime;
    rendered.gain.setTargetAtTime(active ? 0 : 1, now, .003);
    stemOutput.gain.setTargetAtTime(active ? audio.volume * (audio.muted ? 0 : 1) * dbGain(source.master.gain_db) : 0, now, .003);
    if (!source) return;
    const weights = busWeights(source), soloed = source.tracks.some(track => track.solo);
    for (const voice of voices) {
      const track = source.tracks.find(track => track.id === voice.id);
      const gain = track && !track.mute && (!soloed || track.solo) ? dbGain(track.gain_db) * weights.get(track.bus) : 0;
      voice.left.gain.setTargetAtTime(gain * Math.min(1, 1 - (track?.pan ?? 0)), now, .003);
      voice.right.gain.setTargetAtTime(gain * Math.min(1, 1 + (track?.pan ?? 0)), now, .003);
    }
  }
  function startVoices() {
    stopVoices();
    if (!context || audio.paused || mode !== 'monitor' || !ready || !compatible) return;
    const when = context.currentTime + .015;
    const offset = audio.currentTime + .015 * audio.playbackRate;
    for (const [id, buffer] of buffers) {
      if (offset >= buffer.duration) continue;
      const player = context.createBufferSource(); player.buffer = buffer; player.playbackRate.value = audio.playbackRate;
      const splitter = context.createChannelSplitter(2), merger = context.createChannelMerger(2);
      const left = context.createGain(), right = context.createGain();
      left.gain.value = 0; right.gain.value = 0;
      player.connect(splitter); splitter.connect(left, 0); splitter.connect(right, buffer.numberOfChannels > 1 ? 1 : 0);
      left.connect(merger, 0, 0); right.connect(merger, 0, 1); merger.connect(stemOutput);
      voices.push({id, player, splitter, merger, left, right}); player.start(when, offset);
    }
    applyLevels();
  }
  function listen(event, callback) { audio.addEventListener(event, callback); events.push([event, callback]); }
  listen('play', () => { ensureContext(); context.resume().catch(error => state(error.message)); });
  listen('playing', startVoices); listen('waiting', stopVoices);
  listen('pause', stopVoices); listen('ended', stopVoices); listen('seeking', stopVoices);
  listen('seeked', startVoices); listen('ratechange', startVoices); listen('volumechange', applyLevels);
  listen('emptied', () => {
    ++request; stopVoices(); buffers.clear(); manifest = null; ready = false; compatible = false;
    mode = 'render'; applyLevels(); state('Rendered master');
  });
  return {
    async resume() { ensureContext(); await context.resume(); },
    async prepare(next) {
      const ticket = ++request;
      if (!next.available) { state('Audition this revision once to prepare live monitoring.'); return false; }
      ensureContext();
      state('Preparing verified native track stems…');
      const decoded = new Map();
      try {
        // Sequential decoding limits peak temporary memory for full-length songs.
        for (const track of next.tracks) {
          const response = await fetch(track.url, {cache: 'no-store'});
          if (!response.ok) throw new Error(`Cannot load ${track.id} stem (${response.status}). Audition and retry.`);
          const bytes = await response.arrayBuffer();
          const hash = [...new Uint8Array(await crypto.subtle.digest('SHA-256', bytes))].map(v => v.toString(16).padStart(2, '0')).join('');
          if (hash !== track.sha256) throw new Error(`Verified stem hash mismatch: ${track.id}`);
          const buffer = await context.decodeAudioData(bytes);
          if (ticket !== request || destroyed) return false;
          if (buffer.numberOfChannels !== 2 || Math.abs(buffer.duration - next.frames / next.sample_rate) > Math.max(1 / next.sample_rate, 1 / context.sampleRate))
            throw new Error(`Invalid stem format or duration: ${track.id}`);
          decoded.set(track.id, buffer);
        }
        if (ticket !== request || destroyed) return false;
        stopVoices(); buffers = decoded; manifest = next; ready = true;
        source ??= next.source; compatible = soundIdentity(source) === soundIdentity(next.source);
        applyLevels(); startVoices(); state(compatible ? 'Live monitoring ready' : 'Notes or devices changed. Audition to update monitoring.');
        return true;
      } catch (error) { if (ticket === request) state(error.message); throw error; }
    },
    updateSource(next) {
      source = structuredClone(next);
      compatible = ready && soundIdentity(source) === soundIdentity(manifest.source);
      if (!compatible && mode === 'monitor') { mode = 'render'; stopVoices(); state('Notes or devices changed. Playing previous render; Audition to update.'); }
      applyLevels();
      state(compatible ? (mode === 'monitor' ? manifest.limitations : 'Canonical native rendered master') :
        'Audition to prepare current monitoring assets.');
      return compatible;
    },
    setMode(next) {
      if (!['render', 'monitor'].includes(next)) throw new Error('Unknown monitoring mode');
      if (next === 'monitor' && (!ready || !compatible)) { state('Audition to prepare current monitoring assets.'); return false; }
      ensureContext(); const changed = mode !== next; mode = next; applyLevels();
      if (changed) startVoices();
      state(mode === 'monitor' ? manifest.limitations : 'Canonical native rendered master'); return true;
    },
    get meters() { return currentMeters; },
    get status() { return {mode, ready, compatible, revision: manifest?.revision, renditionId: manifest?.rendition_id}; },
    destroy() { destroyed = true; request++; stopVoices(); cancelAnimationFrame(frame); for (const [name, fn] of events) audio.removeEventListener(name, fn); context?.close(); },
  };
}
