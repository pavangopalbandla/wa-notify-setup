#!/usr/bin/env python3
"""
WA State Parks Deluxe Cabin Notification Automation
Sets up email notifications for all weekends and long weekends
through September 2026 for deluxe cabins at 4 parks.

Usage: python wa_notify_setup.py
Requirements: pip install playwright && playwright install chromium
"""
import asyncio
from datetime import datetime, timedelta
from playwright.async_api import async_playwright

PARKS = {
    'Lincoln Rock': '-2147483554',
    'Rasar': '-2147483509',
    'Deception Pass': '-2147483270',
    'Pearrygin Lake': '-2147483524'
}
BASE_URL = 'https://washington.goingtocamp.com'
RESULTS_URL = f'{BASE_URL}/create-booking/results'


def generate_weekends():
    weekends = []
    start = datetime(2026, 3, 27)
    end = datetime(2026, 9, 30)
    cur = start
    while cur.weekday() != 4:
        cur += timedelta(days=1)
    while cur <= end:
        sun = cur + timedelta(days=2)
        if sun <= end:
            weekends.append({
                'arrival': cur.strftime('%Y-%m-%d'),
                'departure': sun.strftime('%Y-%m-%d'),
                'nights': '2',
                'display': f"{cur.strftime('%b %d')} - {sun.strftime('%b %d')}"
            })
        cur += timedelta(days=7)
    for a, d, label in [
        ('2026-05-22', '2026-05-25', 'Memorial Day'),
        ('2026-07-03', '2026-07-06', 'July 4th'),
        ('2026-09-04', '2026-09-07', 'Labor Day'),
    ]:
        weekends.append({'arrival': a, 'departure': d, 'nights': '3', 'display': label})
    weekends.sort(key=lambda x: x['arrival'])
    return weekends


def build_url(park, w):
    mid = PARKS[park]
    qs = '&'.join(f'{k}={v}' for k, v in {
        'mapId': mid,
        'searchTabGroupId': '1',
        'bookingCategoryId': '1',
        'startDate': w['arrival'],
        'endDate': w['departure'],
        'nights': w['nights'],
        'isReserving': 'true',
        'peopleCapacityCategoryCounts': '[[-32767,null,1,null]]',
        'view': 'map',
    }.items())
    return f'{RESULTS_URL}?{qs}'


async def main():
    weekends = generate_weekends()
    total = len(weekends) * len(PARKS)
    print(f'Will create {total} notifications ({len(weekends)} weekends x {len(PARKS)} parks)\n')

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        ctx = await browser.new_context()
        page = await ctx.new_page()

        # Step 1: Navigate to site
        await page.goto(BASE_URL, timeout=60000)
        await page.wait_for_load_state('domcontentloaded')

        # Step 2: Check if logged in, if not wait for manual login
        logged_in = await page.query_selector('text=Sign out')
        if not logged_in:
            print('=' * 60)
            print('NOT LOGGED IN - Please log in manually in the browser.')
            print('Click "Sign In" on the site header, enter your')
            print('credentials, then come back here and press ENTER.')
            print('=' * 60)
            input('\nPress ENTER after you have logged in...')

            # Verify login succeeded
            await page.reload()
            await page.wait_for_load_state('domcontentloaded')
            logged_in = await page.query_selector('text=Sign out')
            if not logged_in:
                print('ERROR: Still not logged in. Exiting.')
                await browser.close()
                return

        print('Logged in! Starting notification setup...\n')

        ok = 0
        fail = 0
        for park in PARKS:
            print(f'{park}:')
            for w in weekends:
                url = build_url(park, w)
                try:
                    await page.goto(url, timeout=30000)
                    await page.wait_for_load_state('load', timeout=15000)
                    await asyncio.sleep(1)  # Extra wait for dynamic content

                    # Try multiple selectors for the notify button
                    btn = page.locator('button:has-text("Notify")')
                    if await btn.count() == 0:
                        # Try alternative selectors
                        btn = page.locator('button:has-text("notify")')
                    if await btn.count() == 0:
                        btn = page.locator('button[aria-label*="Notify"]')
                    if await btn.count() == 0:
                        btn = page.locator('button[aria-label*="notify"]')

                    if await btn.count() > 0:
                        await btn.first.click()
                        ok += 1
                        print(f'  + {w["display"]}')
                    else:
                        fail += 1
                        print(f'  x {w["display"]} (no button)')
                except Exception as e:
                    fail += 1
                    print(f'  x {w["display"]} ({e})')
                await asyncio.sleep(0.3)
            print()

        await browser.close()

    print(f'Done! {ok}/{total} notifications created, {fail} failed.')


if __name__ == '__main__':
    asyncio.run(main())