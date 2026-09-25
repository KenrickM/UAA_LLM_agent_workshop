#!/usr/bin/env python3
"""
UAA Chancellor Mail & Calendar — a fake email + calendar web app for the
"Next Day Preparation" agent workshop.

The data is stored in markdown files so that workshop participants can point
their agents straight at them:

    data/calendar.md   — 14 days of calendar entries
    data/inbox.md      — 150+ emails (event-related + spam/newsletters/etc.)

Run:
    python3 app.py                # http://localhost:8321
    python3 app.py --port 9000    # custom port
    python3 app.py --data-dir /some/other/dir

HTTP surface:
    GET  /              -> /calendar
    GET  /calendar      -> week-view calendar (?start=YYYY-MM-DD, ?day=YYYY-MM-DD)
    GET  /event         -> event details (?d=YYYY-MM-DD&i=N)
    GET  /inbox         -> inbox list, newest first (?q=search)
    GET  /email         -> one email (?i=N, ?d=YYYY-MM-DD)
    GET  /send          -> send a test email (POST form)
    GET  /calendar.md   -> raw markdown (what the agent should read)
    GET  /inbox.md      -> raw markdown (what the agent should read)
    GET  /api/health    -> JSON status
    POST /api/send      -> append a new email (JSON or form)
"""
from __future__ import annotations

import argparse
import html
import json
import re
import urllib.parse
from datetime import date, datetime, time, timedelta
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse, parse_qs

HERE = Path(__file__).resolve().parent
DATA_DIR = HERE / "data"
CALENDAR_FILE = "calendar.md"
INBOX_FILE = "inbox.md"

WEEKDAY_SHORT = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
WEEKDAY_LONG = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday",
                "Saturday", "Sunday"]

# Calendar week grid: 07:00–22:00 in 30-minute slots
GRID_START_H, GRID_END_H = 7, 22
SLOTS_PER_DAY = (GRID_END_H - GRID_START_H) * 2

# ---------------------------------------------------------------------------
# Calendar parsing (line-based)
# ---------------------------------------------------------------------------

class CalEvent:
    __slots__ = ("start", "end", "title", "where", "notes")

    def __init__(self, start: str, end: str, title: str, where: str, notes: str):
        self.start, self.end, self.title, self.where, self.notes = \
            start, end, title, where, notes

    def minutes(self, field: str) -> int:
        h, m = getattr(self, field).split(":")
        return int(h) * 60 + int(m)

    def start_min(self) -> int:
        return self.minutes("start")

    def end_min(self) -> int:
        return self.minutes("end")


DAY_HEAD_RE = re.compile(
    r"^## (Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday), "
    r"(\w+) (\d{1,2}), (\d{4})\s*$")
EVENT_RE = re.compile(r"^- (\d{2}):(\d{2})\s*[–-]\s*(\d{2}):(\d{2})\s+—\s+\*\*(.+?)\*\*\s*$")


def parse_calendar(text: str) -> dict[str, list[CalEvent]]:
    """Return {iso-date: [CalEvent]}"""
    days: dict[str, list[CalEvent]] = {}
    cur: date | None = None
    ev: CalEvent | None = None
    for line in text.splitlines():
        m = DAY_HEAD_RE.match(line)
        if m:
            wd, mon, dd, yy = m.groups()
            months = {m2: i for i, m2 in enumerate(
                ["January", "February", "March", "April", "May", "June",
                 "July", "August", "September", "October", "November",
                 "December"], start=1)}
            cur = date(int(yy), months[mon], int(dd))
            days.setdefault(cur.isoformat(), [])
            ev = None
            continue
        if cur is None:
            continue
        m = EVENT_RE.match(line)
        if m:
            sh, sm, eh, em, title = m.groups()
            ev = CalEvent(f"{sh}:{sm}", f"{eh}:{em}", title.strip(), "", "")
            days[cur.isoformat()].append(ev)
            continue
        m = re.match(r"^  - Location:\s*(.+?)\s*$", line)
        if m and ev:
            ev.where = m.group(1)
            continue
        m = re.match(r"^  - Notes:\s*(.+?)\s*$", line)
        if m and ev:
            ev.notes = m.group(1)
            continue
    return days


# ---------------------------------------------------------------------------
# Inbox parsing (line-based)
# ---------------------------------------------------------------------------

class Msg:
    __slots__ = ("day", "tstamp", "frm", "subject", "body")

    def __init__(self, day: str, tstamp: str, frm: str, subject: str, body: str):
        self.day, self.tstamp, self.frm, self.subject, self.body = \
            day, tstamp, frm, subject, body

    @property
    def key(self) -> str:
        return f"{self.day} {self.tstamp}"


MSG_HEAD_RE = re.compile(
    r"^## \[(\d{4}-\d{2}-\d{2}) (\d{2}:\d{2})\] From: (.+?)\s*$")


def parse_inbox(text: str) -> list[Msg]:
    msgs: list[Msg] = []
    cur: Msg | None = None
    body_lines: list[str] = []
    for line in text.splitlines():
        m = MSG_HEAD_RE.match(line)
        if m:
            if cur:
                cur.body = "\n".join(body_lines).strip()
                msgs.append(cur)
            cur = Msg(m.group(1), m.group(2), m.group(3), "", [])
            body_lines = []
            continue
        if cur is None:
            continue
        if line == "---":
            continue
        if line.startswith("**Subject:** ") and not cur.subject:
            cur.subject = line[len("**Subject:** "):]
            continue
        if line.startswith("_End of inbox export._"):
            break
        body_lines.append(line)
    if cur:
        cur.body = "\n".join(body_lines).strip()
        msgs.append(cur)
    # drop any trailing empty
    msgs = [m for m in msgs if m.subject or m.body]
    # present newest first: reverse-chronological by "YYYY-MM-DD HH:MM"
    # (zero-padded, so lexicographic == chronological). Stable for equal keys.
    msgs.sort(key=lambda m: m.key, reverse=True)
    return msgs


def split_name_addr(frm: str) -> tuple[str, str]:
    m = re.match(r"^(.*?)\s*<(.+?)>\s*$", frm)
    if m:
        return m.group(1).strip() or m.group(2), m.group(2)
    return frm, frm


def pretty_from(frm: str) -> str:
    name, addr = split_name_addr(frm)
    return name if name and name != addr else addr

# ---------------------------------------------------------------------------
# Rendering helpers
# ---------------------------------------------------------------------------

def esc(s: str) -> str:
    return html.escape(s, quote=False)


def escq(s: str) -> str:
    return html.escape(s, quote=True)


def parse_date(s: str | None, default: date) -> date:
    if not s:
        return default
    try:
        return datetime.strptime(s[:10], "%Y-%m-%d").date()
    except ValueError:
        return default


def monday_of(d: date) -> date:
    return d - timedelta(days=d.weekday())


def slot_of(minutes: int) -> int:
    return max(0, min(SLOTS_PER_DAY - 1, (minutes - GRID_START_H * 60) // 30))


def slot_label(slot: int) -> str:
    mins = GRID_START_H * 60 + slot * 30
    return f"{mins // 60:02d}:{mins % 60:02d}"


def layout_day(events: list[CalEvent]) -> list[tuple[CalEvent, int, int, int, int]]:
    """Return (event, slot_start, slot_end, col, ncols) for a day.
    Overlapping events share columns; non-overlapping get one column."""
    evs = [e for e in events if e.end_min() > GRID_START_H * 60
           and e.start_min() < GRID_END_H * 60]
    evs.sort(key=lambda e: (e.start_min(), e.end_min()))
    # group into clusters of transitively-overlapping intervals
    clusters: list[list[CalEvent]] = []
    cur: list[CalEvent] = []
    cur_end = -1
    for e in evs:
        if cur and e.start_min() >= cur_end:
            clusters.append(cur)
            cur = []
            cur_end = -1
        cur.append(e)
        cur_end = max(cur_end, e.end_min())
    if cur:
        clusters.append(cur)
    out = []
    for cluster in clusters:
        # greedy interval coloring within the cluster
        col_end: list[int] = []
        ev_cols: dict[int, int] = {}
        for e in cluster:
            s, en = e.start_min(), e.end_min()
            for c, end in enumerate(col_end):
                if s >= end:
                    col_end[c] = en
                    ev_cols[id(e)] = c
                    break
            else:
                ev_cols[id(e)] = len(col_end)
                col_end.append(en)
        ncols = len(col_end)
        for e in cluster:
            out.append((e, slot_of(e.start_min()), slot_of(e.end_min()),
                        ev_cols[id(e)], ncols))
    return out


_DAYH = SLOTS_PER_DAY * 44

PAGE_CSS = """
:root { --aurora1:#7df9ff; --aurora2:#8affc1; --aurora3:#c4b5fd;
        --bg:#0b1020; --panel:#121a30; --panel2:#0e1526;
        --text:#e8edf7; --muted:#8b96ad; --accent:#7df9ff;
        --line:rgba(125,249,255,.14); --line2:rgba(125,249,255,.28); }
* { box-sizing:border-box; }
body { margin:0; font-family:ui-sans-serif,system-ui,'Segoe UI',Roboto,sans-serif;
       background:radial-gradient(1200px 500px at 70% -10%, rgba(125,249,255,.13), transparent 60%),
                  radial-gradient(900px 400px at 20% -10%, rgba(196,181,253,.11), transparent 60%),
                  var(--bg); color:var(--text); min-height:100vh; }
header { display:flex; align-items:center; gap:14px; padding:16px 24px;
         border-bottom:1px solid var(--line2);
         background:rgba(10,15,30,.7); backdrop-filter:blur(6px);
         position:sticky; top:0; z-index:5; }
.logo { font-size:26px; }
h1 { font-size:16.5px; margin:0; letter-spacing:.4px; }
.subtitle { color:var(--muted); font-size:12.5px; margin-top:2px; }
nav { display:flex; gap:8px; margin-left:auto; flex-wrap:wrap; }
nav a { text-decoration:none; color:var(--text); background:var(--panel);
        border:1px solid var(--line2); padding:8px 14px; border-radius:10px;
        font-size:13.5px; }
nav a.active { background:linear-gradient(90deg, rgba(125,249,255,.22), rgba(196,181,253,.22));
               border-color:var(--accent); }
main { max-width:1240px; margin:0 auto; padding:22px 20px 70px; }
a { color:var(--aurora1); }
.card { background:var(--panel); border:1px solid var(--line);
        border-radius:14px; padding:20px 22px; margin-bottom:16px; }
.muted { color:var(--muted); }
.small { font-size:12.5px; }
.row { display:flex; gap:12px; align-items:center; flex-wrap:wrap; }
.spread { justify-content:space-between; }
.btn { display:inline-block; text-decoration:none; background:var(--panel2);
  border:1px solid var(--line2); color:var(--text); border-radius:10px;
  padding:8px 14px; font-size:13.5px; cursor:pointer; }
.btn:hover { border-color:var(--accent); }
.btn.primary { background:linear-gradient(90deg, rgba(125,249,255,.25), rgba(196,181,253,.25));
  border-color:var(--accent); }
/* agent hint */
.agent-hint { background:rgba(125,249,255,.07); border:1px dashed var(--line2);
  border-radius:12px; padding:13px 17px; margin-bottom:16px; font-size:13px; line-height:1.55; }
.agent-hint h3 { margin:0 0 7px; font-size:13.5px; color:var(--accent); }
.agent-hint code { background:var(--panel2); padding:2px 7px; border-radius:6px;
  font-size:12px; color:var(--aurora2); }
/* ---------- calendar ---------- */
.cal-toolbar { display:flex; align-items:center; gap:10px; flex-wrap:wrap; margin-bottom:14px; }
.cal-title { font-size:18px; font-weight:650; min-width:220px; }
.cal-grid-wrap { overflow-x:auto; background:var(--panel); border:1px solid var(--line);
  border-radius:14px; }
table.cal { border-collapse:collapse; width:100%; min-width:980px; table-layout:fixed; }
table.cal th, table.cal td { border:1px solid var(--line); vertical-align:top; }
table.cal thead th { position:sticky; top:0; background:var(--panel2); padding:9px 8px;
  font-size:13px; text-align:left; z-index:2; }
table.cal thead th .dow { color:var(--muted); font-size:11px; text-transform:uppercase;
  letter-spacing:.8px; display:block; }
table.cal thead th .dnum { font-size:15px; }
table.cal thead th.today .dnum { background:var(--accent); color:#08131f;
  border-radius:8px; padding:1px 8px; }
td.hourcol { width:58px; min-width:58px; background:var(--panel2); }
td.hourcol div { height:44px; }
td.hourcol div span { font-size:10.5px; color:var(--muted); display:block;
  transform:translateY(-7px); padding-left:6px; }
td.daycell { position:relative; height:@DAYHpx; padding:0; }
.slotline { position:absolute; left:0; right:0; border-top:1px solid rgba(125,249,255,.06); }
.slotline.half { border-top-style:dashed; }
.event { position:absolute; left:2px; right:2px; border-radius:7px; padding:3px 7px;
  font-size:11.5px; line-height:1.3; overflow:hidden; cursor:pointer; text-decoration:none;
  color:#08131f; display:block; border-left:3px solid rgba(8,19,31,.45); }
.event:hover { filter:brightness(1.12); }
.event .ev-time { font-size:10px; opacity:.75; display:block; }
.event .ev-title { font-weight:600; display:block; }
.ev-c0 { background:linear-gradient(180deg,#9ff3ff,#5fd6e8); }
.ev-c1 { background:linear-gradient(180deg,#c9ffdd,#7fe0a8); }
.ev-c2 { background:linear-gradient(180deg,#e5d9ff,#b39ddb); }
.ev-c3 { background:linear-gradient(180deg,#ffe3b3,#f0b96a); }
.ev-c4 { background:linear-gradient(180deg,#ffc9d4,#ef94a8); }
.ev-c5 { background:linear-gradient(180deg,#d6ecff,#8fc1e8); }
.nowline { position:absolute; left:0; right:0; height:2px; background:#ff5d5d; z-index:3; }
.nowline::before { content:''; position:absolute; left:-4px; top:-3px; width:8px;
  height:8px; border-radius:50%%; background:#ff5d5d; }
/* agenda */
.agenda-item { display:flex; gap:12px; padding:9px 10px; border-bottom:1px solid var(--line);
  text-decoration:none; color:var(--text); border-radius:8px; }
.agenda-item:hover { background:var(--panel2); }
.agenda-time { font-family:ui-monospace,monospace; font-size:12px; color:var(--accent);
  min-width:104px; padding-top:1px; }
.agenda-title { font-size:13.5px; font-weight:600; }
.agenda-where { font-size:12px; color:var(--muted); }
/* ---------- inbox ---------- */
.mail-search { display:flex; gap:10px; margin-bottom:14px; }
.mail-search input { flex:1; background:var(--panel2); color:var(--text);
  border:1px solid var(--line2); border-radius:10px; padding:10px 14px; font-size:14px; }
table.mail { width:100%; border-collapse:collapse; }
table.mail td { padding:10px 12px; border-bottom:1px solid var(--line); font-size:13.5px;
  vertical-align:top; }
table.mail tr.unread td { background:rgba(125,249,255,.035); }
table.mail tr:hover td { background:var(--panel2); }
.mail-time { font-family:ui-monospace,monospace; font-size:12px; color:var(--muted);
  white-space:nowrap; width:132px; }
.mail-from { color:var(--aurora1); white-space:nowrap; width:250px; overflow:hidden;
  text-overflow:ellipsis; max-width:250px; }
.mail-subj { font-weight:500; }
.mail-subj .preview { color:var(--muted); font-weight:400; font-size:12px;
  display:block; margin-top:2px; overflow:hidden; text-overflow:ellipsis;
  white-space:nowrap; max-width:520px; }
a.mailrow { text-decoration:none; color:inherit; display:block; }
.badge { font-size:10.5px; padding:2px 9px; border-radius:999px; border:1px solid;
  white-space:nowrap; }
.badge.related { color:var(--aurora2); border-color:rgba(138,255,193,.4); }
.badge.spam { color:#f0a5a5; border-color:rgba(240,165,165,.4); }
.badge.newsletter { color:#f5d76e; border-color:rgba(245,215,110,.4); }
.badge.request { color:var(--accent); border-color:rgba(125,249,255,.4); }
.badge.misc { color:var(--aurora3); border-color:rgba(196,181,253,.4); }
/* email detail */
.email-head { border-bottom:1px solid var(--line); padding-bottom:14px; margin-bottom:16px; }
.email-subj { font-size:19px; font-weight:650; margin:0 0 8px; }
.email-meta { display:flex; gap:18px; flex-wrap:wrap; font-size:13px; color:var(--muted); }
.email-meta b { color:var(--text); font-weight:600; }
.email-body { white-space:pre-wrap; font-size:14px; line-height:1.65; }
.email-nav { display:flex; justify-content:space-between; margin-top:20px; gap:10px; }
/* event detail */
.dt-time { font-size:14px; color:var(--accent); font-family:ui-monospace,monospace; }
.dt-title { font-size:20px; font-weight:650; margin:6px 0 14px; }
dt { color:var(--muted); font-size:12.5px; text-transform:uppercase; letter-spacing:.6px;
  margin-top:14px; }
dd { margin:4px 0 0; font-size:14px; line-height:1.55; }
/* send form */
label { display:block; font-size:13px; color:var(--muted); margin:14px 0 6px; }
input[type=text], textarea { width:100%; background:var(--panel2); color:var(--text);
  border:1px solid var(--line2); border-radius:10px; padding:10px 12px;
  font-size:14px; font-family:inherit; }
textarea { min-height:130px; resize:vertical; }
.flash { margin:14px 0 0; font-size:13.5px; color:var(--aurora2); }
footer { text-align:center; color:var(--muted); font-size:12px; padding:18px; }
""".replace("@DAYH", str(_DAYH))

AGENT_HINT = """
<div class="agent-hint">
<h3>&#129303; For your agent</h3>
The source of truth for this app is two plain markdown files — read them directly:
<code>GET /calendar.md</code> (14 days of entries) and <code>GET /inbox.md</code>
(every email, newest first, each starting with a <code>## [YYYY-MM-DD HH:MM] From: ...</code> heading).
They also exist on disk at <code>{data_dir}/calendar.md</code> and <code>{data_dir}/inbox.md</code>.
</div>
""".strip()


def shell(active: str, title: str, body: str, hint: bool = False) -> str:
    h = AGENT_HINT.format(data_dir=DATA_DIR) if hint else ""
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(title)} — UAA Chancellor Mail &amp; Calendar</title>
<style>{PAGE_CSS}</style>
</head>
<body>
<header>
  <div class="logo">&#127773;</div>
  <div>
    <h1>UAA Chancellor Mail &amp; Calendar</h1>
    <div class="subtitle">Dr. Ingrid Halvorsen &middot; University of Alaska Anchorage &middot; (simulated)</div>
  </div>
  <nav>
    <a href="/calendar" class="{ 'active' if active=='calendar' else '' }">&#128197; Calendar</a>
    <a href="/inbox" class="{ 'active' if active=='inbox' else '' }">&#9993; Inbox</a>
    <a href="/send" class="{ 'active' if active=='send' else '' }">&#10133; Send</a>
  </nav>
</header>
<main>
{h}
{body}
</main>
<footer>Fake mailbox &amp; calendar for the Next Day Preparation agent workshop. All data is simulated.
Data files: <code>data/calendar.md</code> &middot; <code>data/inbox.md</code></footer>
</body>
</html>"""

# ---------------------------------------------------------------------------
# Calendar pages
# ---------------------------------------------------------------------------

def cal_page(days: dict[str, list[CalEvent]], today: date, start: date,
             day_focus: date | None) -> str:
    monday = monday_of(start)
    week = [monday + timedelta(days=i) for i in range(7)]
    # title
    y1, y2 = week[0].year, week[6].year
    t1 = week[0].strftime("%B %d")
    t2 = week[6].strftime("%B %d, %Y" if y1 != y2 else "")
    title = f"{t1} – {t2}"

    prev_m, next_m = monday - timedelta(days=7), monday + timedelta(days=7)

    # build grid
    day_blocks = []
    for i, d in enumerate(week):
        iso = d.isoformat()
        evs = days.get(iso, [])
        layout = layout_day(evs)
        cells = []
        for s in range(1, SLOTS_PER_DAY):
            half = (s % 2 == 0)  # :00 lines solid, :30 dashed
            cells.append(f'<div class="slotline{" half" if half else ""}" '
                         f'style="top:{s*44-1}px"></div>')
        ev_html = []
        for (e, s0, s1, col, ncols) in layout:
            idx = evs.index(e)
            top = s0 * 44 + 1
            height = max(22, (s1 - s0) * 44 - 3)
            width_pct = 100.0 / ncols
            left = col * width_pct
            style = (f"top:{top}px;height:{height}px;left:calc({left}% + 2px);"
                     f"right:auto;width:calc({width_pct}% - 4px);")
            ev_html.append(
                f'<a class="event ev-c{col % 6}" style="{style}" '
                f'href="/event?d={iso}&i={idx}" title="{escq(e.title)}">'
                f'<span class="ev-time">{e.start}–{e.end}</span>'
                f'<span class="ev-title">{esc(e.title)}</span></a>')
        # now line
        nowline = ""
        if d == today:
            nowdt = datetime.now()
            nm = nowdt.hour * 60 + nowdt.minute
            if GRID_START_H * 60 <= nm <= GRID_END_H * 60:
                top = (nm - GRID_START_H * 60) / 30 * 44
                nowline = f'<div class="nowline" style="top:{top:.1f}px"></div>'
        is_today = " today" if d == today else ""
        day_blocks.append(
            f'<td class="daycell">{"".join(cells)}{"".join(ev_html)}{nowline}</td>')

    head_cells = []
    for d in week:
        cls = " class='today'" if d == today else ""
        head_cells.append(
            f'<th{cls}><span class="dow">{WEEKDAY_SHORT[d.weekday()]}</span>'
            f'<span class="dnum">{d.strftime("%b %d")}</span></th>')

    hour_cells = []
    for s in range(0, SLOTS_PER_DAY, 2):
        label = slot_label(s)
        hour_cells.append(
            f'<td class="hourcol"><div style="height:88px"><span>{label}</span>'
            f'<div style="height:44px"></div></div></td>')

    # one body row: hour column + 7 tall day cells with absolutely
    # positioned events
    body = ('<tr>'
            '<td class="hourcol">' + "".join(
                f'<div style="height:44px"><span style="font-size:10.5px;'
                f'color:var(--muted);display:block;transform:translateY(-7px);'
                f'padding-left:6px">{slot_label(s)}</span></div>'
                for s in range(0, SLOTS_PER_DAY, 2)) + "</td>"
            + "".join(day_blocks) + "</tr>")

    grid = (f'<table class="cal"><thead>'
            f'<tr><th class="hourcol" style="width:58px"></th>{"".join(head_cells)}</tr>'
            f'</thead><tbody>{body}</tbody></table>')

    # agenda for focused day
    focus = day_focus or (today if today in week else week[0])
    if focus not in week:
        focus = week[0]
    agenda_evs = sorted(days.get(focus.isoformat(), []), key=lambda e: e.start)
    agenda = ""
    if agenda_evs:
        items = []
        for idx, e in enumerate(agenda_evs):
            items.append(
                f'<a class="agenda-item" href="/event?d={focus.isoformat()}&i={idx}">'
                f'<span class="agenda-time">{e.start}–{e.end}</span>'
                f'<span><span class="agenda-title">{esc(e.title)}</span><br>'
                f'<span class="agenda-where">{esc(e.where)}</span></span></a>')
        agenda = (f'<div class="card" style="margin-top:16px">'
                  f'<h3 style="margin:0 0 8px;font-size:15px">'
                  f'&#128197; {WEEKDAY_LONG[focus.weekday()]}, '
                  f'{focus.strftime("%B %d, %Y")} — {len(agenda_evs)} event(s)</h3>'
                  f'{"".join(items)}</div>')

    toolbar = f"""
<div class="cal-toolbar">
  <a class="btn" href="/calendar?start={prev_m.isoformat()}">&#8592; Prev</a>
  <a class="btn" href="/calendar?start={monday.isoformat()}">Today</a>
  <a class="btn" href="/calendar?start={next_m.isoformat()}">Next &#8594;</a>
  <span class="cal-title">{esc(title)}</span>
  <span class="muted small">Click an event for details</span>
</div>"""

    return f"""
{toolbar}
<div class="cal-grid-wrap">{grid}</div>
{agenda}
"""


def event_page(days: dict[str, list[CalEvent]], today: date, d: date,
               idx: int) -> str:
    iso = d.isoformat()
    evs = days.get(iso, [])
    if idx < 0 or idx >= len(evs):
        return ('<div class="card">Event not found. '
                f'<a href="/calendar?start={monday_of(d).isoformat()}">Back to calendar</a></div>')
    e = evs[idx]
    dur = e.end_min() - e.start_min()
    dur_s = f"{dur // 60} h {dur % 60:02d} m" if dur % 60 else f"{dur // 60} h"
    monday = monday_of(d)
    notes_html = ""
    if e.notes:
        notes_html = f"<dt>Notes</dt><dd>{esc(e.notes)}</dd>"
    where_html = f"<dt>Location</dt><dd>{esc(e.where or '—')}</dd>"
    return f"""
<div class="card">
  <div class="row spread">
    <a class="btn" href="/calendar?start={monday.isoformat()}">&#8592; Week of {monday.strftime("%b %d")}</a>
    <a class="btn" href="/calendar?day={d.isoformat()}">View this day</a>
  </div>
  <div class="dt-time" style="margin-top:16px">{WEEKDAY_LONG[d.weekday()]}, {d.strftime("%B %d, %Y")} &middot; {e.start}–{e.end} ({dur_s})</div>
  <div class="dt-title">{esc(e.title)}</div>
  <dl>{where_html}{notes_html}</dl>
</div>
"""

# ---------------------------------------------------------------------------
# Inbox pages
# ---------------------------------------------------------------------------

SPAM_HINTS = ("WIN-A-WOLF", "FREE CRUISE", "Mammoth Mortgage", "Permafrost Financial",
              "the moose knows", "FLASH SALE", "90% off", "95% off", "walrus-view",
              "cruise reservation", "mystery rattle (used)", "Tundra: '5 Signs",
              "Tundra: 'Is Your", "Tundra: 'Mystery Rattle", "Tundra: 'Aurora Season",
              "Tundra: 'Chancellor", "90% off", "zamboni is NOT", "UNDER OFFER",
              "thaw has BEGUN", "thaw is a SOCIAL", "ground is a FACT",
              "LAST CHANCE: Arctic")
NEWS_HINTS = ("UAK Weekly", "IHE:", "APM:", "DKNG:", "KENA:", "Chamber:",
              "Alaska Business:", "Aurora Spotlight:", "UAA News:",
              "AK Electric Co-op:", "UAA Athletics:", "NWS:")


def guess_tag(frm: str, subj: str, body: str) -> str:
    hay = subj + " " + frm
    if any(h in hay for h in SPAM_HINTS):
        return "spam"
    if any(h in hay for h in NEWS_HINTS):
        return "newsletter"
    low = (subj + " " + frm).lower()
    if any(k in low for k in ("ticket #", "hr:", "facilities:", "campus police",
                              "food & dining", "delta", "hyatt", "nws",
                              "advancement:", "alumni:", "aurora club:",
                              "student senate:", "it ticket")):
        return "request"
    return "misc"


def mail_list_page(msgs: list[Msg], q: str) -> str:
    q2 = q.strip().lower()
    rows = []
    shown = 0
    for i, m in enumerate(msgs):
        if q2:
            hay = (m.frm + " " + m.subject + " " + m.body).lower()
            if q2 not in hay:
                continue
        shown += 1
        name = pretty_from(m.frm)
        tag = guess_tag(m.frm, m.subject, m.body)
        preview = " ".join(m.body.split())[:120]
        rows.append(
            f'<tr><td class="mail-time">{m.day} {m.tstamp}</td>'
            f'<td class="mail-from">{esc(name)}</td>'
            f'<td class="mail-subj"><a class="mailrow" href="/email?i={i}&d={m.day}">'
            f'{esc(m.subject)}<span class="preview">{esc(preview)}</span></a>'
            f' <span class="badge {tag}">{tag}</span></td></tr>')
    count_txt = (f'{len(msgs)} messages' if not q2
                 else f'{shown} of {len(msgs)} messages match "{esc(q)}"')
    search = f"""
<form method="get" action="/inbox" class="mail-search">
  <input type="text" name="q" value="{escq(q)}" placeholder="Search subject, sender, or body...">
  <button class="btn primary" type="submit">Search</button>
</form>"""
    table = (f'<div class="card" style="padding:0;overflow:hidden">'
             f'<table class="mail">{"".join(rows) if rows else "<tr><td class=\"muted\">No matches.</td></tr>"}'
             f'</table></div>')
    return f"""
<div class="row spread" style="margin-bottom:10px">
  <h3 style="margin:0;font-size:16px">&#9993; Inbox</h3>
  <span class="muted small">{count_txt} &middot; newest first</span>
</div>
{search}
{table}
"""


def mail_page(msgs: list[Msg], i: int) -> str:
    if i < 0 or i >= len(msgs):
        return '<div class="card">Message not found. <a href="/inbox">Back to inbox</a></div>'
    m = msgs[i]
    name, addr = split_name_addr(m.frm)
    tag = guess_tag(m.frm, m.subject, m.body)
    prev_btn = (f'<a class="btn" href="/email?i={i-1}&d={m.day}">&#8592; Newer</a>'
                if i > 0 else '<span></span>')
    next_btn = (f'<a class="btn" href="/email?i={i+1}&d={m.day}">Older &#8594;</a>'
                if i < len(msgs) - 1 else '<span></span>')
    return f"""
<div class="card">
  <div class="row spread" style="margin-bottom:12px">
    <a class="btn" href="/inbox">&#8592; Inbox</a>
    <span class="muted small">Message {i+1} of {len(msgs)} &middot;
    <span class="badge {tag}">{tag}</span></span>
  </div>
  <div class="email-head">
    <div class="email-subj">{esc(m.subject)}</div>
    <div class="email-meta">
      <span>&#9993; From: <b>{esc(name)}</b> <span class="muted">&lt;{esc(addr)}&gt;</span></span>
      <span>&#128197; {m.day} {m.tstamp}</span>
      <span>To: <b>Dr. Ingrid Halvorsen</b> &lt;ingrid.halvorsen@alaska.edu&gt;</span>
    </div>
  </div>
  <div class="email-body">{esc(m.body) if m.body else '<span class="muted">(no body)</span>'}</div>
  <div class="email-nav">{prev_btn}{next_btn}</div>
</div>
"""


def send_page() -> str:
    return """
<div class="card" style="max-width:640px">
<h3 style="margin-top:0;">Send a test email</h3>
<p class="subtitle" style="margin-top:0">Appends a new message to the simulated
inbox — useful for testing that your agent picks up fresh mail. Stored in
<code>data/inbox.md</code>.</p>
<form method="post" action="/send">
  <label>From</label>
  <input type="text" name="from" placeholder="e.g. Surprised Donor &lt;donor@example.org&gt;" required>
  <label>Subject</label>
  <input type="text" name="subject" placeholder="e.g. Re: tomorrow's donor breakfast" required>
  <label>Body</label>
  <textarea name="body" placeholder="Message body (plain text)..." required></textarea>
  <p><button class="btn primary" type="submit">Send to inbox</button></p>
</form>
</div>
"""

# ---------------------------------------------------------------------------
# Data access
# ---------------------------------------------------------------------------

def read_file(name: str) -> str | None:
    p = DATA_DIR / name
    if not p.exists():
        return None
    return p.read_text(encoding="utf-8")


def count_emails(text: str) -> int:
    return len(re.findall(r"^## \[\d{4}-\d{2}-\d{2}", text, re.M))


def count_events(text: str) -> int:
    return len(re.findall(r"^- \d{2}:\d{2}", text, re.M))


def newest_inbox_timestamp(text: str) -> datetime:
    """Return the newest timestamp among existing inbox entries.

    Falls back to the current time (truncated to the minute) when the inbox is
    empty. The returned value is guaranteed to be >= every existing entry.
    """
    stamps = re.findall(r"^## \[(\d{4}-\d{2}-\d{2}) (\d{2}:\d{2})\]", text, re.M)
    if not stamps:
        return datetime.now().replace(second=0, microsecond=0)
    best = max(f"{d} {t}" for d, t in stamps)
    return datetime.strptime(best, "%Y-%m-%d %H:%M")


def append_email(frm: str, subj: str, body: str) -> str:
    text = read_file(INBOX_FILE)
    if text is None:
        raise RuntimeError("inbox.md not found — run generate.py first")
    # Date the new mail a couple of minutes after the most recent message so it
    # is always the newest entry in the inbox (rather than using wall-clock time).
    now = newest_inbox_timestamp(text) + timedelta(minutes=2)
    entry = (f"\n## [{now.strftime('%Y-%m-%d')} {now.strftime('%H:%M')}] From: {frm}\n"
             f"**Subject:** {subj}\n\n{body.strip()}\n\n---\n")
    marker = "_End of inbox export._"
    if marker in text:
        text = text.replace(marker, entry + marker, 1)
    else:
        text = text.rstrip() + "\n" + entry
    new_count = count_emails(text)
    text = re.sub(r"^Total messages: \d+", f"Total messages: {new_count}", text,
                  flags=re.M)
    (DATA_DIR / INBOX_FILE).write_text(text, encoding="utf-8")
    return now.strftime("%Y-%m-%d %H:%M")

# ---------------------------------------------------------------------------
# HTTP handler
# ---------------------------------------------------------------------------

class Handler(BaseHTTPRequestHandler):
    server_version = "UAAWorkshop/1.1"

    def log_message(self, fmt: str, *args):
        print("[http]", fmt % args)

    def _send(self, code: int, body: bytes, ctype: str):
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def _html(self, active: str, title: str, body: str, hint: bool = False,
              code: int = 200):
        self._send(code, shell(active, title, body, hint).encode("utf-8"),
                   "text/html; charset=utf-8")

    def _redirect(self, loc: str):
        self.send_response(302)
        self.send_header("Location", loc)
        self.end_headers()

    def do_GET(self):
        url = urlparse(self.path)
        path = url.path.rstrip("/") or "/"
        qs = {k: v[0] for k, v in parse_qs(url.query).items()}
        today = date.today()

        if path == "/":
            self._redirect("/calendar")
        elif path == "/calendar":
            cal = read_file(CALENDAR_FILE)
            if cal is None:
                self._send(503, "calendar.md missing - run: python3 generate.py".encode(),
                           "text/plain; charset=utf-8")
                return
            days = parse_calendar(cal)
            day_focus = parse_date(qs.get("day"), today) if qs.get("day") else None
            if day_focus:
                start = monday_of(day_focus)
            else:
                start = parse_date(qs.get("start"), monday_of(today))
            self._html("calendar", "Calendar",
                       cal_page(days, today, start, day_focus), hint=True)
        elif path == "/event":
            cal = read_file(CALENDAR_FILE)
            days = parse_calendar(cal) if cal else {}
            d = parse_date(qs.get("d"), date.today())
            try:
                idx = int(qs.get("i", "-1"))
            except ValueError:
                idx = -1
            self._html("calendar", "Event",
                       event_page(days, today, d, idx), hint=True)
        elif path == "/inbox":
            box = read_file(INBOX_FILE)
            if box is None:
                self._send(503, "inbox.md missing - run: python3 generate.py".encode(),
                           "text/plain; charset=utf-8")
                return
            msgs = parse_inbox(box)
            self._html("inbox", "Inbox", mail_list_page(msgs, qs.get("q", "")),
                       hint=True)
        elif path == "/email":
            box = read_file(INBOX_FILE)
            msgs = parse_inbox(box) if box else []
            try:
                i = int(qs.get("i", "-1"))
            except ValueError:
                i = -1
            self._html("inbox", "Email", mail_page(msgs, i), hint=True)
        elif path == "/send":
            self._html("send", "Send", send_page())
        elif path == "/calendar.md":
            self._raw(CALENDAR_FILE)
        elif path == "/inbox.md":
            self._raw(INBOX_FILE)
        elif path == "/api/health":
            cal = read_file(CALENDAR_FILE)
            box = read_file(INBOX_FILE)
            payload = {
                "status": "ok",
                "data_dir": str(DATA_DIR),
                "calendar_events": count_events(cal) if cal else 0,
                "inbox_messages": count_emails(box) if box else 0,
                "endpoints": {
                    "calendar_md": "/calendar.md",
                    "inbox_md": "/inbox.md",
                    "send_api": "POST /api/send",
                },
            }
            self._send(200, json.dumps(payload, indent=2).encode(),
                       "application/json")
        else:
            self._send(404, b"not found", "text/plain")

    def do_POST(self):
        url = urlparse(self.path)
        if url.path.rstrip("/") in ("/api/send", "/send"):
            try:
                frm, subj, body = self._read_send_payload()
            except ValueError as e:
                self._send(400, str(e).encode(), "application/json")
                return
            ts = append_email(frm, subj, body)
            if url.path.rstrip("/") == "/api/send":
                self._send(201, json.dumps({"ok": True, "received_at": ts}).encode(),
                           "application/json")
            else:
                # the new message was appended to inbox.md; locate it now that
                # the parsed list is sorted newest-first
                box = read_file(INBOX_FILE)
                msgs = parse_inbox(box) if box else []
                new_day, new_tstamp = ts[:10], ts[11:16]
                i = next((idx for idx, m in enumerate(msgs)
                          if m.day == new_day and m.tstamp == new_tstamp), 0)
                self._redirect(f"/email?i={i}&d={new_day}")
        else:
            self._send(404, b"not found", "text/plain")

    def _raw(self, name: str):
        text = read_file(name)
        if text is None:
            self._send(404, f"{name} not found".encode(), "text/plain")
            return
        self._send(200, text.encode("utf-8"), "text/markdown; charset=utf-8")

    def _read_send_payload(self):
        ctype = self.headers.get("Content-Type", "")
        length = int(self.headers.get("Content-Length", 0))
        raw = self.rfile.read(length) if length else b""
        if "application/json" in ctype:
            try:
                data = json.loads(raw.decode("utf-8"))
            except json.JSONDecodeError:
                raise ValueError("invalid JSON")
        else:
            form = parse_qs(raw.decode("utf-8"))
            data = {k: v[0] for k, v in form.items()}
        frm = (data.get("from") or "").strip()
        subj = (data.get("subject") or "").strip()
        body = (data.get("body") or "").strip()
        if not frm or not subj or not body:
            raise ValueError("fields 'from', 'subject', 'body' are required")
        return frm, subj, body

# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    global DATA_DIR
    ap = argparse.ArgumentParser(
        description="UAA Chancellor Mail & Calendar (workshop simulator)")
    ap.add_argument("--port", type=int, default=8321)
    ap.add_argument("--host", default="0.0.0.0")
    ap.add_argument("--data-dir", type=Path, default=HERE / "data")
    args = ap.parse_args()
    DATA_DIR = args.data_dir.resolve()

    for name in (CALENDAR_FILE, INBOX_FILE):
        if not (DATA_DIR / name).exists():
            print(f"warning: {DATA_DIR/name} missing — run 'python3 generate.py' first")

    httpd = ThreadingHTTPServer((args.host, args.port), Handler)
    print(f"UAA Chancellor Mail & Calendar running at http://{args.host}:{args.port}")
    print(f"  data dir: {DATA_DIR}")
    print("  agent endpoints: GET /calendar.md  GET /inbox.md  POST /api/send")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nshutting down")


if __name__ == "__main__":
    main()
