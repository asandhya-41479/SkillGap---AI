"""Module 5 fix: Gemini text with non-English characters (e.g. a stray "摘要") is never shown.
The summary falls back to the deterministic one; such items are dropped (then retried / templated)."""
import json

from app.services.roadmap.roadmap_llm import _parse


def item(key="fastapi", **over):
    base = {"skill_key": key, "reason": "FastAPI is required for this role and builds on your Python.",
            "topics": ["Routing", "Validation"],
            "practical_tasks": [{"title": "Exercise", "description": "Build a small example.", "type": "exercise"}],
            "project_task": "Add one endpoint to your practice project.", "milestone": "A tested endpoint."}
    base.update(over)
    return base


def reply(summary, *items):
    return json.dumps({"summary": summary, "items": list(items)})


def test_clean_english_output_is_accepted():
    summary, items = _parse(reply("Three skills planned over eight weeks, starting with FastAPI.", item()), {"fastapi"})
    assert summary.startswith("Three skills") and "fastapi" in items


def test_summary_with_chinese_word_falls_back():
    summary, items = _parse(reply("Three skills planned over eight weeks. 摘要", item()), {"fastapi"})
    assert summary is None                      # caller then uses the deterministic summary
    assert "fastapi" in items


def test_item_with_non_english_text_is_dropped():
    _, items = _parse(reply("Plan for eight weeks.", item(milestone="完成一个端点 endpoint")), {"fastapi"})
    assert items == {}                          # caller retries, then uses the template


def test_typographic_quotes_and_dashes_are_allowed():
    s = "Learn FastAPI — the “fast” framework… it’s required."
    summary, items = _parse(reply(s, item(reason=s)), {"fastapi"})
    assert summary == s and "fastapi" in items


def test_deterministic_template_with_accented_skill_is_not_filtered():
    from app.services.roadmap.roadmap_llm import ItemContent
    ok = ItemContent(skill_key="español", reason="Required by the target role for Español content.",
                     topics=["Core concepts of Español", "Usage"],
                     practical_tasks=[{"title": "Español basics", "description": "Practise.", "type": "exercise"}],
                     project_task="Apply Español to one feature.", milestone="A working example.")
    assert ok.skill_key == "español"             # the guard lives in _parse (Gemini text), not in the model
