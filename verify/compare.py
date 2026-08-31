# -*- coding: utf-8 -*-
"""Diff the live site data (state_reports_output.js) against the PDF tables."""
import json, re, difflib, unicodedata
from extract import parse, ROWS

JS_NAME = {   # PDF heading  ->  key used in state_reports_output.js
    'Northern Mariana Islands': 'Commonwealth of the Northern Mariana Islands',
    'US Virgin Islands':        'United States Virgin Islands',
    'Washington, DC':           'District of Columbia',
}

def norm(s):
    s = unicodedata.normalize('NFKC', s or '')
    s = s.replace('**', '')
    s = s.replace('’', "'").replace('‘', "'")
    s = s.replace('“', '"').replace('”', '"')
    for h in '–—‑‐−': s = s.replace(h, '-')
    s = s.replace(' ', ' ').replace('​', '')
    return re.sub(r'\s+', ' ', s).strip()

def words(s):
    return norm(s).lower().split()

STATUS_RE = re.compile(r'^(Yes|No|N/A)\b\s*(?:[A-Z]\s+)?', re.I)

def split_status(cell):
    """The Yes/No badge is centred inside the Overview cell, so it lands first."""
    t = norm(cell)
    m = STATUS_RE.match(t)
    if not m:
        return None, t
    return m.group(1).replace('n/a', 'N/A').capitalize().replace('N/a', 'N/A'), t[m.end():].strip()

def load_js():
    s = open('/Users/evacab/Desktop/COS-State-Maps/COS-State-Map/state_reports_output.js',
             encoding='utf-8').read()
    return json.loads(s[s.index('{'):s.rindex('}') + 1])

def pdf_records():
    data, order = parse()
    recs = {}
    for pdf_name, cells in data.items():
        key = JS_NAME.get(pdf_name, pdf_name)
        rec = {'pdfName': pdf_name}
        rec['landscape'] = norm(' '.join(cells['landscape']))
        for r in ('vnm', 'cs', 'other'):
            st, txt = split_status(' '.join(cells[r]))
            rec[r] = {'status': st, 'text': txt}
        for r in ('size', 'eligibility', 'benefitDist'):
            rec[r] = norm(' '.join(cells[r]))
        rec['activeCities'] = norm(' '.join(cells['activeCities']))
        rec['refs_text'] = norm(' '.join(cells['references']))
        recs[key] = rec
    return recs

def ratio(a, b):
    return difflib.SequenceMatcher(None, words(a), words(b)).ratio()

if __name__ == '__main__':
    js, pdf = load_js(), pdf_records()
    print('js states:', len(js), ' pdf states:', len(pdf))
    print('only in js :', sorted(set(js) - set(pdf)))
    print('only in pdf:', sorted(set(pdf) - set(js)))

    problems = []
    for name in sorted(pdf):
        if name not in js:
            continue
        j, p = js[name], pdf[name]
        # statuses
        for k in ('vnm', 'cs', 'other'):
            sj = (j.get('policies', {}).get(k) or {}).get('status')
            sp = p[k]['status']
            if sj != sp:
                problems.append((name, 'STATUS ' + k, sj, sp))
        # prose
        pairs = [('landscape', j.get('landscape', ''), p['landscape']),
                 ('activeCities', j.get('activeCities', ''), p['activeCities'])]
        for k in ('vnm', 'cs', 'other'):
            pairs.append(('text ' + k, (j.get('policies', {}).get(k) or {}).get('text', ''),
                          p[k]['text']))
        for k in ('size', 'eligibility', 'benefitDist'):
            pairs.append(('detail ' + k, (j.get('details', {}) or {}).get(k, ''), p[k]))
        for label, a, b in pairs:
            if norm(a) == norm(b):
                continue
            r = ratio(a, b)
            problems.append((name, label + f' [{r:.3f}]', norm(a), norm(b)))

    print('\n==== %d field differences ====' % len(problems))
    for name, label, a, b in problems:
        print(f'\n--- {name} :: {label}')
        print('  JS :', (a or '(empty)')[:300])
        print('  PDF:', (b or '(empty)')[:300])
