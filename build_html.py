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
    /* ── Legend: compact control docked inside the map, so it stays
       visible while a state report is open ── */
    .map-legend {
      background: rgba(255,255,255,.94); border: 1px solid var(--slate-200);
      border-radius: 9px; padding: 9px 11px; box-shadow: var(--shadow);
      backdrop-filter: blur(3px);
    }
    .map-legend .legend-title {
      font-size: 0.6rem; font-weight: 700; text-transform: uppercase;
      letter-spacing: .07em; color: var(--slate-400); margin-bottom: 6px;
    }
    .legend-item { display: flex; align-items: center; gap: 7px; margin-bottom: 4px; }
    .legend-item:last-child { margin-bottom: 0; }
    .legend-swatch { width: 11px; height: 11px; border-radius: 3px; flex-shrink: 0;
                     border: 1px solid rgba(0,0,0,.12); }
    .legend-label { font-size: 0.72rem; color: var(--slate-600); line-height: 1.25;
                    white-space: nowrap; }

    /* ── Status explainer cards (welcome panel) ── */
    .status-guide { display: flex; flex-direction: column; gap: 9px; margin-top: 14px; }
    .status-card {
      border: 1px solid var(--slate-200); border-left-width: 4px;
      border-radius: 8px; padding: 10px 12px; background: var(--slate-50);
    }
    .status-card.active  { border-left-color: #0f766e; }
    .status-card.limited { border-left-color: #14b8a6; }
    .status-card.none    { border-left-color: #99f6e4; }
    .status-card.unknown { border-left-color: #94a3b8; }
    .status-card-head {
      display: flex; align-items: baseline; justify-content: space-between; gap: 8px;
      font-size: 0.8rem; font-weight: 700; color: var(--slate-800); margin-bottom: 4px;
    }
    .status-card-count { font-size: 0.7rem; font-weight: 600; color: var(--slate-500);
                         white-space: nowrap; }
    .status-card-desc { font-size: 0.73rem; line-height: 1.55; color: var(--slate-600); }

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
    .report-body { padding: 14px 16px 18px; display: flex; flex-direction: column; gap: 16px; }

    /* Section heading (above fact sheet / details) */
    .fact-title {
      font-size: 0.66rem; font-weight: 700; text-transform: uppercase;
      letter-spacing: .08em; color: var(--slate-400); margin-bottom: 8px;
    }

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

    /* ── Footer ── */
    footer {
      font-size: 0.72rem; color: var(--slate-400);
      text-align: center; padding: 14px 0;
      border-top: 1px solid var(--slate-200);
    }
    footer a { color: var(--slate-400); }

    /* ── Leaflet override ── */
    .leaflet-container { font-family: 'Inter', sans-serif; background: #d4dadc; }
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
    Community solar policy data from the <strong>Renewable Energy Clinic</strong> &nbsp;|&nbsp;
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
L.tileLayer('https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png?key=cb1_2j66_1_bdc1c1c1638e90dfd3765aa1', {
  attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>',
  subdomains: 'abcd', maxZoom: 19
}).addTo(map);

let geojsonLayer, activeLayer = null;

geojsonLayer = L.geoJSON(STATES_DATA, {
  style: styleState,
  onEachFeature: onEachFeature
}).addTo(map);

map.setView([38.5, -96], 4);

/* Compact legend, docked in the map so it persists across state reports. */
const legendControl = L.control({ position: 'bottomleft' });
legendControl.onAdd = function() {
  const div = L.DomUtil.create('div', 'map-legend');
  div.innerHTML = '<div class="legend-title">Program Status</div>'
    + [['#0f766e', 'Active program'],
       ['#14b8a6', 'Limited / emerging'],
       ['#99f6e4', 'No program'],
       ['#94a3b8', 'No data']]
      .map(function(e) {
        return '<div class="legend-item"><span class="legend-swatch" style="background:'
          + e[0] + '"></span><span class="legend-label">' + e[1] + '</span></div>';
      }).join('');
  L.DomEvent.disableClickPropagation(div);
  return div;
};
legendControl.addTo(map);

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
// True when a detail value carries real content (not blank / N/A).
function hasVal(v) {
  return v && v.trim() && v.trim().toUpperCase() !== 'N/A';
}

function toggleAccordion(headEl) {
  headEl.parentElement.classList.toggle('open');
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
  function statusCard(cls, title, count, desc) {
    return '<div class="status-card ' + cls + '">'
      + '<div class="status-card-head"><span>' + title + '</span>'
      + '<span class="status-card-count">' + count + ' states</span></div>'
      + '<div class="status-card-desc">' + desc + '</div></div>';
  }

  document.getElementById('panel-content').innerHTML =
    '<div class="welcome-wrap">'
    + '<div class="welcome-icon">&#127759;</div>'
    + '<div class="welcome-title">Community Solar State Reports</div>'
    + '<p class="welcome-body">Community-owned solar (COS) policy across all 50 states, '
    + 'Washington DC, and the US territories. Click any state for its full report.</p>'
    + '<div class="fact-title" style="margin-top:18px">What the statuses mean</div>'
    + '<div class="status-guide">'
    + statusCard('active', 'Active Program', na,
        'Community solar is enabled in law or regulation \u2014 subscribers share a project '
      + 'and get credits on their utility bills.')
    + statusCard('limited', 'Limited / Emerging', nl,
        'No full statewide program, but some building blocks exist: virtual net metering, '
      + 'a capped pilot, or utility and co-op shared solar.')
    + statusCard('none', 'No Program', nn,
        'No community solar policy and no virtual net metering, so there is no pathway for '
      + 'shared ownership \u2014 though legislation may be pending.')
    + '</div>'
    + '</div>';
  document.getElementById('info-panel').scrollTop = 0;
}

/* ════════════════════════════════════
   STATE REPORT PANEL
   ════════════════════════════════════ */
function showStateReport(stateName) {
  const r = STATE_REPORTS[stateName] || {};
  const status  = r.status   || 'unknown';
  const pol     = r.policies || {};
  const det     = r.details  || {};
  const sources = r.sources  || [];

  const badgeClass = { active:'badge-active', limited:'badge-limited', none:'badge-none' }[status] || 'badge-none';
  const badgeText  = { active:'Active Program', limited:'Limited / Emerging', none:'No Program' }[status] || 'Unknown';

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
    + '<div class="fact-title">Policies at a glance</div>'
    + '<div class="policy-list">'
    + policyItem('Community Solar', pol.cs)
    + policyItem('Virtual / Remote Net Metering', pol.vnm)
    + policyItem('Other State Support for COS', pol.other)
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
    + detailRow('Benefit Dist.', det.benefitDist);
  const detailsHtml = detailRows
    ? '<div class="fact-section"><div class="fact-title">Program details</div>'
      + '<div class="detail-rows">' + detailRows + '</div></div>'
    : '';

  // ── Collapsible accordions for the longer narrative ──
  function accordion(title, bodyHtml) {
    return '<div class="accordion">'
      + '<button type="button" class="acc-head" onclick="toggleAccordion(this)">'
      + '<span>' + esc(title) + '</span><span class="caret">&#9656;</span>'
      + '</button>'
      + '<div class="acc-body">' + bodyHtml + '</div></div>';
  }
  const landscapeHtml = (r.landscape && r.landscape.trim())
    ? accordion('Landscape overview', blocks(r.landscape)) : '';
  const citiesHtml = (r.activeCities && r.activeCities.trim())
    ? accordion('Active cities & communities', blocks(r.activeCities)) : '';
  const sourcesHtml = sources.length
    ? accordion('Sources (' + sources.length + ')',
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
    + '<button class="report-back" onclick="showWelcome()">&#8592; All States</button>'
    + '<div class="report-state-name">' + esc(stateName) + '</div>'
    + '<span class="report-status-badge ' + badgeClass + '">' + badgeText + '</span>'
    + '</div>'
    + '<div class="report-body">'
    + policiesHtml
    + detailsHtml
    + landscapeHtml
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

# Write both the canonical page name and index.html so the site's root URL
# (https://<user>.github.io/<repo>/) serves the map directly instead of 404ing.
for out_name in ('community_solar_reports.html', 'index.html'):
    with open(out_name, 'w', encoding='utf-8') as f:
        f.write(html)

import os
size = os.path.getsize('index.html')
print(f'Built community_solar_reports.html + index.html  ({size:,} bytes / {size/1024:.0f} KB)')
