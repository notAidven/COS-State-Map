# State Report Panel Redesign — Design

- **Date:** 2026-06-29
- **Status:** Approved (pending spec review)
- **Branch:** `redesign-state-report-panel`

## Problem

When a user clicks a state on the map, the side panel renders the per-state
report as dense blocks of text. Two root causes make it read as a "wall of
text" rather than a scannable report:

1. **Ragged hard line breaks.** The data was extracted from a PDF; every
   PDF line-wrap newline was preserved and the renderer turns *every* `\n`
   into a `<br>`. Sentences break mid-phrase into a jagged column.
2. **Encoding junk from PDF parsing.** Private-use font characters leaked in
   (e.g. `15E0082` which should read `15-E-0082`) and quotes were mangled
   (`community sponsorˮ`).

Even within the existing "section card" layout, content is presented as long
unbroken paragraphs that are hard to skim.

## Goals

- Clicking a state opens a **scannable fact sheet first**: status and the key
  yes/no policy posture readable at a glance, with full narrative available on
  demand.
- **Clean, correctly-encoded text** that flows as readable prose.
- Pull data from the **Google Doc source** (clean Unicode, real reference
  titles) instead of the lossy PDF path, and make the build reproducible.
- **Cover all 56 jurisdictions** the Doc and the map already support.

## Non-goals

- No change to the map itself, drag-to-resize, panel collapse toggle, welcome
  screen, fonts, or color system.
- No surfacing of the Doc's general/introductory sections (Solar For All,
  coalition explainers, Key Findings). Per-state focus only.
- No new runtime dependencies; the build stays pure Python stdlib.

## Source of truth & data pipeline

The source PDF and the generated `.js` data files are gitignored and absent
from the repo; the only surviving copy of the data was inlined in the built
HTML. We replace the PDF path with the cleaner Google Doc and make the build
reproducible offline:

```
Google Doc
   │  (exported once via Drive, committed to the repo)
   ▼
report_source.md                ← new committed source of truth
   │  parse_doc_data.py          ← new parser (stdlib only)
   ▼
state_reports_output.js         ← generated (gitignored, as today)
   │  build_html.py              ← inlines data + new render layer
   ▼
community_solar_reports.html    ← built artifact (committed, as today)
```

- **`report_source.md`** — the Doc's text representation, committed so the
  pipeline runs without Drive access or the PDF. (The repo already committed
  the full report text inlined in the HTML, so committing the source text is
  consistent with current practice.)
- **`parse_doc_data.py`** — replaces `extract_pdf_data.py`. Drops the
  `pdfplumber` dependency entirely.
- **`extract_pdf_data.py`** — **removed** (superseded; PDF source no longer
  used).
- **`fetch_states_geojson.py`**, **`build_html.py`** — kept; `build_html.py`'s
  data contract is unchanged, only its render layer changes.

> **Build prerequisite:** `build_html.py` inlines both `states_data_output.js`
> and `state_reports_output.js`. The former is gitignored and absent from this
> clone, so it must be regenerated via `fetch_states_geojson.py` (network) or
> recovered from the GeoJSON already inlined in the committed HTML (offline).
> The plan will pick one; recovery-from-HTML keeps the build offline-reproducible.

### Parser design (`parse_doc_data.py`)

Each jurisdiction in the Doc is a 3-column table (`Category | Feature |
Overview`). The parser is **label-anchored** (validated against all 56
jurisdictions during design):

1. Split the document into per-state blocks on the state-name header row
   (`## **State Name**`).
2. Within each block, locate known feature labels as anchors
   (`Community-Owned Solar Landscape`, `Virtual or Remote Net Metering`,
   `Community Solar`, `Other State Support…`, `Size`, `Eligibility`,
   `Benefit Distribution`, `Active Cities/Communities`, `References`) and
   slice the text between consecutive anchors. Anchors match the table-cell
   label form (e.g. `| Community Solar |`) to avoid matching the phrase inside
   narrative prose.
3. For each policy cell, extract the embedded status marker
   (`**Yes**` / `**No**` / `**N/A**`) and the explanatory text after it.
4. Deep-unescape backslash-escaped Markdown (handles the double-escaping in the
   Doc's nested status mini-tables) and decode `&#10;` newline entities.
5. Extract references as `[Title](url)` pairs **and** bare `<url>` links, so
   varied reference formatting in the Doc is captured with real titles.

The parser emits the **same `STATE_REPORTS` schema** the build already expects,
so `build_html.py`'s data contract is unchanged:

```js
{
  landscape: string,
  policies: {
    vnm:   { status: "Yes"|"No"|"N/A"|"", text: string },
    cs:    { status: ..., text: string },
    other: { status: ..., text: string }
  },
  details: { size: string, eligibility: string, benefitDist: string },
  activeCities: string,
  sources: [ { url: string, title: string } ],
  status: "active"|"limited"|"none"
}
```

### Jurisdiction name mapping

The map GeoJSON already contains all 56 features, but uses different names than
the Doc. The parser keys `STATE_REPORTS` by the **GeoJSON `NAME`** so the
existing JS lookups (`STATE_REPORTS[name]`) work with no JS changes. Known
remaps:

| Doc name | GeoJSON `NAME` |
|---|---|
| `Washington, DC` | `District of Columbia` |
| `US Virgin Islands` | `United States Virgin Islands` |
| `Northern Mariana Islands` | `Commonwealth of the Northern Mariana Islands` |

All other 53 names match directly. The parser asserts every emitted key exists
in the GeoJSON name set (and that all 56 GeoJSON features are covered) so a
future Doc rename fails loudly instead of silently dropping a jurisdiction.

## Panel redesign — "scannable fact sheet first"

Replaces the body produced by `showStateReport()`. The sticky header
(state name + status badge) and the "← All States" back button are retained.

```
┌─ CALIFORNIA ───────────────── ● Active ─┐   sticky header (retained)
├──────────────────────────────────────────┤
│ POLICIES AT A GLANCE                       │   fact sheet — always visible
│   Community Solar           ✔ Yes      ▸  │   row click → expand explanation
│   Virtual / Remote Net Met. ✔ Yes      ▸  │
│   Other State Support       ✔ Yes      ▸  │
├──────────────────────────────────────────┤
│ PROGRAM DETAILS                            │   compact key/value
│   Size          41–600 MW caps             │   (whole block hidden if all N/A)
│   Eligibility   Low-income / all (ECR)     │
│   Benefit Dist. 100 MW low-income carve-out│
├──────────────────────────────────────────┤
│ ▸ Landscape overview                       │   collapsed accordions
│ ▸ Active cities & communities              │
│ ▸ Sources (7)                              │
└──────────────────────────────────────────┘
```

### Components & behavior

- **Status badge** — `Active` / `Limited / Emerging` / `No Program`, same
  three-tier scheme and colors as today.
- **Policies at a glance** — three rows (Community Solar, Virtual / Remote Net
  Metering, Other State Support), each with a `Yes` / `No` / `N/A` badge.
  - Each row is the **accordion trigger for its own explanation**: clicking the
    row expands the cleaned explanatory paragraph inline beneath it. A row with
    no explanatory text shows the badge only and is not expandable.
  - This unifies the at-a-glance summary and the detail-on-demand — no separate
    redundant "policies" section.
- **Program details** — `Size`, `Eligibility`, `Benefit Distribution` as
  compact label/value rows. The **entire block is omitted** when all three are
  `N/A`/empty (e.g. Texas), so states with no program don't show empty scaffolding.
- **Collapsed accordion sections** (collapsed by default per chosen direction):
  - **Landscape overview** — the narrative paragraph(s).
  - **Active cities & communities** — omitted if empty.
  - **Sources (N)** — list of links using the Doc's real titles; omitted if none.
- **Interaction model** — pure CSS/JS toggle (no framework). Clicking a
  collapsed header or an expandable policy row toggles its open state and
  rotates its `▸`/`▾` caret. Multiple sections may be open at once.
- **Empty/no-data states** — a jurisdiction with no report still shows the
  header and status; sections with no content are simply absent rather than
  showing "No information available." filler.

### Text cleanup & formatting rules

Applied in the parser so the stored data is already clean:

- Preserve real Unicode (curly quotes `'` `"`, en-dashes `–`).
- **Collapse soft wraps:** single newlines inside a field that are mid-sentence
  PDF/wrap artifacts are joined into flowing text; blank-line (double-newline)
  breaks are preserved as paragraph separators.
- Strip residual Markdown table scaffolding (`|`, `:-:`) and leftover escape
  backslashes.
- The renderer splits on real paragraph breaks into `<p>` elements rather than
  converting every `\n` to `<br>`.

### Status classification

Refine `active` / `limited` / `none` using the now-reliable explicit signals:

- **`active`** — Community Solar `Yes` **and** at least one concrete program
  detail (size/eligibility/benefit not all N/A).
- **`none`** — Community Solar `No` **and** VNM `No` **and** landscape clearly
  states no program/policy.
- **`limited`** — everything else (emerging, enabled-but-thin, mixed signals).

Map colors and the legend are unchanged. The welcome panel's counts update to
reflect all 56 jurisdictions.

## File changes

| File | Change |
|---|---|
| `report_source.md` | **add** — committed Doc text (source of truth) |
| `parse_doc_data.py` | **add** — label-anchored Doc parser → `state_reports_output.js` |
| `extract_pdf_data.py` | **remove** — superseded by the Doc parser |
| `build_html.py` | **modify** — new fact-sheet/accordion render layer in `showStateReport()` + supporting CSS; welcome counts to 56 |
| `community_solar_reports.html` | **regenerate** — built artifact |

`.gitignore` needs no change: both generated `.js` files stay ignored and
`report_source.md` is unmatched by any rule (commits normally).

## Testing & verification

1. **Parser correctness:** running `parse_doc_data.py` yields all 56
   jurisdictions; assert no policy `status` is empty where the Doc has a marker,
   zero private-use (`U+E000–U+F8FF`) characters in any field, and every emitted
   key maps to a GeoJSON feature (and all 56 features are covered).
2. **Build:** `build_html.py` runs clean and regenerates the HTML.
3. **Render check:** open the built HTML in a browser and screenshot
   representative jurisdictions — an active state (California), a no-program
   state (Texas), and a newly-wired territory (Puerto Rico or DC) — to confirm
   the fact sheet reads at a glance, accordions expand/collapse, the details
   block hides correctly when all N/A, and prose flows without ragged breaks.

## Risks / open items

- **Reference-format variance:** a few states format references differently in
  the Doc; the parser captures both `[title](url)` and bare `<url>` forms, but
  reference counts should be spot-checked against the Doc during implementation.
- **Status edge cases:** a small number of `Other State Support` cells did not
  yield a clean marker in the prototype; the implementation will confirm each of
  the 56 against the Doc and fall back to empty (badge hidden) rather than
  guessing.
- **Committing `report_source.md`:** assumes the report text is OK to keep in
  the repo (it already was, inlined in the HTML). Flag if it should stay
  gitignored instead.
