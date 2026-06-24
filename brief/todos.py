import json
from datetime import date
from . import config

PRIORITY_WEIGHT = {"high": 100, "medium": 50, "low": 10}


class TodoStore:
    def __init__(self):
        self.data = json.loads(config.TODOS_FILE.read_text())

    def save(self) -> None:
        tmp = config.TODOS_FILE.with_suffix(".tmp")
        tmp.write_text(json.dumps(self.data, indent=2))
        tmp.replace(config.TODOS_FILE)

    def _next_id(self) -> str:
        nums = [int(t["id"].split("-")[1]) for t in self.data["tasks"]]
        return f"t-{(max(nums) + 1 if nums else 1):03d}"

    def add(self, title: str, priority: str = "medium", due: str | None = None) -> None:
        self.data["tasks"].append({
            "id": self._next_id(), "title": title, "priority": priority,
            "added": date.today().isoformat(), "due": due, "done": False,
        })

    def complete(self, match: str) -> str | None:
        """Mark the first open task whose title contains `match` as done."""
        m = match.lower()
        for t in self.data["tasks"]:
            if not t["done"] and m in t["title"].lower():
                t["done"] = True
                return t["title"]
        return None

    def _score(self, task: dict, today: date) -> int:
        s = PRIORITY_WEIGHT.get(task["priority"], 50)
        s += (today - date.fromisoformat(task["added"])).days
        if task["due"]:
            left = (date.fromisoformat(task["due"]) - today).days
            if left <= 0:        s += 200
            elif left <= 7:      s += (8 - left) * 20
            elif left <= 30:     s += (31 - left)
        return s

    def select(self, n: int) -> list[dict]:
        today = date.today()
        open_tasks = [t for t in self.data["tasks"] if not t["done"]]
        return sorted(open_tasks, key=lambda t: self._score(t, today),
                      reverse=True)[:n]