import requests
import time

BASE = 'http://127.0.0.1:8001'
ALL_OPTS = {
    'page_info': True, 'headings': True, 'text': True,
    'links': True, 'images': True, 'tables': True, 'lists': True,
}

def scrape(url, render_js=False, opts=None):
    opts = opts or ALL_OPTS
    t0 = time.time()
    r = requests.post(
        BASE + '/api/scrape',
        json={'url': url, 'options': opts, 'render_js': render_js},
        timeout=90,
    )
    elapsed = round(time.time() - t0, 2)
    return r.status_code, r.json(), elapsed


def counts(data):
    pi = data.get('page_info') or {}
    return {
        'headings': pi.get('headings_count', 0),
        'text':     pi.get('text_blocks_count', 0),
        'links':    pi.get('links_count', 0),
        'images':   pi.get('images_count', 0),
        'tables':   pi.get('tables_count', 0),
        'lists':    pi.get('lists_count', 0),
    }


# ── TEST 1: Backend up ─────────────────────────────────────────────
print('=' * 60)
print('TEST 1: Backend health check')
r = requests.get(BASE + '/', timeout=5)
svc = r.json().get('service', '?')
print('  GET / -> status=%d  service=%s' % (r.status_code, svc))

# ── TEST 2: Fast path unchanged on static site ─────────────────────
print()
print('TEST 2: Fast path (render_js=false) on example.com')
code, data, t = scrape('https://example.com', render_js=False)
print('  HTTP %d in %ss  render_js_used=%s' % (code, t, data.get('render_js_used')))
print('  counts=%s' % counts(data))

# ── TEST 3 & 4: Before/after on JS-heavy site ─────────────────────
TARGET = 'https://books.toscrape.com'
print()
print('TEST 3: BEFORE — fast path on JS-heavy site (%s)' % TARGET)
code, data_fast, t_fast = scrape(TARGET, render_js=False)
fc = counts(data_fast)
print('  HTTP %d in %ss  render_js_used=%s' % (code, t_fast, data_fast.get('render_js_used')))
print('  counts=%s' % fc)

print()
print('TEST 4: AFTER — browser path (render_js=true) same site')
code, data_js, t_js = scrape(TARGET, render_js=True)
jc = counts(data_js)
print('  HTTP %d in %ss  render_js_used=%s' % (code, t_js, data_js.get('render_js_used')))
print('  counts=%s' % jc)

print()
print('BEFORE vs AFTER:')
print('  %-10s  %6s  %6s  %6s' % ('field', 'fast', 'js', 'diff'))
for k in fc:
    diff = jc[k] - fc[k]
    sign = '+' if diff >= 0 else ''
    print('  %-10s  %6d  %6d  %s%d' % (k, fc[k], jc[k], sign, diff))

# ── TEST 5: SSRF still blocked for render_js=true ─────────────────
print()
print('TEST 5: SSRF protection with render_js=true')
code5, data5, _ = scrape('http://127.0.0.1/', render_js=True)
print('  HTTP %d (expected 400)' % code5)
print('  detail=%s' % data5.get('detail', 'none')[:100])

# ── TEST 6: Timeout/error on bad URL ──────────────────────────────
print()
print('TEST 6: Friendly error on non-existent domain with render_js=true')
code6, data6, t6 = scrape('https://this-domain-does-not-exist-xyzabc.com', render_js=True)
print('  HTTP %d in %ss' % (code6, t6))
print('  detail=%s' % str(data6.get('detail', ''))[:120])

print()
print('ALL TESTS COMPLETE')
