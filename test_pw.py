import asyncio
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        print('Navigating...')
        await page.goto('https://washington.goingtocamp.com/create-booking/results?searchTabGroupId=1&bookingCategoryId=1&startDate=2026-05-22&endDate=2026-05-24&nights=2&isReserving=true&peopleCapacityCategoryCounts=%5B%5B-32767%2Cnull%2C1%2Cnull%5D%5D&view=map')
        await page.wait_for_load_state('networkidle', timeout=15000)
        
        try:
             await page.wait_for_selector('input', timeout=10000)
        except Exception as e:
             print('Timeout waiting for input:', e)
        
        inputs = await page.locator('input').all()
        print(f'Inputs found: {len(inputs)}')
        for i in inputs:
            pid = await i.get_attribute('id')
            plabel = await i.get_attribute('aria-label')
            pplace = await i.get_attribute('placeholder')
            val = await i.input_value()
            if pid or plabel or pplace:
                print(f' - ID: {pid}, Label: {plabel}, Place: {pplace}, Val: {val}')
            
        await browser.close()
        
asyncio.run(main())
