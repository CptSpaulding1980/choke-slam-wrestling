#!/usr/bin/env python3
"""Real browser regression smoke. Requires Python playwright + Chromium.
Run after Sass and Eleventy: python3 scripts/smoke_design.py --output /absolute/report-dir
No manager, remote sync or production writes. Serves docs on a loopback-only random port.
"""
import argparse
import functools
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
import json
import re
from pathlib import Path
import threading
from urllib.parse import unquote
from playwright.sync_api import sync_playwright


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    docs = Path('docs').resolve()
    prefix = '/choke-slam-wrestling'

    class Handler(SimpleHTTPRequestHandler):
        def translate_path(self, path):
            path = unquote(path.split('?')[0])
            if path.startswith(prefix):
                path = path[len(prefix):]
            return super().translate_path(path)

        def log_message(self, format, *args):
            pass

    server = ThreadingHTTPServer(('127.0.0.1', 0), functools.partial(Handler, directory=str(docs)))
    threading.Thread(target=server.serve_forever, daemon=True).start()
    base = f'http://127.0.0.1:{server.server_port}{prefix}/'
    paths = ['', 'home/', 'events/', 'events/2026-09-14-s08e02-all-in/',
             'wrestler/', 'wrestler/kazuchika-okada/', 'championships/',
             'championships/choke-slam-world-championship/', 'teams/',
             'teams/militanter-mummenschanz/', 'teams/saint-rebel-radicalz/',
             'teams/sweet-n-sour-elite/', 'statistiken/',
             'statistiken/globale-statistiken/', 'highlights/', 's08/']
    results = []
    failures = []
    errors = []
    console_errors = []
    with sync_playwright() as p:
        browser = p.chromium.launch()
        context = browser.new_context(reduced_motion='reduce')
        page = context.new_page()
        page.on('pageerror', lambda error: errors.append(str(error)))
        page.on('console', lambda message: console_errors.append({'url': page.url, 'message': message.text, 'location': message.location}) if message.type == 'error' else None)
        # Avoid downloading whole VODs in a visual smoke; source URLs/order are checked below.
        page.route('**/*.mp4', lambda route: route.abort())
        home_html = None
        for width in (1440, 390, 768):
            page.set_viewport_size({'width': width, 'height': 1000 if width == 1440 else 844})
            for path in paths:
                response = page.goto(base + path, wait_until='domcontentloaded')
                page.wait_for_selector('.csw-navigation.nav-enhanced')
                page.locator('.brand-logo').wait_for()
                page.wait_for_function('document.querySelector(".brand-logo").naturalWidth > 0')
                page.wait_for_function('document.querySelector("#csw-banner-img").naturalWidth > 0')
                data = page.evaluate('''() => ({
                    width: innerWidth, scrollWidth: document.documentElement.scrollWidth,
                    bannerHeight: document.querySelector('#csw-banner-img').getBoundingClientRect().height,
                    bannerSource: document.querySelector('#csw-banner-img').getAttribute('src'),
                    headings: [...document.querySelectorAll('main h1')].map(e => e.textContent.trim()),
                    current: [...document.querySelectorAll('.csw-menu [aria-current]')].map(e => e.textContent.trim()),
                    tables: document.querySelectorAll('main table').length,
                    wrappedTables: document.querySelectorAll('main .table-scroll > table').length,
                    bodyBackground: getComputedStyle(document.body).backgroundColor,
                    links: document.querySelectorAll('main a[href]').length,
                    logo: document.querySelector('.brand-logo').naturalWidth,
                    bannerLoaded: document.querySelector('#csw-banner-img').naturalWidth,
                    overflow: [...document.querySelectorAll('main *')].filter(e => e.getBoundingClientRect().right > innerWidth + 1 && !e.closest('.table-scroll')).map(e => e.tagName + '.' + e.className).slice(0, 12)
                })''')
                data.update(path=path, viewport=width, status=response.status)
                results.append(data)
                if response.status != 200 or data['scrollWidth'] > width + 1 or data['overflow']:
                    failures.append({'layout': data})
                if len(data['headings']) != 1 or len(data['current']) != 1:
                    failures.append({'headings/navigation': data})
                if data['bannerHeight'] != (220 if path == 'highlights/' else 200):
                    failures.append({'banner-height': data})
                if data['tables'] != data['wrappedTables']:
                    failures.append({'table-regions': data})
                if width <= 768:
                    toggle = page.locator('.menu-toggle')
                    assert toggle.is_visible()
                    toggle.focus()
                    page.keyboard.press('Enter')
                    assert toggle.get_attribute('aria-expanded') == 'true'
                    assert page.locator('#csw-menu a').first.is_visible()
                    page.keyboard.press('Tab')
                    assert page.locator('#csw-menu a').first.evaluate('(e) => e === document.activeElement')
                    page.keyboard.press('Escape')
                    assert toggle.get_attribute('aria-expanded') == 'false'
                    assert toggle.evaluate('(e) => e === document.activeElement')
                    assert not page.locator('#csw-menu').is_visible()
                if not path:
                    content = page.locator('main').inner_html()
                    home_html = re.sub(r'>\s+<', '><', content.strip())
                    assert 'Digital Garden' not in content
                    assert page.locator('.league-team img').count() == 3
                    assert page.locator('.hub-card').count() == 7
                    assert page.locator('.league-team').nth(1).inner_text().find('Special Response Rangers') >= 0
                    page.locator('.league-team-grid').scroll_into_view_if_needed()
                    page.wait_for_function('[...document.querySelectorAll(".league-team img")].every(e => e.naturalWidth > 0)')
                if path == 'home/':
                    assert re.sub(r'>\s+<', '><', page.locator('main').inner_html().strip()) == home_html
                if path == 'events/2026-09-14-s08e02-all-in/':
                    article = page.locator('article').inner_html()
                    assert article.index('Date:') < article.index('Venue:') < article.index('S08E02_All_In_poster_v2.png') < article.index('<video') < article.index('>Matches<')
                    assert page.locator('article video source').count() == 2
                    assert page.locator('.event-poster').count() == 1
                    assert page.locator('.table-scroll table tbody tr').count() == 15
                if path == 'teams/saint-rebel-radicalz/':
                    assert data['headings'] == ['Special Response Rangers']
                    assert page.locator('.team-member-card').count() == 5
                if path == 'highlights/':
                    season_filter = page.locator('.hl-filter [data-filter="s08"]')
                    season_filter.click()
                    assert season_filter.get_attribute('aria-pressed') == 'true'
                    assert page.locator('.hl-card:visible').count() == 4
                    page.locator('.hl-filter [data-filter="all"]').click()
                    assert page.locator('.hl-card:visible').count() == page.locator('.hl-card').count()
                if width in (1440, 390) and path in ('', 'teams/saint-rebel-radicalz/', 'events/2026-09-14-s08e02-all-in/'):
                    page.locator('main').evaluate('(e) => e.scrollIntoView()')
                    page.evaluate('window.scrollTo(0,0)')
                    # Capture real images after load, without fabricated placeholders.
                    page.wait_for_function('document.querySelector("#csw-banner-img").complete', timeout=30000)
                    name = 'landing' if not path else 'team' if path.startswith('teams') else 'event'
                    page.screenshot(path=str(output / f'{name}-{width}.png'), full_page=True)
        # Navigation remains usable when scripting is disabled.
        nojs = browser.new_context(java_script_enabled=False, viewport={'width': 390, 'height': 844})
        fallback = nojs.new_page()
        fallback.goto(base, wait_until='domcontentloaded')
        assert fallback.locator('#csw-menu a').count() == 8
        assert fallback.locator('#csw-menu a').last.is_visible()
        nojs.close()
        # Skiplink really moves keyboard focus to the main landmark.
        page.goto(base, wait_until='domcontentloaded')
        page.keyboard.press('Tab')
        assert page.locator('.skip-link').evaluate('(e) => e === document.activeElement')
        page.keyboard.press('Enter')
        assert page.locator('main').evaluate('(e) => e === document.activeElement')
        browser.close()
    server.shutdown()
    report = {'pages': results, 'failures': failures, 'jsErrors': errors, 'consoleErrors': console_errors,
              'videoPolicy': 'MP4 requests aborted intentionally, source/order checked; no playback claim',
              'checks': ['keyboard Enter/Tab/Escape', 'no-JS navigation', 'skiplink focus', 'root/home parity', 'poster/two VODs/matches order', '3 current logos/7 hub links', 'table-only overflow']}
    (output / 'browser-report.json').write_text(json.dumps(report, indent=2))
    print(json.dumps({'viewports': [1440, 390, 768], 'pageChecks': len(results), 'failures': failures,
                      'jsErrors': errors, 'consoleErrors': len(console_errors), 'report': str(output/'browser-report.json')}, indent=2))
    assert not failures and not errors and not console_errors


if __name__ == '__main__':
    main()
