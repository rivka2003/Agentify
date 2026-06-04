"""Pure helpers behind run-mapped's failure recovery. No network/LLM."""

from agentify.cli import _failure_payload, _repeat_failure_hint
from agentify.recipe import RecipeFailure


def _failure(*, partial=None, url="https://x/", op="click", step=2, reason="boom"):
    e = RecipeFailure(step, reason, op=op)
    e.url = url
    e.partial = partial or {}
    return e


def test_failure_payload_carries_context():
    e = _failure(partial={"title": "Widget"}, url="https://shop/cart", op="select", step="2.then[1]")
    payload = _failure_payload(e)
    assert payload["failed_step"] == "2.then[1]"
    assert payload["op"] == "select"
    assert payload["url"] == "https://shop/cart"
    assert payload["partial"] == {"title": "Widget"}
    assert "RecipeFailure" in payload["error"]


def test_failure_payload_omits_partial_when_empty():
    assert "partial" not in _failure_payload(_failure(partial={}))


def test_repeat_hint_fires_only_after_threshold_consecutive():
    assert _repeat_failure_hint(["search"], "search") is None              # 1x
    hint = _repeat_failure_hint(["search", "search"], "search")            # 2x
    assert hint and "search" in hint
    assert _repeat_failure_hint(["search", "search", "search"], "search")  # 3x still fires


def test_repeat_hint_requires_consecutive_not_total():
    # A different tool in between breaks the streak.
    assert _repeat_failure_hint(["search", "login", "search"], "search") is None
