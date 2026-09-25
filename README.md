# Next Day Preparation — Workshop Simulator

A fake **email + calendar** web app for the AI Symposium agent-LLM workshop. 
Participants build a **"Email Action Items" via CoPilot** and also
build a **"Next Day Preparation" agent** via CoPilot or Hermes Agent.
It reads the simulated calendar for
*tomorrow* (current day always 9/25), summarizes the day's schedule, 
then scans the simulated inbox for
emails relevant to each calendar event and attaches them as context.

The mailbox belongs to **Dr. Ingrid Halvorsen, Chancellor of the University
of Alaska Anchorage** — so the data includes board meetings, state budget
testimony, a permafrost-lab ribbon cutting, an aurora donor gala, Arctic wolf
pack telemetry, Ralph the Walrus (mascot), and a suspicious amount of spam.

Everything is self-contained: **Python 3, no
real email or calendar accounts.**

## Quick start

```bash
source /home/vscode/calendar_email_env/bin/activate
python3 app.py
```

Open in a browser; on github codespace you'll be given a link, if running standalone open on <http://localhost:8321> .

Options:

```bash
python3 generate.py 2026-09-01   # date the sample data relative to a specific day
python3 app.py --port 9000       # custom port
python3 app.py --host 0.0.0.0    # expose on the LAN (for a workshop room)
```

## What's in the data

- `data/calendar.md` — **14 days** of calendar entries (today + next 13 days),
  45 events. Each day is a `## Weekday, Month D, YYYY` heading; each event is
  `- HH:MM–HH:MM — **Title**` with indented `Location:` and `Notes:` lines.
- `data/inbox.md` — **154 emails**, newest first, spread over the past two
  weeks. Each message starts with a `## [YYYY-MM-DD HH:MM] From: ...` heading,
  followed by a `**Subject:**` line and the body.

The corpus is deliberately mixed:

| Kind | What it is |
|---|---|
| **Event-related** (~30) | Agendas, logistics, reminders, confirmations for calendar events — *especially for tomorrow and the day after* (donor breakfast, ribbon cutting, chancellor forum, aurora forecast review, Juneau trip, the gala). |
| **Spam** (~30) | Free-cruise scams, "the moose knows" forwards, Win-a-Wolf, Mammoth Mortgage… |
| **Newsletters** (~15) | University comms, local news, campus paper, NWS bulletins. |
| **Requests / ops** (~60) | IT tickets (the snow-machine automation system is "learning"), HR, facilities, campus police, food & dining, flight/hotel confirmations, press, development. |
| **Misc** (~20) | Regent notes, student forwards, the blue-folder inventory… |

**Relevance is never labeled.** The markdown files contain no tags; the
agent must decide for itself which emails belong to which event. (The web UI
shows small category badges as a human convenience, derived at render time —
the markdown the agent reads has none of that.)

## Web app

| URL | What it does |
|---|---|
| `/calendar` | Week view: 7 day-columns (Mon–Sun) × hour rows (07:00–22:00). Prev/Next/Today navigation, today highlighted, red "now" line. Below the grid: an agenda list for the focused day. |
| `/event?d=YYYY-MM-DD&i=N` | Event details (time, duration, location, notes). |
| `/inbox` | Inbox list, **newest first**: date/time, author, subject, one-line preview. Search box filters subject/sender/body. |
| `/email?i=N` | One email, full body, Newer/Older navigation. |
| `/send` | Form to append a test email to the simulated inbox (great for testing that an agent picks up *fresh* mail). |
| `/calendar.md`, `/inbox.md` | **Raw markdown — the files the agent should read.** |
| `/api/health` | JSON status (counts, data dir). |
| `POST /api/send` | JSON: `{"from": ..., "subject": ..., "body": ...}` — appends an email, returns the timestamp. |

## The workshop exercise (suggested)

For the calendar agent, here is a possible spec:

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

Things to look at:

- The markdown format blocks at the top of each data file describe the
  layout explicitly (LLM-friendly on purpose).
- The "next day" is relative to *today*: regenerate with `python3 generate.py`
  any day and the same scenario works, because all dates are computed from
  the current date.
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
 app.py          # web app (stdlib http.server, no dependencies)
 generate.py     # sample-data generator (dates relative to today)
 README.md
 data/
     calendar.md # 14 days of events
     inbox.md    # 154 emails
```

## Email tasks to try:
- Extract top action items
- Find a time to schedule the Title II meeting

## Calendar tasks to try:
- Find emails related to tomorrow's calendar items to provide context

## Starting Hermes Agent
In the terminal area, click the "+" and choose "New Terminal" then run:
```
sh ./setup.sh
```
If you do not see a new browser page, click on the "Ports" tab and then click on the globe icon to open the Hermes dashboard in a new window.

- To try: In chat or in cron, direct the agent to do email reconnaissance to provide context for the next day's calendar events.  They are located in data/calendar.md and data/inbox.md.
- Try having your agent send data to a Google Space!  Create a space in Google Chat, under the space's name choose Apps and Integration, create webhook, copy the URL, and provide to Hermes agent for delivery.
