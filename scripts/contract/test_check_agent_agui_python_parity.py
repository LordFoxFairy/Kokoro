from __future__ import annotations

import copy
import json
import shutil
from datetime import datetime
from pathlib import Path
from typing import Any

import pytest
from ag_ui.core import ActivitySnapshotEvent, TextMessageContentEvent
from kokoro_agent.presentation import AgentAguiCandidateSource, build_agui_candidate

from scripts.contract.check_agent_agui_python_parity import (
    AgentAguiPythonParityError,
    validate_corpus,
    validate_repository,
)


ROOT = Path(__file__).resolve().parents[2]


def _corpus() -> dict[str, Any]:
    return json.loads(
        (ROOT / "contract/corpus/agui-presentation-v1.json").read_text(encoding="utf-8")
    )


def _profile() -> dict[str, Any]:
    return json.loads(
        (ROOT / "contract/registry/agui-agent-candidate-profile-v1.yaml").read_text(
            encoding="utf-8"
        )
    )


def _repository_fixture(
    tmp_path: Path,
    *,
    corpus: dict[str, Any] | None = None,
    profile: dict[str, Any] | None = None,
) -> Path:
    fixture_root = tmp_path / "repository"
    for relative in (
        "kokoro-agent/pyproject.toml",
        "kokoro-agent/uv.lock",
        "contract/registry/agui-upstream-profile.yaml",
    ):
        target = fixture_root / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / relative, target)
    candidate_profile_path = (
        fixture_root / "contract/registry/agui-agent-candidate-profile-v1.yaml"
    )
    candidate_profile_path.parent.mkdir(parents=True, exist_ok=True)
    candidate_profile_path.write_text(
        json.dumps(profile or _profile()), encoding="utf-8"
    )
    corpus_path = fixture_root / "contract/corpus/agui-presentation-v1.json"
    corpus_path.parent.mkdir(parents=True, exist_ok=True)
    corpus_path.write_text(json.dumps(corpus or _corpus()), encoding="utf-8")
    return fixture_root


def _milliseconds(recorded_at: str) -> int:
    return int(
        datetime.fromisoformat(recorded_at.replace("Z", "+00:00")).timestamp() * 1000
    )


def _replace_case_event(
    target_case: dict[str, Any],
    source_case: dict[str, Any],
    *,
    event_model: type[ActivitySnapshotEvent] | type[TextMessageContentEvent],
) -> None:
    source_document = target_case["candidateEnvelope"]["source"]
    event_document = copy.deepcopy(source_case["candidateEnvelope"]["event"])
    event_document["timestamp"] = _milliseconds(source_document["recordedAt"])
    rebuilt = build_agui_candidate(
        event_model.model_validate(event_document),
        source=AgentAguiCandidateSource.model_validate(source_document),
    )
    target_case["candidateEnvelope"] = rebuilt.model_dump(
        mode="json", by_alias=True, exclude_none=True
    )


def test_rebuilds_every_root_candidate_with_pinned_agent_python() -> None:
    assert validate_repository(ROOT) == 15


def test_rejects_root_candidate_digest_drift() -> None:
    corpus = copy.deepcopy(_corpus())
    envelope = corpus["agentCandidateEnvelopeCases"][0]["candidateEnvelope"]
    envelope["eventDigest"] = f"sha256:{'0' * 64}"
    with pytest.raises(
        AgentAguiPythonParityError, match="agent_agui_python_envelope_invalid"
    ):
        validate_corpus(corpus, _profile())


def test_rejects_missing_or_duplicate_candidate_coverage() -> None:
    corpus = copy.deepcopy(_corpus())
    corpus["agentCandidateEnvelopeCases"].append(
        copy.deepcopy(corpus["agentCandidateEnvelopeCases"][0])
    )
    with pytest.raises(
        AgentAguiPythonParityError, match="agent_agui_python_candidate_duplicate"
    ):
        validate_corpus(corpus, _profile())


def test_registry_added_event_arm_requires_a_canonical_python_envelope(
    tmp_path: Path,
) -> None:
    profile = _profile()
    profile["allowedEventTypes"].append("STATE_SNAPSHOT")
    fixture_root = _repository_fixture(tmp_path, profile=profile)

    with pytest.raises(
        AgentAguiPythonParityError,
        match="agent_agui_python_candidate_coverage_invalid",
    ):
        validate_repository(fixture_root)


def test_missing_text_start_cannot_hide_behind_duplicate_text_content(
    tmp_path: Path,
) -> None:
    corpus = _corpus()
    cases = corpus["agentCandidateEnvelopeCases"]
    text_start = next(
        case
        for case in cases
        if case["candidateEnvelope"]["event"]["type"] == "TEXT_MESSAGE_START"
    )
    text_content = next(
        case
        for case in cases
        if case["candidateEnvelope"]["event"]["type"] == "TEXT_MESSAGE_CONTENT"
    )
    _replace_case_event(text_start, text_content, event_model=TextMessageContentEvent)
    fixture_root = _repository_fixture(tmp_path, corpus=corpus)

    with pytest.raises(
        AgentAguiPythonParityError,
        match="agent_agui_python_candidate_coverage_invalid",
    ):
        validate_repository(fixture_root)


def test_missing_activity_cannot_hide_behind_duplicate_discriminator(
    tmp_path: Path,
) -> None:
    corpus = _corpus()
    activity_cases = [
        case
        for case in corpus["agentCandidateEnvelopeCases"]
        if case["candidateEnvelope"]["event"]["type"] == "ACTIVITY_SNAPSHOT"
    ]
    _replace_case_event(
        activity_cases[1], activity_cases[0], event_model=ActivitySnapshotEvent
    )
    fixture_root = _repository_fixture(tmp_path, corpus=corpus)

    with pytest.raises(
        AgentAguiPythonParityError,
        match="agent_agui_python_activity_coverage_invalid",
    ):
        validate_repository(fixture_root)


def test_observed_activity_not_declared_by_registry_is_rejected(tmp_path: Path) -> None:
    profile = _profile()
    profile["allowedActivityTypes"].remove("kokoro.error.v1")
    fixture_root = _repository_fixture(tmp_path, profile=profile)

    with pytest.raises(
        AgentAguiPythonParityError,
        match="agent_agui_python_activity_coverage_invalid",
    ):
        validate_repository(fixture_root)


def test_text_start_role_shape_drift_is_rejected(tmp_path: Path) -> None:
    corpus = _corpus()
    text_start = next(
        case
        for case in corpus["agentCandidateEnvelopeCases"]
        if case["candidateEnvelope"]["event"]["type"] == "TEXT_MESSAGE_START"
    )
    text_start["candidateEnvelope"]["event"]["role"] = "user"
    fixture_root = _repository_fixture(tmp_path, corpus=corpus)

    with pytest.raises(
        AgentAguiPythonParityError, match="agent_agui_python_envelope_invalid"
    ):
        validate_repository(fixture_root)
