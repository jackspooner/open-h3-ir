---
name: openh3-ir-compiler
description: Maintain or call the local OpenH3-IR compiler fork, including deterministic plans, reference bindings, camera intent and offline validation.
---

# OpenH3-IR compiler

This fork owns Brief-to-Context-IR compilation, deterministic draft metadata and
validation. RouterText owns its deployed source pin, local inference bridge and
service preparation; use `routertext-2-service` for those operations.

Read [README](../../README.md), [compiler rules](../../AGENTS.md) and the
[calling guide](../../docs/calling-the-api.md) before changing or using the relevant
surface. Python >=3.10 and the declared package dependencies are required. Prepare
a worktree with `python -m pip install -e '.[dev]'`; this installs code/dependencies
but starts no service. Run `python -m pytest -q` and `h3ir controls` separately.

A Brief contains intent, duration, optional shot count, dialogue and typed assets.
Returned plans retain labels, asset wiring, timing and camera metadata alongside
validated prompt text and findings. Preserve exact dialogue and source hashes.
Compilation normally calls the configured language/vision backend; even `llm=False`
can analyze assets. Offline tests must stub analysis and the backend explicitly.
Do not treat draft fallback as successful written enrichment or silently change models.

For a static single shot, pin `shots: 1` and state a direct sentence such as
`One continuous static medium shot of the person in the reference.` or
`Keep the camera static.` in intent/constraints. The draft selects `Static Shot`
with no amplitude/speed, even at extreme creativity. The recognizer deliberately
does not map automatic/multi-shot edits or negated/sequential instructions. This
is not a general prose parser: write-first output retains the draft plan, and
arbitrary written camera prose is not back-projected into it. Check both outputs.

The compiler itself loads no H3 weights. Actual reference analysis, language-model
inference, GPU admission and downstream video rendering belong to their owners.
Source tests and controls do not prove live activation, prose quality or video
fidelity. Preserve old prepared revisions/state during upgrades; activate only
through the service owner's workload-aware procedure.
