"""
Extract structured per-state COS report data from Report Draft.pdf.

Table structure (3 cols):
  Col 0: Category ("Community Ownership", "Enabling/Inhibiting...",
                   "Details regarding...", "Active Cities/Communities", "References")
  Col 1: Feature  ("Community-Owned Solar Landscape", "Virtual or Remote Net Metering",
                   "Community Solar", "Other State Support...",
                   "Size", "Eligibility", "Benefit Distribution")
  Col 2: Overview (full text, sometimes starting with "Yes" or "No")
"""

import pdfplumber
import json
import re
import sys

PDF_PATH = r'Report Draft.pdf'

STATE_NAMES = [
    "Alabama","Alaska","Arizona","Arkansas","California","Colorado","Connecticut",
    "Delaware","Florida","Georgia","Hawaii","Idaho","Illinois","Indiana","Iowa",
    "Kansas","Kentucky","Louisiana","Maine","Maryland","Massachusetts","Michigan",
    "Minnesota","Mississippi","Missouri","Montana","Nebraska","Nevada",
    "New Hampshire","New Jersey","New Mexico","New York","North Carolina",
    "North Dakota","Ohio","Oklahoma","Oregon","Pennsylvania","Rhode Island",
    "South Carolina","South Dakota","Tennessee","Texas","Utah","Vermont",
    "Virginia","Washington","West Virginia","Wisconsin","Wyoming"
]
STATE_SET = set(STATE_NAMES)

def clean(s):
    if s is None:
        return ''
    # Replace common ligature / special chars from font encoding
    s = s.replace('', '(').replace('', ')')
    s = s.replace('ʼ', "'").replace('’', "'").replace('‘', "'")
    s = s.replace('“', '"').replace('”', '"')
    s = s.replace('–', '-').replace('—', '-')
    return s.strip()

def split_status_text(raw):
    """Split a cell like 'Yes\nExplanation...' into ('Yes', 'Explanation...')."""
    raw = clean(raw)
    m = re.match(r'^(Yes|No|N/A)\s*\n?(.*)', raw, re.DOTALL | re.IGNORECASE)
    if m:
        return m.group(1).strip(), m.group(2).strip()
    return '', raw

def make_title_from_url(url):
    title = re.sub(r'^https?://(www\.)?', '', url)
    parts = title.split('/')
    if len(parts) > 2:
        return parts[0] + '/...'
    return title[:80]

def extract_inline_urls(text):
    return re.findall(r'https?://[^\s\)\]\n"\'<>]+', text)

def extract_urls_from_annots(page):
    urls = []
    if page.annots:
        for annot in page.annots:
            uri = annot.get('uri') or annot.get('URI')
            if uri and str(uri).startswith('http'):
                urls.append(str(uri))
    return urls

def classify_status(data):
    """Derive active/limited/none from the structured data."""
    cs_status  = (data.get('policies') or {}).get('cs', {}).get('status', '').lower()
    vnm_status = (data.get('policies') or {}).get('vnm', {}).get('status', '').lower()
    landscape  = (data.get('landscape') or '').lower()
    details    = (data.get('details') or {})
    has_size   = (details.get('size') or '').lower() not in ('n/a', '', 'none')

    none_phrases = ['does not have', 'no community-owned', 'no policies',
                    'has not enabled', 'no program', 'has not enacted']

    if cs_status == 'yes' or (cs_status != 'no' and vnm_status == 'yes'):
        if has_size:
            return 'active'
        return 'active' if cs_status == 'yes' else 'limited'
    if any(p in landscape for p in none_phrases) and cs_status in ('no', ''):
        return 'none'
    return 'limited'


def parse_state_table(table, page):
    """Parse a single state's 3-col table into structured data."""
    state_data = {
        'landscape':   '',
        'policies':    {'vnm': {'status': '', 'text': ''},
                        'cs':  {'status': '', 'text': ''},
                        'other': {'status': '', 'text': ''}},
        'details':     {'size': '', 'eligibility': '', 'benefitDist': ''},
        'activeCities':'',
        'sources':     []
    }

    current_section = None  # 'ownership' | 'policies' | 'details' | 'cities' | 'refs'
    current_feature = None

    for row in table:
        c0 = clean(row[0] if len(row) > 0 else '')
        c1 = clean(row[1] if len(row) > 1 else '')
        c2 = clean(row[2] if len(row) > 2 else '')

        # Detect section by category column — check 'details' BEFORE 'enabling'
        # because "Details regarding enabling/inhibiting..." contains both keywords
        c0_lower = c0.lower()
        if c0_lower.startswith('community') and ('ownership' in c0_lower):
            current_section = 'ownership'
        elif c0_lower.startswith('details'):
            current_section = 'details'
        elif 'enabling' in c0_lower or 'inhibiting' in c0_lower:
            current_section = 'policies'
        elif c0_lower.startswith('active'):
            current_section = 'cities'
        elif 'references' in c0_lower:
            current_section = 'refs'
        # Skip header row
        if c0.lower() in ('category', 'feature', 'overview'):
            continue
        # Skip separator rows
        if not c0 and not c1 and not c2:
            continue
        if c0 in STATE_SET:
            continue

        # Route by section
        if current_section == 'ownership':
            if c2:
                state_data['landscape'] = c2

        elif current_section == 'policies':
            feat = c1.lower() if c1 else current_feature
            if 'virtual' in feat or 'remote' in feat or 'net' in feat:
                status, text = split_status_text(c2)
                state_data['policies']['vnm'] = {'status': status, 'text': text}
                current_feature = feat
            elif 'community\nsolar' in feat or feat == 'community solar':
                status, text = split_status_text(c2)
                state_data['policies']['cs'] = {'status': status, 'text': text}
                current_feature = feat
            elif 'other' in feat or 'support' in feat:
                status, text = split_status_text(c2)
                state_data['policies']['other'] = {'status': status, 'text': text}
                current_feature = feat

        elif current_section == 'details':
            feat = c1.lower() if c1 else ''
            if 'size' in feat:
                state_data['details']['size'] = c2
            elif 'eligib' in feat:
                state_data['details']['eligibility'] = c2
            elif 'benefit' in feat or 'distribut' in feat:
                state_data['details']['benefitDist'] = c2

        elif current_section == 'cities':
            # The city text is in col 0 or col 1 depending on the page
            text = c0 if not c0.lower().startswith('active') else (c1 or c2)
            # Sometimes it's in the column that has content
            if not text and c1:
                text = c1
            if not state_data['activeCities'] and text:
                state_data['activeCities'] = text

        elif current_section == 'refs':
            # References are often in col 0 or col 1
            ref_text = c0 if len(c0) > 10 else c1
            for url in extract_inline_urls(ref_text):
                state_data['sources'].append({'url': url, 'title': make_title_from_url(url)})

    # Also collect hyperlink annotations from the page
    annot_urls = extract_urls_from_annots(page)
    existing = {s['url'] for s in state_data['sources']}
    for url in annot_urls:
        if url not in existing:
            state_data['sources'].append({'url': url, 'title': make_title_from_url(url)})
            existing.add(url)

    state_data['status'] = classify_status(state_data)
    return state_data


def build_reports(pdf_path):
    reports = {}

    with pdfplumber.open(pdf_path) as pdf:
        print(f'PDF: {len(pdf.pages)} pages', file=sys.stderr)
        for i, page in enumerate(pdf.pages):
            tables = page.extract_tables()
            for table in tables:
                if not table or len(table) < 2:
                    continue
                # First row should be the state name
                first_cell = clean(table[0][0] if table[0] else '')
                if first_cell in STATE_SET:
                    state_name = first_cell
                    data = parse_state_table(table, page)
                    if state_name in reports:
                        # Merge additional pages for same state
                        if not reports[state_name]['landscape'] and data['landscape']:
                            reports[state_name]['landscape'] = data['landscape']
                        for k in ('vnm', 'cs', 'other'):
                            if not reports[state_name]['policies'][k]['text'] and data['policies'][k]['text']:
                                reports[state_name]['policies'][k] = data['policies'][k]
                        for k in ('size', 'eligibility', 'benefitDist'):
                            if not reports[state_name]['details'][k] and data['details'][k]:
                                reports[state_name]['details'][k] = data['details'][k]
                        if not reports[state_name]['activeCities'] and data['activeCities']:
                            reports[state_name]['activeCities'] = data['activeCities']
                        seen = {s['url'] for s in reports[state_name]['sources']}
                        for s in data['sources']:
                            if s['url'] not in seen:
                                reports[state_name]['sources'].append(s)
                                seen.add(s['url'])
                    else:
                        reports[state_name] = data
                    sys.stderr.write(f'  Page {i+1}: {state_name} — cs={data["policies"]["cs"]["status"]}, status={data["status"]}\n')

    return reports


reports = build_reports(PDF_PATH)

# Fill in any missing states
for state in STATE_NAMES:
    if state not in reports:
        print(f'WARNING: {state} not found in PDF', file=sys.stderr)
        reports[state] = {
            'landscape': '',
            'policies': {'vnm': {'status': '', 'text': ''}, 'cs': {'status': '', 'text': ''}, 'other': {'status': '', 'text': ''}},
            'details': {'size': '', 'eligibility': '', 'benefitDist': ''},
            'activeCities': '',
            'sources': [],
            'status': 'limited'
        }

# Emit JS
lines = ['const STATE_REPORTS = {']
for i, state in enumerate(STATE_NAMES):
    data = reports[state]
    comma = '' if i == len(STATE_NAMES) - 1 else ','
    lines.append(f'  {json.dumps(state)}: ' + json.dumps(data, ensure_ascii=False) + comma)
lines.append('};')

with open('state_reports_output.js', 'w', encoding='utf-8') as f:
    f.write('\n'.join(lines))

# Summary
print('\n=== Summary ===')
for state in STATE_NAMES:
    d = reports[state]
    cs = d['policies']['cs']['status'] or '?'
    vnm = d['policies']['vnm']['status'] or '?'
    print(f'  {state:20s}  {d["status"]:8s}  cs={cs:3s}  vnm={vnm:3s}  src={len(d["sources"]):3d}')

active  = sum(1 for d in reports.values() if d['status'] == 'active')
limited = sum(1 for d in reports.values() if d['status'] == 'limited')
none_   = sum(1 for d in reports.values() if d['status'] == 'none')
print(f'\nactive={active}  limited={limited}  none={none_}')
print('Written state_reports_output.js')
