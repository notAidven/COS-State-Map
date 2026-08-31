"""Assembles community_solar_reports.html by inlining both JS data files."""

with open('states_data_output.js', 'r', encoding='utf-8') as f:
    states_data_js = f.read()

with open('state_reports_output.js', 'r', encoding='utf-8') as f:
    state_reports_js = f.read()

html = r"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Community Solar and Community-Owned Solar State Reports</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Inter:ital,wght@0,400;0,500;0,600;0,700;1,400&display=swap" rel="stylesheet">
  <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
  <style>
    :root {
      --primary:        #0f766e;
      --primary-light:  #14b8a6;
      --primary-dark:   #0d5d56;
      --primary-xdark:  #094444;
      --primary-bg:     #f0fdfa;
      --primary-bg2:    #ccfbf1;

      /* Overall-status palette: three high-contrast hues.
         "No data" is folded into "no enabling policy" (grey). */
      --st-both:    #14713d;   /* CS + state support for community ownership */
      --st-cs:      #e2711d;   /* community solar only */
      --st-none:    #c3ccd4;   /* no enabling policy / no data */

      /* Single-category layers, matching the report's Fig. 1 colours */
      --cat-vnm:    #2e7d32;
      --cat-cs:     #1f5fa8;
      --cat-cos:    #dfa008;
      --cat-off:    #c3ccd4;

      --yes-bg:   #dcfce7; --yes-fg:   #166534;
      --no-bg:    #fee2e2; --no-fg:    #991b1b;
      --na-bg:    #f1f5f9; --na-fg:    #64748b;
      --slate-50:  #f8fafc; --slate-100: #f1f5f9;
      --slate-200: #e2e8f0; --slate-300: #cbd5e1;
      --slate-400: #94a3b8; --slate-500: #64748b;
      --slate-600: #475569; --slate-700: #334155;
      --slate-800: #1e293b; --slate-900: #0f172a;
      --shadow:    0 1px 3px 0 rgb(0 0 0/.1),0 1px 2px -1px rgb(0 0 0/.1);
      --shadow-md: 0 4px 6px -1px rgb(0 0 0/.1),0 2px 4px -2px rgb(0 0 0/.1);
    }
    *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
    body { font-family: 'Inter', sans-serif; background: var(--slate-50); color: var(--slate-800); }
    .container { max-width: 1400px; margin: 0 auto; padding: 20px 24px; }

    /* ── Header ── */
    header { margin-bottom: 14px; display: flex; align-items: baseline; gap: 14px; flex-wrap: wrap; }
    header h1 { font-size: 1.4rem; font-weight: 700; color: var(--primary-dark); }
    header .subtitle { color: var(--slate-500); font-size: 0.85rem; }

    /* ── View tabs (Map / List / About) ── */
    .view-tabs { display: flex; gap: 4px; margin-bottom: 14px;
                 border-bottom: 1px solid var(--slate-200); }
    .view-tab {
      background: none; border: none; border-bottom: 2px solid transparent;
      font-family: inherit; font-size: 0.84rem; font-weight: 600; color: var(--slate-500);
      padding: 8px 14px; cursor: pointer; margin-bottom: -1px;
    }
    .view-tab:hover { color: var(--primary-dark); }
    .view-tab.active { color: var(--primary-dark); border-bottom-color: var(--primary); }
    .view { display: none; }
    .view.active { display: block; }

    /* ── Layer switcher above the map ── */
    .layer-bar {
      display: flex; align-items: center; gap: 10px; flex-wrap: wrap;
      margin-bottom: 10px;
    }
    .layer-bar-label {
      font-size: 0.66rem; font-weight: 700; text-transform: uppercase;
      letter-spacing: .07em; color: var(--slate-400);
    }
    .segmented { display: flex; flex-wrap: wrap; gap: 4px; background: var(--slate-200);
                 padding: 3px; border-radius: 9px; }
    .seg-btn {
      background: none; border: none; font-family: inherit; cursor: pointer;
      font-size: 0.76rem; font-weight: 600; color: var(--slate-600);
      padding: 6px 12px; border-radius: 7px; white-space: nowrap;
    }
    .seg-btn:hover { color: var(--primary-xdark); }
    .seg-btn.active { background: white; color: var(--primary-dark); box-shadow: var(--shadow); }

    /* ── Main grid ── */
    .main-content {
      display: grid;
      grid-template-columns: 1.8fr 6px 1fr;
      gap: 0;
      margin-bottom: 12px;
      transition: grid-template-columns 0.3s ease;
    }
    .main-content.panel-collapsed { grid-template-columns: 1fr 6px 0 !important; }
    .main-content.panel-collapsed .info-panel {
      padding: 0; border-width: 0; box-shadow: none;
      margin-left: 0; background: transparent; overflow: visible;
    }
    .main-content.panel-collapsed #panel-content { display: none; }

    /* ── Map ── */
    #map {
      height: 620px; border-radius: 14px;
      box-shadow: var(--shadow-md); overflow: hidden; margin-right: 12px;
    }

    /* ── Off-map jurisdictions ── */
    .jump-bar {
      display: flex; align-items: center; gap: 8px; flex-wrap: wrap;
      margin-bottom: 14px;
    }
    .jump-label {
      font-size: 0.66rem; font-weight: 700; text-transform: uppercase;
      letter-spacing: .07em; color: var(--slate-400);
    }
    .jump-chip {
      background: white; border: 1px solid var(--slate-300); border-radius: 99px;
      font-family: inherit; font-size: 0.74rem; font-weight: 600; color: var(--slate-600);
      padding: 5px 12px; cursor: pointer;
      display: inline-flex; align-items: center; gap: 6px;
    }
    .jump-chip:hover { border-color: var(--primary); color: var(--primary-dark);
                       background: var(--primary-bg); }
    .jump-dot { width: 9px; height: 9px; border-radius: 99px;
                border: 1px solid rgba(0,0,0,.15); flex-shrink: 0; }

    /* ── Resize handle ── */
    .resize-handle {
      width: 6px; cursor: col-resize;
      background: var(--slate-200); border-radius: 3px; align-self: stretch;
    }
    .resize-handle:hover { background: var(--primary-light); }

    /* ── Sidebar ── */
    .info-panel {
      position: relative; background: white;
      border-radius: 14px; border: 1px solid var(--slate-200);
      max-height: 620px; overflow-y: auto; overflow-x: hidden;
      box-shadow: var(--shadow); margin-left: 12px;
    }

    /* ── Panel toggle ── */
    .panel-toggle-btn {
      position: absolute; left: -34px; top: 12px;
      width: 26px; height: 30px; background: white;
      border: 1px solid var(--slate-200); border-radius: 6px 0 0 6px; border-right: none;
      cursor: pointer; font-size: 17px; color: var(--slate-400); z-index: 1000;
      display: flex; align-items: center; justify-content: center;
      transition: color 0.15s, background 0.15s;
    }
    .panel-toggle-btn:hover { color: var(--primary); background: var(--primary-bg); }

    /* ── Welcome panel ── */
    .welcome-wrap { padding: 22px; }
    .welcome-title { font-size: 1.05rem; font-weight: 700; color: var(--primary-dark); margin-bottom: 8px; }
    .welcome-body  { font-size: 0.82rem; line-height: 1.65; color: var(--slate-600); }
    .cat-count { display: flex; align-items: center; gap: 8px; margin-bottom: 10px;
                 font-size: 0.78rem; font-weight: 600; color: var(--slate-700); }
    .welcome-body + .welcome-body { margin-top: 8px; }

    /* ── Legend: compact control docked inside the map, so it stays
       visible while a state report is open ── */
    .map-legend {
      background: rgba(255,255,255,.94); border: 1px solid var(--slate-200);
      border-radius: 9px; padding: 9px 11px; box-shadow: var(--shadow);
      backdrop-filter: blur(3px); max-width: 260px;
    }
    .map-legend .legend-title {
      font-size: 0.6rem; font-weight: 700; text-transform: uppercase;
      letter-spacing: .07em; color: var(--slate-400); margin-bottom: 6px;
    }
    .legend-item { display: flex; align-items: flex-start; gap: 7px; margin-bottom: 5px; }
    .legend-item:last-child { margin-bottom: 0; }
    .legend-swatch { width: 12px; height: 12px; border-radius: 3px; flex-shrink: 0;
                     margin-top: 2px; border: 1px solid rgba(0,0,0,.18); }
    .legend-label { font-size: 0.72rem; color: var(--slate-700); line-height: 1.3; font-weight: 600; }
    .legend-count { font-weight: 400; color: var(--slate-500); }

    /* ── Status explainer cards (welcome panel) ── */
    .status-guide { display: flex; flex-direction: column; gap: 9px; margin-top: 12px; }
    .status-card {
      border: 1px solid var(--slate-200); border-left-width: 5px;
      border-radius: 8px; padding: 10px 12px; background: var(--slate-50);
    }
    .status-card.both { border-left-color: var(--st-both); }
    .status-card.cs   { border-left-color: var(--st-cs); }
    .status-card.none { border-left-color: var(--st-none); }
    .status-card-head {
      display: flex; align-items: baseline; justify-content: space-between; gap: 8px;
      font-size: 0.8rem; font-weight: 700; color: var(--slate-800); margin-bottom: 4px;
    }
    .status-card-count { font-size: 0.7rem; font-weight: 600; color: var(--slate-500);
                         white-space: nowrap; }
    .status-card-rule { font-size: 0.68rem; font-weight: 600; color: var(--primary);
                        margin-bottom: 5px; }
    .status-card-desc { font-size: 0.73rem; line-height: 1.55; color: var(--slate-600); }

    /* ══════════════════════════════════════
       STATE REPORT PANEL
       ══════════════════════════════════════ */
    .state-report { padding: 0; }

    /* Sticky header bar */
    .report-header {
      position: sticky; top: 0; z-index: 10;
      background: var(--primary-dark); color: white;
      padding: 14px 18px 13px; border-radius: 13px 13px 0 0;
    }
    .report-back {
      display: inline-flex; align-items: center; gap: 5px;
      background: none; border: none; cursor: pointer;
      color: var(--primary-bg2); font-size: 0.75rem; font-family: inherit;
      padding: 0; margin-bottom: 8px; opacity: .85;
    }
    .report-back:hover { opacity: 1; }
    .report-state-name { font-size: 1.3rem; font-weight: 700; line-height: 1.2; }
    .report-status-badge {
      display: inline-block; margin-top: 7px;
      padding: 3px 10px; border-radius: 99px;
      font-size: 0.68rem; font-weight: 700; text-transform: uppercase; letter-spacing: .06em;
      color: #06281a;
    }
    /* Two explicit yes/no pills: community solar vs. community ownership */
    .report-pills { display: flex; gap: 6px; flex-wrap: wrap; margin-top: 9px; }
    .report-pill {
      display: inline-flex; align-items: center; gap: 6px;
      background: rgba(255,255,255,.13); border: 1px solid rgba(255,255,255,.22);
      border-radius: 7px; padding: 4px 9px;
      font-size: 0.68rem; font-weight: 600; color: #d9f5ef;
    }
    .report-pill b { font-weight: 700; }
    .pill-yes b { color: #7ee2b0; }
    .pill-no  b { color: #ffc0b8; }

    /* Report body */
    .report-body { padding: 14px 16px 18px; display: flex; flex-direction: column; gap: 16px; }

    /* Section heading (above fact sheet / details) */
    .fact-title {
      font-size: 0.66rem; font-weight: 700; text-transform: uppercase;
      letter-spacing: .08em; color: var(--slate-400); margin-bottom: 8px;
    }

    /* ── Community ownership landscape (always open, top of report) ── */
    .landscape-box {
      border: 1px solid var(--slate-300); border-left: 5px solid var(--primary);
      border-radius: 10px; padding: 12px 14px; background: var(--primary-bg);
    }
    .landscape-box .fact-title { color: var(--primary); }
    .detail-row { grid-template-columns: 116px 1fr; }
    .landscape-box p { font-size: 0.81rem; line-height: 1.65; color: var(--slate-700); }
    .landscape-box p + p { margin-top: 7px; }

    /* ── Policies at a glance ── */
    .policy-list {
      border: 1px solid var(--slate-300); border-radius: 10px; overflow: hidden;
    }
    .policy-item { border-bottom: 1px solid var(--slate-300); }
    .policy-item:last-child { border-bottom: none; }
    .policy-head {
      display: flex; align-items: center; justify-content: space-between; gap: 10px;
      width: 100%; background: var(--slate-200); border: none; font-family: inherit;
      padding: 11px 13px; text-align: left; cursor: default;
    }
    .policy-item.expandable .policy-head { cursor: pointer; }
    .policy-item.expandable .policy-head:hover { background: var(--slate-300); }
    .policy-item.open .policy-head { background: var(--slate-300); }
    .policy-name { font-size: 0.82rem; font-weight: 600; color: var(--slate-800); }
    .policy-right { display: flex; align-items: center; gap: 9px; flex-shrink: 0; }
    .caret {
      color: var(--slate-500); font-size: 0.62rem; width: 9px;
      transition: transform .18s ease; display: inline-block;
    }
    .policy-item.open .caret, .accordion.open .caret { transform: rotate(90deg); }
    .policy-detail { display: none; padding: 12px 13px; background: white;
                     border-top: 1px solid var(--slate-200); }
    .policy-item.open .policy-detail { display: block; }
    .policy-detail p { font-size: 0.8rem; line-height: 1.68; color: var(--slate-600); }
    .policy-detail p + p { margin-top: 8px; }

    /* ── Bullet lists inside prose blocks ── */
    .md-list { list-style: disc; margin: 7px 0 0; padding-left: 20px; }
    .md-list li { line-height: 1.6; margin-bottom: 5px; }
    .md-list li:last-child { margin-bottom: 0; }
    p + .md-list { margin-top: 7px; }
    .policy-detail .md-list li { font-size: 0.8rem; color: var(--slate-600); }
    .acc-body .md-list li { font-size: 0.8rem; color: var(--slate-600); }
    .detail-v .md-list li { font-size: 0.8rem; color: var(--slate-700); }
    .detail-v p + p { margin-top: 6px; }

    /* Yes / No / N/A badge */
    .yn-badge {
      display: inline-block; padding: 2px 9px; border-radius: 99px;
      font-size: 0.66rem; font-weight: 700; text-transform: uppercase;
      letter-spacing: .06em; white-space: nowrap; flex-shrink: 0;
    }
    .yn-yes { background: var(--yes-bg); color: var(--yes-fg); }
    .yn-no  { background: var(--no-bg);  color: var(--no-fg); }
    .yn-na  { background: var(--na-bg);  color: var(--na-fg); }

    /* ── Program details (key / value) ── */
    .detail-rows { display: flex; flex-direction: column; gap: 10px; }
    .detail-row {
      display: grid; grid-template-columns: 104px 1fr; gap: 12px; align-items: baseline;
    }
    .detail-k {
      font-size: 0.66rem; font-weight: 700; text-transform: uppercase;
      letter-spacing: .05em; color: var(--primary);
    }
    .detail-v { font-size: 0.8rem; line-height: 1.6; color: var(--slate-700); }

    /* ── Collapsible accordions ── */
    .accordion { border: 1px solid var(--slate-300); border-radius: 10px; overflow: hidden; }
    .acc-head {
      display: flex; align-items: center; justify-content: space-between; gap: 10px;
      width: 100%; background: var(--slate-200); border: none; font-family: inherit;
      padding: 11px 13px; text-align: left; cursor: pointer;
      font-size: 0.8rem; font-weight: 600; color: var(--slate-800);
    }
    .acc-head:hover { background: var(--slate-300); color: var(--primary-xdark); }
    .accordion.open .acc-head { background: var(--slate-300); }
    .acc-body { display: none; padding: 12px 13px; background: white;
                border-top: 1px solid var(--slate-200); }
    .accordion.open .acc-body { display: block; }
    .acc-body p { font-size: 0.8rem; line-height: 1.7; color: var(--slate-600); }
    .acc-body p + p { margin-top: 9px; }

    /* Sources */
    .sources-list { list-style: none; padding: 0; }
    .sources-list li { margin-bottom: 8px; }
    .sources-list li:last-child { margin-bottom: 0; }
    .sources-list a {
      font-size: 0.78rem; color: var(--primary); text-decoration: none;
      line-height: 1.45; display: block;
    }
    .sources-list a:hover { text-decoration: underline; }

    /* ══════════════════════════════════════
       LIST / DATABASE VIEW
       ══════════════════════════════════════ */
    .list-toolbar {
      display: flex; align-items: center; gap: 10px; flex-wrap: wrap;
      margin-bottom: 12px;
    }
    .search-input {
      font-family: inherit; font-size: 0.82rem; color: var(--slate-800);
      border: 1px solid var(--slate-300); border-radius: 8px;
      padding: 8px 12px; min-width: 290px; background: white;
    }
    .search-input:focus { outline: 2px solid var(--primary-light); outline-offset: -1px; }
    .filter-select {
      font-family: inherit; font-size: 0.82rem; color: var(--slate-800); background: white;
      border: 1px solid var(--slate-300); border-radius: 8px; padding: 8px 10px;
    }
    .btn {
      font-family: inherit; font-size: 0.78rem; font-weight: 600; cursor: pointer;
      background: white; color: var(--slate-600);
      border: 1px solid var(--slate-300); border-radius: 8px; padding: 8px 13px;
    }
    .btn:hover { border-color: var(--primary); color: var(--primary-dark); background: var(--primary-bg); }
    .list-count { font-size: 0.78rem; color: var(--slate-500); margin-left: auto; }

    .table-wrap {
      background: white; border: 1px solid var(--slate-200); border-radius: 12px;
      box-shadow: var(--shadow); overflow-x: auto; margin-bottom: 14px;
    }
    table.db { border-collapse: collapse; width: 100%; min-width: 620px; }
    table.db thead th {
      position: sticky; top: 0; z-index: 2;
      background: white; text-align: left;
      font-size: 0.63rem; font-weight: 600; text-transform: uppercase; letter-spacing: .07em;
      color: var(--slate-400); padding: 12px 14px 10px;
      border-bottom: 1px solid var(--slate-200);
      white-space: nowrap; cursor: pointer; user-select: none;
    }
    table.db thead th.num { text-align: center; }
    table.db thead th:hover { color: var(--primary); }
    table.db thead th .sort-arrow { color: var(--primary); font-size: 0.55rem; margin-left: 4px; }
    table.db tbody tr { cursor: pointer; }
    table.db tbody tr + tr td { border-top: 1px solid var(--slate-100); }
    table.db tbody tr:hover td { background: var(--primary-bg); }
    table.db td { padding: 11px 14px; font-size: 0.81rem; color: var(--slate-700);
                  vertical-align: middle; }
    table.db td.num { text-align: center; }
    td.db-name { font-weight: 600; color: var(--slate-900); white-space: nowrap; }
    .mk-yes { font-weight: 600; color: var(--yes-fg); }
    .mk-no  { color: var(--slate-400); }
    .db-status {
      display: inline-flex; align-items: center; gap: 8px;
      font-size: 0.78rem; color: var(--slate-600); white-space: nowrap;
    }
    .db-dot { width: 9px; height: 9px; border-radius: 99px; flex-shrink: 0; }
    .db-empty { padding: 26px; text-align: center; color: var(--slate-500); font-size: 0.85rem; }


    /* ── Footer ── */
    footer {
      font-size: 0.72rem; color: var(--slate-400);
      text-align: center; padding: 14px 0;
      border-top: 1px solid var(--slate-200);
    }
    footer a { color: var(--slate-400); }

    /* ── Leaflet override ── */
    .leaflet-container { font-family: 'Inter', sans-serif; background: #d4dadc; }

    @media (max-width: 900px) {
      .main-content, .main-content.panel-collapsed { grid-template-columns: 1fr !important; }
      .resize-handle { display: none; }
      #map { margin-right: 0; height: 440px; }
      .info-panel { margin-left: 0; margin-top: 12px; max-height: none; }
      .panel-toggle-btn { display: none; }
    }
  </style>
</head>
<body>
<div class="container">
  <header>
    <h1>A Review of State Community Solar and Community-owned Solar Policies</h1>
  </header>

  <div class="view-tabs">
    <button class="view-tab active" data-view="map"  onclick="setView('map')">Map</button>
    <button class="view-tab"        data-view="list" onclick="setView('list')">List</button>
  </div>

  <!-- ═══════════ MAP VIEW ═══════════ -->
  <section id="view-map" class="view active">
    <div class="layer-bar">
      <span class="layer-bar-label">Show on map</span>
      <div class="segmented" id="layer-seg">
        <button class="seg-btn active" data-layer="overall" onclick="setLayer('overall')">Overall status</button>
        <button class="seg-btn" data-layer="vnm"   onclick="setLayer('vnm')">Virtual or Remote Net Metering</button>
        <button class="seg-btn" data-layer="cs"    onclick="setLayer('cs')">Community Solar</button>
        <button class="seg-btn" data-layer="other" onclick="setLayer('other')">Other State Support for Community-Owned Solar</button>
      </div>
    </div>

    <div class="main-content" id="main-content">
      <div id="map"></div>
      <div class="resize-handle" id="resize-handle"></div>
      <div id="info-panel" class="info-panel">
        <button id="panel-toggle" class="panel-toggle-btn" title="Collapse panel">&#8250;</button>
        <div id="panel-content"></div>
      </div>
    </div>

    <div class="jump-bar" id="jump-bar">
      <span class="jump-label">Jump to</span>
    </div>
  </section>

  <!-- ═══════════ LIST VIEW ═══════════ -->
  <section id="view-list" class="view">
    <div class="list-toolbar">
      <input type="search" id="list-search" class="search-input"
             placeholder="Search jurisdictions and policy text&hellip;" oninput="renderList()">
      <select id="filter-status" class="filter-select" onchange="renderList()">
        <option value="">All statuses</option>
        <option value="both">CS + community ownership</option>
        <option value="cs">Community solar only &mdash; limited</option>
        <option value="none">No enabling policies</option>
      </select>
      <select id="filter-type" class="filter-select" onchange="renderList()">
        <option value="">States, DC &amp; territories</option>
        <option value="State">States only</option>
        <option value="District">District of Columbia</option>
        <option value="Territory">Territories only</option>
      </select>
      <button class="btn" onclick="downloadCsv()">Download CSV</button>
      <span class="list-count" id="list-count"></span>
    </div>
    <div class="table-wrap">
      <table class="db">
        <thead>
          <tr>
            <th onclick="sortList('name')">Jurisdiction<span class="sort-arrow" id="sa-name"></span></th>
            <th onclick="sortList('status')">Overall status<span class="sort-arrow" id="sa-status"></span></th>
            <th class="num" onclick="sortList('vnm')">Virtual or Remote<br>Net Metering<span class="sort-arrow" id="sa-vnm"></span></th>
            <th class="num" onclick="sortList('cs')">Community<br>Solar<span class="sort-arrow" id="sa-cs"></span></th>
            <th class="num" onclick="sortList('other')">Other State Support for<br>Community-Owned Solar<span class="sort-arrow" id="sa-other"></span></th>
          </tr>
        </thead>
        <tbody id="list-body"></tbody>
      </table>
    </div>
  </section>

  <footer>
    <strong>Renewable Energy Clinic</strong> &nbsp;|&nbsp; Updated as of June 14, 2026 &nbsp;|&nbsp;
    Map boundaries: <a href="https://github.com/notAidven/community-solar-map" target="_blank">notAidven/community-solar-map</a>
  </footer>
</div>

<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
<script>
"""

html += "/* ── DATA A: STATES_DATA ── */\n"
html += states_data_js + "\n\n"
html += "/* ── DATA B: STATE_REPORTS ── */\n"
html += state_reports_js + "\n\n"

html += r"""
/* ════════════════════════════════════
   CLASSIFICATION
   ════════════════════════════════════

   Community solar and community-owned solar are NOT the same thing, so the
   overall status is derived from the two distinct "yes or no" categories on
   each state's page in the report:

     · Community Solar                          -> pol.cs
     · Other State Support for Community-Owned
       Solar                                    -> pol.other

   both  = the state answers Yes to both, i.e. community solar exists AND the
           state directs funding or an incentive structure toward community
           ownership.
   cs    = community solar (or the virtual/remote net metering that underpins
           it) exists, but nothing in state policy supports community
           OWNERSHIP -> limited.
   none  = No to all three categories. "No data" is folded in here, so the map
           uses exactly three colours.
   ════════════════════════════════════ */

const TERRITORIES = {
  'American Samoa': 1,
  'Guam': 1,
  'Commonwealth of the Northern Mariana Islands': 1,
  'Puerto Rico': 1,
  'United States Virgin Islands': 1
};
/* Short labels for the chips and the table; the keys above stay canonical. */
const DISPLAY_NAME = {
  'Commonwealth of the Northern Mariana Islands': 'Northern Mariana Islands',
  'United States Virgin Islands': 'US Virgin Islands',
  'District of Columbia': 'Washington, DC'
};
/* Jurisdictions the continental view cannot show at a clickable size;
   reachable via the chip row under the map. */
const OFF_MAP = [
  'Alaska', 'Hawaii', 'District of Columbia', 'Puerto Rico',
  'United States Virgin Islands', 'Guam', 'American Samoa',
  'Commonwealth of the Northern Mariana Islands'
];

function disp(name) { return DISPLAY_NAME[name] || name; }
function jType(name) {
  if (TERRITORIES[name]) return 'Territory';
  if (name === 'District of Columbia') return 'District';
  return 'State';
}
function isYes(p) { return !!(p && p.status === 'Yes'); }

function overallStatus(name) {
  const r = STATE_REPORTS[name];
  if (!r || !r.policies) return 'none';
  const p = r.policies;
  if (isYes(p.cs) && isYes(p.other)) return 'both';
  if (isYes(p.cs) || isYes(p.vnm))   return 'cs';
  return 'none';
}

/* Labels are the report's own category names; each status is stated as the
   yes/no rule that produces it, so nothing here is editorial. */
const STATUS_META = {
  both: {
    color: '#14713d',
    short: 'CS + community ownership',
    rule:  'Community Solar: Yes  \u00b7  Other State Support for Community-Owned Solar: Yes'
  },
  cs: {
    color: '#e2711d',
    short: 'Community solar only \u2014 limited',
    rule:  'Community Solar or Virtual or Remote Net Metering: Yes  \u00b7  '
         + 'Other State Support for Community-Owned Solar: No'
  },
  none: {
    color: '#c3ccd4',
    short: 'No enabling policies',
    rule:  'No to all three categories'
  }
};

/* Single-category layers: the three "yes or no" columns from the report, in
   the colours used for Figs. 1-3. Each `note` is quoted from Key Findings. */
const CATEGORY_META = {
  vnm: {
    key: 'vnm', color: '#2e7d32', title: 'Virtual or Remote Net Metering',
    note: 'Virtual net metering is a bill-crediting system for community solar. When '
        + 'community solar projects generate power that\u2019s not used on site, it\u2019s fed '
        + 'back into the grid, generating net metering credits that are shared among '
        + 'subscribers based on their share of the array. These credits reduce '
        + 'subscribers\u2019 electricity bills.'
  },
  cs: {
    key: 'cs', color: '#1f5fa8', title: 'Community Solar',
    note: 'Enabling policies may include state laws that require utilities to allow the '
        + 'creation of community solar programs (Alaska) or more direct incentives, such as '
        + 'offering low-income households a 20% discount to participate in a community '
        + 'solar project (California). Inhibiting policies may include exceptions to state '
        + 'recommendations, such as allowing utilities to decline to participate in a '
        + 'community solar program (Arizona).'
  },
  other: {
    key: 'other', color: '#dfa008', title: 'Other State Support for Community-Owned Solar',
    note: 'On each state\u2019s page, this category is marked \u201cyes\u201d only if there is '
        + 'funding or an incentive structure directed by that state\u2019s government.'
  }
};
const OFF_COLOR = '#c3ccd4';

const ALL_NAMES = Object.keys(STATE_REPORTS).sort();

function statusCounts() {
  const c = { both: 0, cs: 0, none: 0 };
  ALL_NAMES.forEach(function(n) { c[overallStatus(n)]++; });
  return c;
}
function categoryCount(key) {
  return ALL_NAMES.filter(function(n) {
    return isYes((STATE_REPORTS[n].policies || {})[key]);
  }).length;
}

/* ════════════════════════════════════
   MAP
   ════════════════════════════════════ */
let currentLayerKey = 'overall';

function fillFor(name) {
  if (currentLayerKey === 'overall') return STATUS_META[overallStatus(name)].color;
  const r = STATE_REPORTS[name];
  const p = (r && r.policies) || {};
  return isYes(p[currentLayerKey]) ? CATEGORY_META[currentLayerKey].color : OFF_COLOR;
}

function styleState(feature) {
  return {
    fillColor: fillFor(feature.properties.NAME),
    weight: 0.9, opacity: 1, color: '#ffffff', fillOpacity: 0.9
  };
}

if (typeof L === 'undefined') {
  document.getElementById('map').textContent = 'Map library failed to load.';
  throw new Error('Leaflet missing');
}

const map = L.map('map', { zoomSnap: 0.5 });
L.tileLayer('https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png?key=cb1_2j66_1_bdc1c1c1638e90dfd3765aa1', {
  attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>',
  subdomains: 'abcd', maxZoom: 19
}).addTo(map);

let geojsonLayer, activeLayer = null;
const LAYER_BY_NAME = {};

geojsonLayer = L.geoJSON(STATES_DATA, {
  style: styleState,
  onEachFeature: onEachFeature
}).addTo(map);

const HOME_VIEW = { center: [38.5, -96], zoom: 4 };
map.setView(HOME_VIEW.center, HOME_VIEW.zoom);

/* Compact legend, docked in the map so it persists across state reports. */
const legendControl = L.control({ position: 'bottomleft' });
legendControl.onAdd = function() {
  const div = L.DomUtil.create('div', 'map-legend');
  div.id = 'map-legend';
  L.DomEvent.disableClickPropagation(div);
  return div;
};
legendControl.addTo(map);

function legendRow(color, label, count) {
  return '<div class="legend-item"><span class="legend-swatch" style="background:' + color
    + '"></span><span class="legend-label">' + label
    + (count === undefined ? '' : ' <span class="legend-count">(' + count + ')</span>')
    + '</span></div>';
}

function renderLegend() {
  const el = document.getElementById('map-legend');
  if (!el) return;
  if (currentLayerKey === 'overall') {
    const c = statusCounts();
    el.innerHTML = '<div class="legend-title">Community solar &amp; community ownership</div>'
      + legendRow(STATUS_META.both.color, STATUS_META.both.short, c.both)
      + legendRow(STATUS_META.cs.color,   STATUS_META.cs.short,   c.cs)
      + legendRow(STATUS_META.none.color, STATUS_META.none.short, c.none);
  } else {
    const m = CATEGORY_META[currentLayerKey];
    const yes = categoryCount(currentLayerKey);
    el.innerHTML = '<div class="legend-title">' + esc(m.title) + '</div>'
      + legendRow(m.color,   'Yes', yes)
      + legendRow(OFF_COLOR, 'No',  ALL_NAMES.length - yes);
  }
}

function setLayer(key) {
  currentLayerKey = key;
  document.querySelectorAll('#layer-seg .seg-btn').forEach(function(b) {
    b.classList.toggle('active', b.dataset.layer === key);
  });
  geojsonLayer.setStyle(styleState);
  if (activeLayer) {
    activeLayer.setStyle({ weight: 3, color: '#0d5d56', fillOpacity: 0.95 });
    activeLayer.bringToFront();
  }
  renderLegend();
  renderJumpBar();
  if (!activeLayer) showWelcome();   // keep the panel's text in step with the map
}

function onEachFeature(feature, layer) {
  const name = feature.properties.NAME;
  LAYER_BY_NAME[name] = layer;
  layer.bindTooltip(disp(name), { sticky: true, direction: 'top', opacity: 0.92 });
  layer.on({
    mouseover: function(e) {
      if (e.target === activeLayer) return;
      e.target.setStyle({ weight: 2.5, color: '#0d5d56', fillOpacity: 1 });
      e.target.bringToFront();
    },
    mouseout: function(e) {
      if (e.target !== activeLayer) geojsonLayer.resetStyle(e.target);
    },
    click: function() { selectState(name, false); }
  });
}

/* Selects a jurisdiction on the map and opens its report. `zoom` is used by
   the off-map chips, since Alaska, Hawaii and the territories sit far outside
   the continental view. */
function selectState(name, zoom) {
  const layer = LAYER_BY_NAME[name];
  if (activeLayer) geojsonLayer.resetStyle(activeLayer);
  if (layer) {
    activeLayer = layer;
    layer.setStyle({ weight: 3, color: '#0d5d56', fillOpacity: 0.95 });
    layer.bringToFront();
    if (zoom) map.fitBounds(layer.getBounds(), { padding: [40, 40], maxZoom: 8 });
  } else {
    activeLayer = null;
  }
  showStateReport(name);
  const mc = document.getElementById('main-content');
  if (mc.classList.contains('panel-collapsed')) {
    mc.classList.remove('panel-collapsed');
    document.getElementById('panel-toggle').innerHTML = '&#8250;';
    setTimeout(function() { map.invalidateSize(); }, 320);
  }
}

/* ── Off-map jurisdiction chips (this is how American Samoa, Guam, the
   Northern Marianas and the USVI become reachable) ── */
function renderJumpBar() {
  const bar = document.getElementById('jump-bar');
  bar.innerHTML = '<span class="jump-label">Jump to</span>'
    + OFF_MAP.map(function(n) {
        return '<button class="jump-chip" onclick="selectState(' + JSON.stringify(n).replace(/"/g, '&quot;') + ', true)">'
          + '<span class="jump-dot" style="background:' + fillFor(n) + '"></span>'
          + esc(disp(n)) + '</button>';
      }).join('')
    + '<button class="jump-chip" onclick="resetMapView()">&#8617; Reset map</button>';
}
function resetMapView() {
  map.setView(HOME_VIEW.center, HOME_VIEW.zoom);
  showWelcome();
}

/* ════════════════════════════════════
   SIDEBAR HELPERS
   ════════════════════════════════════ */
function esc(s) {
  return String(s)
    .replace(/&/g,'&amp;').replace(/</g,'&lt;')
    .replace(/>/g,'&gt;').replace(/"/g,'&quot;');
}

function ynBadge(status) {
  if (!status) return '';
  const cls = { Yes:'yn-yes', No:'yn-no', 'N/A':'yn-na' }[status] || 'yn-na';
  return '<span class="yn-badge ' + cls + '">' + esc(status) + '</span>';
}

// Minimal, safe markdown: escape HTML first, then render **bold**.
function inlineMd(s) {
  return esc(s).replace(/\*\*([^*]+?)\*\*/g, '<strong>$1</strong>');
}
// Render text into <p> paragraphs and <ul> bullet lists, preserving the
// Google Doc's line breaks (each line is its own paragraph; "- " lines are
// grouped into a bulleted list). Inline **bold** is rendered per line.
function blocks(s) {
  const lines = (s || '').split('\n').map(function(l) { return l.trim(); })
                         .filter(Boolean);
  let html = '', items = [];
  function flushList() {
    if (items.length) {
      html += '<ul class="md-list">'
        + items.map(function(t) { return '<li>' + inlineMd(t) + '</li>'; }).join('')
        + '</ul>';
      items = [];
    }
  }
  lines.forEach(function(ln) {
    if (ln.indexOf('- ') === 0) {
      items.push(ln.slice(2));
    } else {
      flushList();
      html += '<p>' + inlineMd(ln) + '</p>';
    }
  });
  flushList();
  return html;
}
// Strip markdown bold for plain-text contexts (table cells, CSV).
function plain(s) { return (s || '').replace(/\*\*/g, '').replace(/\s*\n\s*/g, ' ').trim(); }

// True when a detail value carries real content (not blank / N/A).
function hasVal(v) {
  return v && v.trim() && v.trim().toUpperCase() !== 'N/A';
}

function toggleAccordion(headEl) {
  headEl.parentElement.classList.toggle('open');
}

function accordion(title, bodyHtml) {
  return '<div class="accordion">'
    + '<button type="button" class="acc-head" onclick="toggleAccordion(this)">'
    + '<span>' + esc(title) + '</span><span class="caret">&#9656;</span>'
    + '</button>'
    + '<div class="acc-body">' + bodyHtml + '</div></div>';
}

/* ════════════════════════════════════
   WELCOME PANEL
   ════════════════════════════════════ */
function showWelcome() {
  if (activeLayer) { geojsonLayer.resetStyle(activeLayer); activeLayer = null; }
  const c = statusCounts();

  function statusCard(key, count) {
    const m = STATUS_META[key];
    return '<div class="status-card ' + key + '">'
      + '<div class="status-card-head"><span>' + esc(m.short) + '</span>'
      + '<span class="status-card-count">' + count + '</span></div>'
      + '<div class="status-card-rule">' + esc(m.rule) + '</div></div>';
  }

  const cat = currentLayerKey === 'overall' ? null : CATEGORY_META[currentLayerKey];
  const yes = cat ? categoryCount(currentLayerKey) : 0;
  document.getElementById('panel-content').innerHTML =
    '<div class="welcome-wrap">'
    + (cat
        ? '<div class="fact-title">' + esc(cat.title) + '</div>'
          + '<div class="cat-count"><span class="db-dot" style="background:' + cat.color
            + '"></span>Yes &middot; ' + yes + ' of ' + ALL_NAMES.length + ' jurisdictions</div>'
          + '<p class="welcome-body">' + cat.note + '</p>'
        : '<div class="fact-title">Overall status</div>'
          + '<div class="status-guide">'
          + statusCard('both', c.both)
          + statusCard('cs',   c.cs)
          + statusCard('none', c.none)
          + '</div>')
    + '</div>';
  document.getElementById('info-panel').scrollTop = 0;
}

/* ════════════════════════════════════
   STATE REPORT PANEL
   ════════════════════════════════════ */
function showStateReport(stateName) {
  const r = STATE_REPORTS[stateName] || {};
  const pol     = r.policies || {};
  const det     = r.details  || {};
  const sources = r.sources  || [];
  const key     = overallStatus(stateName);
  const meta    = STATUS_META[key];

  // ── Two explicit pills: community solar is not community ownership ──
  function pill(label, yes) {
    return '<span class="report-pill ' + (yes ? 'pill-yes' : 'pill-no') + '">'
      + esc(label) + ' <b>' + (yes ? 'Yes' : 'No') + '</b></span>';
  }

  // ── Community ownership landscape, shown open at the top ──
  const landscapeHtml = (r.landscape && r.landscape.trim())
    ? '<div class="landscape-box"><div class="fact-title">Community-owned solar landscape</div>'
      + blocks(r.landscape) + '</div>'
    : '';

  // ── Fact sheet: policies at a glance (each row expands its explanation) ──
  function policyItem(name, p) {
    p = p || {};
    const expandable = !!(p.text && p.text.trim());
    return '<div class="policy-item' + (expandable ? ' expandable' : '') + '">'
      + '<button type="button" class="policy-head"'
        + (expandable ? ' onclick="toggleAccordion(this)"' : '') + '>'
      + '<span class="policy-name">' + esc(name) + '</span>'
      + '<span class="policy-right">' + ynBadge(p.status)
        + (expandable ? '<span class="caret">&#9656;</span>' : '') + '</span>'
      + '</button>'
      + (expandable ? '<div class="policy-detail">' + blocks(p.text) + '</div>' : '')
      + '</div>';
  }
  const policiesHtml =
    '<div class="fact-section">'
    + '<div class="fact-title">Enabling/Inhibiting Policies and Programs</div>'
    + '<div class="policy-list">'
    + policyItem('Virtual or Remote Net Metering', pol.vnm)
    + policyItem('Community Solar', pol.cs)
    + policyItem('Other State Support for Community-Owned Solar', pol.other)
    + '</div></div>';

  // ── Fact sheet: program details (only populated rows; hidden if all N/A) ──
  function detailRow(label, v) {
    return hasVal(v)
      ? '<div class="detail-row"><span class="detail-k">' + label + '</span>'
        + '<div class="detail-v">' + blocks(v) + '</div></div>'
      : '';
  }
  const detailRows = detailRow('Size', det.size)
    + detailRow('Eligibility', det.eligibility)
    + detailRow('Benefit Distribution', det.benefitDist);
  // Collapsed by default: for states with an active program this block runs
  // to ~1,000 characters, which swamped the panel when it sat open while
  // every other long section was behind an accordion.
  const detailsHtml = detailRows
    ? accordion('Details regarding enabling/inhibiting policies and programs',
                '<div class="detail-rows">' + detailRows + '</div>')
    : '';

  const citiesHtml = (r.activeCities && r.activeCities.trim())
    ? accordion('Active Cities/Communities', blocks(r.activeCities)) : '';
  const sourcesHtml = sources.length
    ? accordion('References (' + sources.length + ')',
        '<ul class="sources-list">'
        + sources.map(function(s) {
            return '<li><a href="' + esc(s.url) + '" target="_blank" rel="noopener noreferrer">'
              + esc(s.title || s.url) + '</a></li>';
          }).join('')
        + '</ul>')
    : '';

  document.getElementById('panel-content').innerHTML =
    '<div class="state-report">'
    + '<div class="report-header">'
    + '<button class="report-back" onclick="resetMapView()">&#8592; All jurisdictions</button>'
    + '<div class="report-state-name">' + esc(disp(stateName)) + '</div>'
    + '<span class="report-status-badge" style="background:' + meta.color
      + (key === 'none' ? ';color:#33414c' : ';color:#ffffff') + '">'
      + esc(meta.short) + '</span>'
    + '<div class="report-pills">'
      + pill('Community Solar', isYes(pol.cs))
      + pill('Other State Support for Community-Owned Solar', isYes(pol.other))
      + pill('Virtual or Remote Net Metering', isYes(pol.vnm))
    + '</div>'
    + '</div>'
    + '<div class="report-body">'
    + landscapeHtml
    + policiesHtml
    + detailsHtml
    + citiesHtml
    + sourcesHtml
    + '</div></div>';

  document.getElementById('info-panel').scrollTop = 0;
}

/* ════════════════════════════════════
   VIEW SWITCHING
   ════════════════════════════════════ */
function setView(v) {
  document.querySelectorAll('.view').forEach(function(s) {
    s.classList.toggle('active', s.id === 'view-' + v);
  });
  document.querySelectorAll('.view-tab').forEach(function(b) {
    b.classList.toggle('active', b.dataset.view === v);
  });
  if (v === 'map') setTimeout(function() { map.invalidateSize(); }, 30);
  if (v === 'list') renderList();
  window.scrollTo({ top: 0 });
}

/* ════════════════════════════════════
   LIST / DATABASE VIEW
   ════════════════════════════════════ */
let sortKey = 'name', sortDir = 1;
const STATUS_ORDER = { both: 0, cs: 1, none: 2 };

function listRows() {
  return ALL_NAMES.map(function(n) {
    const r = STATE_REPORTS[n], p = r.policies || {};
    return {
      name: n,
      label: disp(n),
      type: jType(n),
      status: overallStatus(n),
      vnm: isYes(p.vnm) ? 'Yes' : 'No',
      cs:  isYes(p.cs)  ? 'Yes' : 'No',
      other: isYes(p.other) ? 'Yes' : 'No',
      landscape: plain(r.landscape),
      haystack: (n + ' ' + plain(r.landscape) + ' ' + plain(p.vnm && p.vnm.text)
                 + ' ' + plain(p.cs && p.cs.text) + ' ' + plain(p.other && p.other.text)
                 + ' ' + plain(r.activeCities)).toLowerCase()
    };
  });
}

function filteredRows() {
  const q  = document.getElementById('list-search').value.trim().toLowerCase();
  const fs = document.getElementById('filter-status').value;
  const ft = document.getElementById('filter-type').value;
  let rows = listRows().filter(function(row) {
    if (fs && row.status !== fs) return false;
    if (ft && row.type !== ft) return false;
    if (q && row.haystack.indexOf(q) === -1) return false;
    return true;
  });
  rows.sort(function(a, b) {
    let av, bv;
    if (sortKey === 'status') { av = STATUS_ORDER[a.status]; bv = STATUS_ORDER[b.status]; }
    else { av = String(a[sortKey === 'name' ? 'label' : sortKey]).toLowerCase();
           bv = String(b[sortKey === 'name' ? 'label' : sortKey]).toLowerCase(); }
    if (av < bv) return -1 * sortDir;
    if (av > bv) return  1 * sortDir;
    return a.label < b.label ? -1 : 1;
  });
  return rows;
}

function sortList(key) {
  if (sortKey === key) sortDir = -sortDir; else { sortKey = key; sortDir = 1; }
  renderList();
}

function renderList() {
  const rows = filteredRows();
  ['name','status','vnm','cs','other'].forEach(function(k) {
    const el = document.getElementById('sa-' + k);
    if (el) el.textContent = (sortKey === k) ? (sortDir === 1 ? '▲' : '▼') : '';
  });
  const body = document.getElementById('list-body');
  document.getElementById('list-count').textContent =
    rows.length + ' of ' + ALL_NAMES.length + ' jurisdictions';
  if (!rows.length) {
    body.innerHTML = '<tr><td colspan="5" class="db-empty">No jurisdictions match those filters.</td></tr>';
    return;
  }
  function mark(v) {
    return v === 'Yes' ? '<span class="mk-yes">Yes</span>' : '<span class="mk-no">No</span>';
  }
  body.innerHTML = rows.map(function(row) {
    const m = STATUS_META[row.status];
    return '<tr onclick="openFromList(' + JSON.stringify(row.name).replace(/"/g, '&quot;') + ')">'
      + '<td class="db-name">' + esc(row.label) + '</td>'
      + '<td><span class="db-status"><span class="db-dot" style="background:' + m.color + '"></span>'
        + esc(m.short) + '</span></td>'
      + '<td class="num">' + mark(row.vnm) + '</td>'
      + '<td class="num">' + mark(row.cs) + '</td>'
      + '<td class="num">' + mark(row.other) + '</td>'
      + '</tr>';
  }).join('');
}

function openFromList(name) {
  setView('map');
  setTimeout(function() { selectState(name, !!LAYER_BY_NAME[name] && OFF_MAP.indexOf(name) !== -1); }, 60);
}

function downloadCsv() {
  const rows = filteredRows();
  const head = ['Jurisdiction','Type','Overall status',
                'Virtual or Remote Net Metering','Community Solar',
                'Other State Support for Community-Owned Solar',
                'Community-owned solar landscape'];
  function q(v) { return '"' + String(v === undefined || v === null ? '' : v).replace(/"/g, '""') + '"'; }
  const csv = [head.map(q).join(',')].concat(rows.map(function(r) {
    return [r.label, r.type, STATUS_META[r.status].short, r.vnm, r.cs, r.other, r.landscape]
      .map(q).join(',');
  })).join('\r\n');
  const url = URL.createObjectURL(new Blob(['﻿' + csv], { type: 'text/csv;charset=utf-8;' }));
  const a = document.createElement('a');
  a.href = url; a.download = 'community_solar_state_policies.csv';
  document.body.appendChild(a); a.click(); document.body.removeChild(a);
  setTimeout(function() { URL.revokeObjectURL(url); }, 1000);
}

/* ════════════════════════════════════
   PANEL TOGGLE
   ════════════════════════════════════ */
document.getElementById('panel-toggle').addEventListener('click', function() {
  const mc = document.getElementById('main-content');
  const collapsed = mc.classList.toggle('panel-collapsed');
  this.innerHTML = collapsed ? '&#8249;' : '&#8250;';
  this.title = collapsed ? 'Expand panel' : 'Collapse panel';
  setTimeout(function() { map.invalidateSize(); }, 320);
});

/* ════════════════════════════════════
   DRAG-TO-RESIZE
   ════════════════════════════════════ */
(function() {
  const handle = document.getElementById('resize-handle');
  const mc     = document.getElementById('main-content');
  let dragging = false, startX = 0, startLeft = 0;
  handle.addEventListener('mousedown', e => {
    dragging  = true;
    startX    = e.clientX;
    startLeft = parseFloat(getComputedStyle(mc).gridTemplateColumns.split(' ')[0]);
    document.body.style.cursor = 'col-resize';
    e.preventDefault();
  });
  document.addEventListener('mousemove', e => {
    if (!dragging) return;
    const newLeft = Math.max(300, Math.min(mc.offsetWidth - 280, startLeft + e.clientX - startX));
    mc.style.gridTemplateColumns = newLeft + 'px 6px 1fr';
    map.invalidateSize();
  });
  document.addEventListener('mouseup', () => {
    if (dragging) { dragging = false; document.body.style.cursor = ''; }
  });
})();

/* Init */
renderLegend();
renderJumpBar();
showWelcome();
renderList();
</script>
</body>
</html>"""

# Write both the canonical page name and index.html so the site's root URL
# (https://<user>.github.io/<repo>/) serves the map directly instead of 404ing.
for out_name in ('community_solar_reports.html', 'index.html'):
    with open(out_name, 'w', encoding='utf-8') as f:
        f.write(html)

import os
size = os.path.getsize('index.html')
print(f'Built community_solar_reports.html + index.html  ({size:,} bytes / {size/1024:.0f} KB)')
