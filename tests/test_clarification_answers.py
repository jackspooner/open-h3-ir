"""A clarification answer is an explicit role, not another inference hint."""
from pathlib import Path

import pytest

from h3ir import service
from h3ir.mode import infer_mode, needs_clarification
from h3ir.models import Mode, Role


@pytest.fixture
def brief_input(monkeypatch):
    monkeypatch.setattr(service, "_require_uploaded", lambda _: None)
    monkeypatch.setattr(service, "_source_of", lambda a: (Path("fixture"), a.sha256))
    return {
        "intent": "animate this photo",
        "assets": [{"kind": "image", "sha256": "a" * 64}],
    }


@pytest.mark.parametrize("answer,role,mode", [
    ("opening_frame", Role.FRAME_ANCHOR_FIRST, Mode.I2VA),
    ("appears_in", Role.SUBJECT, Mode.REF2VA),
])
def test_question_answer_resolves_role_without_changing_hash(brief_input, answer, role, mode):
    unresolved = service._to_brief(service.BriefIn(**brief_input))
    unresolved.assets[0].px = (1024, 1024)
    question = needs_clarification(infer_mode(unresolved, [], backend=None))
    assert question and answer in [o["id"] for o in question["options"]]
    resolved = service._to_brief(service.BriefIn(
        **brief_input, answer={question["id"]: answer}))
    resolved.assets[0].px = (1024, 1024)
    decision = infer_mode(resolved, [], backend=None)
    assert resolved.assets[0].sha256 == "a" * 64
    assert resolved.assets[0].role is role
    assert resolved.assets[0].role_stated is True
    assert decision.mode is mode
    assert needs_clarification(decision) is None


def test_opening_frame_targets_an_image_even_when_audio_is_first(brief_input):
    brief_input["assets"].insert(0, {"kind": "audio", "sha256": "b" * 64})
    resolved = service._to_brief(service.BriefIn(
        **brief_input, answer={"anchor_or_reference": "opening_frame"}))
    assert resolved.assets[0].role is Role.BGM
    assert resolved.assets[1].role is Role.FRAME_ANCHOR_FIRST


def test_reference_answer_settles_two_ambiguous_images(brief_input):
    brief_input["assets"].append({"kind": "image", "sha256": "b" * 64})
    resolved = service._to_brief(service.BriefIn(
        **brief_input, answer={"anchor_or_reference": "appears_in"}))
    assert all(a.role_stated and a.role is Role.SUBJECT for a in resolved.assets)
    assert infer_mode(resolved, [], backend=None).mode is Mode.REF2VA
