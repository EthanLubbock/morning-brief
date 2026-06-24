from datetime import date, timedelta

from brief.todos import TodoStore


def test_select_excludes_done(sandbox):
    picked = TodoStore().select(10)
    titles = [t["title"] for t in picked]
    assert "done already" not in titles
    assert len(picked) == 3


def test_select_orders_by_score(sandbox):
    # medium-soon (due in 3d) scores above high-no-due above low-old
    picked = TodoStore().select(3)
    assert [t["id"] for t in picked] == ["t-002", "t-001", "t-003"]


def test_select_respects_n(sandbox):
    assert len(TodoStore().select(2)) == 2


def test_add_assigns_sequential_id_and_persists(sandbox):
    store = TodoStore()
    store.add("buy flowers", "high", None)
    store.save()
    reloaded = TodoStore()
    new = [t for t in reloaded.data["tasks"] if t["title"] == "buy flowers"]
    assert len(new) == 1
    assert new[0]["id"] == "t-005"
    assert new[0]["priority"] == "high"
    assert new[0]["added"] == date.today().isoformat()


def test_complete_marks_first_match(sandbox):
    store = TodoStore()
    title = store.complete("high no due")
    assert title == "high no due"
    done = next(t for t in store.data["tasks"] if t["id"] == "t-001")
    assert done["done"] is True


def test_complete_substring_match(sandbox):
    store = TodoStore()
    assert store.complete("soon") == "medium soon"


def test_complete_no_match_returns_none(sandbox):
    assert TodoStore().complete("nonexistent task") is None


def test_overdue_task_scores_highest(sandbox):
    data = {"tasks": [
        {"id": "t-001", "title": "overdue", "priority": "low",
         "added": date.today().isoformat(),
         "due": (date.today() - timedelta(days=2)).isoformat(), "done": False},
        {"id": "t-002", "title": "high future", "priority": "high",
         "added": date.today().isoformat(), "due": None, "done": False},
    ]}
    sandbox.write_todos(data)
    assert TodoStore().select(1)[0]["title"] == "overdue"