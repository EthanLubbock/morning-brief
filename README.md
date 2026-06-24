# Morning Brief
 
A Raspberry Pi service that emails a daily morning summary and processes reply-based commands to manage the week.
 
## What it does
 
Each morning at 06:30 it sends an email containing:
 
- Today's workout from the weekly training plan
- Upcoming calendar events (next 7 days)
- Active tasks with priorities and due dates
- Bin collection reminder when due
Reply to the email to interact:
 
- Add or complete tasks
- Add scheduling constraints ("can't do gym Monday, dentist")
- Switch between default and game week modes
- Persist changes across weekly resets
GPT-4.1-mini parses reply intent and replans the week accordingly. State resets every Sunday at 21:00, preserving persisted constraints and open todos.
 
## Stack
 
- Python 3.13, systemd timers
- OpenAI `gpt-4.1-mini` for email parsing and replanning
- iCloud CalDAV for calendar feeds
- Gmail bot account for send/receive
## Structure
 
```
brief/              # Main package
  morning.py        # Generates and sends the daily email
  inbox.py          # Polls Gmail and processes replies
  llm.py            # OpenAI parse and replan calls
  state.py          # week_state.json read/write
  calendar_feed.py  # iCloud feed fetching
  config.py         # Constants and env vars
data/               # Runtime state (gitignored)
  week_state.json
  todos.json
  bins.json
base_plan.yaml      # Base training programme
```
 
## Setup
 
1. Copy `.env.example` to `.env` and fill in credentials
2. `pip install -r requirements.txt`
3. Copy systemd units from `systemd/` to `/etc/systemd/system/`
4. `sudo systemctl enable --now brief-morning.timer brief-inbox.timer brief-reset.timer`
## Timers
 
| Timer | Schedule |
|---|---|
| `brief-morning` | Daily 06:30 |
| `brief-inbox` | Every 10 minutes |
| `brief-reset` | Sunday 21:00 |
