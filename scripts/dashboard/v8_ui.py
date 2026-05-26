from __future__ import annotations

import html
import sys
from pathlib import Path

import streamlit as st
import streamlit.components.v1 as components

scripts_dir = Path(__file__).resolve().parent.parent
if str(scripts_dir) not in sys.path:
    sys.path.insert(0, str(scripts_dir))

from dashboard.v8_store import get_v8_store, v8_snapshot

_comp = components.declare_component(
    "v8_dashboard",
    path=str(Path(__file__).resolve().parent / "v8_component"),
)

NOTEBOOK_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:opsz,wght@9..40,400;9..40,500;9..40,600;9..40,700&family=Noto+Serif+SC:wght@400;600;700&family=Playfair+Display:ital,wght@0,400;0,700;1,400&family=JetBrains+Mono:wght@400;500&display=swap');

:root {
    --paper: #f7f3eb;
    --paper-hover: #f3efe7;
    --paper-soft: #edebe4;
    --ink: #2c2c2c;
    --ink-2: #5c5c5c;
    --ink-3: #8c8c8c;
    --rule: rgba(0,0,0,0.06);
    --rule-strong: rgba(0,0,0,0.14);
    --accent: #c4956a;
    --accent-light: #fdf6ee;
    --green: #4a7c59;
    --green-light: #f0f7f2;
    --red: #b85450;
    --red-light: #fdf2f2;
    --amber: #b8860b;
    --amber-light: #fdf8ef;
    --blue: #5b7fa6;
    --blue-light: #f0f4f8;
    --purple: #7c6a8a;
    --purple-light: #f5f0f8;
    --teal: #4a8c7f;
    --teal-light: #f0f7f5;
}

* { margin: 0; padding: 0; box-sizing: border-box; }

body {
    color: var(--ink);
    font-family: 'DM Sans', 'Noto Serif SC', -apple-system, BlinkMacSystemFont, sans-serif;
    background: var(--paper);
}

@keyframes fadeIn {
    from { opacity: 0; transform: translateY(8px); }
    to { opacity: 1; transform: translateY(0); }
}

@media (prefers-reduced-motion: reduce) {
    @keyframes fadeIn {
        from { opacity: 1; transform: none; }
        to { opacity: 1; transform: none; }
    }
}

.v8-page {
    max-width: 1080px;
    margin: 0 auto;
    padding: 10px 12px 20px;
}

@media (max-width: 768px) {
    .v8-page { padding: 8px 8px 16px; }
}

.v8-topbar {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding-bottom: 12px;
}

.v8-brand {
    font-size: 10px;
    font-weight: 700;
    color: var(--accent);
    letter-spacing: 0.15em;
    text-transform: uppercase;
    font-family: 'DM Sans', sans-serif;
}

.v8-db-path {
    font-size: 11px;
    color: var(--ink-3);
    font-family: 'JetBrains Mono', monospace;
}

.v8-hero-title {
    font-family: 'Noto Serif SC', serif;
    font-size: 32px;
    font-weight: 700;
    color: var(--ink);
    margin: 0;
    line-height: 1.25;
    letter-spacing: 0;
}

@media (max-width: 768px) {
    .v8-hero-title { font-size: 28px; }
}

.v8-hero-row {
    display: flex;
    align-items: baseline;
    justify-content: space-between;
    margin-top: 6px;
}

.v8-hero-desc {
    font-size: 14px;
    color: var(--ink-2);
    margin: 0;
    line-height: 1.65;
    font-family: 'DM Sans', sans-serif;
}

.v8-refresh-btn {
    font-size: 12px;
    font-weight: 500;
    color: var(--ink-3);
    background: transparent;
    border: 1px solid var(--rule-strong);
    border-radius: 6px;
    padding: 4px 14px;
    cursor: pointer;
    font-family: 'DM Sans', sans-serif;
    transition: all 0.2s ease;
    white-space: nowrap;
    flex-shrink: 0;
    margin-left: 12px;
    line-height: 1.5;
}

.v8-refresh-btn:hover {
    background: var(--paper-hover);
    border-color: var(--accent);
    color: var(--accent);
}

.v8-metrics {
    display: flex;
    gap: 0;
    border-top: 2px solid var(--rule-strong);
    border-bottom: 2px solid var(--rule-strong);
    padding: 20px 0 16px;
    margin-top: 20px;
}

.v8-metric {
    flex: 1;
    text-align: center;
}

.v8-metric-num {
    font-family: 'Playfair Display', serif;
    font-size: 30px;
    font-weight: 700;
    color: var(--ink);
    line-height: 1;
    font-variant-numeric: tabular-nums;
    letter-spacing: -0.5px;
}

.v8-metric-label {
    font-size: 12px;
    font-weight: 500;
    color: var(--ink-2);
    margin-top: 4px;
    font-family: 'DM Sans', sans-serif;
}

.v8-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    column-gap: 28px;
}

@media (max-width: 768px) {
    .v8-grid { grid-template-columns: 1fr; column-gap: 0; }
}

.v8-section {
    padding: 24px 0 8px;
    border-top: 1px solid rgba(0,0,0,0.04);
}

.v8-section .v8-row {
    padding: 14px 0;
    gap: 16px;
}

.v8-section .v8-row:hover {
    padding: 14px 12px;
}

.v8-entry-header {
    display: flex;
    align-items: center;
    gap: 10px;
    margin-bottom: 14px;
}

.v8-entry-dot {
    width: 9px;
    height: 9px;
    border-radius: 50%;
    flex-shrink: 0;
}

.v8-entry-title {
    font-family: 'Noto Serif SC', serif;
    font-size: 18px;
    font-weight: 600;
    color: var(--ink);
    margin: 0;
    line-height: 1.3;
}

.v8-entry-count {
    font-size: 12px;
    color: var(--ink-3);
    font-family: 'DM Sans', sans-serif;
    margin-left: auto;
}

.v8-row {
    display: grid;
    grid-template-columns: auto 1fr auto;
    align-items: flex-start;
    gap: 14px;
    padding: 12px 0;
    border-bottom: 1px solid var(--rule);
    animation: fadeIn 0.3s ease both;
    transition: background 0.2s ease;
}

.v8-row:hover {
    background: var(--paper-hover);
    margin: 0 -12px;
    padding: 12px 12px;
    border-radius: 6px;
}

.v8-pills {
    display: flex;
    flex-wrap: wrap;
    gap: 4px;
    min-width: 110px;
}

.v8-pill {
    display: inline-flex;
    align-items: center;
    padding: 2px 9px;
    border-radius: 8px;
    font-size: 11px;
    font-weight: 600;
    white-space: nowrap;
    line-height: 1.5;
    font-family: 'DM Sans', sans-serif;
}

.v8-pill-accent { background: var(--accent-light); color: var(--accent); }
.v8-pill-green { background: var(--green-light); color: var(--green); }
.v8-pill-red { background: var(--red-light); color: var(--red); }
.v8-pill-amber { background: var(--amber-light); color: var(--amber); }
.v8-pill-blue { background: var(--blue-light); color: var(--blue); }
.v8-pill-purple { background: var(--purple-light); color: var(--purple); }
.v8-pill-teal { background: var(--teal-light); color: var(--teal); }
.v8-pill-gray { background: var(--paper-soft); color: var(--ink-2); }

.v8-content {
    font-size: 14px;
    color: var(--ink-2);
    line-height: 1.55;
    overflow-wrap: anywhere;
    font-family: 'DM Sans', sans-serif;
}

.v8-meta {
    text-align: right;
    min-width: 70px;
}

.v8-time {
    font-size: 12px;
    color: var(--ink-3);
    white-space: nowrap;
    font-variant-numeric: tabular-nums;
    font-family: 'JetBrains Mono', monospace;
}

.v8-detail {
    font-size: 11px;
    color: var(--ink-3);
    margin-top: 2px;
    font-family: 'JetBrains Mono', monospace;
}

.v8-empty {
    padding: 28px 0 32px;
    text-align: center;
    font-size: 14px;
    color: var(--ink-3);
    line-height: 1.6;
    font-family: 'DM Sans', sans-serif;
}

.v8-empty-icon {
    font-size: 24px;
    margin-bottom: 6px;
    opacity: 0.5;
}

.v8-reason {
    display: flex;
    align-items: center;
    gap: 14px;
    padding: 14px 0;
    border-bottom: 1px solid rgba(0,0,0,0.04);
    animation: fadeIn 0.3s ease both;
}

.v8-reason:last-child { border-bottom: none; }

.v8-reason-num {
    font-family: 'Playfair Display', serif;
    font-size: 22px;
    font-weight: 700;
    color: var(--ink);
    line-height: 1;
    min-width: 32px;
    font-variant-numeric: tabular-nums;
}

.v8-reason-label {
    font-size: 14px;
    font-weight: 600;
    color: var(--ink);
    line-height: 1.3;
    font-family: 'Noto Serif SC', serif;
}

.v8-reason-code {
    font-size: 11px;
    color: var(--ink-3);
    margin-top: 2px;
    font-family: 'JetBrains Mono', monospace;
}

.v8-footer {
    border-top: 2px solid var(--rule-strong);
    margin-top: 40px;
    padding-top: 20px;
}

.v8-footer-inner {
    display: flex;
    align-items: center;
    justify-content: space-between;
    font-size: 12px;
    color: var(--ink-3);
    font-family: 'DM Sans', sans-serif;
}
</style>
"""


def esc(value: object) -> str:
    return html.escape("" if value is None else str(value))


def snip(value: object, limit: int = 100) -> str:
    text = "" if value is None else str(value)
    text = " ".join(text.split())
    if len(text) <= limit:
        return esc(text)
    return esc(text[: limit - 1].rstrip()) + "\u2026"


def pill(label: str, style: str = "gray") -> str:
    return f'<span class="v8-pill v8-pill-{style}">{esc(label)}</span>'


def _reason(label: str) -> str:
    m = {
        "missing_source": "\u7f3a\u5c11\u6765\u6e90\u4e8b\u4ef6",
        "missing_scope": "\u7f3a\u5c11\u4f5c\u7528\u57df",
        "missing_supporting_evidence": "\u7f3a\u5c11\u652f\u6301\u8bc1\u636e",
        "contradicting_evidence": "\u5b58\u5728\u77db\u76fe\u8bc1\u636e",
        "missing_procedural_evidence": "\u7f3a\u5c11\u6d41\u7a0b\u8bc1\u636e",
        "stale": "\u5df2\u8fc7\u671f",
        "status_blocked": "\u72b6\u6001\u88ab\u963b\u6b62",
        "risk_blocked": "\u98ce\u9669\u7b49\u7ea7\u88ab\u963b\u6b62",
        "scope_mismatch": "\u4f5c\u7528\u57df\u4e0d\u5339\u914d",
        "no_task_match": "\u4efb\u52a1\u4e0d\u5339\u914d",
    }
    return m.get(label, label)


def _pol(p: str) -> str:
    return {"supports": "\u652f\u6301", "weakens": "\u524a\u5f31", "contradicts": "\u77db\u76fe", "neutral": "\u4e2d\u6027"}.get(p, p)


def _header(title: str, count: str = "", dot_color: str = "accent") -> str:
    c = f'<span class="v8-entry-count">{esc(count)}</span>' if count else ""
    return f'<div class="v8-entry-header"><div class="v8-entry-dot" style="background:var(--{dot_color})"></div><h2 class="v8-entry-title">{esc(title)}</h2>{c}</div>'


def _row(pills: str, content: str, time: str, detail: str = "", delay: int = 0) -> str:
    d = f'<div class="v8-detail">{esc(detail)}</div>' if detail else ""
    return f'<div class="v8-row" style="animation-delay:{delay}ms"><div class="v8-pills">{pills}</div><div class="v8-content">{content}</div><div class="v8-meta"><div class="v8-time">{esc(time)}</div>{d}</div></div>'


def _empty(icon: str, text: str) -> str:
    return f'<div class="v8-empty"><div class="v8-empty-icon">{icon}</div>{esc(text)}</div>'


def _section(title: str, count: str, dot: str, body: str) -> str:
    return f'<div class="v8-section">{_header(title, count, dot)}{body}</div>'


def _build_events(rows: list) -> str:
    if not rows:
        return _empty("\U0001F4DD", "\u6682\u65e0\u4e8b\u4ef6\u3002\u5f00\u59cb\u4f7f\u7528\u540e\u4f1a\u5728\u8fd9\u91cc\u663e\u793a\u3002")
    out = ""
    for i, r in enumerate(rows):
        p = pill(r.get("event_type", ""), "blue") + pill(r.get("actor", ""), "gray")
        s = r.get("scope", {}) or {}
        d = " \u00b7 ".join(f"{k}={v}" for k, v in s.items()) if s else ""
        out += _row(p, snip(r.get("content", ""), 120), r.get("created_at", "")[:16], d, i * 50)
    return out


def _build_candidates(rows: list) -> str:
    if not rows:
        return _empty("\U0001F4AD", "\u6682\u65e0\u5019\u9009\u89c2\u70b9\u3002")
    out = ""
    for i, r in enumerate(rows):
        p = pill(r.get("candidate_type", ""), "purple") + pill(r.get("status", ""), "blue")
        t = snip(r.get("trigger", ""), 40)
        n = len(r.get("source_event_ids", []))
        out += _row(p, snip(r.get("content", ""), 120), r.get("created_at", "")[:16], f"{t} \u00b7 {n} \u6761\u6765\u6e90", i * 50)
    return out


def _build_evidence(rows: list) -> str:
    if not rows:
        return _empty("\U0001F50D", "\u6682\u65e0\u8bc1\u636e\u3002")
    out = ""
    for i, r in enumerate(rows):
        pol = r.get("polarity", "")
        ps = "green" if pol == "supports" else "red" if pol == "contradicts" else "amber"
        p = pill(r.get("evidence_type", ""), "teal") + pill(_pol(pol), ps)
        n = len(r.get("source_event_ids", []))
        out += _row(p, snip(r.get("content", ""), 100), r.get("created_at", "")[:16], f"{n} \u6761\u6765\u6e90", i * 50)
    return out


def _build_memories(rows: list) -> str:
    if not rows:
        return _empty("\U0001F9E0", "\u6682\u65e0\u8bb0\u5fc6\u3002")
    out = ""
    for i, r in enumerate(rows):
        p = pill(r.get("memory_type", ""), "purple") + pill(r.get("status", ""), "green")
        conf = r.get("confidence", "")
        fr = r.get("freshness", "")
        out += _row(p, snip(r.get("content", ""), 120), r.get("updated_at", "")[:16], f"\u7f6e\u4fe1\u5ea6 {conf} \u00b7 \u65b0\u9c9c\u5ea6 {fr}", i * 50)
    return out


def _build_contexts(rows: list) -> str:
    if not rows:
        return _empty("\U0001F4E6", "\u6682\u65e0\u68c0\u7d22\u8bb0\u5f55\u3002")
    out = ""
    for i, r in enumerate(rows):
        sel = len(r.get("selected", []))
        rej = len(r.get("rejected", []))
        p = pill(f"\u91c7\u7528 {sel}", "green" if sel > 0 else "gray") + pill(f"\u62d2 {rej}", "red" if rej > 0 else "gray")
        s = r.get("scope", {}) or {}
        d = " \u00b7 ".join(f"{k}={v}" for k, v in s.items()) if s else ""
        out += _row(p, snip(r.get("task", ""), 80), r.get("created_at", "")[:16], d, i * 50)
    return out


def _build_reasons(rows: list) -> str:
    if not rows:
        return _empty("\u2705", "\u5168\u90e8\u901a\u8fc7\uff0c\u6682\u65e0\u62d2\u7edd\u8bb0\u5f55\u3002")
    out = ""
    for i, r in enumerate(rows):
        rea = r.get("reason", "")
        cnt = r.get("count", 0)
        out += f'<div class="v8-reason" style="animation-delay:{i * 50}ms"><div class="v8-reason-num">{esc(cnt)}</div><div><div class="v8-reason-label">{esc(_reason(rea))}</div><div class="v8-reason-code">{esc(rea)}</div></div></div>'
    return out


def render_dashboard() -> None:
    store = get_v8_store()
    snap = v8_snapshot(store)
    h = snap["health"]
    c = snap["counts"]
    recent = snap["recent"]
    reasons = snap["reason_summary"]

    mi = [
        (c.get("raw_events", 0), "\u539f\u59cb\u4e8b\u4ef6"),
        (c.get("candidates", 0), "\u5019\u9009\u89c2\u70b9"),
        (c.get("evidence", 0), "\u8bc1\u636e"),
        (c.get("memories", 0), "\u8bb0\u5fc6"),
        (c.get("context_pack_runs", 0), "\u68c0\u7d22"),
    ]
    metrics_html = "".join(
        f'<div class="v8-metric"><div class="v8-metric-num">{esc(n)}</div><div class="v8-metric-label">{esc(lb)}</div></div>'
        for n, lb in mi
    )

    ev_n = len(recent["raw_events"])
    ca_n = len(recent["candidates"])
    ei_n = len(recent["evidence"])
    rs_n = sum(r.get("count", 0) for r in reasons)
    mm_n = len(recent["memories"])
    cx_n = len(recent["context_pack_runs"])

    ev_s = f"{ev_n} \u6761"
    ca_s = f"{ca_n} \u6761"
    ei_s = f"{ei_n} \u6761"
    rs_s = f"{rs_n} \u6b21"
    mm_s = f"{mm_n} \u6761"
    cx_s = f"{cx_n} \u6761"

    s_events = _section("\u6700\u8fd1\u4e8b\u4ef6", ev_s, "blue", _build_events(recent["raw_events"]))
    s_cands = _section("\u5019\u9009\u89c2\u70b9", ca_s, "purple", _build_candidates(recent["candidates"]))
    s_evid = _section("\u8bc1\u636e", ei_s, "teal", _build_evidence(recent["evidence"]))
    s_reasons = _section("\u62d2\u7edd\u539f\u56e0", rs_s, "red", _build_reasons(reasons))
    s_mems = _section("\u8bb0\u5fc6", mm_s, "green", _build_memories(recent["memories"]))
    s_ctxs = _section("\u68c0\u7d22\u8bb0\u5f55", cx_s, "amber", _build_contexts(recent["context_pack_runs"]))
    db_path = esc(h.get("db_path", ""))

    page_html = f"""{NOTEBOOK_CSS}
    <div class="v8-page">
      <div class="v8-topbar">
        <div class="v8-brand">Mnemosyne \u00b7 V8</div>
        <div class="v8-db-path">{db_path}</div>
      </div>
      <h1 class="v8-hero-title">\u5e2e\u4f60\u8bb0\u4f4f\u91cd\u8981\u7684\u4e8b</h1>
      <div class="v8-hero-row">
        <p class="v8-hero-desc">\u6bcf\u4e00\u6761\u7ecf\u9a8c\u90fd\u6709\u6e90\u5934\u3001\u6709\u8bc1\u636e\u3001\u6709\u72b6\u6001\u3002\u968f\u65f6\u7ffb\u5f00\u67e5\u770b\u5b83\u8bb0\u4f4f\u4e86\u4ec0\u4e48\u3001\u4e3a\u4ec0\u4e48\u8fd9\u6837\u5224\u65ad\u3002</p>
        <button class="v8-refresh-btn">\u5237\u65b0</button>
      </div>
      <div class="v8-metrics">{metrics_html}</div>
      <div class="v8-grid">
        {s_events}
        {s_cands}
        {s_evid}
        {s_reasons}
        {s_mems}
        {s_ctxs}
      </div>
      <div class="v8-footer">
        <div class="v8-footer-inner">
          <span>Mnemosyne V8 \u00b7 \u8bb0\u5f55\u6709\u6e90\u5934 \u00b7 \u5224\u65ad\u6709\u4f9d\u636e</span>
          <span>{db_path}</span>
        </div>
      </div>
    </div>"""

    result = _comp(html_content=page_html, key="v8_dashboard")

    if result == "refresh":
        get_v8_store.cache_clear()
        st.rerun()
