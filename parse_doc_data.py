"""
Parse per-jurisdiction COS report data from the Google Doc text export.

Source: report_source.md  (the Doc's text representation, committed)
Output: state_reports_output.js  (const STATE_REPORTS = {...};)

Each jurisdiction in the Doc is a 3-column table (Category | Feature | Overview).
The parser is label-anchored: it splits the document into per-state blocks, then
slices each block between known feature labels (matched in their table-cell form
so the label can't match the same phrase inside narrative prose).

Keys in the output are the GeoJSON `NAME` values (see NAME_MAP) so the map's
existing `STATE_REPORTS[name]` lookups work with no JS changes.
"""

import json
import re
import sys

DOC_PATH = 'report_source.md'
OUT_PATH = 'state_reports_output.js'
GEOJSON_PATH = 'states_data_output.js'

# Doc jurisdiction name -> GeoJSON NAME (only the ones that differ)
NAME_MAP = {
    'Washington, DC': 'District of Columbia',
    'US Virgin Islands': 'United States Virgin Islands',
    'Northern Mariana Islands': 'Commonwealth of the Northern Mariana Islands',
}

# ── Text helpers ────────────────────────────────────────────────────────────

_PUNCT = r'!-/:-@\[-`{-~'  # all ASCII punctuation (for un-escaping markdown)

def deep_unescape(s):
    """Decode &#10; newlines and strip backslash-escaped markdown punctuation.

    The Doc's nested status mini-tables are escaped more than once, so we
    iterate until the string stops changing."""
    if not s:
        return ''
    s = s.replace('&#10;', '\n')
    prev = None
    while prev != s:
        prev = s
        s = re.sub(r'\\([' + _PUNCT + r'])', r'\1', s)
    return s

def strip_table(s):
    """Remove markdown table scaffolding (alignment rows and cell pipes)."""
    s = re.sub(r'\|?\s*:-+:\s*\|?', ' ', s)
    return s.replace('|', ' ')

def normalize_prose(s):
    """Keep the Doc's intentional line breaks (paragraphs and bullet items) on
    their own lines so the renderer can lay them out with real spacing.

    The source is a Google Doc markdown export: inside a cell every newline is an
    intentional break (the Doc never soft-wraps), so — unlike the old PDF path —
    we must NOT collapse single newlines into spaces, or paragraph/list gaps are
    lost. Inline citation links are reduced to their text (the URLs live in the
    Sources list); **bold** is left intact for the renderer. Bullet items written
    as "  - " (inline or after a break) are normalized onto their own "- " line."""
    s = re.sub(r'\[([^\]]*?)\]\(https?://[^)\s]*?\)', r'\1', s)  # [text](url) -> text
    s = re.sub(r'\s*<https?://[^>\s]+>', '', s)                  # drop bare <url>
    s = re.sub(r'[ \t]*\n[ \t]*', '\n', s)        # tidy whitespace around breaks
    s = re.sub(r'[ \t]{2,}-[ \t]+', '\n- ', s)    # inline "  - " bullet -> own line
    s = re.sub(r'\n-[ \t]+', '\n- ', s)           # normalize bullet markers
    lines = [re.sub(r'[ \t]{2,}', ' ', ln).strip() for ln in s.split('\n')]
    return '\n'.join(ln for ln in lines if ln)

# Labels that may trail into a slice from the next table row; cut them off.
TRAILING_LABELS = [
    'Enabling/Inhibiting Policies and Programs',
    'Details regarding enabling/inhibiting policies and programs',
    'Active Cities/Communities',
    'References',
]

def cut_trailing(s):
    for lab in TRAILING_LABELS:
        i = s.find(lab)
        if i != -1:
            s = s[:i]
    return s

# ── Field extractors ─────────────────────────────────────────────────────────

def status_and_text(seg):
    """Pull the **Yes**/**No**/**N/A** marker and the explanatory text after it."""
    seg = deep_unescape(seg)
    m = re.search(r'\*\*\s*(Yes|No|N/A)\s*\*\*', seg, re.I)
    status = ''
    if m:
        raw = m.group(1)
        status = 'N/A' if raw.upper() == 'N/A' else raw.capitalize()
        seg = seg[m.end():]
    seg = cut_trailing(seg)
    seg = strip_table(seg)
    text = normalize_prose(seg)
    # The Doc export prepends a stray "D" to some policy explanations
    # (e.g. "DVirtual...", "DSigned..."); it always precedes a capital letter,
    # so a real sentence ("Delaware...", "D.C. ...") is never affected.
    text = re.sub(r'^D(?=[A-Z])', '', text)
    return status, text

def plain_field(seg, label):
    """Clean a non-status cell (landscape, size, eligibility, benefit, cities)."""
    seg = deep_unescape(seg)
    seg = re.sub(re.escape(label), '', seg, count=1)
    seg = cut_trailing(seg)
    seg = strip_table(seg)
    return normalize_prose(seg)

def extract_refs(seg):
    seg = deep_unescape(seg)
    refs, seen = [], set()
    # Markdown links [Title](url)  (optionally with a leading **Label -** before bare urls)
    for m in re.finditer(r'\[([^\]]+?)\]\((https?://[^)\s]+?)\)', seg):
        title = re.sub(r'\s+', ' ', m.group(1)).strip()
        url = m.group(2).strip()
        if url not in seen:
            refs.append({'url': url, 'title': title})
            seen.add(url)
    # Bare <url>, optionally preceded by a **Label -** that becomes the title
    for m in re.finditer(r'(?:\*\*\s*([^*]+?)\s*\*\*\s*)?<(https?://[^>\s]+?)>', seg):
        label = (m.group(1) or '').strip().rstrip('-').strip()
        url = m.group(2).strip()
        if url not in seen:
            refs.append({'url': url, 'title': label or url})
            seen.add(url)
    return refs

# ── Status classification (drives map color) ─────────────────────────────────

NONE_PHRASES = [
    'does not have', 'no community-owned', 'no policies', 'has not enabled',
    'no program', 'has not enacted', 'not codified', 'has not codified',
]

def classify(d):
    cs = d['policies']['cs']['status'].lower()
    vnm = d['policies']['vnm']['status'].lower()
    landscape = d['landscape'].lower()
    has_detail = any(
        (d['details'][k] or '').strip().upper() not in ('', 'N/A', 'NONE')
        for k in ('size', 'eligibility', 'benefitDist')
    )
    if cs == 'yes':
        return 'active'
    if vnm == 'yes' or has_detail:
        return 'limited'
    if cs in ('no', '') and any(p in landscape for p in NONE_PHRASES):
        return 'none'
    return 'limited'

# ── Block parsing ─────────────────────────────────────────────────────────────

STATE_HDR = re.compile(r'\|\s*\\#\\#\s*\\\*\\\*(.+?)\\\*\\\*\s*\|')

# (key, anchor pattern) in document order. Cell-form anchors avoid matching the
# same phrase inside narrative prose.
ANCHORS = [
    ('landscape',   r'Community-Owned Solar Landscape'),
    ('vnm',         r'\| Virtual or Remote Net Metering \|'),
    ('cs',          r'\| Community Solar \|'),
    ('other',       r'\| Other State Support'),  # matches full + short label variants
    ('size',        r'\| Size \|'),
    ('eligibility', r'\| Eligibility \|'),
    ('benefitDist', r'\| Benefit Distribution \|'),
    ('activeCities', r'\| Active Cities/Communities \|'),
    ('references',  r'\| References'),
]

def parse_block(block):
    d = {
        'landscape': '',
        'policies': {'vnm': {'status': '', 'text': ''},
                     'cs': {'status': '', 'text': ''},
                     'other': {'status': '', 'text': ''}},
        'details': {'size': '', 'eligibility': '', 'benefitDist': ''},
        'activeCities': '',
        'sources': [],
    }
    found = []
    for key, pat in ANCHORS:
        m = re.search(pat, block)
        if m:
            found.append((key, m.start()))
    found.sort(key=lambda x: x[1])
    segs = {}
    for i, (key, pos) in enumerate(found):
        end = found[i + 1][1] if i + 1 < len(found) else len(block)
        segs[key] = block[pos:end]

    if 'landscape' in segs:
        d['landscape'] = plain_field(segs['landscape'], 'Community-Owned Solar Landscape')
    for key in ('vnm', 'cs', 'other'):
        if key in segs:
            st, tx = status_and_text(segs[key])
            d['policies'][key] = {'status': st, 'text': tx}
    if 'size' in segs:
        d['details']['size'] = plain_field(segs['size'], 'Size')
    if 'eligibility' in segs:
        d['details']['eligibility'] = plain_field(segs['eligibility'], 'Eligibility')
    if 'benefitDist' in segs:
        d['details']['benefitDist'] = plain_field(segs['benefitDist'], 'Benefit Distribution')
    if 'activeCities' in segs:
        d['activeCities'] = plain_field(segs['activeCities'], 'Active Cities/Communities')
    if 'references' in segs:
        d['sources'] = extract_refs(segs['references'])
    d['status'] = classify(d)
    return d

def build_reports(doc_text):
    matches = list(STATE_HDR.finditer(doc_text))
    reports = {}
    for i, m in enumerate(matches):
        name = m.group(1).strip()
        start = m.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(doc_text)
        key = NAME_MAP.get(name, name)
        reports[key] = parse_block(doc_text[start:end])
    return reports

# ── Validation ────────────────────────────────────────────────────────────────

def geojson_names():
    txt = open(GEOJSON_PATH, encoding='utf-8').read()
    obj = txt[txt.index('{'):txt.rindex('}') + 1]
    data = json.loads(obj)
    return {f['properties']['NAME'] for f in data['features']}

def validate(reports):
    errors = []
    geo = geojson_names()
    for name in reports:
        if name not in geo:
            errors.append(f'report key not in GeoJSON: {name!r}')
    for name in geo:
        if name not in reports:
            errors.append(f'GeoJSON feature has no report: {name!r}')
    # No private-use (PDF font) characters anywhere
    blob = json.dumps(reports, ensure_ascii=False)
    pua = sorted({hex(ord(c)) for c in blob if 0xE000 <= ord(c) <= 0xF8FF})
    if pua:
        errors.append(f'private-use chars present: {pua}')
    return errors

# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    doc = open(DOC_PATH, encoding='utf-8').read()
    reports = build_reports(doc)

    errors = validate(reports)

    # Diagnostics
    no_status = {k: [n for n, d in reports.items() if not d['policies'][k]['status']]
                 for k in ('vnm', 'cs', 'other')}
    no_sources = [n for n, d in reports.items() if not d['sources']]
    counts = {s: sum(1 for d in reports.values() if d['status'] == s)
              for s in ('active', 'limited', 'none')}

    print(f'Jurisdictions parsed: {len(reports)}', file=sys.stderr)
    print(f'Status counts: {counts}', file=sys.stderr)
    print(f'Missing policy status: '
          f"vnm={len(no_status['vnm'])} cs={len(no_status['cs'])} other={len(no_status['other'])}",
          file=sys.stderr)
    if no_status['cs']:
        print(f"  cs missing: {no_status['cs']}", file=sys.stderr)
    if no_status['other']:
        print(f"  other missing: {no_status['other']}", file=sys.stderr)
    print(f'Jurisdictions with no sources ({len(no_sources)}): {no_sources}', file=sys.stderr)

    if errors:
        print('\nVALIDATION ERRORS:', file=sys.stderr)
        for e in errors:
            print(f'  - {e}', file=sys.stderr)
        sys.exit(1)

    names = sorted(reports)
    lines = ['const STATE_REPORTS = {']
    for i, name in enumerate(names):
        comma = '' if i == len(names) - 1 else ','
        lines.append(f'  {json.dumps(name)}: '
                     + json.dumps(reports[name], ensure_ascii=False) + comma)
    lines.append('};')
    with open(OUT_PATH, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))
    print(f'\nWrote {OUT_PATH} ({len(reports)} jurisdictions)', file=sys.stderr)


if __name__ == '__main__':
    main()
