import difflib, json
from compare import load_js, pdf_records, norm, words

js, pdf = load_js(), pdf_records()
def fields(name):
    j, p = js[name], pdf[name]
    yield 'landscape', j.get('landscape',''), p['landscape']
    for k in ('vnm','cs','other'):
        yield 'text '+k, (j.get('policies',{}).get(k) or {}).get('text',''), p[k]['text']
    for k in ('size','eligibility','benefitDist'):
        yield 'detail '+k, (j.get('details',{}) or {}).get(k,''), p[k]
    yield 'activeCities', j.get('activeCities',''), p['activeCities']

BULLET = {'●','·','○','▪'}
for name in sorted(pdf):
    for label, a, b in fields(name):
        wa, wb = words(a), words(b)
        if wa == wb: continue
        sm = difflib.SequenceMatcher(None, wa, wb)
        ops = [o for o in sm.get_opcodes() if o[0] != 'equal']
        # ignore pure bullet-marker substitutions ("-" in JS vs "●" in PDF)
        real = []
        for tag,i1,i2,j1,j2 in ops:
            A, B = wa[i1:i2], wb[j1:j2]
            if set(A) <= {'-'} and set(B) <= BULLET and len(A)==len(B): continue
            real.append((tag, ' '.join(wa[max(0,i1-4):i1]), A, B, ' '.join(wb[j2:j2+4])))
        if not real: continue
        print(f'\n### {name} :: {label}')
        for tag, before, A, B, after in real:
            print(f'   …{before}…  JS[{" ".join(A)!r}]  PDF[{" ".join(B)!r}]  …{after}…')
