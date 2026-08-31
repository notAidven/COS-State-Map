# -*- coding: utf-8 -*-
"""Correct state_reports_output.js against `Report Draft.pdf`.

Word-level, and deliberately conservative: it applies only edits it can prove
safe, and prints everything else for manual review.

  AUTO  paragraph breaks the original Google-Doc parse dropped, which glued the
        end of one paragraph to the start of the next ("...2027.Subscribers...").
        Restored as "\n", which the page renders as a new <p>.
  SKIP  bullet markers: the PDF uses "●", the JS uses "- " so the renderer can
        build a <ul>. Left alone.
  MANUAL anything else — reported, not applied.
"""
import json, re, difflib, sys
sys.path.insert(0, '.')
from compare import load_js, pdf_records, norm

PATH = '/Users/evacab/Desktop/COS-State-Maps/COS-State-Map/state_reports_output.js'
BULLETS = set('●·○▪•')

def toks(s):
    return norm(s).lower().split()

def strip_marks(w):
    return w.replace('**', '')

# One-off corrections verified against the PDF page image/text.
MANUAL = {
    ('District of Columbia', 'other'): ('C allows communities', 'DC allows communities'),
    ('Oregon', 'vnm'):                 ('D**Traditional net',   '**Traditional net'),
}

def fix_field(raw, pdf_txt, tag, log):
    a, b = toks(raw), toks(pdf_txt)
    if a == b:
        return raw, True
    ok = True
    inserts = []          # token index in `a` after which to break the paragraph
    for op, i1, i2, j1, j2 in difflib.SequenceMatcher(None, a, b).get_opcodes():
        if op == 'equal':
            continue
        A, B = a[i1:i2], b[j1:j2]
        if set(''.join(B)) & BULLETS and set(''.join(A)) <= set('-'):
            continue                                        # bullet marker
        if op == 'replace' and len(A) == 1 and len(B) == 2 and A[0] == B[0] + B[1]:
            inserts.append((i1, B[0], B[1]))                 # dropped paragraph break
            log.append((tag, 'AUTO  paragraph break',
                        ' '.join(a[max(0, i1 - 5):i1]) + f'  [{B[0]} ¶ {B[1]}]'))
            continue
        ok = False
        log.append((tag, 'MANUAL ' + op,
                    f'JS{A!r} PDF{B!r}  …{" ".join(b[max(0,j1-5):j1])}…'))
    # apply the paragraph breaks against the raw string, right to left
    for _, first, second in sorted(inserts, key=lambda t: -t[0]):
        def loose(t):                       # curly vs straight quotes, dash variants
            out = []
            for ch in t:
                if ch == '"':   out.append('["\u201c\u201d]')
                elif ch == "'": out.append("['\u2018\u2019]")
                elif ch == '-': out.append('[-\u2010\u2011\u2013\u2014]')
                else:           out.append(re.escape(ch))
            return ''.join(out)
        pat = re.compile('(' + loose(first.rstrip('.,;:)')) + r'[^\sA-Za-z0-9]*)(\*{0,2})('
                         + loose(second[:6]) + ')', re.I)
        m = None
        for m in pat.finditer(raw):
            pass                                            # last occurrence wins
        if not m:
            log.append((tag, 'MANUAL could not locate break', f'{first!r} + {second!r}'))
            ok = False
            continue
        raw = raw[:m.start(2)] + '\n' + raw[m.start(2):]
    return raw, ok

# URLs the Google-Doc parse truncated at a bracket; the full targets come from
# the PDF's own link annotations.
URL_FIXES = {
 'https://web.archive.org/web/20250220054405/https://www.guamlegislature.com/Bills_Introduced_33rd/Bill%20No.%20B363-33%20(COR':
 'https://web.archive.org/web/20250220054405/https://www.guamlegislature.com/Bills_Introduced_33rd/Bill%20No.%20B363-33%20(COR).pdf',
 'https://www.guamlegislature.com/36th_Guam_Legislature/Voting_Records_36th/ABill%20No.%20351-36%20(COR':
 'https://www.guamlegislature.com/36th_Guam_Legislature/Voting_Records_36th/ABill%20No.%20351-36%20(COR)%20PASSED.pdf',
 'https://www.hawaiianelectric.com/clean-energy-hawaii/selling-power-to-the-utility/competitive-bidding-for-system-resources/community-based-renewable-energy-(cbre':
 'https://www.hawaiianelectric.com/clean-energy-hawaii/selling-power-to-the-utility/competitive-bidding-for-system-resources/community-based-renewable-energy-(cbre)-for-low-and-moderate-income-(lmi)-rfps',
}

def main(apply_changes):
    js, pdf = load_js(), pdf_records()
    log, clean = [], 0
    for name in js:
        for r in js[name].get('sources', []):
            if r['url'] in URL_FIXES:
                log.append((f'{name}/sources', 'AUTO  truncated url',
                            r['url'][-40:] + ' -> …' + URL_FIXES[r['url']][-40:]))
                r['url'] = URL_FIXES[r['url']]
    for name in sorted(js):
        p = pdf[name]
        j = js[name]
        fields = [('landscape', j, 'landscape', p['landscape']),
                  ('activeCities', j, 'activeCities', p['activeCities'])]
        for k in ('vnm', 'cs', 'other'):
            fields.append((k, j['policies'][k], 'text', p[k]['text']))
        for k in ('size', 'eligibility', 'benefitDist'):
            fields.append((k, j['details'], k, p[k]))
        for label, container, key, pdf_txt in fields:
            tag = f'{name}/{label}'
            raw = container.get(key, '')
            if (name, label) in MANUAL:
                old, new = MANUAL[(name, label)]
                assert old in raw, tag
                raw = raw.replace(old, new, 1)
                log.append((tag, 'AUTO  manual fix', f'{old!r} -> {new!r}'))
            raw, ok = fix_field(raw, pdf_txt, tag, log)
            container[key] = raw
            clean += ok
        for k in ('vnm', 'cs', 'other'):
            if p[k]['status'] and j['policies'][k].get('status') != p[k]['status']:
                log.append((f'{name}/{k}', 'AUTO  status',
                            f"{j['policies'][k].get('status')} -> {p[k]['status']}"))
                j['policies'][k]['status'] = p[k]['status']

    auto = [l for l in log if l[1].startswith('AUTO')]
    man  = [l for l in log if l[1].startswith('MANUAL')]
    print(f'fields verified clean: {clean}/{56*8}')
    print(f'\n==== {len(auto)} automatic corrections ====')
    for tag, what, ctx in auto:
        print(f'  {tag:44s} {what:24s} {ctx}')
    print(f'\n==== {len(man)} needing manual review ====')
    for tag, what, ctx in man:
        print(f'  {tag:44s} {what:24s} {ctx}')

    if apply_changes:
        body = ',\n  '.join(json.dumps({k: v}, ensure_ascii=False)[1:-1] for k, v in js.items())
        open(PATH, 'w', encoding='utf-8').write(
            'const STATE_REPORTS = {\n  ' + body + '\n};\n')
        print('\nwrote', PATH)

main('--apply' in sys.argv)
