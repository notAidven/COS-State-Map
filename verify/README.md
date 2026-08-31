# Verifying state_reports_output.js against the source PDF

Checks every field of all 56 state/territory reports against `Report Draft.pdf`.

## Setup

    pdftotext -layout "Report Draft.pdf" report.txt      # poppler
    python3 -m venv venv && ./venv/bin/pip install pypdf

Run everything from this directory, with `report.txt` alongside these scripts and
the PDF path in `refs2.py` pointing at the source.

## Scripts

| script | what it does |
| --- | --- |
| `extract.py` | Parses the three-column state tables out of `report.txt`. Column offsets drift page to page and the Active Cities / References rows are merged across columns, so gutters are detected per page. |
| `compare.py` | Field-by-field diff of the site data against the PDF. |
| `worddiff.py` | Word-level diff, ignoring the bullet-marker difference (PDF `●` vs the `- ` the page renders as `<ul>`). **This is the authoritative check — it should print nothing.** |
| `refs2.py` | Rebuilds each state's reference list from the PDF's link annotations (restricted to the References row) and compares URLs. |
| `fix_data.py` | Applies corrections. Conservative: auto-applies only dropped paragraph breaks and a short list of verified one-off fixes; anything else is reported under "needing manual review". Not idempotent — the one-off fixes assert on a second run. |

## Status

As of the last run: 448/448 prose fields and all 168 Yes/No statuses match the
PDF; reference URL sets match for all 56 jurisdictions. The only remaining
`compare.py` differences are the intentional bullet-marker substitutions.
