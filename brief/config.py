import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
BASE_PLAN_FILE = ROOT / "base_plan.yaml"
TODOS_FILE = DATA / "todos.json"
BINS_FILE = DATA / "bins.json"
WEEK_STATE_FILE = DATA / "week_state.json"

OWNER_EMAIL = os.environ["OWNER_EMAIL"]
GMAIL_USER = os.environ["GMAIL_USER"]
GMAIL_APP_PASSWORD = os.environ["GMAIL_APP_PASSWORD"]
OPENAI_API_KEY = os.environ["OPENAI_API_KEY"]
OPENAI_MODEL = os.environ.get("OPENAI_MODEL", "gpt-4.1-mini")

IMAP_HOST = "imap.gmail.com"
SMTP_HOST = "smtp.gmail.com"
SMTP_PORT = 465

# role: "mine" / "shared" constrain the schedule. A future "partner"
# calendar would be awareness-only (handled in llm.replan_week).
CALENDARS = [
    {"name": "Ethan",  "role": "mine",   "url": os.environ.get("ICS_URL_ETHAN", "")},
    {"name": "Shared", "role": "shared", "url": os.environ.get("ICS_URL_SHARED", "")},
]

BIN_EXPIRY_WARN_DAYS = 28
TODOS_IN_BRIEF = 3