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

CABINS = {
    'Lincoln Rock': [
        ('C5', '-2147479340'), ('C6', '-2147479342'), ('C7', '-2147479347'), ('C8', '-2147479345'),
        ('C9', '-2147479341'), ('C10', '-2147479344'), ('C11', '-2147479346'), ('C12', '-2147479343')
    ],
    'Rasar': [
        ('C1-Skagit', '-2147477909'), ('C2-Baker', '-2147477908'), ('C3-Sauk', '-2147477905'),
        ('C4-Coho', '-2147475880'), ('C5-Chinook', '-2147475879')
    ],
    'Deception Pass': [
        ('C7', '-2147475890'), ('C8', '-2147475889')
    ],
    'Pearrygin Lake': [
        ('C1', '-2147478462'), ('C2', '-2147478461')
    ]
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


def build_url(park, cabin_id, w):
    mid = PARKS[park]
    qs = '&'.join(f'{k}={v}' for k, v in {
        'mapId': mid,
        'searchTabGroupId': '1',
        'bookingCategoryId': '1',
        'startDate': w['arrival'],
        'endDate': w['departure'],
        'nights': w['nights'],
        'isReserving': 'true',
        'resourceLocationId': cabin_id,
        'peopleCapacityCategoryCounts': '[[-32767,null,1,null]]',
        'view': 'map',
    }.items())
    return f'{RESULTS_URL}?{qs}'


async def main():
    weekends = generate_weekends()
    total_cabins = sum(len(c) for c in CABINS.values())
    total = len(weekends) * total_cabins
    print(f'Will create {total} notifications ({len(weekends)} weekends x {total_cabins} cabins)\n')

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
            for cabin_name, cabin_id in CABINS[park]:
                print(f'  {cabin_name}:')
                for w in weekends:
                    url = build_url(park, cabin_id, w)
                    try:
                        await page.goto(url, timeout=30000)
                        await page.wait_for_load_state('load', timeout=15000)
                        await asyncio.sleep(1)  # Extra wait for dynamic content

                        # Wait up to 10 seconds for the notify button to appear and click it
                        btn = page.locator('button:has-text("Notify"), button:has-text("notify"), button[aria-label*="Notify"], button[aria-label*="notify"]')
                        try:
                            await btn.first.click(timeout=10000)
                            ok += 1
                            print(f'    + {w["display"]}')
                        except Exception:
                            fail += 1
                            print(f'    x {w["display"]} (no button)')
                    except Exception as e:
                        fail += 1
                        print(f'    x {w["display"]} ({e})')
                    await asyncio.sleep(0.3)
            print()

        await browser.close()

    print(f'Done! {ok}/{total} notifications created, {fail} failed.')


if __name__ == '__main__':
    asyncio.run(main())