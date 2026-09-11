/** Render actual font specimens. Install Playwright externally; see assets/specimens/README.md. */
const { chromium } = require('playwright');
const fs = require('node:fs');
const path = require('node:path');
const assert = require('node:assert/strict');
const root = path.resolve(__dirname, '..');
const baseline = process.argv[2];
if (!baseline) throw new Error('Pass the uniform-scale baseline Regular WOFF2 path.');
const data = file => fs.readFileSync(file).toString('base64');
(async () => {
  const browser = await chromium.launch({headless:true});
  try {
    const page = await browser.newPage({viewport:{width:1100,height:1600},deviceScaleFactor:2});
    await page.setContent(fs.readFileSync(path.join(root,'assets/specimens/specimens.html'),'utf8'));
    const faces = [['Regular',400,'normal'],['Bold',700,'normal'],['Italic',400,'italic']];
    await page.addStyleTag({content: faces.map(([style,weight,slant]) =>
      `@font-face{font-family:Covendard;src:url(data:font/woff2;base64,${data(path.join(root,`fonts/webfont/Covendard-${style}.woff2`))});font-weight:${weight};font-style:${slant}}`
    ).join('\n') + `@font-face{font-family:CoveBaseline;src:url(data:font/woff2;base64,${data(baseline)})}`});
    for (const font of ['400 30px Covendard','700 24px Covendard','italic 400 24px Covendard','400 30px CoveBaseline']) {
      assert.ok((await page.evaluate(font => document.fonts.load(font,'가A'),font)).length);
    }
    await page.evaluate(()=>document.fonts.ready);
    const widths = await page.evaluate(()=>{
      const ctx=document.createElement('canvas').getContext('2d');
      const text=document.querySelector('.old .samples').textContent.split('\n')[0];
      ctx.font='30px CoveBaseline';const old=ctx.measureText(text).width;
      ctx.font='30px Covendard';return [old,ctx.measureText(text).width];
    });
    assert.ok(Math.abs(widths[0]-widths[1])<0.01,'Comparison text advances must match');
    for (const id of ['code','spacing']) {
      const element=page.locator(`#${id}`);
      assert.ok(await element.evaluate(el=>el.scrollWidth===el.clientWidth),'Specimen must not overflow');
      await element.screenshot({path:path.join(root,`assets/specimens/${id}.png`)});
    }
    console.log('Two specimens rendered at 2x. Fonts loaded; comparison advances match:',widths);
  } finally { await browser.close(); }
})().catch(error=>{console.error(error);process.exitCode=1;});
