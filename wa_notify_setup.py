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
    'Deception Pass': '-2147483388'
}

BASE_URL = 'https://washington.goingtocamp.com'
RESULTS_URL = f'{BASE_URL}/create-booking/results'


def generate_weekends():
    weekends = []
    start = datetime(2026, 3, 27)
    end = datetime(2026, 4, 30)
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
                    await asyncio.sleep(2)  # Extra wait for dynamic content
                    
                    # Fallback: manually select park if URL routing fails to auto-populate the dropdown
                    try:
                        park_input = page.locator('input[aria-label*="Park" i], input[placeholder*="Park" i], input[placeholder*="Where" i]').first
                        if await park_input.is_visible(timeout=2000):
                            current_val = await park_input.input_value()
                            if park.lower() not in current_val.lower():
                                await park_input.fill("")
                                await asyncio.sleep(0.2)
                                await park_input.fill(park)
                                await asyncio.sleep(1)
                                
                                # Click the corresponding autocomplete option
                                option = page.locator(f'mat-option:has-text("{park}"), .mdc-list-item:has-text("{park}"), div[role="option"]:has-text("{park}")').first
                                if await option.is_visible(timeout=3000):
                                    await option.click()
                                    await asyncio.sleep(0.5)
                                    
                                    # Click the Search button to reload the page with the correct park
                                    search_btn = page.locator('button:has-text("Search"), button[aria-label="Search"]').first
                                    if await search_btn.is_visible(timeout=2000):
                                        await search_btn.click()
                                        await asyncio.sleep(2)
                    except Exception as e:
                        print(f"      [Diagnostic: Error in manual park selection: {e}]")

                    # Wait up to 10 seconds for the notify button to appear and click it
                    notify_btn = page.locator('button:has-text("Notify"), button:has-text("notify"), button[aria-label*="Notify"], button[aria-label*="notify"]')
                    try:
                        await notify_btn.first.click(timeout=10000)
                        
                        # Now wait for the modal and click "Save notification"
                        await asyncio.sleep(0.5) # small wait for modal animation
                        save_btn = page.locator('button:has-text("Save notification"), button:has-text("Save Notification"), button:has-text("save notification")')
                        await save_btn.first.click(timeout=5000)
                        
                        ok += 1
                        print(f'    + {w["display"]} (Saved!)')
                    except Exception:
                        fail += 1
                        print(f'    x {w["display"]} (no button or save failed)')
                except Exception as e:
                    fail += 1
                    print(f'    x {w["display"]} ({e})')
                await asyncio.sleep(0.3)
            print()

        await browser.close()

    print(f'Done! {ok}/{total} notifications created, {fail} failed.')


if __name__ == '__main__':
    asyncio.run(main())