"""Modules 3-4: when one Gemini model is overloaded (503), the next model in the chain is used."""
import pytest

from app.services.gemini_fallback import MODELS, generate_with_fallback


class FakeModels:
    def __init__(self, fail_first):
        self.calls, self.fail_first = [], fail_first

    def generate_content(self, model, contents, **kw):
        self.calls.append(model)
        if len(self.calls) <= self.fail_first:
            raise RuntimeError("503 UNAVAILABLE: high demand")
        return type("R", (), {"text": f"answer from {model}"})()


class FakeClient:
    def __init__(self, fail_first):
        self.models = FakeModels(fail_first)


def test_first_model_answers():
    c = FakeClient(0)
    assert generate_with_fallback(c, "p").text == f"answer from {MODELS[0]}"
    assert c.models.calls == [MODELS[0]]


def test_overloaded_model_falls_through_to_next():
    c = FakeClient(2)
    assert generate_with_fallback(c, "p").text == f"answer from {MODELS[2]}"
    assert c.models.calls == list(MODELS)


def test_all_models_failing_raises_so_callers_keep_their_fallback():
    with pytest.raises(RuntimeError):
        generate_with_fallback(FakeClient(3), "p")


def test_same_chain_as_module5():
    from app.services.roadmap.roadmap_llm import MODELS as M5
    assert tuple(MODELS) == tuple(M5)
