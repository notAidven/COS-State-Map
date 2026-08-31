# -*- coding: utf-8 -*-
"""Parse the state-profile tables out of `Report Draft.pdf` (via pdftotext -layout).

The tables are three columns (Category | Feature | Overview) whose character
offsets drift from page to page, and the last two rows (Active Cities /
References) are merged across columns 2-3, so the gutters are detected per page
rather than assumed.
"""
import re, json, unicodedata

RAW   = open('report.txt', encoding='utf-8').read()
PAGES = RAW.split('\f')

def clean_lines(pg):
    out = []
    for ln in pg.split('\n'):
        if not ln.strip():
            continue
        if re.fullmatch(r'\s*\d{1,3}\s*', ln):        # page number
            continue
        out.append(ln.rstrip('\n').rstrip())
    return out

def gutter_after(lines, start, ignore=()):
    """First column start to the right of `start`, from a >=3-char whitespace gutter."""
    lines = [l for l in lines if len(l) > start and l.strip() not in ignore]
    if not lines:
        return None
    w = max(len(l) for l in lines)
    x = start
    while x < w:
        if all(x >= len(l) or l[x] == ' ' for l in lines):
            j = x
            while j < w and all(j >= len(l) or l[j] == ' ' for l in lines):
                j += 1
            if j - x >= 3 and j < w and x > start:
                return j
            x = j
        else:
            x += 1
    return None

# Rows appear in a fixed order on every state page; matching is sequential so a
# label word cannot re-trigger an earlier row.
ROWS = ['landscape', 'vnm', 'cs', 'other', 'size', 'eligibility', 'benefitDist',
        'activeCities', 'references']

def starts_row(row, c0, c1):
    if row == 'landscape':   return c1.startswith('Community-') or c1.startswith('Community‑')
    if row == 'vnm':         return c1.startswith('Virtual')
    if row == 'cs':          return c1 == 'Community' or c1.startswith('Community Solar')
    if row == 'other':       return c1.startswith('Other State')
    if row == 'size':        return c1.startswith('Size')
    if row == 'eligibility': return c1.startswith('Eligibility')
    if row == 'benefitDist': return c1.startswith('Benefit')
    if row == 'activeCities':return c0.startswith('Active Cities')
    if row == 'references':  return c0.startswith('References')
    return False

SKIP_C1 = ('Feature',)
# Feature-column labels; when a page break splits one, the orphan can land in
# the Overview column's character range on the continuation page.
LABEL_FRAGMENTS = {
    'Community-', 'Owned Solar', 'Landscape', 'Virtual or', 'Remote Net',
    'Metering', 'Community', 'Solar', 'Other State', 'Support for',
    'Community-ow', 'ned Solar', 'Size', 'Eligibility', 'Benefit', 'Distribution',
}
SKIP_C0 = ('Category', 'State Profiles', 'Appendix')

def parse_page(pg, acc, state_names):
    """Append this page's cell fragments into `acc` (dict row -> list of str)."""
    lines = clean_lines(pg)
    if not lines:
        return
    c1 = gutter_after(lines, 0, ignore=state_names)
    if c1 is None:
        return
    # The merged Active Cities / References rows destroy the col2|col3 gutter,
    # so measure it only on the rows above them.
    body = []
    for l in lines:
        head = l[:c1].strip()
        if head.startswith('Active Cities') or head.startswith('References'):
            break
        body.append(l)
    c2 = gutter_after(body, c1, ignore=state_names)

    merged = False
    for l in lines:
        col0 = l[:c1].strip()
        rest = l[c1:]
        if col0.startswith('Active Cities') or col0.startswith('References'):
            merged = True
        if merged or c2 is None:
            cola, colb = '', rest.strip()
        else:
            cola, colb = rest[:c2 - c1].strip(), rest[c2 - c1:].strip()

        if col0 in SKIP_C0 or cola.startswith(SKIP_C1):
            continue
        if not merged and not cola and colb in LABEL_FRAGMENTS:
            continue
        if col0 in state_names and not cola and not colb:
            continue                                   # the state heading itself

        i = ROWS.index(acc['_row']) + 1 if acc['_row'] else 0
        for row in ROWS[i:]:
            if starts_row(row, col0, cola):
                acc['_row'] = row
                break
        if acc['_row'] and colb:
            acc[acc['_row']].append(colb)

# ── Split the document into states ────────────────────────────────────────────
STATE_HEADINGS = [
    'Alabama','American Samoa','Alaska','Arizona','Arkansas','California','Colorado',
    'Connecticut','Delaware','Florida','Georgia','Guam','Hawaii','Idaho','Illinois',
    'Indiana','Iowa','Kansas','Kentucky','Louisiana','Maine','Maryland','Massachusetts',
    'Michigan','Minnesota','Mississippi','Missouri','Montana','Nebraska','Nevada',
    'New Hampshire','New Jersey','New Mexico','New York','North Carolina','North Dakota',
    'Northern Mariana Islands','Ohio','Oklahoma','Oregon','Pennsylvania','Puerto Rico',
    'Rhode Island','South Carolina','South Dakota','Tennessee','Texas','US Virgin Islands',
    'Utah','Vermont','Virginia','Washington','Washington, DC','West Virginia','Wisconsin',
    'Wyoming']
HEADSET = set(STATE_HEADINGS)

def page_state(pg):
    """The state a page opens, if any (heading sits alone at the top-left)."""
    for ln in clean_lines(pg):
        s = ln.strip()
        if s in ('State Profiles',):
            continue
        return s if s in HEADSET else None
    return None

def parse():
    out, order, cur = {}, [], None
    for pg in PAGES:
        s = page_state(pg)
        if s and s not in out:
            cur = s
            out[s] = {r: [] for r in ROWS}
            out[s]['_row'] = None
            order.append(s)
        if cur is None:
            continue
        if 'Key Findings' in pg and cur is None:
            continue
        parse_page(pg, out[cur], HEADSET)
    for s in out:
        out[s].pop('_row', None)
    return out, order

if __name__ == '__main__':
    data, order = parse()
    print(len(order), 'states parsed')
    missing = HEADSET - set(order)
    if missing: print('MISSING:', missing)
    import sys
    for s in sys.argv[1:]:
        print('=====', s)
        for r in ROWS:
            print(' ', r, '::', ' '.join(data[s][r])[:400])
