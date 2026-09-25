#!/usr/bin/env python3
"""
Sample data generator for the "Next Day Preparation" agent workshop.

Creates data/calendar.md and data/inbox.md (relative to today's date) for a
simulated mailbox + calendar belonging to the Chancellor of the
University of Alaska Anchorage.

Usage:
    python3 generate.py            # dates relative to today
    python3 generate.py 2026-09-01 # dates relative to a specific date
"""
from __future__ import annotations

import random
import sys
from datetime import date, datetime, timedelta
from pathlib import Path

HERE = Path(__file__).resolve().parent
DATA = HERE / "data"

CHANCELLOR = "Dr. Ingrid Halvorsen"
CHANCELLOR_TITLE = "Chancellor, University of Alaska Anchorage"
CHANCELLOR_ADDR = "ingrid.halvorsen@alaska.edu"
OFFICE = "UAA Administration Building, 4200 UAA Loop Rd, Anchorage"
ADMIN_SUITE = "Administration Building, 2nd floor (suite 210)"

RNG = random.Random(20260819)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def hhmm(h: int, m: int = 0) -> str:
    return f"{h:02d}:{m:02d}"


def event(start: str, end: str, title: str, where: str = OFFICE,
          notes: str = "") -> dict:
    return {"start": start, "end": end, "title": title, "where": where,
            "notes": notes}


# ---------------------------------------------------------------------------
# Calendar — 14 days (offsets 0..13 from "today")
# ---------------------------------------------------------------------------
# Anchors are keyed by weekday (0=Mon) so the schedule stays believable
# whatever day the workshop runs. One-off events are keyed by offset.

WEEKDAY_ANCHORS: dict[int, list[dict]] = {
    0: [
        event("08:30", "11:00", "Board of Regents Meeting — Full Session",
              "Regents Chamber, UAA Administration Building",
              "Agenda: FY27 operating budget, endowment policy update, campus "
              "master plan comment period. Regent chair: K. Kwan. "
              "Regents: T. Redcloud, D. Okafor, P. Lindqvist, R. Boudreaux, "
              "S. Houghton, campus regent L. Taimi."),
        event("15:00", "16:00", "Office Hours (open to faculty, staff and students)",
              ADMIN_SUITE, "First-come, first-served. Student body president "
              "Maya Chen may stop by about the student senate budget request."),
    ],
    1: [
        event("10:00", "12:00", "Faculty Senate Business Meeting",
              "Knik Hall A, UAA Anchorage",
              "Faculty senate chair: Prof. Amara Diallo. Topics: faculty "
              "workload policy revision, new Arctic Engineering program "
              "proposal, library bond issue."),
    ],
    2: [
        event("13:30", "14:30", "Cabinet Review — Enrollment & Student Success",
              "Video conference (link from VP Student Affairs) + Administration "
              "Building 3rd floor bridge",
              "VP Student Affairs: Dr. Sam Whitcomb. VP Research: Dr. Priya "
              "Raman. Agenda: fall headcount, Aurora Club funding, new "
              "advisor positions."),
        event("16:00", "17:30", "Athletics Department Check-in",
              "Administration Building, conference room C",
              "Athletic director: Mike Frazier. Topics: Seawolves season "
              "readiness, NIL compliance memo, ice arena maintenance report."),
    ],
    3: [
        event("09:00", "10:30", "Executive Council Meeting",
              "Regents Chamber, UAA Administration Building",
              "All VPs and deans. Topics: space utilization plan, shared "
              "services consolidation, permafrost lab funding."),
    ],
    4: [
        event("11:00", "12:30", "1:1 with Provost — Dr. Elena Marsh",
              ADMIN_SUITE, "Mid-year curriculum portfolio review; faculty "
              "recruiting for the new Arctic Engineering program."),
        event("13:00", "13:45", "1:1 with CFO — Rajesh Iyer",
              ADMIN_SUITE, "FY27 mid-year cash position; state appropriation "
              "status."),
    ],
    5: [
        event("12:00", "14:00", "Seawolves Home Game Day — Front-Row Seating",
              "UAA Ice Arena, 4200 UAA Loop Rd",
              "Front-row seats for the chancellor's office. Athletic director "
              "Mike Frazier will meet at the arena office at 11:30. "
              "Mascot Ralph the Walrus has a photo op scheduled at 13:15."),
    ],
}

# One-off events, keyed by day offset from today (0 = today).
ONE_OFFS: dict[int, list[dict]] = {
    1: [
        event("08:30", "09:30", "Donor Breakfast — Halvorsen Family Foundation",
              "Copper River Room, UAA Administration Building",
              "Guests: Alan and Marjorie Halvorsen (founders of the Halvorsen "
              "Family Foundation), plus Development Director Carol "
              "Whitfield. Discussion: $2.5M gift for the Arctic Engineering "
              "program endowment; naming possibilities for the new lab wing."),
        event("10:00", "11:30", "Statewide Higher Education Chancellor Forum",
              "Video conference (UAA Administration Building bridge room)",
              "Hosted by University of Alaska System president Dr. Thomas "
              "Reed. Other chancellors: UAS (Fairbanks), UAF (Juneau), "
              "Alaska Pacific University. Topics: shared online program "
              "consortium, state budget testimony dates, weather-related "
              "transportation contingencies."),
        event("13:00", "14:30", "Arctic Wolf Center Field Station Debrief",
              "Video conference + Administration Building 3rd floor bridge",
              "Dr. Lena Kovic, director of the UAA Arctic Wolf Center. "
              "Q3 wolf telemetry results, wolf pack 'Nanuwak' GPS data, "
              "co-op student placements, and the fall pack visit to campus."),
        event("16:00", "17:00", "Aurora Watch Briefing — Auroral Forecast Review",
              "UAA Geophysical Institute (GI), Building 1",
              "Dr. S. Nakamura (GI geomagnetism). Topic: Kp-index outlook "
              "for the coming week and whether the donor gala will get an "
              "aurora night. The aurora committee wants a written "
              "recommendation by 5 PM."),
    ],
    2: [
        event("09:30", "11:00", "Ribbon Cutting — New Permafrost Research "
              "Laboratory",
              "GI Building 3, UAA campus",
              "New permafrost laboratory (Bldg 3, west wing). Speaker order: "
              "Chancellor, Dr. Priya Raman (VP Research), Rep. Ada Q. "
              "Moses (AK-23 district), Prof. J. Beringer (GI). Ribbon "
              "cutting at 10:40. Photo op with the permafrost core samples "
              "at 11:00. Media invited: DKNG, KENA, Alaska Public Media."),
        event("11:30", "12:30", "Press Availability — Permafrost Lab",
              "GI Building 3, front steps",
              "15-minute press availability after the ribbon cutting. "
              "Talking points from University Communications (J. Brooks). "
              "Bring the laminated fact sheet and the 10,000-year-old "
              "mammoth-tusk fact (approved by comms)."),
        event("15:00", "16:30", "Donor Gala Planning Session",
              "Copper River Room, UAA Administration Building",
              "Carol Whitfield (Development) and Tundra Trails Catering. "
              "Venue: the Aurora Ballroom, Hyatt Regency Anchorage, 5 PM "
              "on gala day. Theme: 'Under the Aurora.' Kp-index forecast "
              "pending from the aurora committee."),
    ],
    3: [
        event("10:00", "12:00", "Alutiiq Regional Library Board — Community "
              "Council",
              "Chugach Hall, UAA Anchorage",
              "Community partners on the Chugach peninsula: Alutiiq "
              "Regional Library, Bering Strait School District, and the "
              "city of King Salmon. Topics: adult literacy night, shared "
              "winter housing data, and the proposed joint "
              "subarctic-weather course."),
        event("14:00", "15:00", "Meeting: Aurora Club Executive Board",
              "Aurora Club House, Knik Hall",
              "The Aurora Club is the student-led northern-lights dance "
              "organization. Topics: fall aurora ball budget, volunteer "
              "safety training, and the 'Best Aurora' photo contest "
              "sponsorship from AK Electric Co-op."),
    ],
    4: [
        event("10:00", "12:30", "State Budget Testimony — Joint Fiscal "
              "Committee",
              "Capitol building, House Room B, Juneau (fly-in)",
              "Joint Fiscal Committee on the state higher education budget. "
              "Chancellor testimony at 10:40 on operating budget and "
              "infrastructure. System president Dr. Thomas Reed testifies "
              "at 10:00. Delegation: CFO Rajesh Iyer, VP Research Dr. Priya "
              "Raman. Flight: 06:15 ANC->JNU (Delta 1201)."),
        event("14:00", "15:00", "Working Lunch with Rep. Ada Q. Moses",
              "Tudor Room, capitol hotel, Juneau",
              "Rep. Moses (AK-23, chair of the fiscal committee's "
              "education subcommittee). Discussion: permafrost lab "
              "follow-on funding and the King Salmon micro-campus proposal."),
    ],
    5: [
        event("15:00", "17:00", "UAA Board of Trustees — Special Session on "
              "Land Use",
              "Regents Chamber, UAA Administration Building",
              "Special session: campus master plan amendments for the "
              "permafrost lab expansion and the new student housing "
              "project near 14th and UAA Loop. Land use attorney: "
              "M. O'Brien, AK Dept. of Natural Resources."),
    ],
    6: [
        event("11:00", "12:30", "Donor Lunch — Bering Sea Fisheries "
              "Partnership",
              "Copper River Room, UAA Administration Building",
              "Guests: Bering Sea Fisheries cooperative, Dr. Priya Raman, "
              "Prof. L. Okafor (fisheries science). Discussion: $750K "
              "grant for the subarctic fisheries genomics project and "
              "co-op placements."),
        event("13:30", "15:00", "Emergency Task Force — Campus Snow & Ice "
              "Preparedness",
              "Facilities Operations Center, UAA campus",
              "Triggered by the incoming polar vortex forecast. Facilities "
              "director: T. Kowalski. Topics: snow equipment, campus road "
              "closure policy, gala guest parking, and whether the ice "
              "arena snow machines can be run in an actual blizzard."),
    ],
    7: [
        event("09:00", "10:30", "Arctic Wolf Center — Pack Visit Planning",
              "Video conference + Administration Building 3rd floor bridge",
              "Dr. Lena Kovic and the wolf center staff. Planning the fall "
              "campus visit with two wolves from pack 'Nanuwak' "
              "(Nanuwak = 'little wolf'). Logistics: handler transport, "
              "liability waiver, student audience size, and whether "
              "mascot Ralph the Walrus will be present."),
        event("13:00", "14:30", "University Communications All-Hands",
              "Video conference",
              "Director: J. Brooks. Topics: fall marketing campaign "
              "('Anchorage Is Calling'), gala media plan, and the "
              "permafrost lab story follow-up."),
    ],
    8: [
        event("10:00", "11:00", "Meeting with the UAA Mascot Committee — "
              "Ralph the Walrus Photo Op",
              "Knik Hall A, UAA Anchorage",
              "Mascot coordinator: D. Redcloud. Scheduling the fall "
              "photo shoot for the new Seawolves posters and the gala "
              "invitation insert. Ralph has two costume sizes and a "
              "strict 90-minute limit in the cold."),
        event("14:00", "15:30", "Research Ethics Board (IRB) — Quarterly "
              "Review",
              "Regents Chamber, UAA Administration Building",
              "IRB chair: Dr. S. Houghton. Topics: wolf telemetry "
              "protocol renewal, student aurora-exposure survey, and the "
              "permafrost core sample handling procedure."),
    ],
    9: [
        event("09:30", "11:00", "Statewide Faculty Association — Leadership "
              "Forum",
              "Video conference",
              "UAA chapter of the statewide faculty association. Topics: "
              "workload policy (see Faculty Senate), sabbatical backlog, "
              "and the joint faculty-chancellor 'open floor' at 10:30."),
        event("13:00", "14:30", "1:1 with VP Student Affairs — Dr. Sam "
              "Whitcomb",
              ADMIN_SUITE, "Fall orientation plan, Aurora Club funding "
              "decision (needed by end of week), and the new advisor "
              "positions."),
    ],
    10: [
        event("10:00", "12:00", "Donor Briefing — Halvorsen Family "
              "Foundation (follow-up)",
              "Copper River Room, UAA Administration Building",
              "Follow-up to the donor breakfast: final endowment documents "
              "for the $2.5M Arctic Engineering gift, naming of the lab "
              "wing, and the planned unveiling ceremony date."),
        event("15:00", "16:00", "Aurora Gala — Final Logistics Check",
              "Video conference (Aurora Ballroom, Hyatt Regency bridge)",
              "Carol Whitfield, Tundra Trails Catering, Hyatt event "
              "manager. Run-of-show, Kp-index forecast update from the "
              "aurora committee, and the emergency snow plan for guest "
              "parking."),
    ],
    11: [
        event("17:00", "21:00", "UAA Donor Gala — 'Under the Aurora'",
              "Aurora Ballroom, Hyatt Regency Anchorage, 100 E 5th Ave",
              "Black-tie. 170 guests. Headline: live aurora forecast "
              "screen and the 'Aurora of the Year' photo contest awards. "
              "Chancellor keynote at 18:30. Carol Whitfield will be at "
              "the front desk by 16:30. Dress: the good blazer; the "
              "northern-lights scarf is encouraged."),
    ],
    12: [
        event("09:00", "10:30", "Post-Gala Debrief — Development Office",
              "Copper River Room, UAA Administration Building",
              "Carol Whitfield and the development team. Gift results from "
              "the gala, donor follow-up list, and the aurora forecast "
              "post-mortem (did we get the lights?)."),
        event("14:00", "15:00", "1:1 with IT Director — Marcus Bell",
              ADMIN_SUITE, "Campus network winter hardening, the new "
              "student portal rollout, and the IT ticket about the "
              "snow-machine automation system (see facilities)."),
    ],
    13: [
        event("10:00", "12:00", "Board of Regents — Monthly Session",
              "Regents Chamber, UAA Administration Building",
              "Monthly session: FY27 budget adoption (carried from the "
              "first-of-month session), gala gift reporting, and the "
              "campus master plan public comment wrap-up."),
        event("13:30", "15:00", "Arctic Wolf Center — Fall Pack Visit "
              "Dry Run",
              "Wolf Center field station (video) + campus receiving area",
              "Dry run of the fall wolf pack visit: handler routes, "
              "student audience flow, Ralph the Walrus cameo timing, and "
              "the backup plan if the weather closes the field station."),
    ],
}


def build_calendar(today: date) -> list[tuple[date, list[dict]]]:
    """Return [(date, [events])] for 14 days, offsets 0..13."""
    days = []
    for off in range(14):
        d = today + timedelta(days=off)
        evs = list(WEEKDAY_ANCHORS.get(d.weekday(), []))
        evs.extend(ONE_OFFS.get(off, []))
        evs.sort(key=lambda e: e["start"])
        days.append((d, evs))
    return days


# ---------------------------------------------------------------------------
# Calendar markdown
# ---------------------------------------------------------------------------

WEEKDAY_LONG = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday",
                "Saturday", "Sunday"]


def render_calendar(days: list[tuple[date, list[dict]]]) -> str:
    lines = [
        "# Calendar — Dr. Ingrid Halvorsen",
        "",
        f"**{CHANCELLOR_TITLE}** · {OFFICE}",
        f"Calendar export generated {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        "",
        "Format: each day is a `##` heading; each event is a bullet with "
        "`HH:MM–HH:MM — Title`, followed by indented `Location:` and "
        "(optional) `Notes:` lines.",
        "",
        "---",
        "",
    ]
    for d, evs in days:
        lines.append(f"## {WEEKDAY_LONG[d.weekday()]}, {d.strftime('%B %d, %Y')}")
        lines.append("")
        if not evs:
            lines.append("_No scheduled events._")
            lines.append("")
            continue
        for e in evs:
            lines.append(f"- {e['start']}–{e['end']} — **{e['title']}**")
            lines.append(f"  - Location: {e['where']}")
            if e["notes"]:
                lines.append(f"  - Notes: {e['notes']}")
        lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("_End of calendar export._")
    lines.append("")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Emails
# ---------------------------------------------------------------------------

class Mail:
    __slots__ = ("day", "hour", "minute", "frm", "subject", "body", "tag")

    def __init__(self, day: date, hour: int, minute: int, frm: str,
                 subject: str, body: str, tag: str):
        self.day, self.hour, self.minute = day, hour, minute
        self.frm, self.subject, self.body, self.tag = frm, subject, body, tag


MAILS: list[Mail] = []


def mail(day: date, hour: int, minute: int, frm: str, subject: str,
         body: str, tag: str) -> None:
    MAILS.append(Mail(day, hour, minute, frm, subject, body, tag))


def P(*paras: str) -> str:
    return "\n\n".join(paras)


# -- Senders ---------------------------------------------------------------

KATIE = "Katie Nakata (Chancellor's Admin) <katie.nakata@alaska.edu>"
CAROL = "Carol Whitfield <cwhitfield@alaska.edu>"
PAM = "D. Redcloud <dredcloud@alaska.edu>"
REED = "Dr. Thomas Reed (UAS President) <t.reed@alaska.edu>"
KOVIC = "Dr. Lena Kovic <lkovic@alaska.edu>"
NAKAMURA = "Dr. S. Nakamura <snakamura@gi.alaska.edu>"
BROOKS = "J. Brooks <jbrooks@alaska.edu>"
FRAZIER = "Mike Frazier <mfrazier@alaska.edu>"
KOWALSKI = "T. Kowalski <tkowalski@facilities.uaa.edu>"
BELL = "Marcus Bell <mbell@uaa.edu>"
WHITCOMB = "Dr. Sam Whitcomb <switcomb@uaa.edu>"
RAMAN = "Dr. Priya Raman <praman@uaa.edu>"
CFO = "Rajesh Iyer (CFO) <riyer@uaa.edu>"
REP_M = "Rep. Ada Q. Moses <ada.moses@akleg.gov>"
OKAFOR = "Prof. L. Okafor <lokafor@uaa.edu>"
DIALLO = "Prof. Amara Diallo (Faculty Senate Chair) <adiallo@uaa.edu>"
MAYA = "Maya Chen (Student Body President) <mchen@uaa.edu>"
KWAN = "K. Kwan (Regent Chair) <k.kwan@uaa.edu>"
HOUGHTON = "Dr. S. Houghton (IRB Chair) <shoughton@uaa.edu>"
TUNDRA = "Tundra Trails Catering <events@tundratrails.com>"
HYATT = "Hyatt Regency Anchorage — Events <events@hyattanchorage.com>"
ELECTRIK = "AK Electric Co-op <sponsors@akelectric.coop>"
DELTA = "Delta Air Lines <confirmations@deltamail.com>"
ITD = "UAA IT Service Desk <itservice@uaa.edu>"
HR = "UAA Human Resources <hr@uaa.edu>"
FACILITIES = "Facilities & Operations <facilities@uaa.edu>"
POLICE = "UAA Campus Police <campuspolice@uaa.edu>"
FOOD = "UAA Food & Dining <dining@uaa.edu>"
WOLFC = "UAA Arctic Wolf Center <wolfcenter@uaa.edu>"
GI = "Geophysical Institute (GI) <gi-office@gi.alaska.edu>"
DEV = "UAA Advancement <development@uaa.edu>"
NWS = "National Weather Service, Anchorage <alerts@nws.noaa.gov>"
UA_NEWS = "University of Alaska Communications <news@alaska.edu>"
SPOT = "The Aurora Spotlight (campus paper) <editor@auroraspotlight.edu>"
ALASKA_BIZ = "Alaska Business <newsroom@alaskabusiness.org>"
IHE = "Inside Higher Ed <news@insidehighered.com>"
APM = "Alaska Public Media <apm@alaska.gov>"
DKNG = "DKNG 2 <news@dkng2.com>"
KENA = "KENA 6 <news@kena6.com>"
CHAMBER = "Alaska Chamber of Commerce <news@akchamber.org>"
ALUMNI = "UAA Alumni Association <alumni@uaa.edu>"
AURORA_CLUB = "Aurora Club (student org) <auroraclub@uaa.edu>"
SEAWOLVES = "UAA Athletics <seawolves@uaa.edu>"

# spam / noise senders
SPAM1 = "Cruises R' Us <deals@cruisesr.com>"
SPAM2 = "Northern Lights Jewelry Co. <promo@nlightjewels.com>"
SPAM3 = "Dr. Moose O. Feller, DVM (retired) <moose@yaho0.com>"
SPAM4 = "Win-a-Wolf (contest) <contest@winawolf.net>"
SPAM5 = "Mammoth Mortgage <offers@mammothmortgage.com>"
SPAM6 = "Permafrost Financial Advisors <advice@permafin.com>"
SPAM7 = "Alaskan Dream Properties <rentals@alaskandreamprop.com>"
SPAM8 = "The Daily Tundra (free newsletter) <daily@thedailytundra.info>"

# ---------------------------------------------------------------------------
# Event-related emails.
#
# IMPORTANT: related emails must be RECEIVED before the agent runs (today or
# earlier) so that an agent preparing for "tomorrow" can find them.
#   t   = today (the agent runs today to prepare for t+1)
#   t-1 = yesterday, t-2 = two days ago, ...
# ---------------------------------------------------------------------------

def event_mails(today: date) -> None:
    t = today
    t1 = today - timedelta(days=1)
    t2 = today - timedelta(days=2)
    t3 = today - timedelta(days=3)
    t4 = today - timedelta(days=4)

    # -- NEXT DAY (t+1): donor breakfast, chancellor forum, wolf center
    #    debrief, aurora watch briefing. Emails arrive t-1 and t. ------
    mail(t1, 16, 5, CAROL, "Re: Halvorsen Family Foundation — donor "
                           "breakfast logistics (tomorrow 8:30)",
         P(
             "Ingrid — confirming for tomorrow's 8:30 breakfast in the "
             "Copper River Room:",
             "• Alan and Marjorie Halvorsen will be here, plus my "
             "colleague Dev Patel (major gifts).",
             "• We're serving the good coffee and the new permafrost-lab "
             "mug (yes, we put the 10,000-year-old-tusk fact on the "
             "bottom).",
             "• Please keep the $2.5M endowment discussion to the "
             "term-sheet language; Rajesh has already flagged that the "
             "naming options are 'Arctic Engineering Lab' vs. 'Halvorsen "
             "Arctic Engineering Institute'. I'd like to hear your "
             "preference before I mention it to them.",
             "• If the aurora shows up at breakfast (long odds, but it "
             "is August), Dev has a camera ready for the 'aurora "
             "breakfast' photo. Do NOT encourage this. He will anyway.",
             "Carol",
         ), "related")
    mail(t1, 15, 30, REED, "Statewide Chancellor Forum — agenda + video "
                           "link (tomorrow 10:00)",
         P(
             "Chancellors —",
             "Tomorrow's 10:00 forum (video, bridge room) agenda:",
             "1. Shared online program consortium — status of the "
             "general-education stack (10:00).",
             "2. State budget testimony dates and the Juneau delegation "
             "plan (10:20).",
             "3. Transportation contingencies: the polar vortex forecast "
             "has several of us looking at snow-day policies (10:40).",
             "4. Open comments (11:15).",
             "The video link is below; the backup dial-in is on the "
             "agenda PDF. I will open.",
             "Tom Reed",
         ), "related")
    mail(t1, 14, 45, KOVIC, "Arctic Wolf Center — Q3 telemetry + "
                            "tomorrow's debrief",
         P(
             "Ingrid,",
             "Ahead of tomorrow's 1:00 debrief, three things from Q3:",
             "• Wolf pack 'Nanuwak' (Nanuwak = 'little wolf') completed "
             "the summer territory shift — GPS shows the whole pack now "
             "holding the corridor along the Chitina River. Telemetry "
             "charts are in the shared drive.",
             "• Two co-op students (B. Marsh, S. Redcloud) finished "
             "their field rotations; both have strong fall placements "
             "pending.",
             "• The fall pack visit to campus is green-lit by the "
             "research ethics board, subject to the handler-transport "
             "plan we'll review later this month (it's on your "
             "calendar).",
             "If you have 2 minutes at the start of the debrief, I'd "
             "like your read on the 'little wolf' photo op with Ralph "
             "the Walrus. The students think it's a good idea. I think "
             "it's a good idea. So does the wolf, apparently.",
             "— Lena",
         ), "related")
    mail(t1, 17, 0, NAKAMURA, "Aurora Watch Briefing (tomorrow 16:00) — "
                              "Kp outlook preview",
         P(
             "Dr. Halvorsen,",
             "For tomorrow's 4:00 aurora watch briefing at the GI, "
             "here's the short version so you're not caught off "
             "guard:",
             "• The solar wind has been quiet, but a coronal hole is "
             "tracking toward Earth. Kp is forecast 3–4 through the "
             "week, with a possible spike to Kp 5 late in the week "
             "into early the next day.",
             "• That window overlaps your donor gala. My preliminary "
             "call: 'good but not guaranteed' — a Kp 5 would be "
             "visible from the Aurora Ballroom windows if the forecast "
             "holds.",
             "• I need your written recommendation by 5 PM tomorrow "
             "(form is in the shared drive; Katie is leaving a paper "
             "copy on your desk).",
             "• Note for the record: I have personally never seen an "
             "aurora from the Aurora Ballroom. I intend to change "
             "that.",
             "— S. Nakamura, Geophysical Institute",
         ), "related")
    mail(t, 6, 55, KATIE, "This morning's brief — tomorrow's schedule + "
                          "two logistics flags",
         P(
             "Good morning! Quick reminder of your schedule for "
             "tomorrow, with the two logistics items we wanted to "
             "flag:",
             "1. **08:30 Donor Breakfast (Copper River Room):** The "
             "Halvorsen family is arriving by car; I've reserved the "
             "admin lot space marked 'H' and asked facilities to keep "
             "the walkway cleared. Carol Whitfield will bring the "
             "endowment one-pager — she asked us to confirm the $2.5M "
             "figure matches the signed term sheet (it does, per "
             "Rajesh).",
             "2. **16:00 Aurora Watch Briefing (GI Building 1):** Dr. "
             "Nakamura needs your sign-off on the gala aurora "
             "recommendation form by 5 PM tomorrow so the committee "
             "can lock the gala plan. Paper copy will be on your desk "
             "in the blue folder.",
             "The Statewide Chancellor Forum (10:00) uses the "
             "bridge-room link Dr. Reed's office circulates an hour "
             "before. No prep materials requested.",
             "— Katie",
         ), "related")
    mail(t, 8, 20, KATIE, "Weather + a press-availability question",
         P(
             "Two quick logistics items:",
             "• Facilities is clearing the Copper River Room walkway "
             "at 8 AM tomorrow sharp. If the donor car is early, I'll "
             "meet them in the admin lot (space 'H').",
             "• Weather: high 52, overcast, 20% flurries. The aurora "
             "forecast is a separate conversation (see Dr. Nakamura), "
             "but for the permafrost-lab ribbon cutting the day after "
             "tomorrow, facilities wants to know by tomorrow afternoon "
             "whether we keep the 11:30 press availability on the "
             "front steps or move it into the GI lobby.",
             "— Katie",
         ), "related")

    # -- DAY AFTER NEXT (t+2): ribbon cutting + press + gala planning --
    mail(t1, 11, 5, BROOKS, "Ribbon cutting (day after tomorrow, 9:30) — "
                            "speaker order + media list confirmed",
         P(
             "Ingrid — locking the plan for the permafrost-lab ribbon "
             "cutting at 9:30 (GI Building 3, west wing):",
             "Speaker order: you, Dr. Raman, Rep. Moses, Prof. "
             "Beringer. Ribbon at 10:40, photo op with the core "
             "samples at 11:00.",
             "Media confirmed: DKNG (one reporter), KENA (two), "
             "Alaska Public Media (audio). The APM producer asked if "
             "we could have the 10,000-year-old mammoth-tusk fact "
             "available as a one-sentence pull quote — I've drafted "
             "it; it's the laminated fact sheet, not the 14-page "
             "version.",
             "Please do not ad-lib the tusk fact; the comms-approved "
             "version is on the laminated fact sheet. (I know. I'm "
             "sorry.)",
             "J. Brooks",
         ), "related")
    mail(t1, 10, 30, REP_M, "Re: Permafrost lab ribbon cutting",
         P(
             "Chancellor Halvorsen,",
             "Confirming I'll speak at the ribbon cutting (the "
             "10:30–10:40 slot, after Dr. Raman). Two asks:",
             "1. The fiscal committee is watching the state's "
             "infrastructure envelope. If you have one line on how "
             "the permafrost lab supports the state's "
             "climate-mitigation plan, I'd like to use it in my "
             "statement that day.",
             "2. I'm bringing my chief of staff, J. Taimi. She has "
             "strong feelings about the parking situation on the west "
             "side of the GI building and would like a word with "
             "facilities. Please keep her away from T. Kowalski.",
             "Ada",
         ), "related")
    mail(t, 9, 30, RAMAN, "Permafrost lab — ribbon cutting + one "
                          "logistics flag",
         P(
             "Ingrid,",
             "All set for the ribbon cutting. One flag: the lab's "
             "permafrost core display case is on the second floor, "
             "and the west-wing elevator is the one that's been "
             "making the noise. Facilities says it's 'fine' with "
             "quotes. If Rep. Moses wants to see the cores, we should "
             "plan on the stairs (three flights) or pre-stage the "
             "case in the lobby.",
             "Also: Prof. Beringer is bringing the 10,000-year-old "
             "tusk fact as a physical card for the media. Comms "
             "approved. Do not let him elaborate.",
             "Priya",
         ), "related")
    mail(t, 10, 15, TUNDRA, "Aurora Gala — catering confirmation + menu "
                            "options (planning session tomorrow 3 PM)",
         P(
             "Dear UAA team,",
             "Confirming Tundra Trails Catering for the 'Under the "
             "Aurora' donor gala (Aurora Ballroom, Hyatt Regency, 5 "
             "PM on gala day, 170 guests). Your two menu options "
             "for tomorrow's planning session:",
             "A) 'Northern Plate' — king crab, pan-seared Arctic "
             "char, and a baked potato bar with the good sour cream.",
             "B) 'Aurora Feast' — same as A, but the char is "
             "smoked, and we add a 'glow' dessert (edible aurora "
             "garnish, blue spirulina, very Instagrammable).",
             "B is $1,200 more. We can hold either through the "
             "planning session.",
             "— Tundra Trails Events",
         ), "related")
    mail(t, 11, 45, HYATT, "Re: Aurora Ballroom — gala day, load-in + "
                           "parking",
         P(
             "Good morning,",
             "Per our planning call, confirming for the 'Under the "
             "Aurora' gala in the Aurora Ballroom:",
             "• Load-in window: 11:00–14:00 (service entrance on 5th "
             "Ave).",
             "• Guest parking: garage validated; we've reserved 40 "
             "spaces. Given the polar vortex forecast, you may want "
             "to post a snow-day note on the invitation insert.",
             "• The ballroom's north windows face the open sky; the "
             "event manager noted that 'if the aurora shows up, the "
             "ceiling is a 24-foot drop so the lights will be very "
             "visible from the dance floor.' (No promises.)",
             "Hyatt Regency Anchorage — Events",
         ), "related")
    mail(t, 13, 20, KATIE, "Re: gala Kp form — paper copy on your desk",
         P(
             "Reminder: the aurora committee's written recommendation "
             "form is the one with the little drawing of a wavy line "
             "over a stick figure. It's in the blue folder on your "
             "desk. Due 5 PM tomorrow (after the 4 PM briefing) so "
             "the committee can lock the gala plan. If you'd like, I "
             "can pre-fill the event details and you just sign the "
             "Kp line.",
             "— Katie",
         ), "related")

    # -- t+3: community council ----------------------------------------
    mail(t2, 15, 30, WOLFC, "Alutiiq community council (next week) — "
                            "literacy night + weather course",
         P(
             "Chancellor —",
             "For the community council, the Alutiiq Regional Library "
             "wants the adult-literacy night to run on the first "
             "Tuesday of the month, and the Bering Strait School "
             "District is on board with the joint subarctic-weather "
             "course (one section, 15 seats, shared with UAA "
             "atmospheric science). King Salmon's mayor asked if the "
             "literacy night could have a 'read to a wolf' segment. "
             "We have discussed this. We are saying no. We are "
             "saying no with love.",
             "— UAA Arctic Wolf Center (community programs)",
         ), "related")

    # -- t+4: Juneau testimony + lunch ----------------------------------
    mail(t1, 14, 10, CFO, "Juneau trip — flight + testimony materials",
         P(
             "Ingrid —",
             "You fly to Juneau at 06:15 (Delta 1201; the gate is "
             "always the departure board). Materials for the 10:40 "
             "fiscal-committee testimony are in the shared drive: "
             "slides, the FY27 one-pager, and the backup tab with "
             "the infrastructure numbers.",
             "One flag: the committee chair's office asked if we "
             "could have the 'permafrost lab follow-on funding' ask "
             "in the first five minutes. I moved it to slide 3. Dr. "
             "Raman is riding shotgun on the infrastructure tab.",
             "Also: Rep. Moses's working lunch — she asked for the "
             "King Salmon micro-campus one-pager (it's the 2-page "
             "PDF, not the 14-page white paper. The 14-page one is "
             "for the wolves, figuratively).",
             "Rajesh",
         ), "related")
    mail(t, 9, 50, REP_M, "Re: Juneau — lunch + King Salmon "
                          "micro-campus",
         P(
             "Ingrid,",
             "Looking forward to the 2 PM lunch. For the King Salmon "
             "micro-campus, the community wants a one-semester pilot "
             "with the adult-literacy night and the joint "
             "subarctic-weather course. I'd like your read on whether "
             "the state would fund a pilot seat. If you say yes, "
             "I'll put it in the fiscal-committee statement. If you "
             "say 'let's see the numbers,' I'll say that too, but "
             "slower.",
             "Ada",
         ), "related")

    # -- t+5: Seawolves game day ----------------------------------------
    mail(t1, 16, 40, FRAZIER, "Seawolves game day — front row + Ralph "
                              "photo op",
         P(
             "Ingrid —",
             "Game day: front-row seats for your office are reserved "
             "(the ones with the good ice, not the ones by the "
             "zamboni). I'll meet you at the arena office at 11:30. "
             "Ralph the Walrus has a photo op at 13:15 (intermission); "
             "he'll be in the 'winter' costume (the scarf). The "
             "Seawolves are favored; I'm not saying how much. The "
             "ice is good. The crowd is good. The walrus is good.",
             "Mike Frazier, Athletic Director",
         ), "related")
    mail(t2, 10, 20, KATIE, "For the record: the walrus + the scarf",
         P(
             "For the record: the walrus's scarf is not a university "
             "asset. It is a personal item. If it appears in the game "
             "day photo op, it will be in the university photo op. We "
             "are not litigating this. We are photographing it.",
             "— Katie",
         ), "related")

    # -- t+6: fisheries lunch + snow task force -------------------------
    mail(t1, 17, 30, OKAFOR, "Bering Sea Fisheries lunch — grant figures "
                             "+ one ask",
         P(
             "Ingrid,",
             "For the fisheries partnership lunch, the $750K genomics "
             "grant is papered except your signature (it's in the "
             "blue folder, under the aurora form). The co-op "
             "placements are three seats; the cooperative wants the "
             "first placement to be a King Salmon resident if at all "
             "possible — it's a small community and the student "
             "would be the first from there to do a UAA co-op.",
             "L. Okafor",
         ), "related")
    mail(t, 8, 55, KOWALSKI, "Snow & ice task force — agenda + polar "
                             "vortex status",
         P(
             "Chancellor,",
             "Per the NWS polar vortex advisory, the task force "
             "meeting is on (it's on your calendar). Agenda:",
             "1. Snow equipment: we have 6 of 8 trucks cleared; the "
             "other two are in the shop (one has the mystery rattle; "
             "we know what the rattle is, we just haven't fixed "
             "it).",
             "2. Campus road closure policy: I recommend a two-stage "
             "closure (UAA Loop first, then the GI spur).",
             "3. Gala guest parking: the Hyatt garage has 40 spaces; "
             "if we close UAA Loop, we need a snow-plowed overflow "
             "lot. I can plow the east lot by 6 PM the night before.",
             "4. The snow machines at the ice arena: yes, they can be "
             "run in a blizzard; no, we are not going to test this "
             "during an actual blizzard; I will put that in writing "
             "so this stops being a question at every meeting.",
             "T. Kowalski, Facilities & Operations",
         ), "related")

    # -- t+7: wolf pack visit planning ----------------------------------
    mail(t2, 16, 30, KOVIC, "Wolf pack visit — handler transport + "
                            "liability waiver",
         P(
             "Ingrid,",
             "For the pack-visit planning call, the two open items: "
             "handler transport (we can use the GI field van, but it "
             "needs a 10-minute pre-trip inspection) and the "
             "liability waiver (legal wants the student audience "
             "sign-off to be one page, not the three-page version).",
             "Also: the students keep asking if Ralph the Walrus "
             "will be there. I said 'it depends on the walrus.' It "
             "does not depend on the walrus. It depends on the mascot "
             "coordinator's schedule. But the walrus is a good "
             "excuse.",
             "— Lena",
         ), "related")

    # -- t+8: mascot committee + IRB ------------------------------------
    mail(t3, 15, 10, PAM, "Ralph the Walrus photo op — costume + "
                          "weather",
         P(
             "Ingrid — for the mascot committee call:",
             "• Ralph has two costume sizes (regular and 'winter', "
             "which is the same costume with a scarf).",
             "• Strict 90-minute limit in the cold, per the mascot "
             "coordinator's physician (the physician is the "
             "coordinator's mother; we do not question the mother).",
             "• The fall poster shoot works for a morning slot; the "
             "gala invitation insert needs one close-up (Ralph "
             "holding the gala date card). I'll bring the card in "
             "two sizes. He has held things before. He holds things "
             "well.",
             "D. Redcloud",
         ), "related")
    mail(t3, 14, 0, HOUGHTON, "IRB quarterly review — agenda + two "
                              "protocol notes",
         P(
             "Dr. Halvorsen —",
             "For the IRB quarterly review: (1) the wolf telemetry "
             "protocol renewal is on track (Dr. Kovic's amendment "
             "addresses the handler-contact question); (2) the "
             "student aurora-exposure survey needs a revised consent "
             "form (the current one says 'you may feel a glow,' "
             "which is not a protected outcome); (3) the permafrost "
             "core sample handling procedure is fine as written "
             "(it's a procedure, not a protocol; it's fine).",
             "Dr. S. Houghton, IRB Chair",
         ), "related")

    # -- t+9: faculty association + student affairs 1:1 ------------------
    mail(t3, 11, 20, DIALLO, "Statewide faculty association forum — "
                             "open-floor topics",
         P(
             "Chancellor —",
             "For the faculty association forum, the open floor will "
             "cover: workload policy (the same revision the senate "
             "is moving), the sabbatical backlog (currently 11 "
             "faculty), and a question about whether the gala "
             "keynote counts as 'university business' for workload "
             "purposes. (It does. I answered that one for you.)",
             "If you'd like, I can bring the senate's "
             "workload-policy draft to the forum so it's in the room "
             "rather than in the hallway.",
             "Prof. Amara Diallo, Faculty Senate Chair",
         ), "related")
    mail(t2, 13, 40, WHITCOMB, "1:1 — fall orientation + aurora club "
                               "funding decision",
         P(
             "Chancellor —",
             "For our 1:1: fall orientation is on track (the new "
             "portal is the learning one; see Marcus's ticket). The "
             "aurora club funding decision is the big one — I'd like "
             "a call by the end of this week so we can lock the fall "
             "budget. The club's fall aurora ball is their biggest "
             "fundraiser, and the 'Best Aurora' photo contest "
             "sponsorship from AK Electric is pending (they sent a "
             "letter; it's nice; it's in the shared drive).",
             "Dr. Sam Whitcomb",
         ), "related")

    # -- t+10: donor follow-up + gala final check ------------------------
    mail(t4, 16, 20, CAROL, "Halvorsen follow-up briefing — endowment "
                            "documents status",
         P(
             "Ingrid — for the follow-up briefing, the endowment "
             "documents are final except the naming page. At the "
             "breakfast we'll hear your preference (Arctic "
             "Engineering Lab vs. Halvorsen Arctic Engineering "
             "Institute). Alan Halvorsen has told me privately that "
             "he 'just wants it to have his name on it, even a "
             "little.' The term sheet allows 'Halvorsen Institute "
             "for Arctic Engineering' as a middle path. I'd like to "
             "bring that to the table.",
             "Carol",
         ), "related")
    mail(t2, 15, 0, NAKAMURA, "Gala aurora outlook — interim update",
         P(
             "Ingrid — interim word on the gala aurora question:",
             "The coronal hole is holding. Kp for gala night is now "
             "forecast 4–5. I'll bring the full recommendation to "
             "the aurora watch briefing (you'll sign the form "
             "there; the little wavy line is the right line). If "
             "I'm right, the 'look out the windows' moment is real. "
             "If I'm wrong, the glow dessert still works and the "
             "dance is very good.",
             "— S. Nakamura",
         ), "related")

    # -- t+11: THE GALA ---------------------------------------------------
    mail(t1, 18, 30, CAROL, "THE GALA — run-of-show + your keynote",
         P(
             "Ingrid — 'Under the Aurora,' 5 PM, Aurora Ballroom, "
             "Hyatt Regency. 170 guests, black-tie (the good blazer; "
             "the northern-lights scarf is encouraged).",
             "Run-of-show:",
             "• 17:00 doors, cocktail hour. Catering is tentatively "
             "Menu B (the 'glow' dessert); we finalize at the "
             "planning session.",
             "• 18:30 your keynote (12 minutes; I've left the "
             "laminated card with the three numbers: 2,500 students "
             "served, 10,000-year-old tusk, Kp 5 'good but not "
             "guaranteed').",
             "• 18:45 'Aurora of the Year' photo contest awards "
             "(winning photo: a moose in front of the aurora, "
             "submitted by a student who is not in our program; the "
             "moose is not ours; we are not responsible for the "
             "moose).",
             "• 19:15 live aurora forecast screen (Dr. Nakamura on "
             "the video link; if Kp hits 5, she will say the words "
             "'look out the windows' and it will be very good).",
             "• 20:30 dance (the Aurora Club does the opening "
             "number; they've been practicing for three months; "
             "they're very good; I watched a rehearsal).",
             "I'll be at the front desk by 16:30. If the aurora "
             "shows up, do NOT announce it; let the windows do the "
             "talking.",
             "Carol",
         ), "related")
    mail(t, 17, 45, NAKAMURA, "Gala aurora forecast — final preview",
         P(
             "Ingrid — final word before the gala:",
             "Kp is now forecast 4–5 for gala night. The coronal "
             "hole is holding. If I'm right, the 'look out the "
             "windows' moment is real. If I'm wrong, the glow "
             "dessert still works and the dance is very good.",
             "My written recommendation will be ready at the aurora "
             "watch briefing tomorrow (form in the blue folder; the "
             "little wavy line is the right line).",
             "— S. Nakamura",
         ), "related")

    # -- t+12: post-gala debrief + IT 1:1 ---------------------------------
    mail(t2, 11, 15, BELL, "IT 1:1 — snow-machine automation + winter "
                           "hardening",
         P(
             "Ingrid —",
             "For our 1:1: (1) campus network winter hardening is on "
             "schedule; (2) the new student portal rolls out next "
             "week; (3) the facilities ticket about the snow-machine "
             "automation system — it's not broken, it's 'learning,' "
             "and I'm not sure a snow machine can learn, but I'm not "
             "closing the ticket until T. Kowalski tells me it's "
             "done. I've asked him in writing. He has not answered. "
             "This is why we have tickets.",
             "Marcus Bell, IT Director",
         ), "related")

    # -- t+13: regents + wolf dry run -------------------------------------
    mail(t3, 9, 45, KWAN, "Regents monthly session — agenda",
         P(
             "Dr. Halvorsen —",
             "Monthly session agenda: (1) FY27 budget adoption "
             "(carried from the first-of-month session; the "
             "endowment gift reporting is attached); (2) the gala "
             "gift results (Carol will present — the number is 'very "
             "good' and I will let her say it); (3) campus master "
             "plan public comment wrap-up (no material objections; "
             "one comment was a poem about parking; I've included "
             "it in the packet; it's good).",
             "K. Kwan, Regent Chair",
         ), "related")

    # -- emails for TODAY's (offset 0) weekday anchors ----------------------
    if today.weekday() == 0:  # Monday: regents + office hours
        mail(t, 7, 30, KWAN, "Regents full session (today) — pre-reads + "
                             "one parking note",
             P(
                 "Dr. Halvorsen — pre-reads are in the shared drive "
                 "(FY27 budget, endowment policy, master plan "
                 "comments). One note: the regents' cars are in the "
                 "admin lot, spaces A–F, per the standing "
                 "arrangement. If space 'H' is empty, that's the "
                 "donor space (it's always empty; we keep it for "
                 "people we haven't met yet).",
                 "K. Kwan",
             ), "related")
    if today.weekday() == 1:  # Tuesday: faculty senate
        mail(t, 8, 15, DIALLO, "Senate business meeting (today) — workload "
                               "policy + Arctic Engineering",
             P(
                 "Chancellor — the senate's business meeting covers "
                 "the workload policy revision (motion at 11:00), "
                 "the new Arctic Engineering program proposal (Dr. "
                 "Raman will present), and the library bond issue. "
                 "If you'd like to speak at open comments, the slot "
                 "is 11:45 and it's two minutes. Two minutes is a "
                 "lot. Use it well.",
                 "Prof. Amara Diallo",
             ), "related")
    if today.weekday() == 2:  # Wednesday: cabinet + athletics
        mail(t, 9, 0, WHITCOMB, "Cabinet review (today) — fall headcount + "
                                "aurora club funding",
             P(
                 "Chancellor — for the cabinet review: fall "
                 "headcount is up 3% (the aurora club is not the "
                 "reason, but it's correlated, and we're not going "
                 "to pretend it isn't). The aurora club funding "
                 "decision is on the agenda — I'd like a call by "
                 "end of week so we can lock the fall budget. Dr. "
                 "Raman will present the research tab. The bridge "
                 "link is in the calendar invite.",
                 "Dr. Sam Whitcomb",
             ), "related")
        mail(t, 15, 30, FRAZIER, "Athletics check-in (today) — NIL memo + "
                                 "ice report",
             P(
                 "Ingrid — the NIL compliance memo is in the shared "
                 "drive (legal cleared it; it's the short version; "
                 "the long version is for the wolves, "
                 "figuratively). The ice arena maintenance report: "
                 "the ice is good, the zamboni is good, the mystery "
                 "rattle is still a mystery (that's the facilities "
                 "truck, not the arena; see T. Kowalski).",
                 "Mike Frazier",
             ), "related")
    if today.weekday() == 3:  # Thursday: executive council
        mail(t, 8, 30, KATIE, "Executive council (today) — space + shared "
                              "services + permafrost funding",
             P(
                 "For today's executive council: the space "
                 "utilization plan is on slide 4 (the 'which "
                 "building is actually full' one), shared services "
                 "consolidation is on slide 7 (it's boring, it's "
                 "good), and the permafrost lab follow-on funding "
                 "is on slide 9 (it's on slide 3 for the fiscal "
                 "committee; here it's on 9; slides are a social "
                 "construct).",
                 "— Katie",
             ), "related")
    if today.weekday() == 4:  # Friday: provost + CFO 1:1s
        mail(t, 9, 30, KATIE, "1:1s (today) — provost at 11, CFO at 13 + "
                              "the blue folder",
             P(
                 "Today: Dr. Marsh at 11 (mid-year curriculum + "
                 "Arctic Engineering recruiting), Rajesh at 13 "
                 "(FY27 mid-year cash + state appropriation "
                 "status). The blue folder on your desk has: the "
                 "aurora Kp form (due tomorrow 5 PM), the fisheries "
                 "grant signature page, and a photo of the walrus "
                 "(not for work, just for morale).",
                 "— Katie",
             ), "related")
    if today.weekday() == 5:  # Saturday: game day
        mail(t, 10, 30, FRAZIER, "GAME DAY (today) — 11:30 arena office, "
                                 "front row, walrus at 13:15",
             P(
                 "Today is the day. 11:30 at the arena office. "
                 "Front row is reserved. The walrus is at 13:15 "
                 "(intermission, 'winter' costume, the scarf). The "
                 "ice is good. Go Seawolves. (I own a Seawolves "
                 "hat. I am not saying it's a good hat. It's a good "
                 "hat.)",
                 "Mike Frazier",
             ), "related")


# ---------------------------------------------------------------------------
# Unrelated emails: spam, newsletters, random requests, IT, HR, food, etc.
# ---------------------------------------------------------------------------

def noise_mails(today: date) -> None:
    def d(off: int) -> date:
        return today + timedelta(days=off)

    # --- spam / scams -----------------------------------------------------
    spam_items = [
        (d(-13), 6, 12, SPAM1, "YOU'VE WON A FREE CRUISE TO THE ARCTIC! (no purchase necessary)",
         "Congratulations! Our computer has selected you for a FREE 10-day "
         "Arctic cruise! To claim your prize, simply reply with your SSN "
         "and bank details. This offer expires in 10 minutes."),
        (d(-13), 21, 40, SPAM6, "Permafrost Financial: your assets are MELTING",
         "Are your assets stuck in solid ground? Diversify into our "
         "Thaw-Resistant Index Fund! Zero lock-in, zero paperwork, zero "
         "assets. Call now to discuss your future."),
        (d(-12), 22, 4, SPAM2, "Northern Lights Jewelry — 90% off 'Aurora' pendants",
         "Only 3 left in stock! Our 'Aurora' pendant is 90% off for 48 "
         "hours. Note: the pendant is not a real aurora. The aurora is a "
         "separate purchase."),
        (d(-12), 8, 18, SPAM7, "Alaskan Dream Properties: 2BR with walrus view",
         "Rare 2-bedroom in South Hill! South-facing windows "
         "(aurora-compatible), a den, and a 'walrus view' from the balcony. "
         "The walrus is not included."),
        (d(-11), 5, 58, SPAM3, "Re: Re: Fwd: The moose knows",
         "My friend's brother works at the moose compound. He says 'the "
         "moose knows.' I don't know what that means, but I'm forwarding it "
         "to you because you seemed like someone who would want to know."),
        (d(-11), 19, 25, SPAM8, "The Daily Tundra: '5 Signs Your Lawn Is a Permafrost Anomaly'",
         "Sign 1: it's brown. Sign 2: it's still brown. Sign 3: you live in "
         "Anchorage. Sign 4: it's August. Sign 5: you clicked."),
        (d(-10), 13, 33, SPAM4, "WIN-A-WOLF: you are a finalist!",
         "You are one of 3 finalists in the Win-a-Wolf contest! To win, "
         "simply pay the $49.99 entry fee. Please do not email the wolf. "
         "The wolf does not have email."),
        (d(-10), 7, 45, SPAM6, "Permafrost Financial: the thaw has BEGUN",
         "Following up on our last note: the thaw has begun. Your "
         "Thaw-Resistant Index Fund is now 'partially thawed.' Please "
         "diversify while you still can."),
        (d(-9), 7, 15, SPAM5, "Mammoth Mortgage: refinance your tusk!",
         "Tired of carrying a 10,000-year-old debt? Refinance with Mammoth "
         "Mortgage! Rates from 3.1% APR. The tusk is not collateral. The "
         "tusk is a fact."),
        (d(-9), 23, 50, SPAM7, "URGENT: your walrus-view property is UNDER OFFER",
         "Another buyer has made an offer on your walrus-view 2-bedroom! "
         "Act now to counter, or lose the view forever."),
        (d(-8), 19, 47, SPAM1, "URGENT: your cruise reservation is CANCELLED",
         "Your reservation for the free Arctic cruise has been CANCELLED "
         "due to inactivity. To reactivate, reply within 1 hour."),
        (d(-8), 6, 30, SPAM8, "The Daily Tundra: 'Is Your Aurora Committee a Committee?'",
         "Opinion: our local aurora committee meets monthly, issues "
         "forecasts, and signs forms with wavy lines. Is it a committee? "
         "The answer, per three chancellors, is 'it's a social construct.'"),
        (d(-7), 4, 59, SPAM3, "The moose knows (part 2)",
         "Following up on my last email. I asked my friend's brother what "
         "'the moose knows' means. He said 'it's about the parking.' I "
         "think it's about the parking."),
        (d(-7), 16, 12, SPAM6, "Permafrost Financial: Q2 'earnings' (the ground)",
         "Our Q2 'earnings' report: the ground is still there. Interest: "
         "0%. Dividends: a small amount of meltwater. Invest in the thaw "
         "before the thaw invests in you."),
        (d(-6), 16, 22, SPAM4, "WIN-A-WOLF: you are STILL a finalist!",
         "Friendly reminder: the other two finalists have paid. You have "
         "not. The wolf is patient. The fee is $49.99."),
        (d(-6), 9, 5, SPAM2, "Aurora pendants now with FREE moose keychain",
         "Buy any 'Aurora' pendant and get a FREE moose keychain! The "
         "keychain is not the real moose. The real moose is a separate "
         "purchase."),
        (d(-5), 8, 44, SPAM7, "Alaskan Dream Properties: the zamboni is NOT included",
         "Correction to our last listing: the zamboni is NOT included with "
         "the walrus-view property. Apologies for the confusion."),
        (d(-5), 21, 15, SPAM8, "The Daily Tundra: 'Mystery Rattle Heard on Campus; Experts Divide'",
         "A persistent rattle has been heard on campus, attributed variously "
         "to a facilities truck, a snow machine, and 'the learning.' One "
         "expert (T. Kowalski) has put it in writing. He has not answered "
         "our follow-up."),
        (d(-4), 23, 11, SPAM5, "Mammoth Mortgage: your tusk is APPROVED!",
         "Congratulations! Your tusk refinance is APPROVED! Sign here (the "
         "tusk). Act now — approval expires when the ice does."),
        (d(-4), 12, 40, SPAM6, "Permafrost Financial: the ground is a FACT",
         "Final reminder: the ground is a fact. Your 'Thaw-Resistant Index "
         "Fund' is not. Diversify."),
        (d(-3), 6, 30, SPAM1, "LAST CHANCE: Arctic cruise, 10 minutes left!",
         "THIS IS THE LAST EMAIL. The 10-minute window is open. Reply now."),
        (d(-3), 17, 55, SPAM7, "FOR SALE: one (1) mystery rattle (used)",
         "Selling my mystery rattle. Works great. Sounds like a facilities "
         "truck. Could be a snow machine. Could be 'the learning.' $49.99. "
         "Cash or tusk (the tusk is not accepted)."),
        (d(-2), 14, 8, SPAM3, "The moose knows (part 3, final)",
         "I've been told to stop emailing you about the moose. This is the "
         "final email. The moose knows. It's about the parking. Goodbye."),
        (d(-2), 20, 25, SPAM8, "The Daily Tundra: 'Aurora Season Opens Early; Locals Unimpressed'",
         "The aurora season has opened early, and locals are unimpressed. "
         "'I've seen it before,' said one resident, who then stood outside "
         "for 40 minutes. The Geophysical Institute at UAA says the Kp "
         "index is 'higher than usual.'"),
        (d(-1), 5, 55, SPAM4, "WIN-A-WOLF: the wolf has SPOKEN",
         "In a rare break from his silence, the wolf has spoken. He says: "
         "'The fee is $49.99.' He also says: 'I am not real.' He also says: "
         "'The parking is fine.'"),
        (d(-1), 18, 40, SPAM6, "Permafrost Financial: the thaw is a SOCIAL CONSTRUCT",
         "Breaking: our researchers have determined the thaw is a social "
         "construct. Your 'Thaw-Resistant Index Fund' is now 'socially "
         "resistant.' Invest in constructs."),
        (d(0), 4, 41, SPAM2, "Aurora pendant FLASH SALE (4 hours!)",
         "FLASH SALE! The 'Aurora' pendant is 95% off for 4 hours!"),
        (d(0), 11, 20, SPAM8, "The Daily Tundra: 'Chancellor Seen Wearing Northern-Lights Scarf'",
         "A chancellor was seen today wearing a northern-lights scarf. When "
         "asked if the scarf is a university asset, the spokesperson said "
         "'it's a personal item,' paused, then said 'it's in the story.'"),
    ]
    for day, h, m, frm, subj, body in spam_items:
        mail(day, h, m, frm, subj, body, "spam")

    # --- newsletters -------------------------------------------------------
    newsletters = [
        (d(-13), 6, 0, UA_NEWS, "UAK Weekly: system-wide updates",
         "This week at the University of Alaska: the permafrost lab breaks "
         "ground in Anchorage (congrats to UAA!); UAF opens a new marine "
         "lab in Juneau; UAS hosts a tundra-research symposium in "
         "Fairbanks. Full story on page 3."),
        (d(-12), 6, 30, IHE, "IHE: 'The State of the Aurora: How Universities Are "
                             "Preparing for the Lights'",
         "A feature on how northern universities are incorporating aurora "
         "forecasts into event planning. We reached out to UAA for comment; "
         "the response was 'we have a geophysical institute; we take this "
         "seriously.'"),
        (d(-11), 7, 15, APM, "APM: 'Chancellors Eye Shared Online Programs'",
         "Our preview of the upcoming statewide chancellor forum: the shared "
         "online program consortium is 'close but not there,' according to "
         "three chancellors who spoke on background."),
        (d(-10), 6, 45, DKNG, "DKNG: 'UAA Permafrost Lab to Host Ribbon Cutting'",
         "The University of Alaska Anchorage will host a ribbon cutting for "
         "its new permafrost research laboratory. The lab, located in GI "
         "Building 3, will study the changing permafrost that underlies "
         "much of the state. A 10,000-year-old mammoth tusk will be on "
         "display."),
        (d(-9), 6, 20, KENA, "KENA: 'Aurora Season Kicks Off Early This Year'",
         "The aurora season has kicked off early this year, with "
         "forecasters predicting a strong season. The Geophysical Institute "
         "at UAA says the Kp index is 'higher than usual.' If you're "
         "planning an event, check the forecast."),
        (d(-8), 7, 0, CHAMBER, "Chamber: 'Higher Ed and the State Budget: What to Watch'",
         "With the state budget season approaching, the chamber outlines "
         "what higher education leaders should watch. Key items: the "
         "operating budget, the infrastructure envelope, and the "
         "'permafrost lab follow-on funding.' We'll be at the fiscal "
         "committee."),
        (d(-7), 6, 15, SPOT, "Aurora Spotlight: 'Seawolves Season Preview: The Ice Is Good'",
         "Our season preview: the Seawolves are favored, the ice is good, "
         "and the mascot (Ralph the Walrus) will be in attendance, wearing "
         "the 'winter' costume (the scarf). The athletic director says 'the "
         "walrus is good.'"),
        (d(-6), 6, 30, UA_NEWS, "UAK Weekly: wolf telemetry update + gala announcement",
         "The UAA Arctic Wolf Center reports that wolf pack 'Nanuwak' has "
         "completed its summer territory shift. Also: UAA announces its "
         "'Under the Aurora' donor gala. The aurora is not included; it is "
         "a separate occurrence."),
        (d(-5), 7, 30, ALASKA_BIZ, "Alaska Business: 'The Economics of the Lights'",
         "A feature on the economic impact of the aurora on northern "
         "tourism. The article notes that 'a Kp 5 event can drive "
         "significant foot traffic,' citing a UAA donor gala that 'expects "
         "170 guests.' It also notes that 'the glow dessert is a separate "
         "line item' — $1,200 more, to be exact."),
        (d(-4), 6, 45, APM, "APM: 'Fiscal Committee to Hear Higher Ed Testimony'",
         "The Joint Fiscal Committee will hear testimony from higher "
         "education leaders on the state budget. The chancellor's office "
         "expects to address the operating budget and infrastructure. The "
         "'permafrost lab follow-on funding' ask lands on slide 3."),
        (d(-3), 6, 20, SPOT, "Aurora Spotlight: 'Gala Countdown: The Lights May Show'",
         "Countdown to the 'Under the Aurora' gala: the Geophysical "
         "Institute forecasts Kp 4–5 for gala night. The event manager at "
         "the Hyatt says the ballroom's north windows face open sky. The "
         "catering team is finalizing the menu (Menu B, the 'glow' "
         "dessert). The dance team — the Aurora Club — is very good; we "
         "watched a rehearsal."),
        (d(-2), 7, 0, KENA, "KENA: 'Polar Vortex Watch: What It Means for Anchorage'",
         "The NWS has issued a polar vortex watch for the region. What it "
         "means: cold, wind, and a possible blizzard. The university's "
         "facilities team is preparing, and the campus road closure policy "
         "is 'two-stage.' The ice arena's snow machines 'can be run in a "
         "blizzard' — they are not going to be."),
        (d(-1), 6, 10, UA_NEWS, "UAA News: 'Seawolves Host This Weekend — Front Row "
                                "for the Chancellor'",
         "The UAA Seawolves host this weekend, and the chancellor's office "
         "has reserved front-row seats. The athletic director says 'the ice "
         "is good.' The mascot (Ralph the Walrus) will be in attendance, "
         "wearing the 'winter' costume (the scarf)."),
        (d(-1), 17, 30, ELECTRIK, "AK Electric Co-op: 'Best Aurora' photo contest — "
                                  "sponsorship confirmed",
         "We're pleased to confirm our sponsorship of the 'Best Aurora' "
         "photo contest at the UAA donor gala! The winning photo — a moose "
         "in front of the aurora — will be displayed at our co-op offices "
         "all season. (The moose is not ours; we are not responsible for "
         "the moose.)"),
        (d(0), 6, 30, SEAWOLVES, "UAA Athletics: 'Game Day Reminder — Front Row "
                                 "Reserved'",
         "Reminder: the chancellor's office has front-row seats reserved "
         "for game day (the ones with the good ice, not the ones by the "
         "zamboni). The athletic director will meet at the arena office at "
         "11:30. Ralph the Walrus has a photo op at 13:15 during "
         "intermission."),
    ]
    for day, h, m, frm, subj, body in newsletters:
        mail(day, h, m, frm, subj, body, "newsletter")

    # --- IT tickets ----------------------------------------------------------
    it_items = [
        (d(-13), 9, 15, ITD, "IT ticket #4821: snow-machine automation 'learning' (opened)",
         "New ticket: the snow-machine automation system is 'learning.' We "
         "are not sure what it's learning. It is not broken, and it is not "
         "working. If you have any thoughts, please reply. We'll keep the "
         "ticket open either way."),
        (d(-12), 10, 30, ITD, "IT ticket #4822: student portal login issues (opened)",
         "Several students are reporting login issues with the new student "
         "portal. The old portal still works. We're rolling out the new one "
         "next week; if you can't log in, use the old one in the meantime."),
        (d(-11), 14, 0, ITD, "IT ticket #4823: the rattle (new)",
         "A new ticket: the mystery rattle from the facilities truck is "
         "'learning' too. We are not sure if the rattle is the truck or the "
         "truck is the rattle. We've asked T. Kowalski in writing; he has "
         "not answered. This is why we have tickets."),
        (d(-10), 11, 45, ITD, "IT ticket #4824: projector in Regents Chamber (not working)",
         "The projector in the Regents Chamber is not working. It's not "
         "broken; it's 'thinking.' We've asked T. Kowalski to look at it; "
         "he's currently looking at the rattle (ticket #4823). In the "
         "meantime, please use the bridge-room projector for meetings."),
        (d(-9), 16, 30, ITD, "IT ticket #4825: email storage (you're at 80%)",
         "Your mailbox is at 80% capacity. Consider archiving older "
         "messages — the spam, the newsletters, and the 'moose knows' "
         "thread are good candidates."),
        (d(-8), 9, 0, ITD, "IT ticket #4826: badge access (GI Building 3, west wing)",
         "Your badge is not working in GI Building 3, west wing. We've "
         "reprogrammed it; it's still not working, and the door is now "
         "'thinking' (see ticket #4824 for the shared vibe). Use the "
         "stairs — three flights — or ask the front desk to hold the door."),
        (d(-7), 13, 15, ITD, "IT ticket #4827: VPN (it's the learning one)",
         "The VPN is behaving like the snow-machine automation system "
         "(ticket #4821): not broken, just learning. If you can't "
         "connect, use the old VPN, which has never learned anything in "
         "its life and is entirely content to remain that way."),
        (d(-6), 15, 45, ITD, "IT ticket #4828: printer in Knik Hall A (out of toner)",
         "The printer in Knik Hall A is out of toner. We've ordered more; "
         "it's on the way. It's always on the way."),
        (d(-5), 10, 30, ITD, "IT ticket #4829: wifi in the Aurora Club House (it's fine)",
         "The wifi in the Aurora Club House is fine. It's not learning. "
         "It's not broken. It's fine. Closing unless someone objects."),
        (d(-4), 14, 15, ITD, "IT ticket #4830: calendar invite sync (the gala)",
         "The calendar invite for the gala is not syncing to some devices. "
         "We've re-synced it; it's still not syncing. The calendar is a "
         "social construct. For now, use the paper copy in the blue "
         "folder."),
        (d(-3), 11, 0, ITD, "IT ticket #4831: the rattle is BACK (reopened)",
         "Ticket #4823 (the rattle) is reopened. The rattle is back, and "
         "louder than before. It's 'learning faster.' We've asked T. "
         "Kowalski in writing again. He has not answered again."),
        (d(-2), 16, 20, ITD, "IT ticket #4832: aurora forecast screen (ballroom)",
         "The aurora forecast screen in the ballroom is not working. It's "
         "not broken; it's 'looking at the windows.' The event manager "
         "says it will work if the aurora shows up. We don't have time to "
         "test that. Use the paper forecast in the blue folder for the "
         "gala."),
        (d(-1), 9, 30, ITD, "IT ticket #4833: portal rollout (next week)",
         "The new student portal rolls out next week (it's the learning "
         "one; see tickets #4821–4830 for context). The old portal keeps "
         "working during the transition. Questions? Reply to this ticket."),
        (d(0), 8, 45, ITD, "IT ticket #4834: the rattle (reopened again)",
         "Ticket #4823 (the rattle) is reopened again. The rattle is back "
         "and 'learning' (see ticket #4821). We've asked T. Kowalski in "
         "writing again. He has not answered again. This is why we have "
         "tickets, and reopens."),
    ]
    for day, h, m, frm, subj, body in it_items:
        mail(day, h, m, frm, subj, body, "request")

    # --- HR --------------------------------------------------------------------
    hr_items = [
        (d(-12), 10, 30, HR, "HR: benefits open enrollment reminder",
         "Open enrollment for benefits is open. Log in to the HR portal to "
         "review your options. If you can't log in to the new portal "
         "(Marcus is rolling it out), the old one still works."),
        (d(-10), 14, 0, HR, "HR: sabbatical backlog — 11 faculty",
         "The sabbatical backlog is currently 11 faculty. The faculty "
         "association will raise this at the upcoming forum. If you'd like "
         "a one-line response for them, we suggest (a) 'we're working on "
         "it' or (b) 'we're working on it, slowly.' Option (c), 'the "
         "backlog is a social construct,' is not approved."),
        (d(-8), 9, 45, HR, "HR: parking permit renewal (chancellor's office)",
         "Your parking permit for the admin lot is up for renewal. Log in "
         "to the HR portal to renew. Note: space 'H' is reserved for "
         "donors; it is always empty, because we keep it for people we "
         "haven't met yet."),
        (d(-6), 13, 10, HR, "HR: wellness program — aurora viewing (counted as exercise)",
         "The wellness program now counts aurora viewing as exercise, per "
         "the geophysical institute. Log your viewing in the wellness "
         "portal. 'Look out the windows' earns 2 points per Kp level."),
        (d(-4), 11, 30, HR, "HR: training registration — 'Aurora Safety for Event Planners'",
         "New training available: 'Aurora Safety for Event Planners' (2 "
         "hours, online). Topics: Kp index basics, 'look out the windows' "
         "protocols, and why the glow dessert is not a safety measure. "
         "Register by the end of the month."),
        (d(-2), 10, 15, HR, "HR: open enrollment CLOSING SOON",
         "Open enrollment closes in 5 days. If you haven't reviewed your "
         "options yet, log in to the HR portal now — or use the old "
         "portal, which is still working and has no opinions."),
        (d(0), 9, 0, HR, "HR: tuition remission — applications due",
         "Reminder: tuition remission applications are due. The remission "
         "covers staff and faculty (not the wolves; the wolves are a "
         "fact, not a benefit). Apply via the HR portal."),
    ]
    for day, h, m, frm, subj, body in hr_items:
        mail(day, h, m, frm, subj, body, "request")

    # --- facilities ---------------------------------------------------------------
    fac_items = [
        (d(-11), 11, 45, FACILITIES, "Facilities: elevator in GI Bldg 3 'making a noise' (status)",
         "Status on the west-wing elevator in GI Building 3: it's 'fine,' "
         "with quotes, per the mechanic. It's making a noise, and we don't "
         "know what the noise is, so we're not fixing it yet. If you need "
         "to move the permafrost core display case, use the stairs (three "
         "flights) or pre-stage it in the lobby."),
        (d(-9), 15, 20, FACILITIES, "Facilities: room booking confirmations (Copper River Room)",
         "Your room bookings are confirmed for the Copper River Room: "
         "donor breakfast, donor lunch, donor briefing, gala planning "
         "session, and post-gala debrief. The room is ready whenever you "
         "are."),
        (d(-7), 9, 0, FACILITIES, "Facilities: snow equipment status (6 of 8 trucks)",
         "Snow equipment status: 6 of 8 trucks are cleared and ready. The "
         "other two are in the shop; one of them has the mystery rattle "
         "(we know what the rattle is; we just haven't fixed it)."),
        (d(-5), 16, 30, FACILITIES, "Facilities: campus road closure policy (two-stage)",
         "Per the NWS polar vortex watch, the campus road closure policy "
         "is two-stage: UAA Loop closes first, then the GI spur. We'll "
         "announce any closure through the usual channels."),
        (d(-3), 12, 15, FACILITIES, "Facilities: gala guest parking plan (final)",
         "Final gala guest parking plan: the Hyatt garage has 40 validated "
         "spaces. If we close UAA Loop, we'll use the east lot as "
         "overflow; I can have it plowed by 6 PM the night before. On the "
         "ice arena snow machines: yes, they can be run in a blizzard. "
         "No, we are not going to test this during an actual blizzard. "
         "This is now in writing so the question stops coming up."),
        (d(-1), 8, 30, FACILITIES, "Facilities: donor breakfast walkway clearance (confirmed)",
         "Confirmation: the Copper River Room walkway will be cleared at 8 "
         "AM sharp on donor breakfast day. The admin lot space 'H' is "
         "held for the donor car."),
        (d(0), 8, 0, FACILITIES, "Facilities: polar vortex prep (status update)",
         "Status: 6 of 8 trucks cleared. The two-stage closure policy is "
         "in place. The east lot will be plowed by 6 PM the night before "
         "the gala. The mystery rattle is 'learning' (see ticket "
         "#4831). Otherwise, the parking is fine."),
    ]
    for day, h, m, frm, subj, body in fac_items:
        mail(day, h, m, frm, subj, body, "request")

    # --- campus police ----------------------------------------------------------------
    police_items = [
        (d(-10), 14, 0, POLICE, "Campus Police: parking lot incident (west side, GI Bldg)",
         "A vehicle was found parked in space 'H' in the admin lot. "
         "Space 'H' is reserved for donors, and the vehicle was not a "
         "donor. We have issued a warning and re-cleared the space. It "
         "remains empty, as it always does."),
        (d(-8), 15, 20, POLICE, "Campus Police: bike theft report (Knik Hall)",
         "A bike was reported stolen from outside Knik Hall. The report "
         "is open; if you've seen a suspicious bike near Knik Hall, "
         "contact the campus police non-emergency line."),
        (d(-6), 10, 45, POLICE, "Campus Police: lost property — one (1) northern-lights scarf",
         "Found: one (1) northern-lights scarf, outside the Aurora Club "
         "House. It's a personal item, not a university asset, but it's "
         "in the lost and found. If this is yours, claim it before the "
         "end of the month."),
        (d(-4), 13, 30, POLICE, "Campus Police: visitor parking (gala day) — plan confirmed",
         "Visitor parking for gala day is confirmed: 40 validated spaces "
         "in the Hyatt garage, with the plowed east lot as overflow if "
         "we close UAA Loop. The two-stage closure policy applies."),
        (d(-2), 11, 15, POLICE, "Campus Police: ribbon cutting day — traffic plan",
         "Traffic plan for the permafrost-lab ribbon cutting: media "
         "parking in the east lot, front steps cleared for the press "
         "availability. If the availability moves indoors (facilities is "
         "deciding based on weather), we'll adjust and announce."),
        (d(0), 10, 0, POLICE, "Campus Police: the 'H' space, again",
         "Space 'H' in the admin lot was found occupied again this "
         "morning. The occupant was not a donor. Second warning issued; "
         "space re-cleared. For the record, we keep this space for "
         "people we haven't met yet. They remain unmet."),
    ]
    for day, h, m, frm, subj, body in police_items:
        mail(day, h, m, frm, subj, body, "request")

    # --- food & dining --------------------------------------------------------------------
    food_items = [
        (d(-11), 14, 0, FOOD, "Food & Dining: fall menu feedback",
         "We're planning the fall menu — please take our 2-minute survey. "
         "The good sour cream (the one from the permafrost-lab mug) is on "
         "the menu, and so is the glow dessert. The moose keychain from "
         "the spam email is not on the menu; it is a keychain, not food."),
        (d(-8), 9, 30, FOOD, "Food & Dining: 'glow' dessert tasting (RSVP)",
         "We're hosting a tasting of the 'glow' dessert (the aurora gala "
         "one) later this month — RSVP by end of week. It's blue "
         "(spirulina). It is not a real aurora. It is a real dessert."),
        (d(-5), 10, 15, FOOD, "Food & Dining: coffee cart — donor breakfast day",
         "The coffee cart will be set up in the Copper River Room for "
         "donor breakfast day: the good coffee, and the permafrost-lab "
         "mug (the 10,000-year-old tusk fact is on the bottom)."),
        (d(-3), 13, 0, FOOD, "Food & Dining: gala catering — menu B confirmed",
         "Menu B ('Aurora Feast') is confirmed for the gala: king crab, "
         "smoked Arctic char, baked potato bar with the good sour cream, "
         "and the 'glow' dessert. The +$1,200 for the glow dessert is in "
         "the final invoice."),
        (d(-1), 11, 0, FOOD, "Food & Dining: fall menu — the good sour cream is back",
         "The good sour cream is back on the fall menu, and the glow "
         "dessert is back too. (The moose keychain is still not back; it "
         "was never here.)"),
        (d(0), 9, 15, FOOD, "Food & Dining: coffee cart — game day (ice arena)",
         "The coffee cart will be at the ice arena on game day, with the "
         "good coffee and the Seawolves hat for sale. The ice is good, "
         "the zamboni is good, and the cart is ready."),
    ]
    for day, h, m, frm, subj, body in food_items:
        mail(day, h, m, frm, subj, body, "request")

    # --- development / alumni / student orgs -------------------------------------------------
    dev_items = [
        (d(-12), 15, 0, DEV, "Advancement: annual fund appeal",
         "The annual fund appeal is live. The $2.5M goal is in sight, "
         "thanks to the Halvorsen Family Foundation. If you want a "
         "one-line ask for donor conversations, 'the lights are coming, "
         "and so is the lab' has tested well with mid-level donors."),
        (d(-9), 10, 30, DEV, "Advancement: matching gift deadline reminder",
         "Reminder: the annual fund matching gift closes at the end of "
         "the month. Donors who give by then get a 2x match. We'll send "
         "one more reminder next week, because people always ask 'what "
         "was the deadline' afterward."),
        (d(-6), 14, 30, ALUMNI, "Alumni: homecoming + aurora viewing",
         "Homecoming is coming, and the aurora outlook for the weekend "
         "looks decent (Kp 3–4). We're adding an optional aurora "
         "viewing slot to the schedule — bring a coat, and do not "
         "announce the lights; let the windows do the talking."),
        (d(-4), 9, 45, ALUMNI, "Alumni: career fair details",
         "The fall career fair is set: 40 employers, including three "
         "that specifically want the new Arctic Engineering program. "
         "Registration for students opens next week. We expect a good "
         "turnout; last year's fair had 600 visitors."),
        (d(-2), 13, 30, AURORA_CLUB, "Aurora Club: fall ball planning",
         "The fall aurora ball is taking shape. The 'Best Aurora' photo "
         "contest sponsorship from AK Electric is confirmed (they sent a "
         "nice letter; it's in the shared drive). We need the funding "
         "decision from your office by end of week so we can lock the "
         "volunteer schedule."),
        (d(-1), 16, 15, MAYA, "Student senate: budget request",
         "The student senate budget request is in the shared drive — "
         "two new advisor positions, more Aurora Club funding, and the "
         "student center repair list. For the record, the aurora club "
         "is correlated with the 3% headcount increase, and we're not "
         "going to pretend it isn't."),
    ]
    for day, h, m, frm, subj, body in dev_items:
        mail(day, h, m, frm, subj, body, "request")

    # --- logistics (flights, hotels) ------------------------------------------------------------
    log_items = [
        (d(-12), 8, 0, DELTA, "Delta confirmation: ANC->JNU (your Juneau trip)",
         "Your flight is confirmed: Delta 1201, ANC->JNU, 06:15. Seat "
         "14A, by the window — good for watching the aurora on the way "
         "to Juneau, if the aurora shows up. The gate is always on the "
         "departure board."),
        (d(-10), 9, 15, HYATT, "Hyatt Regency: hotel block (your Juneau trip)",
         "Your hotel block is confirmed for the Juneau trip: Hyatt "
         "Regency Anchorage, room 502, by the window. Check-in is "
         "standard; the aurora is optional but visible from 502 if "
         "cooperative."),
        (d(-8), 10, 0, DELTA, "Delta: gate change (your Juneau trip)",
         "Gate change on your flight Delta 1201: the new gate is on the "
         "departure board. (It was always on the departure board. The "
         "departure board is the gate.)"),
        (d(-6), 11, 30, HYATT, "Hyatt Regency: gala load-in (confirmation)",
         "Your load-in window for the gala is confirmed: 11:00–14:00 "
         "through the service entrance on 5th Ave. The ballroom's north "
         "windows face open sky; if the aurora shows up, the 24-foot "
         "ceiling means the lights will be very visible from the dance "
         "floor. No promises."),
        (d(-4), 14, 45, DELTA, "Delta: weather advisory (your Juneau trip)",
         "Advisory: possible weather delays on your Juneau trip due to "
         "the polar vortex watch. Monitor the departure board. We'll "
         "do our best; the weather will do its own."),
        (d(-2), 15, 30, HYATT, "Hyatt Regency: gala day — parking validation",
         "Parking validation for gala day is confirmed: 40 validated "
         "spaces in our garage, plus the university's plowed overflow "
         "lot if UAA Loop closes. The parking is fine. It's always "
         "fine."),
    ]
    for day, h, m, frm, subj, body in log_items:
        mail(day, h, m, frm, subj, body, "request")

    # --- media / press -----------------------------------------------------------------------------
    media_items = [
        (d(-11), 13, 0, APM, "APM: interview request (permafrost lab, ribbon cutting)",
         "We'd like to interview you ahead of the permafrost lab ribbon "
         "cutting — 15 minutes, audio. The 10,000-year-old mammoth-tusk "
         "fact is available for us to use as a pull quote, per comms. "
         "Let us know if you're available; we'll work around your "
         "schedule."),
        (d(-8), 10, 15, DKNG, "DKNG: one question for the ribbon cutting",
         "One question for the ribbon cutting, if you'll have it: 'What "
         "does the permafrost lab mean for the state's "
         "climate-mitigation plan?' Rep. Moses is asking for the same "
         "one-liner, so it's apparently the question of the week. The "
         "laminated fact sheet has the approved version."),
        (d(-5), 9, 0, KENA, "KENA: op-ed invitation — aurora season",
         "We'd like you to write a 500-word op-ed on the early aurora "
         "season — what it means for the state, and why UAA has a whole "
         "committee for it. Deadline is the end of the month. We'll "
         "supply the headline; you supply the wavy line."),
        (d(-2), 14, 30, APM, "APM: aurora forecast screen (gala day)",
         "We'll have a camera on the aurora forecast screen at the "
         "gala. Dr. Nakamura will be on the video link; if Kp hits 5, "
         "she will say 'look out the windows,' and we will be there. "
         "Note: the screen is 'learning' (IT ticket #4832), so we'll "
         "also film the paper forecast in the blue folder, just in "
         "case."),
    ]
    for day, h, m, frm, subj, body in media_items:
        mail(day, h, m, frm, subj, body, "request")

    # --- NWS / weather ---------------------------------------------------------------------------------
    nws_items = [
        (d(-9), 12, 0, NWS, "NWS: polar vortex watch (Anchorage region)",
         "A polar vortex watch is in effect for the Anchorage region. "
         "Conditions: cold, windy, with a possible blizzard. Follow "
         "official guidance and plan travel accordingly."),
        (d(-5), 18, 30, NWS, "NWS: aurora outlook bulletin",
         "Aurora outlook: Kp index forecast 3–5 for the coming week. "
         "Best viewing windows are late evening, under clear skies. If "
         "you're planning an outdoor event, check the short-term "
         "forecast before you start the tents."),
        (d(-1), 7, 45, NWS, "NWS: polar vortex watch (extended)",
         "The polar vortex watch is extended through the weekend. "
         "Continued cold and wind, with a possible blizzard. Campus "
         "and city services are preparing; the university's two-stage "
         "road closure policy is in place."),
    ]
    for day, h, m, frm, subj, body in nws_items:
        mail(day, h, m, frm, subj, body, "request")

    # --- forwarded chains / misc --------------------------------------------------------------------------
    misc = [
        (d(-13), 16, 45, "T. Redcloud (regent) <tredcloud@uaa.edu>",
         "Fwd: aurora forecast from last spring",
         "Forwarding the aurora forecast from last spring — Kp hit 5 and "
         "the lights showed up over the whole downtown skyline. Photo "
         "attached. This is why the aurora committee takes its forms "
         "seriously."),
        (d(-12), 13, 20, "P. Lindqvist (regent) <plindqvist@uaa.edu>",
         "Re: master plan comment period (one more comment)",
         "One more comment came in on the master plan: it's about "
         "parking. It's always about parking. The comment period closes "
         "soon; I'll make sure it's in the packet."),
        (d(-11), 9, 0, "R. Boudreaux (regent) <rboudreaux@uaa.edu>",
         "Re: endowment policy update",
         "The endowment policy update is in the shared drive. The $2.5M "
         "Arctic Engineering gift will be the first test of the new "
         "policy — the board should be comfortable with that before the "
         "first-of-month session."),
        (d(-10), 8, 30, "D. Okafor (regent) <dokafor@uaa.edu>",
         "Re: FY27 budget — infrastructure tab",
         "FY27 budget draft is in the shared drive. The infrastructure "
         "tab is where the action is (Dr. Raman is riding shotgun). If "
         "the fiscal committee hears the permafrost-lab ask in the "
         "first five minutes, that's a first for this budget cycle."),
        (d(-9), 14, 15, "S. Houghton (regent) <shoughton@uaa.edu>",
         "Re: IRB room + the projector that's 'thinking'",
         "For the record: the IRB meets in the Regents Chamber, and the "
         "chamber's projector is 'thinking' again (ticket #4824). We'll "
         "borrow the bridge-room projector, which has never thought a "
         "thought in its life and is entirely content to remain that "
         "way."),
        (d(-8), 11, 30, "L. Taimi (campus regent) <l.taimi@uaa.edu>",
         "Re: the 'H' space (again)",
         "The 'H' space in the admin lot was occupied again, and the "
         "occupant was not a donor. It's always empty because we keep "
         "it for people we haven't met yet. They remain unmet. I've "
         "asked campus police to log it as a 'near miss.' They have a "
         "form for everything."),
        (d(-7), 10, 0, "UAA Library <library@uaa.edu>",
         "Library: bond issue briefing for the senate",
         "The library bond issue lands on the senate's agenda this "
         "month. We've prepared a 2-page overview (the 14-page version "
         "exists but is, in the dean's words, 'for the wolves, "
         "figuratively'). The bond is real; the wolves are not."),
        (d(-6), 9, 30, "UAA Police Union <policeunion@uaa.edu>",
         "Re: officer safety report — for the file",
         "The officer safety report is in the shared drive, for the "
         "file and for the record. Nothing alarming: one near-miss at "
         "the west entrance, one bike theft (still open), and a "
         "standing reminder that the 'H' space is reserved."),
        (d(-5), 15, 45, "UAA Foundation <foundation@uaa.edu>",
         "Re: matching gift — deadline reminder",
         "Reminder: the annual fund matching gift closes at the end of "
         "the month, and the $2.5M goal is in sight thanks to the "
         "Halvorsen Family Foundation. If you want a one-line ask for "
         "your next donor conversation, 'the lights are coming and so "
         "is the lab' has tested well with mid-level donors."),
        (d(-4), 12, 0, "UAA Sustainability Office <sustainability@uaa.edu>",
         "Re: campus sustainability report (permafrost lab section)",
         "The campus sustainability report is in the shared drive. The "
         "permafrost lab section is on page 3 — it's always on page 3 — "
         "and it's the part the state's climate-mitigation office "
         "actually reads."),
        (d(-3), 10, 30, "UAA Housing <housing@uaa.edu>",
         "Re: student housing project — master plan status",
         "The student housing project near 14th and UAA Loop is on the "
         "master plan amendments (the special session is on your "
         "calendar). Community feedback has been ... enthusiastic, with "
         "one recurring theme: the parking."),
        (d(-2), 8, 45, "UAA Transit <transit@uaa.edu>",
         "Re: campus transit schedule (winter draft)",
         "Winter draft of the campus transit schedule is in the shared "
         "drive. Headways tighten during aurora season — the 9:40 PM "
         "run to the GI has never looked emptier when a Kp 5 is on, "
         "and never fuller when it isn't. Facilities will plow the bus "
         "lanes under the two-stage closure policy."),
        (d(-10), 17, 25, "B. Marsh (co-op student) <bmarsh@uaa.edu>",
         "Fwd: wolf GPS data (the good chart)",
         "Forwarding the wolf GPS chart Lena sent. The whole pack is "
         "holding the corridor along the Chitina River — that's the "
         "good news. The other charts exist, but this is the one to "
         "show people."),
        (d(-8), 18, 40, "S. Redcloud (co-op student) <sredcloud@uaa.edu>",
         "Re: the 'little wolf' photo op with Ralph",
         "Following up on the 'little wolf' photo op with Ralph the "
         "Walrus: the students think it's a good idea. I think it's a "
         "good idea. So does the wolf, apparently (he's not in this "
         "email thread, but the energy is there)."),
        (d(-6), 20, 15, "Dev Patel (major gifts) <dpatel@alaska.edu>",
         "Re: aurora breakfast photo — the camera is ready",
         "For the record: the camera is ready. If the aurora shows up "
         "at breakfast, I will take the photo. I will not encourage "
         "it. (I will encourage it. I'm a major gifts person; the "
         "aurora is a separate occurrence, but a good one.)"),
        (d(-4), 21, 30, "J. Taimi (chief of staff, Rep. Moses) <j.taimi@akleg.gov>",
         "Re: parking on the west side of the GI building",
         "Following up on the parking situation on the west side of the "
         "GI building: my principal has strong feelings about it and "
         "would like a word with facilities. Please keep me away from "
         "T. Kowalski. I've met him; he's 'learning,' and I am not "
         "learning, and we are not learning together."),
        (d(-2), 19, 50, MAYA, "Re: student senate budget request — the aurora club is the reason",
         "For the record: the aurora club is the reason for the 3% "
         "headcount increase. (It's not. It's correlated. We're not "
         "going to pretend it isn't.) The full request is in the "
         "shared drive; it's the 2-page one, not the 14-page one."),
        (d(-1), 15, 45, "L. Taimi (campus regent) <l.taimi@uaa.edu>",
         "Re: the poem about parking (it's good)",
         "For the record: the poem about parking is good. I've "
         "included it in the regents packet. It's on page 3, which is "
         "where the permafrost lab is, because page 3 is a social "
         "construct and everything good lives there. The poem is about "
         "the 'H' space, the donor space that is always empty. It gets "
         "why."),
        (d(0), 7, 30, "Katie Nakata (Chancellor's Admin) <katie.nakata@alaska.edu>",
         "The blue folder (inventory, for the record)",
         "For the record, the blue folder on your desk contains: (1) "
         "the aurora Kp form (due tomorrow 5 PM; the little wavy line "
         "is the right line); (2) the fisheries grant signature page "
         "($750K, real); (3) a photo of the walrus (not for work, just "
         "for morale — the scarf is a personal item, but it's in the "
         "story, and it's always in the story)."),
        (d(0), 12, 30, "GI Office <gi-office@gi.alaska.edu>",
         "GI: permafrost core display case (status)",
         "Status on the permafrost core display case: it's staged on "
         "the second floor, but the west-wing elevator is the one "
         "that's been making the noise (facilities says it's 'fine' "
         "with quotes). If Rep. Moses wants to see the cores before the "
         "ribbon cutting, we should either pre-stage the case in the "
         "lobby or plan on the stairs (three flights). The "
         "10,000-year-old tusk fact stays on the laminated card — Prof. "
         "Beringer has been told, firmly, not to elaborate."),
    ]
    for day, h, m, frm, subj, body in misc:
        mail(day, h, m, frm, subj, body, "misc")

# ---------------------------------------------------------------------------
# Render inbox
# ---------------------------------------------------------------------------

def render_inbox(today: date) -> str:
    # newest first
    mails = sorted(
        MAILS,
        key=lambda m: (m.day, m.hour, m.minute),
        reverse=True,
    )
    lines = [
        "# Inbox — Dr. Ingrid Halvorsen <ingrid.halvorsen@alaska.edu>",
        "",
        f"Mailbox export generated {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        f"Total messages: {len(mails)}",
        "",
        "Format: each message is a `##` heading with "
        "`[YYYY-MM-DD HH:MM] From: ...`, followed by a `**Subject:**` "
        "line and the body. Messages are newest-first.",
        "",
        "---",
        "",
    ]
    for m in mails:
        lines.append(f"## [{m.day.strftime('%Y-%m-%d')} {m.hour:02d}:{m.minute:02d}] "
                     f"From: {m.frm}")
        lines.append(f"**Subject:** {m.subject}")
        lines.append("")
        lines.append(m.body)
        lines.append("")
        lines.append("---")
        lines.append("")
    lines.append("_End of inbox export._")
    lines.append("")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    if len(sys.argv) > 1:
        base = datetime.strptime(sys.argv[1], "%Y-%m-%d").date()
    else:
        base = date.today()

    global MAILS
    MAILS = []
    event_mails(base)
    noise_mails(base)

    days = build_calendar(base)
    DATA.mkdir(exist_ok=True)
    (DATA / "calendar.md").write_text(render_calendar(days), encoding="utf-8")
    (DATA / "inbox.md").write_text(render_inbox(base), encoding="utf-8")

    n_events = sum(len(evs) for _, evs in days)
    print(f"Wrote {DATA/'calendar.md'} ({n_events} events over 14 days from "
          f"{base})")
    print(f"Wrote {DATA/'inbox.md'} ({len(MAILS)} emails)")
    tags: dict[str, int] = {}
    for m in MAILS:
        tags[m.tag] = tags.get(m.tag, 0) + 1
    for tag in sorted(tags):
        print(f"  {tag}: {tags[tag]}")


if __name__ == "__main__":
    main()
