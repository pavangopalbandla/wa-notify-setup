#!/usr/bin/env python3
"""Debug script to see what buttons are on the notification page."""
import asyncio
from playwright.async_api import async_playwright

BASE_URL = 'https://washington.goingtocamp.com'
RESULTS_URL = f'{BASE_URL}/create-booking/results'

# Lincoln Rock park ID
PARK_ID = '-2147483554'
WEEKEND = {
    'arrival': '2026-03-27',
    'departure': '2026-03-29',
    'nights': '2'
}

qs = '&'.join(f'{k}={v}' for k, v in {
    'mapId': PARK_ID,
    'searchTabGroupId': '1',
    'bookingCategoryId': '1',
    'startDate': WEEKEND['arrival'],
    'endDate': WEEKEND['departure'],
    'nights': WEEKEND['nights'],
    'isReserving': 'true',
    'peopleCapacityCategoryCounts': '[[-32767,null,1,null]]',
    'view': 'map',
}.items())
url = f'{RESULTS_URL}?{qs}'

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        ctx = await browser.new_context()
        page = await ctx.new_page()

        print(f"Navigating to: {url}\n")
        await page.goto(url, timeout=30000)
        await page.wait_for_load_state('load', timeout=15000)
        await asyncio.sleep(2)

        # Get all buttons
        buttons = await page.locator('button').all()
        print(f"Found {len(buttons)} buttons:\n")

        for i, btn in enumerate(buttons):
            text = await btn.text_content()
            aria_label = await btn.get_attribute('aria-label')
            visible = await btn.is_visible()
            print(f"  Button {i}: text='{text}' aria-label='{aria_label}' visible={visible}")

        # Check for notify specifically
        notify_buttons = await page.locator('button:has-text("Notify")').all()
        print(f"\nButtons with 'Notify' text: {len(notify_buttons)}")

        await browser.close()

if __name__ == '__main__':
    asyncio.run(main())
