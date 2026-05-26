function esc(v) {
    if (v == null) return '';
    const d = document.createElement('div');
    d.textContent = String(v);
    return d.innerHTML;
}

function snip(v, limit = 100) {
    let t = (v || '').toString().replace(/\s+/g, ' ').trim();
    if (t.length <= limit) return esc(t);
    return esc(t.substring(0, limit - 1).trimEnd()) + '\u2026';
}

function pill(label, style = 'gray') {
    return `<span class="v8-pill v8-pill-${style}">${esc(label)}</span>`;
}

const reasonMap = {
    missing_source: '\u7f3a\u5c11\u6765\u6e90\u4e8b\u4ef6',
    missing_scope: '\u7f3a\u5c11\u4f5c\u7528\u57df',
    missing_supporting_evidence: '\u7f3a\u5c11\u652f\u6301\u8bc1\u636e',
    contradicting_evidence: '\u5b58\u5728\u77db\u76fe\u8bc1\u636e',
    missing_procedural_evidence: '\u7f3a\u5c11\u6d41\u7a0b\u8bc1\u636e',
    stale: '\u5df2\u8fc7\u671f',
    status_blocked: '\u72b6\u6001\u88ab\u963b\u6b62',
    risk_blocked: '\u98ce\u9669\u7b49\u7ea7\u88ab\u963b\u6b62',
    scope_mismatch: '\u4f5c\u7528\u57df\u4e0d\u5339\u914d',
    no_task_match: '\u4efb\u52a1\u4e0d\u5339\u914d',
    low_confidence: '\u7f6e\u4fe1\u5ea6\u8fc7\u4f4e',
};

function reasonLabel(code) {
    return reasonMap[code] || code;
}

const polMap = { supports: '\u652f\u6301', weakens: '\u524a\u5f31', contradicts: '\u77db\u76fe', neutral: '\u4e2d\u6027' };
function polLabel(p) { return polMap[p] || p; }

function header(title, count = '', dotColor = 'accent') {
    const c = count ? `<span class="v8-entry-count">${esc(count)}</span>` : '';
    return `<div class="v8-entry-header"><div class="v8-entry-dot" style="background:var(--${dotColor})"></div><h2 class="v8-entry-title">${esc(title)}</h2>${c}</div>`;
}

function row(pills, content, time, detail = '', delay = 0) {
    const d = detail ? `<div class="v8-detail">${esc(detail)}</div>` : '';
    return `<div class="v8-row" style="animation-delay:${delay}ms"><div class="v8-pills">${pills}</div><div class="v8-content">${content}</div><div class="v8-meta"><div class="v8-time">${esc(time)}</div>${d}</div></div>`;
}

function empty(icon, text) {
    return `<div class="v8-empty"><div class="v8-empty-icon">${icon}</div>${esc(text)}</div>`;
}

function section(title, count, dot, body) {
    return `<div class="v8-section">${header(title, count, dot)}${body}</div>`;
}

function parseJsonField(obj, field) {
    const raw = obj[field];
    if (!raw) return {};
    if (typeof raw === 'object') return raw;
    try { return JSON.parse(raw); } catch { return {}; }
}

function buildEvents(rows) {
    if (!rows || !rows.length) return empty('\uD83D\uDCDD', '\u6682\u65e0\u4e8b\u4ef6\u3002\u5f00\u59cb\u4f7f\u7528\u540e\u4f1a\u5728\u8fd9\u91cc\u663e\u793a\u3002');
    return rows.map((r, i) => {
        const p = pill(r.event_type || '', 'blue') + pill(r.actor || '', 'gray');
        const s = parseJsonField(r, 'scope_json');
        const d = Object.entries(s).map(([k, v]) => `${k}=${v}`).join(' \u00b7 ');
        return row(p, snip(r.content, 120), (r.created_at || '').substring(0, 16), d, i * 50);
    }).join('');
}

function buildCandidates(rows) {
    if (!rows || !rows.length) return empty('\uD83D\uDCAD', '\u6682\u65e0\u5019\u9009\u89c2\u70b9\u3002');
    return rows.map((r, i) => {
        const p = pill(r.candidate_type || '', 'purple') + pill(r.status || '', 'blue');
        const t = snip(r.trigger || '', 40);
        const n = (r.source_event_ids || []).length;
        return row(p, snip(r.content, 120), (r.created_at || '').substring(0, 16), `${t} \u00b7 ${n} \u6761\u6765\u6e90`, i * 50);
    }).join('');
}

function buildEvidence(rows) {
    if (!rows || !rows.length) return empty('\uD83D\uDD0D', '\u6682\u65e0\u8bc1\u636e\u3002');
    return rows.map((r, i) => {
        const pol = r.polarity || '';
        const ps = pol === 'supports' ? 'green' : pol === 'contradicts' ? 'red' : 'amber';
        const p = pill(r.evidence_type || '', 'teal') + pill(polLabel(pol), ps);
        const n = (parseJsonField(r, 'source_event_ids_json') || []).length || (r.source_event_ids || []).length;
        return row(p, snip(r.content, 100), (r.created_at || '').substring(0, 16), `${n} \u6761\u6765\u6e90`, i * 50);
    }).join('');
}

function buildMemories(rows) {
    if (!rows || !rows.length) return empty('\uD83E\uDDE0', '\u6682\u65e0\u8bb0\u5fc6\u3002');
    return rows.map((r, i) => {
        const p = pill(r.memory_type || '', 'purple') + pill(r.status || '', 'green');
        const conf = r.confidence != null ? r.confidence : '';
        const fr = r.freshness != null ? r.freshness : '';
        return row(p, snip(r.content, 120), (r.updated_at || '').substring(0, 16), `\u7f6e\u4fe1\u5ea6 ${conf} \u00b7 \u65b0\u9c9c\u5ea6 ${fr}`, i * 50);
    }).join('');
}

function buildContexts(rows) {
    if (!rows || !rows.length) return empty('\uD83D\uDCE6', '\u6682\u65e0\u68c0\u7d22\u8bb0\u5f55\u3002');
    return rows.map((r, i) => {
        const pack = parseJsonField(r, 'pack_json');
        const sel = (pack.items || []).length;
        const rej = (pack.rejected || []).length;
        const p = pill(`\u91c7\u7528 ${sel}`, sel > 0 ? 'green' : 'gray') + pill(`\u62d2 ${rej}`, rej > 0 ? 'red' : 'gray');
        const s = parseJsonField(r, 'scope_json');
        const d = Object.entries(s).map(([k, v]) => `${k}=${v}`).join(' \u00b7 ');
        return row(p, snip(r.task || '', 80), (r.created_at || '').substring(0, 16), d, i * 50);
    }).join('');
}

function buildReasons(rows) {
    if (!rows || !rows.length) return empty('\u2705', '\u5168\u90e8\u901a\u8fc7\uff0c\u6682\u65e0\u62d2\u7edd\u8bb0\u5f55\u3002');
    return rows.map((r, i) => {
        return `<div class="v8-reason" style="animation-delay:${i * 50}ms"><div class="v8-reason-num">${esc(r.count)}</div><div><div class="v8-reason-label">${esc(reasonLabel(r.reason))}</div><div class="v8-reason-code">${esc(r.reason)}</div></div></div>`;
    }).join('');
}

function summarizeReasons(contextRuns) {
    const counts = {};
    contextRuns.forEach(r => {
        const pack = parseJsonField(r, 'pack_json');
        (pack.rejected || []).forEach(rej => {
            const reason = rej.reason || 'unknown';
            counts[reason] = (counts[reason] || 0) + 1;
        });
    });
    return Object.entries(counts).map(([reason, count]) => ({ reason, count }));
}

function renderDashboard(data) {
    const counts = data.counts || {};
    const metrics = [
        [counts.raw_events || 0, '\u539f\u59cb\u4e8b\u4ef6'],
        [counts.candidates || 0, '\u5019\u9009\u89c2\u70b9'],
        [counts.evidence || 0, '\u8bc1\u636e'],
        [counts.memories || 0, '\u8bb0\u5fc6'],
        [counts.context_pack_runs || 0, '\u68c0\u7d22'],
    ];
    const metricsHtml = metrics.map(([n, lb]) =>
        `<div class="v8-metric"><div class="v8-metric-num">${esc(n)}</div><div class="v8-metric-label">${esc(lb)}</div></div>`
    ).join('');

    const events = data.recent?.raw_events || [];
    const candidates = data.recent?.candidates || [];
    const evidence = data.recent?.evidence || [];
    const memories = data.recent?.memories || [];
    const contexts = data.recent?.context_pack_runs || [];
    const reasons = summarizeReasons(contexts);

    const grid = `
        ${section('\u6700\u8fd1\u4e8b\u4ef6', `${events.length} \u6761`, 'blue', buildEvents(events))}
        ${section('\u5019\u9009\u89c2\u70b9', `${candidates.length} \u6761`, 'purple', buildCandidates(candidates))}
        ${section('\u8bc1\u636e', `${evidence.length} \u6761`, 'teal', buildEvidence(evidence))}
        ${section('\u62d2\u7edd\u539f\u56e0', `${reasons.reduce((s, r) => s + r.count, 0)} \u6b21`, 'red', buildReasons(reasons))}
        ${section('\u8bb0\u5fc6', `${memories.length} \u6761`, 'green', buildMemories(memories))}
        ${section('\u68c0\u7d22\u8bb0\u5f55', `${contexts.length} \u6761`, 'amber', buildContexts(contexts))}
    `;

    const dbPath = data.health?.db_path || 'demo data';

    document.getElementById('v8-metrics').innerHTML = metricsHtml;
    document.getElementById('v8-grid').innerHTML = grid;
    document.getElementById('v8-db-path-top').textContent = dbPath;
    document.getElementById('v8-db-path-bottom').textContent = dbPath;

    const banner = document.getElementById('v8-offline-banner');
    if (data._offline) {
        banner.style.display = 'block';
        banner.textContent = '\u6f14\u793a\u6570\u636e \u2014 \u542f\u52a8 REST API \u67e5\u770b\u5b9e\u65f6\u6570\u636e';
    } else {
        banner.style.display = 'none';
    }
}
