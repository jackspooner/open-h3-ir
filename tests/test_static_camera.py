"""Explicit single-shot camera direction survives the draft and write-first paths."""
import pytest

import h3ir.compile as compiler
from h3ir.draft import deterministic_draft
from h3ir.models import AssetCard, AssetKind, AssetRef, Brief, DialogueLine, Mode, Role
from h3ir.plan import ProfileOptions
from h3ir.render import render_ir


INTENT = ("One continuous static medium shot of the person in the reference. "
          "The person looks toward the camera and says the exact supplied line. "
          "Soft room ambience, no music, no on-screen text.")
WRITTEN = """subject_definitions:
<Subject 1> is the person in <Picture 1>, with short dark hair.

summary:
[reference generation] The target video shows <Subject 1> greeting the viewer.

retention_analysis:
<Subject 1> (appears in [Shot 1]): fully_preserved - the short dark hair is retained.

detailed_description:
The target video is in live-action style.
[Shot 1] A medium shot holds on <Subject 1>. The camera holds a static shot. <Subject 1> (S1) says: <d>[English] Welcome home.</d>

overall_soundscape:
Soft room ambience continues throughout.

non_diegetic_music:
N/A
"""


class OfflineBackend:
    class cfg:
        model = "offline-fixture"

    def require_available(self):
        pass

    def server_version(self):
        return "offline-fixture"


@pytest.mark.parametrize("creativity", ["restrained", "balanced", "bold", "extreme"])
@pytest.mark.parametrize("written", [False, True])
def test_original_reference_dialogue_request(monkeypatch, creativity, written):
    brief = Brief(intent=INTENT, seconds=8, shots=1, creativity=creativity,
                  dialogue=[DialogueLine(text="Welcome home.")],
                  assets=[AssetRef(kind=AssetKind.IMAGE, role=Role.SUBJECT,
                                   sha256="reference", px=(1024, 1024), role_stated=True)])
    cards = {"reference": AssetCard(sha256="reference", kind=AssetKind.IMAGE,
              style="Live-action", summary="a person", subjects=[
                  {"kind": "person", "descriptor": "the person", "attributes": ["short dark hair"]}])}
    monkeypatch.setattr(compiler, "analyse_all", lambda *a, **kw: cards)
    monkeypatch.setattr(compiler, "compose_brief", lambda *a, **kw: WRITTEN)
    doc = compiler.compile_brief(brief, backend=OfflineBackend(), llm=written)
    assert doc.source == ("written" if written else "draft")
    camera = doc.plan.shots[0].camera
    assert (camera.type, camera.amplitude, camera.speed) == ("Static Shot", None, None)
    assert "The camera holds a static shot" in doc.prompt
    assert "<d>[English] Welcome home.</d>" in doc.prompt
    assert doc.plan.manifest[0].sha256 == "reference"
    assert not [f for f in doc.findings if f.severity == "ERROR"]
    if written:
        assert doc.prompt == WRITTEN


@pytest.mark.parametrize("intent,constraints", [
    ("A static shot of the harbour.", []),
    ("One continuous static medium shot of a person.", []),
    ("A person waves. Keep the camera static.", []),
    ("A person waves.", ["Static camera."]),
    ("The camera remains static while a person waves.", []),
])
def test_positive_single_shot_instructions(intent, constraints):
    plan = deterministic_draft(Brief(intent=intent, constraints=constraints, shots=1), Mode.T2VA, {})
    assert plan.shots[0].camera.type == "Static Shot"
    assert "The camera holds a static shot" in render_ir(plan, ProfileOptions()).prompt


@pytest.mark.parametrize("intent,shots", [
    ("A person waves.", 1),
    ("A static sculpture stands in a room.", 1),
    ("Do not use a static medium shot.", 1),
    ("The camera is not static.", 1),
    ("A static shot is not wanted.", 1),
    ("A static shot, then push in.", 1),
    ("A static shot of the harbour.", 2),
    ("A static shot of the harbour.", None),
])
def test_unspecified_negative_or_unpinned_direction_keeps_rotation(intent, shots):
    plan = deterministic_draft(Brief(intent=intent, shots=shots), Mode.T2VA, {})
    assert plan.shots[0].camera.type == "Push In"
