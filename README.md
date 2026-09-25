# Next Day Preparation — Workshop Simulator

A fake **email + calendar** web app for an agent-LLM workshop. Participants
build a **"Next Day Preparation" agent**: it reads the simulated calendar for
*tomorrow*, summarizes the day's schedule, then scans the simulated inbox for
emails relevant to each calendar event and attaches them as context.

The mailbox belongs to **Dr. Ingrid Halvorsen, Chancellor of the University
of Alaska Anchorage** — so the data includes board meetings, state budget
testimony, a permafrost-lab ribbon cutting, an aurora donor gala, Arctic wolf
pack telemetry, Ralph the Walrus (mascot), and a suspicious amount of spam.

Everything is self-contained: **Python 3 stdlib only, no dependencies, no
real email or calendar accounts.**

## Quick start

```bash
cd next-day-prep
python3 generate.py        # (re)creates data/calendar.md + data/inbox.md,
                           # anchored on the workshop day: Fri 2026-09-25
python3 app.py             # serves the web app on http://localhost:8321
```

Open <http://localhost:8321> in a browser.

Options:

```bash
python3 generate.py 2026-10-02    # shift the whole world to a different "today"
python3 generate.py "$(date +%F)" # ...or anchor it on the real current date
python3 app.py --port 9000       # custom port
python3 app.py --host 0.0.0.0    # expose on the LAN (for a workshop room)
python3 app.py --today 2026-10-02  # override which date the UI calls "today"
```

**The simulated day is hard-coded to Friday 2026-09-25** (`SIM_TODAY` in both
`generate.py` and `app.py`), so the data, the answer key below, and the
calendar's **Today** button all line up no matter when you run it. `generate.py`
records the date it generated for in `data/base_date.txt` and `app.py` reads
that, so a shifted dataset stays consistent too; `SIM_TODAY` is only the
fallback when the file is missing.

Nothing reads the machine clock. The world's "now" is the newest timestamp in
the inbox — **Fri Sep 25, 17:45** on a fresh dataset — shown in the page header,
used for the red now-line on the calendar, reported by `GET /api/health` as
`now` / `today` / `tomorrow`, and stated in the "For your agent" box on the
calendar and inbox pages. Send something through `/send` and the clock ticks
forward to 17:47 with it, which is the point: the only way the world moves is
the mail.

## What's in the data

- `data/calendar.md` — **14 days** of calendar entries (today + next 13 days),
  45 events. Each day is a `## Weekday, Month D, YYYY` heading; each event is
  `- HH:MM–HH:MM — **Title**` with indented `Location:` and `Notes:` lines.
- `data/inbox.md` — **161 emails**, newest first, spread over the past two
  weeks. Each message starts with a `## [YYYY-MM-DD HH:MM] From: ...` heading,
  followed by a `**Subject:**` line and the body. Messages whose `From` is
  marked `(sent)` are copies of mail the Chancellor sent out.

The corpus is deliberately mixed:

| Kind | What it is |
|---|---|
| **Event-related** (~39, incl. the 8-message scheduling thread below) | Agendas, logistics, reminders, confirmations for calendar events — *especially for tomorrow and the day after* (donor breakfast, ribbon cutting, chancellor forum, aurora forecast review, Juneau trip, the gala). |
| **Spam** (~30) | Free-cruise scams, "the moose knows" forwards, Win-a-Wolf, Mammoth Mortgage… |
| **Newsletters** (~15) | University comms, local news, campus paper, NWS bulletins. |
| **Requests / ops** (~60) | IT tickets (the snow-machine automation system is "learning"), HR, facilities, campus police, food & dining, flight/hotel confirmations, press, development. |
| **Misc** (~20) | Regent notes, student forwards, the blue-folder inventory… |

### The scheduling thread (a second, harder exercise)

Buried in the recent mail is an eight-message thread, **"Title II working
session - which slots work for you?"**: the Chancellor's invitation (stored as
a sent message, so it shows a `sent` badge) plus seven replies, each quoting
the original at the bottom.

The invitation offers six slots for next week. Every reply says yes to some and
no to others, in prose, with caveats and no consistent format — the agent has
to read all seven and intersect them.

| Slot (week of Sep 28) | Who can make it |
|---|---|
| Mon Sep 28, 12:00–13:00 | 5 of 7 |
| Mon Sep 28, 15:00–16:00 | 4 of 7 |
| Tue Sep 29, 16:00–17:00 | 2 of 7 |
| **Wed Sep 30, 09:00–10:00** | **7 of 7** |
| Thu Oct 1, 12:00–13:00 | 3 of 7 |
| Thu Oct 1, 16:00–17:00 | 3 of 7 |

**Answer key (facilitator only):** Wed Sep 30, 09:00–10:00 is the only
slot every participant can attend, and the Chancellor has nothing in the
calendar at that time. The generator guarantees the six proposed slots stay
free on the Chancellor's own schedule (`clear_slots_for_titleii()` nudges or
drops clashing events), so the seven replies are the only thing deciding it.

Suggested prompt for this one: *"Read the inbox, find the thread about the
working session, and tell me which slot everyone can make."* Good follow-up:
*"Draft Katie's reply-all booking the room."*

**Relevance is never labeled.** The markdown files contain no tags; the
agent must decide for itself which emails belong to which event. The web UI
shows small category badges (`spam`, `newsletter`, `request`, `misc`, `sent`)
derived from subject/sender patterns at render time — the markdown the agent
reads has none of that. The heuristic deliberately **never** labels relevance:
the `misc` badge covers a lot of the most important mail in the inbox, so tell
participants not to let the badges do their reasoning.

## Web app

| URL | What it does |
|---|---|
| `/calendar` | Week view: 7 day-columns (Mon–Sun) × hour rows (07:00–22:00). Prev/Next/Today navigation, today highlighted, red "now" line. `?start=YYYY-MM-DD` moves the visible week, `?day=YYYY-MM-DD` focuses one day (that day's agenda is listed under the grid). |
| `/event?d=YYYY-MM-DD&i=N` | Event details (time, duration, location, notes). |
| `/inbox` | Inbox list, **newest first**: date/time, author, subject, one-line preview. Search box filters subject/sender/body. |
| `/email?i=N` | One email, full body, Newer/Older navigation. |
| `/send` | Form to append a test email to the simulated inbox (great for testing that an agent picks up *fresh* mail). |
| `/calendar.md`, `/inbox.md` | **Raw markdown — the files the agent should read.** |
| `/api/health` | JSON status: `today` / `tomorrow` (what the simulator calls today), counts, data dir. Handy for an agent working out which day is "next day". |
| `POST /api/send` | JSON: `{"from": ..., "subject": ..., "body": ...}` — appends an email, returns the timestamp. |

## The workshop exercise (suggested)

Give participants this spec:

> Build an agent that, when run in the morning:
> 1. Reads the calendar for **the next day** (`data/calendar.md` or
>    `GET /calendar.md`).
> 2. Produces a **schedule summary** for that day (time, title, location).
> 3. Scans the inbox (`data/inbox.md` or `GET /inbox.md`) and, **for each
>    calendar event**, finds the emails that provide context for it
>    (agendas, logistics, reminders, confirmations, relevant threads) and
>    attaches them under that event in the summary.
> 4. Ignores spam, newsletters, and requests unrelated to tomorrow's
>    schedule (or lists them briefly as "skipped").
> 5. Only uses emails *received before now* — tomorrow's mail doesn't exist
>    yet.
>
> **Success test:** run the agent, read its output for tomorrow, and check
> each event has the right context (e.g., the donor breakfast gets the
> endowment/naming discussion and parking info; the aurora briefing gets the
> Kp forecast; the ribbon cutting gets speaker order, media list, and the
> elevator warning) and that no spam or unrelated IT ticket snuck in.
>
> **Bonus:** after sending a new email with `/send` (or `POST /api/send`)
> that references one of tomorrow's events, re-run the agent and confirm the
> new mail shows up in the right place.

Things to point participants at:

- The markdown format blocks at the top of each data file describe the
  layout explicitly (LLM-friendly on purpose).
- "Today" in the simulation is **Friday Sep 25, 2026**, so the next day the
  agent prepares is **Saturday Sep 26, 2026** — which is when the donor
  breakfast, the aurora briefing and the rest land. This is hard-coded
  (`SIM_TODAY`), so the app and the answer key agree no matter when you run it.
  `GET /api/health` reports `today` / `tomorrow` if an agent needs to ask.
- Deliberate traps: emails for *other* days that mention the same topics
  (the Juneau testimony, the gala planning, a second Kp forecast), near-miss
  names, and the recurring "mystery rattle" that mentions almost nothing but
  distracts.

## Resetting

```bash
python3 generate.py     # wipes both files and regenerates the scenario
```

Any emails appended via `/send` disappear on regeneration.

## Files

```
next-day-prep/
├── app.py          # web app (stdlib http.server, no dependencies)
├── generate.py     # sample-data generator (anchored on SIM_TODAY, 2026-09-25)
├── README.md
└── data/
    ├── calendar.md    # 14 days of events
    ├── inbox.md       # 161 emails
    └── base_date.txt  # which date the data was generated for (read by app.py)
```
