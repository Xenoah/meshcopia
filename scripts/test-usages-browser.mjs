import assert from 'node:assert/strict';
import {expect} from '@playwright/test';
export async function testUsagesBrowser(page, home) {
 await page.goto(home+'assets/commons-bar-stool/');
 const section=page.locator('.asset-usages');
 assert.ok(await section.isVisible());
 assert.ok((await section.textContent()).includes('Commons cafe'));
 assert.ok((await section.textContent()).includes('FURN_Bar'));
 assert.equal(await section.locator('a').first().getAttribute('href'),'https://github.com/Xenoah/vrcworld_tech-tech-cafe/tree/784e040a866c0081d6641c03cbf7f23d48a59dc2');
 await section.locator('summary').click();
 assert.ok(await section.getByText('FURN_StoolSeat',{exact:true}).isVisible());
 await section.locator('a').last().click();
 await page.waitForURL(url=>url.searchParams.get('q')==='Commons cafe');
 await page.waitForSelector('[data-card]');
 // SSR cards can appear before the catalog module applies the URL query.
 await expect(page.locator('#asset-search')).toHaveValue('Commons cafe',{timeout:30000});
 assert.ok(await page.locator('[data-preview="commons-bar-stool"]').isVisible());
 assert.equal(await page.locator('[data-preview="studio-chair"]').isVisible(),false);
 await page.locator('#asset-search').fill('FURN_StoolSeat');
 assert.equal(await page.locator('[data-card]:visible').count(),1);
 const viewport=page.viewportSize();
 await page.setViewportSize({width:390,height:844});
 await page.goto(home+'assets/commons-bar-stool/');
 await page.locator('.asset-usages').scrollIntoViewIfNeeded();
 assert.ok(await page.locator('.asset-usages').isVisible());
 assert.ok(await page.evaluate(()=>document.documentElement.scrollWidth<=window.innerWidth+1));
 await page.screenshot({path:'test-results/mobile-origin-usage.png',fullPage:false});
 await page.setViewportSize(viewport);
}
