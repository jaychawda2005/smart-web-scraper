import requests
import time

BASE = 'http://127.0.0.1:8001'
ALL_OPTS = {
    'page_info': True, 'headings': True, 'text': True,
    'links': True, 'images': True, 'tables': True, 'lists': True,
}

def scrape(url, render_js=False):
    t0 = time.time()
    r = requests.post(
        BASE + '/api/scrape',
        json={'url': url, 'options': ALL_OPTS, 'render_js': render_js},
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


# Test multiple JS-heavy sites to find a clear difference
SITES = [
    'https://react.dev',
    'https://www.reddit.com',
    'https://vuejs.org',
]

for site in SITES:
    print('=' * 60)
    print('SITE: %s' % site)

    print('  FAST PATH (render_js=false):')
    code, data_fast, t_fast = scrape(site, render_js=False)
    fc = counts(data_fast)
    print('    HTTP %d in %ss | %s' % (code, t_fast, fc))

    print('  BROWSER PATH (render_js=true):')
    code, data_js, t_js = scrape(site, render_js=True)
    jc = counts(data_js)
    print('    HTTP %d in %ss | %s' % (code, t_js, jc))

    print('  DIFF:')
    any_diff = False
    for k in fc:
        diff = jc[k] - fc[k]
        if diff != 0:
            any_diff = True
            sign = '+' if diff >= 0 else ''
            print('    %s: %d -> %d  (%s%d)' % (k, fc[k], jc[k], sign, diff))
    if not any_diff:
        print('    (no difference - site uses server-side rendering)')
    print()

print('DONE')
