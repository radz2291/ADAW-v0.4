/* Opt-in browser verification. Requires Playwright supplied by the test environment. */
const assert = require("node:assert/strict");
const { execFileSync } = require("node:child_process");
const { createHash } = require("node:crypto");
const { readFileSync } = require("node:fs");
const { chromium } = require("playwright");

async function checkCatalog(page, origin) {
  await page.goto(origin);
  await page.getByRole("heading", { name: "Night Circuit", exact: true }).waitFor();
  assert.equal(await page.locator(".timeline-row").count(), 12);
  await page.getByRole("button", { name: "kick", exact: true }).click();
  await page.locator("#event-select").selectOption({ index: 1 });
  assert.equal(await page.locator("#edit-start_tick").inputValue(), "15360");
  await page.getByRole("button", { name: "Plugins", exact: true }).click();
  assert.equal(await page.locator("#binding-prism-instrument").inputValue(), "0.4");
  const first = await page.locator("#audio").getAttribute("src");
  await page.getByRole("button", { name: "B", exact: true }).click();
  await page.waitForFunction((src) => document.getElementById("audio").getAttribute("src") !== src, first);
  await page.waitForFunction(() => Math.round(document.getElementById("audio").duration) === 75);
  await play(page);
  await page.getByRole("button", { name: "Pause", exact: true }).click();
  return { timelineRows: 12, firstKickTick: 15360, pluginOutput: .4, comparisonPlayback: true };
}

async function checkTimeMap(page, origin) {
  await page.goto(origin);
  await page.getByRole("heading", { name: "Glass Current", exact: true }).waitFor();
  const changes = await page.locator(".time-marker").allTextContents();
  assert.deepEqual(changes, ["120 BPM · 4/4", "104 BPM · 4/4", "104 BPM · 3/4"]);
  return { timeMap: changes };
}

async function play(page) {
  await page.getByRole("button", { name: "Play", exact: true }).click();
  await page.waitForFunction(() => document.getElementById("audio").currentTime > .1);
}

async function checkExport(page, origin, reportPath) {
  const { export: expected } = JSON.parse(readFileSync(reportPath, "utf8"));
  await page.setViewportSize({ width: 390, height: 844 });
  await page.goto(origin);
  await page.locator("#rendition-a").selectOption(expected.rendition);
  await page.getByText("Record listening decision", { exact: true }).click();
  const player = page.locator('audio[aria-label="Exact verified export playback"]');
  const src = await player.getAttribute("src");
  assert.equal(src, `/api/v1/exports/${expected.id}/audio`);
  const response = await fetch(origin + src);
  assert.equal(response.status, 200);
  const sha256 = createHash("sha256").update(Buffer.from(await response.arrayBuffer())).digest("hex");
  assert.equal(sha256, expected.audio_sha256);
  await player.evaluate((audio) => audio.play());
  await page.waitForFunction(() => document.querySelector('audio[aria-label="Exact verified export playback"]').currentTime > .1);
  const viewport = await page.evaluate(() => [document.documentElement.clientWidth, document.documentElement.scrollWidth]);
  assert.deepEqual(viewport, [390, 390]);
  return { exactExportSha256: sha256, exactExportPlayback: true, viewportWidth: 390 };
}

async function changeVst(page, origin, root, python) {
  const inspect = () => JSON.parse(execFileSync(python, [
    "-m", "app", "--root", root, "--timeout", "30", "project-inspect",
  ], { encoding: "utf8", timeout: 45000 })).data;
  const rendition = async (id) => {
    const response = await fetch(`${origin}/api/v1/renditions/${id}`);
    assert.equal(response.status, 200);
    return (await response.json()).data;
  };
  const before = inspect();
  assert.equal(before.source.brief, "Two-second test tone for HTTP and CLI parity");
  const firstTrack = before.source.tracks[0];
  assert.equal(firstTrack.id, "tone");
  assert.equal(firstTrack.kind, "vst");
  assert.equal(firstTrack.instrument.parameters["0"], .8);
  const baseline = await rendition(before.last_playable_rendition);

  await page.goto(origin);
  await page.getByRole("heading", { name: "Independent client fixture", exact: true }).waitFor();
  await page.getByRole("button", { name: "Plugins", exact: true }).click();
  const binding = page.locator("#binding-tone-instrument");
  assert.equal(await binding.inputValue(), "0.8");
  await binding.fill("0.4");
  await page.getByRole("button", { name: "Stage", exact: true }).click();
  await page.getByRole("button", { name: "Apply", exact: true }).waitFor();
  assert.equal(inspect().revision, before.revision);
  await page.getByRole("button", { name: "Apply", exact: true }).click();
  await page.getByText(/Project head is now/).waitFor();
  const after = inspect();
  assert.notEqual(after.revision, before.revision);
  assert.equal(after.source.tracks[0].instrument.parameters["0"], .4);
  assert.equal(await binding.inputValue(), "0.4");

  await page.getByRole("button", { name: "Render head", exact: true }).click();
  await page.getByText(/is ready in comparison slot B/).waitFor({ timeout: 45000 });
  const result = await rendition(await page.locator("#rendition-b").inputValue());
  assert.equal(result.revision, after.revision);
  const ratio = result.quality.rms / baseline.quality.rms;
  assert.ok(Math.abs(ratio - .5) < .04, ratio);
  await play(page);
  return {
    initialValue: .8, finalValue: .4, stagedHeadIntact: true, cliReadback: true,
    baselineRms: baseline.quality.rms, renderedRms: result.quality.rms, rmsRatio: ratio,
    revision: result.revision, rendition: result.id, playback: true,
  };
}

async function main() {
  const [mode, origin, root, python = ".venv/Scripts/python.exe"] = process.argv.slice(2);
  if (!origin || !["night", "time-map", "vst", "export"].includes(mode) || (["vst", "export"].includes(mode) && !root)) {
    throw new Error("Usage: node verify-browser.cjs <night|time-map|vst|export> <local-origin> [disposable-vst-root|export-report.json] [python]");
  }
  const address = new URL(origin);
  assert.equal(address.protocol, "http:");
  assert.equal(address.hostname, "127.0.0.1");
  const browser = await chromium.launch({ channel: "msedge", headless: true });
  try {
    const page = await browser.newPage({ viewport: { width: 1440, height: 1000 } });
    const errors = [];
    page.on("pageerror", (error) => errors.push(error.message));
    let result;
    if (mode === "night") result = await checkCatalog(page, origin);
    if (mode === "time-map") result = await checkTimeMap(page, origin);
    if (mode === "vst") result = await changeVst(page, origin, root, python);
    if (mode === "export") result = await checkExport(page, origin, root);
    assert.deepEqual(errors, []);
    console.log(JSON.stringify({ browser: "Edge headless", mode, ...result, pageErrors: errors }));
  } finally {
    await browser.close();
  }
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
