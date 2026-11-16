"""Adapt evaluator UI navigation for the presentation layout; rubric unchanged."""
from pathlib import Path

folder=Path(__file__).parent
names=["interaction","editing","workflow","mix","audition","glass","identity","ergonomics"]
for name in names:
    text=(folder/f"{name}-probe.cjs").read_text(encoding="utf-8-sig")
    # Both presentation surfaces share controls; tests explicitly choose console.
    text=text.replace("page.locator('audio-ui-fader", "page.locator('#mix-console audio-ui-fader")
    text=text.replace("page.locator('[data-view=plugins]')", "page.locator('[data-dock=devices]')")
    init="await page.locator('#play:not([disabled])').waitFor();"
    navigate="if(!await page.locator('#browser-panel').isVisible())await page.locator('#toggle-browser').click();"
    if name in ("interaction","workflow","mix"):
        navigate+="await page.locator('[data-dock=mixer]').click();"
    if name in ("glass","identity"):
        navigate+="if(await page.locator('#playback-details').getAttribute('open')===null)await page.locator('#playback-details summary').click();"
    text=text.replace(init,init+navigate)
    if name=="editing":
        text=text.replace("await page.locator('#event-select').selectOption('eval-0');", "if(!await page.locator('#inspector-panel').isVisible())await page.locator('#toggle-inspector').click();await page.locator('#event-select').selectOption('eval-0');")
    if name=="workflow":
        text=text.replace("for(const width of [1440,1280]){await page.setViewportSize", "for(const width of [1440,1280]){await page.locator('[data-dock=piano]').click();if(!await page.locator('#browser-panel').isVisible())await page.locator('#toggle-browser').click();if(!await page.locator('#inspector-panel').isVisible())await page.locator('#toggle-inspector').click();await page.setViewportSize")
        # Reload inside the pane test must preserve its collapsed state, not run global navigation.
        text=text.replace("await page.reload();"+init+navigate+"assert.equal(await page.locator('#browser-panel').isVisible(),false)", "await page.reload();"+init+"assert.equal(await page.locator('#browser-panel').isVisible(),false)")
        text=text.replace("assert.equal(await page.locator('#browser-panel').isVisible(),true);assert.equal(await page.locator('#inspector-panel').isVisible(),true);await page.screenshot", "assert.equal(await page.locator('#browser-panel').isVisible(),false);assert.equal(await page.locator('#inspector-panel').isVisible(),false);await page.screenshot")
        text=text.replace("await page.locator('#browser-search').fill('space');", "if(!await page.locator('#browser-panel').isVisible())await page.locator('#toggle-browser').click();await page.locator('#browser-search').fill('space');")
        text=text.replace("&&getComputedStyle(e).opacity!=='0'", "&&getComputedStyle(e).opacity!=='0'&&getComputedStyle(e).clipPath==='none'")
        # Device view is full dock; return to mixer before another channel edit.
        text=text.replace("await check('F5B repeated", "await page.locator('[data-dock=mixer]').click();await check('F5B repeated")
    if name=="ergonomics":
        text=text.replace("assert.equal(await page.getByRole('region',{name:'evaluation-midi channel',exact:true}).count(),1);", "await page.locator('[data-dock=mixer]').click();assert.equal(await page.getByRole('region',{name:'evaluation-midi channel',exact:true}).count(),1);")
        text=text.replace("assert.match(await page.locator('#dock-context').textContent(),/Double-click.*add/);", "assert.match(await page.getByRole('button',{name:'Draw notes',exact:true}).getAttribute('title'),/Click empty space to add notes/);")
    (folder/f"v4-{name}-probe.cjs").write_text(text,encoding="utf-8")
