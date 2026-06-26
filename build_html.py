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
  <title>Community Solar State Reports</title>
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
      --teal-300:       #5eead4;
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
    header { margin-bottom: 18px; display: flex; align-items: baseline; gap: 16px; flex-wrap: wrap; }
    header h1 { font-size: 1.4rem; font-weight: 700; color: var(--primary-dark); }
    header .subtitle { color: var(--slate-500); font-size: 0.85rem; }

    /* ── Main grid ── */
    .main-content {
      display: grid;
      grid-template-columns: 1.8fr 6px 1fr;
      gap: 0;
      margin-bottom: 20px;
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
    .welcome-wrap { padding: 24px; }
    .welcome-icon { font-size: 2rem; margin-bottom: 10px; }
    .welcome-title { font-size: 1.05rem; font-weight: 700; color: var(--primary-dark); margin-bottom: 8px; }
    .welcome-body  { font-size: 0.82rem; line-height: 1.65; color: var(--slate-600); }
    .count-pills   { margin-top: 14px; display: flex; gap: 8px; flex-wrap: wrap; }
    .count-pill {
      border-radius: 99px; padding: 4px 13px;
      font-size: 0.75rem; font-weight: 600;
    }
    .count-pill.active  { background: var(--primary-bg);  color: var(--primary-dark); }
    .count-pill.limited { background: #f0fdfa; color: #0d9488; }
    .count-pill.none    { background: var(--slate-100); color: var(--slate-500); }

    /* ── Legend ── */
    .legend {
      margin-top: 14px; padding: 12px 14px;
      background: var(--slate-50); border-radius: 10px; border: 1px solid var(--slate-200);
    }
    .legend-title { font-size: 0.7rem; font-weight: 700; text-transform: uppercase;
                    letter-spacing: .06em; color: var(--slate-400); margin-bottom: 8px; }
    .legend-row { display: flex; align-items: center; gap: 8px; font-size: 0.78rem;
                  color: var(--slate-600); margin-bottom: 5px; }
    .legend-swatch { width: 13px; height: 13px; border-radius: 3px; flex-shrink: 0;
                     border: 1px solid rgba(0,0,0,.1); }

    /* ══════════════════════════════════════
       STATE REPORT PANEL
       ══════════════════════════════════════ */
    .state-report { padding: 0; }

    /* Sticky header bar */
    .report-header {
      position: sticky; top: 0; z-index: 10;
      background: var(--primary-dark); color: white;
      padding: 14px 18px 12px; border-radius: 13px 13px 0 0;
    }
    .report-back {
      display: inline-flex; align-items: center; gap: 5px;
      background: none; border: none; cursor: pointer;
      color: var(--primary-bg2); font-size: 0.75rem; font-family: inherit;
      padding: 0; margin-bottom: 8px; opacity: .85;
    }
    .report-back:hover { opacity: 1; }
    .report-state-name {
      font-size: 1.3rem; font-weight: 700; line-height: 1.2;
    }
    .report-status-badge {
      display: inline-block; margin-top: 6px;
      padding: 2px 10px; border-radius: 99px;
      font-size: 0.68rem; font-weight: 700; text-transform: uppercase; letter-spacing: .07em;
    }
    .badge-active  { background: rgba(255,255,255,.2); color: #a7f3d0; }
    .badge-limited { background: rgba(255,255,255,.15); color: #99f6e4; }
    .badge-none    { background: rgba(255,255,255,.1); color: #cbd5e1; }

    /* Report body */
    .report-body { padding: 16px 18px 20px; }

    /* Section card */
    .section-card {
      border: 1px solid var(--slate-200);
      border-radius: 10px;
      margin-bottom: 12px;
      overflow: hidden;
    }
    .section-title {
      background: var(--primary-bg);
      padding: 8px 14px;
      font-size: 0.7rem; font-weight: 700; text-transform: uppercase;
      letter-spacing: .07em; color: var(--primary-dark);
      border-bottom: 1px solid var(--primary-bg2);
    }
    .section-body { padding: 12px 14px; }

    /* Landscape narrative */
    .landscape-text {
      font-size: 0.82rem; line-height: 1.72; color: var(--slate-700);
    }

    /* Policy rows */
    .policy-row {
      display: grid; grid-template-columns: 1fr auto;
      gap: 10px; align-items: start;
      padding: 8px 0; border-bottom: 1px solid var(--slate-100);
    }
    .policy-row:last-child { border-bottom: none; padding-bottom: 0; }
    .policy-row-left { }
    .policy-feature {
      font-size: 0.75rem; font-weight: 600; color: var(--slate-700);
      margin-bottom: 3px;
    }
    .policy-text {
      font-size: 0.78rem; line-height: 1.65; color: var(--slate-600);
    }
    .policy-text em { font-style: italic; color: var(--slate-400); }

    /* Yes / No / N/A badge */
    .yn-badge {
      display: inline-block; padding: 2px 9px; border-radius: 99px;
      font-size: 0.68rem; font-weight: 700; text-transform: uppercase;
      letter-spacing: .06em; white-space: nowrap; flex-shrink: 0;
    }
    .yn-yes { background: var(--yes-bg); color: var(--yes-fg); }
    .yn-no  { background: var(--no-bg);  color: var(--no-fg); }
    .yn-na  { background: var(--na-bg);  color: var(--na-fg); }

    /* Detail rows (size / eligibility / benefit) */
    .detail-grid {
      display: grid; grid-template-columns: 1fr; gap: 8px;
    }
    .detail-item {}
    .detail-label {
      font-size: 0.68rem; font-weight: 700; text-transform: uppercase;
      letter-spacing: .07em; color: var(--primary); margin-bottom: 2px;
    }
    .detail-value {
      font-size: 0.8rem; line-height: 1.65; color: var(--slate-700);
    }
    .detail-value.na { color: var(--slate-400); font-style: italic; }

    /* Active cities */
    .cities-text {
      font-size: 0.8rem; line-height: 1.7; color: var(--slate-700);
    }

    /* Sources */
    .sources-list { list-style: none; padding: 0; }
    .sources-list li { margin-bottom: 5px; }
    .sources-list a {
      font-size: 0.76rem; color: var(--primary); text-decoration: none;
      word-break: break-all; line-height: 1.4; display: block;
    }
    .sources-list a:hover { text-decoration: underline; }

    /* ── Footer ── */
    footer {
      font-size: 0.72rem; color: var(--slate-400);
      text-align: center; padding: 14px 0;
      border-top: 1px solid var(--slate-200);
    }
    footer a { color: var(--slate-400); }

    /* ── Leaflet override ── */
    .leaflet-container { font-family: 'Inter', sans-serif; }
  </style>
</head>
<body>
<div class="container">
  <header>
    <h1>Community Solar State Reports</h1>
    <span class="subtitle">Click any state to view its COS policy report.</span>
  </header>

  <div class="main-content" id="main-content">
    <div id="map"></div>
    <div class="resize-handle" id="resize-handle"></div>
    <div id="info-panel" class="info-panel">
      <button id="panel-toggle" class="panel-toggle-btn" title="Collapse panel">&#8250;</button>
      <div id="panel-content"></div>
    </div>
  </div>

  <footer>
    Community solar policy data from <em>Report Draft</em> &mdash; MIT Energy Initiative &nbsp;|&nbsp;
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
   MAP
   ════════════════════════════════════ */
const STATUS_COLORS = {
  active:  '#0f766e',
  limited: '#14b8a6',
  none:    '#99f6e4',
  unknown: '#94a3b8'
};

function getStateColor(name) {
  const r = STATE_REPORTS[name];
  return STATUS_COLORS[r ? r.status : 'unknown'] || STATUS_COLORS.limited;
}

function styleState(feature) {
  return {
    fillColor: getStateColor(feature.properties.NAME),
    weight: 0.8, opacity: 1, color: '#ffffff', fillOpacity: 0.82
  };
}

if (typeof L === 'undefined') {
  document.getElementById('map').textContent = 'Map library failed to load.';
  throw new Error('Leaflet missing');
}

const map = L.map('map', { zoomSnap: 0.5 });
L.tileLayer('https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png', {
  attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>',
  subdomains: 'abcd', maxZoom: 19
}).addTo(map);

let geojsonLayer, activeLayer = null;

geojsonLayer = L.geoJSON(STATES_DATA, {
  style: styleState,
  onEachFeature: onEachFeature
}).addTo(map);

map.setView([38.5, -96], 4);

function onEachFeature(feature, layer) {
  const name = feature.properties.NAME;
  layer.on({
    mouseover: function(e) {
      if (e.target === activeLayer) return;
      e.target.setStyle({ weight: 2.5, color: '#0d5d56', fillOpacity: 0.95 });
      e.target.bringToFront();
    },
    mouseout: function(e) {
      if (e.target !== activeLayer) geojsonLayer.resetStyle(e.target);
    },
    click: function(e) {
      if (activeLayer) geojsonLayer.resetStyle(activeLayer);
      activeLayer = e.target;
      activeLayer.setStyle({ weight: 3, color: '#0d5d56', fillOpacity: 0.95 });
      activeLayer.bringToFront();
      showStateReport(name);
      const mc = document.getElementById('main-content');
      if (mc.classList.contains('panel-collapsed')) {
        mc.classList.remove('panel-collapsed');
        document.getElementById('panel-toggle').innerHTML = '&#8250;';
        setTimeout(() => map.invalidateSize(), 320);
      }
    }
  });
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

function policyRow(featureName, status, text) {
  const hasText = text && text.trim();
  const textHtml = hasText
    ? '<div class="policy-text">' + esc(text).replace(/\n/g, '<br>') + '</div>'
    : '<div class="policy-text"><em>No information available.</em></div>';
  return '<div class="policy-row">'
    + '<div class="policy-row-left">'
    + '<div class="policy-feature">' + esc(featureName) + '</div>'
    + textHtml
    + '</div>'
    + '<div>' + ynBadge(status) + '</div>'
    + '</div>';
}

function detailItem(label, value) {
  const isNA = !value || value.trim() === 'N/A';
  return '<div class="detail-item">'
    + '<div class="detail-label">' + esc(label) + '</div>'
    + '<div class="detail-value' + (isNA ? ' na' : '') + '">'
    + (isNA ? 'N/A' : esc(value).replace(/\n/g, '<br>'))
    + '</div></div>';
}

/* ════════════════════════════════════
   WELCOME PANEL
   ════════════════════════════════════ */
function showWelcome() {
  if (activeLayer) { geojsonLayer.resetStyle(activeLayer); activeLayer = null; }
  const vals = Object.values(STATE_REPORTS);
  const na = vals.filter(r => r.status === 'active').length;
  const nl = vals.filter(r => r.status === 'limited').length;
  const nn = vals.filter(r => r.status === 'none').length;
  document.getElementById('panel-content').innerHTML =
    '<div class="welcome-wrap">'
    + '<div class="welcome-icon">&#127759;</div>'
    + '<div class="welcome-title">Community Solar State Reports</div>'
    + '<p class="welcome-body">This map shows the state of community-owned solar (COS) policy across all 50 US states. '
    + 'Click any state to read its detailed policy report.</p>'
    + '<div class="count-pills">'
    + '<span class="count-pill active">' + na + ' Active Programs</span>'
    + '<span class="count-pill limited">' + nl + ' Limited / Emerging</span>'
    + '<span class="count-pill none">' + nn + ' No Program</span>'
    + '</div>'
    + '<div class="legend">'
    + '<div class="legend-title">Program Status</div>'
    + '<div class="legend-row"><div class="legend-swatch" style="background:#0f766e"></div>Active Program</div>'
    + '<div class="legend-row"><div class="legend-swatch" style="background:#14b8a6"></div>Limited / Emerging</div>'
    + '<div class="legend-row"><div class="legend-swatch" style="background:#99f6e4"></div>No Program</div>'
    + '<div class="legend-row"><div class="legend-swatch" style="background:#94a3b8"></div>No Data</div>'
    + '</div></div>';
  document.getElementById('info-panel').scrollTop = 0;
}

/* ════════════════════════════════════
   STATE REPORT PANEL
   ════════════════════════════════════ */
function showStateReport(stateName) {
  const r = STATE_REPORTS[stateName] || {};
  const status  = r.status  || 'unknown';
  const pol     = r.policies || {};
  const det     = r.details  || {};
  const sources = r.sources  || [];

  const badgeClass = { active:'badge-active', limited:'badge-limited', none:'badge-none' }[status] || 'badge-none';
  const badgeText  = { active:'Active Program', limited:'Limited / Emerging', none:'No Program' }[status] || 'Unknown';

  // ── Section 1: Community Ownership Landscape ──
  const landscapeHtml = r.landscape
    ? '<div class="section-card">'
      + '<div class="section-title">Community Ownership Landscape</div>'
      + '<div class="section-body">'
      + '<div class="landscape-text">' + esc(r.landscape).replace(/\n/g, '<br>') + '</div>'
      + '</div></div>'
    : '';

  // ── Section 2: Enabling / Inhibiting Policies ──
  const vnm   = pol.vnm   || {};
  const cs    = pol.cs    || {};
  const other = pol.other || {};
  const policiesHtml =
    '<div class="section-card">'
    + '<div class="section-title">Enabling / Inhibiting Policies &amp; Programs</div>'
    + '<div class="section-body">'
    + policyRow('Virtual or Remote Net Metering', vnm.status,   vnm.text)
    + policyRow('Community Solar',                cs.status,    cs.text)
    + policyRow('Other State Support for COS',    other.status, other.text)
    + '</div></div>';

  // ── Section 3: Program Details ──
  const hasDetails = (det.size && det.size !== 'N/A')
                  || (det.eligibility && det.eligibility !== 'N/A')
                  || (det.benefitDist && det.benefitDist !== 'N/A');
  const detailsHtml =
    '<div class="section-card">'
    + '<div class="section-title">Program Details</div>'
    + '<div class="section-body"><div class="detail-grid">'
    + detailItem('Size', det.size || '')
    + detailItem('Eligibility', det.eligibility || '')
    + detailItem('Benefit Distribution', det.benefitDist || '')
    + '</div></div></div>';

  // ── Section 4: Active Cities / Communities ──
  const citiesHtml = r.activeCities
    ? '<div class="section-card">'
      + '<div class="section-title">Active Cities &amp; Communities</div>'
      + '<div class="section-body">'
      + '<div class="cities-text">' + esc(r.activeCities).replace(/\n/g,'<br>') + '</div>'
      + '</div></div>'
    : '';

  // ── Section 5: Sources ──
  const sourcesHtml = sources.length
    ? '<div class="section-card">'
      + '<div class="section-title">Sources (' + sources.length + ')</div>'
      + '<div class="section-body">'
      + '<ul class="sources-list">'
      + sources.map(s =>
          '<li><a href="' + esc(s.url) + '" target="_blank" rel="noopener noreferrer">'
          + esc(s.title || s.url) + '</a></li>'
        ).join('')
      + '</ul></div></div>'
    : '';

  document.getElementById('panel-content').innerHTML =
    '<div class="state-report">'
    + '<div class="report-header">'
    + '<button class="report-back" onclick="showWelcome()">&#8592; All States</button>'
    + '<div class="report-state-name">' + esc(stateName) + '</div>'
    + '<span class="report-status-badge ' + badgeClass + '">' + badgeText + '</span>'
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
   PANEL TOGGLE
   ════════════════════════════════════ */
document.getElementById('panel-toggle').addEventListener('click', function() {
  const mc = document.getElementById('main-content');
  const collapsed = mc.classList.toggle('panel-collapsed');
  this.innerHTML = collapsed ? '&#8249;' : '&#8250;';
  this.title = collapsed ? 'Expand panel' : 'Collapse panel';
  setTimeout(() => map.invalidateSize(), 320);
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
showWelcome();
</script>
</body>
</html>"""

with open('community_solar_reports.html', 'w', encoding='utf-8') as f:
    f.write(html)

import os
size = os.path.getsize('community_solar_reports.html')
print(f'Built community_solar_reports.html  ({size:,} bytes / {size/1024:.0f} KB)')
