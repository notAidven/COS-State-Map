# -*- coding: utf-8 -*-
"""Rebuild each state's reference list from the PDF: link annotations inside the
References row, paired with the anchor text drawn over them."""
import re, sys
from pypdf import PdfReader
sys.path.insert(0, '.')
from extract import PAGES, page_state
from compare import load_js, JS_NAME

READER = PdfReader('/Users/evacab/Downloads/Report Draft.pdf')
NPAGES = len(READER.pages)

def page_words(i):
    """[(x, y, text)] for every text run drawn on page i."""
    runs = []
    def visit(text, cm, tm, font, size):
        t = text.strip('\n')
        if t.strip():
            # the text matrix is relative to the current transform
            x = cm[0] * tm[4] + cm[2] * tm[5] + cm[4]
            y = cm[1] * tm[4] + cm[3] * tm[5] + cm[5]
            runs.append((round(x, 1), round(y, 1), t))
    READER.pages[i].extract_text(visitor_text=visit)
    return runs

def refs_y(i):
    """y of the 'References' row label on page i, or None."""
    for x, y, t in page_words(i):
        if t.strip().startswith('References') and x < 150:
            return y
    return None

def page_annots(i):
    out = []
    for a in READER.pages[i].get('/Annots') or []:
        o = a.get_object()
        act = o.get('/A')
        if not act:
            continue
        uri = act.get_object().get('/URI')
        if not uri:
            continue
        r = [float(v) for v in o['/Rect']]
        out.append({'x0': r[0], 'y0': r[1], 'x1': r[2], 'y1': r[3], 'uri': str(uri)})
    return out

def anchor_text(i, ann):
    """Text runs whose baseline sits inside the annotation rectangle."""
    parts = []
    for x, y, t in page_words(i):
        if ann['y0'] - 2 <= y <= ann['y1'] and ann['x0'] - 3 <= x <= ann['x1'] + 3:
            parts.append((y, x, t))
    parts.sort(key=lambda p: (-p[0], p[1]))
    return re.sub(r'\s+', ' ', ' '.join(p[2] for p in parts)).strip()

def state_pages():
    spans, cur = {}, None
    for i, pg in enumerate(PAGES[:NPAGES]):
        s = page_state(pg)
        if s and s not in spans:
            cur = s; spans[s] = []
        if cur:
            spans[cur].append(i)
    return spans

def pdf_refs(idxs):
    """Ordered [(title, url)] from the References row of a state's pages."""
    out, started = [], False
    for i in idxs:
        y = refs_y(i)
        if y is not None:
            started = True
        if not started:
            continue
        cut = y + 6 if y is not None else 1e9
        anns = [a for a in page_annots(i) if a['y0'] <= cut]
        anns.sort(key=lambda a: (-round(a['y1'], 0), a['x0']))
        # a single reference may be split into several link rects across lines
        merged = []
        for a in anns:
            if merged and merged[-1]['uri'] == a['uri']:
                merged[-1]['text'] += ' ' + anchor_text(i, a)
            else:
                a = dict(a); a['text'] = anchor_text(i, a)
                merged.append(a)
        for a in merged:
            out.append((re.sub(r'\s+', ' ', a['text']).strip(), a['uri']))
    return out

if __name__ == '__main__':
    js = load_js()
    spans = state_pages()
    diff = 0
    for pdf_name, idxs in spans.items():
        key = JS_NAME.get(pdf_name, pdf_name)
        jrefs = js[key].get('sources', [])
        prefs = pdf_refs(idxs)
        ju = [r['url'] for r in jrefs]
        pu = [u for _, u in prefs]
        def canon(u): return u.rstrip('/.').replace('http://', 'https://')
        if [canon(u) for u in ju] == [canon(u) for u in pu]:
            continue
        diff += 1
        print(f'\n### {key}   js={len(ju)}  pdf={len(pu)}')
        sj, sp = {canon(u) for u in ju}, {canon(u) for u in pu}
        for u in ju:
            if canon(u) not in sp: print('   JS-only :', u)
        for t, u in prefs:
            if canon(u) not in sj: print('   PDF-only:', u, ' [', t[:60], ']')
        if sj == sp: print('   (same set, different order)')
    print(f'\n{diff} states differ (of {len(spans)})')
