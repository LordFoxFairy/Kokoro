#!/usr/bin/env python3
"""Rebuild Root's Agent AG-UI corpus through the pinned Python adapter."""

from __future__ import annotations

import argparse
import importlib.metadata
import json
import tomllib
from collections.abc import Mapping
from pathlib import Path
from typing import Any, NoReturn, cast

from ag_ui.core import (
    ActivitySnapshotEvent,
    BaseEvent,
    RunErrorEvent,
    RunFinishedEvent,
    RunStartedEvent,
    TextMessageContentEvent,
    TextMessageEndEvent,
    TextMessageStartEvent,
)
from kokoro_agent.presentation import (
    AGUI_UPSTREAM_COMMIT,
    AGUI_UPSTREAM_PYTHON_VERSION,
    AgentAguiCandidateSource,
    build_agui_candidate,
)


AGUI_REPOSITORY = "https://github.com/ag-ui-protocol/ag-ui"
AGUI_PYTHON_SUBDIRECTORY = "sdks/python"
EXPECTED_CANDIDATE_COUNT = 6

_EVENT_MODELS: Mapping[str, type[BaseEvent]] = {
    "ACTIVITY_SNAPSHOT": ActivitySnapshotEvent,
    "RUN_ERROR": RunErrorEvent,
    "RUN_FINISHED": RunFinishedEvent,
    "RUN_STARTED": RunStartedEvent,
    "TEXT_MESSAGE_CONTENT": TextMessageContentEvent,
    "TEXT_MESSAGE_END": TextMessageEndEvent,
    "TEXT_MESSAGE_START": TextMessageStartEvent,
}


class AgentAguiPythonParityError(ValueError):
    """Stable fail-closed error for the executable Python parity gate."""


def _fail(code: str, detail: str) -> NoReturn:
    raise AgentAguiPythonParityError(f"{code}: {detail}")


def _mapping(value: object, *, code: str, detail: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        _fail(code, detail)
    return cast(Mapping[str, Any], value)


def _sequence(value: object, *, code: str, detail: str) -> list[Any]:
    if not isinstance(value, list):
        _fail(code, detail)
    return cast(list[Any], value)


def _load_json(path: Path) -> Mapping[str, Any]:
    try:
        document = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        _fail("agent_agui_python_input_invalid", f"{path}: {error}")
    return _mapping(
        document,
        code="agent_agui_python_input_invalid",
        detail=f"{path} must contain an object",
    )


def _load_toml(path: Path) -> Mapping[str, Any]:
    try:
        document = tomllib.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, tomllib.TOMLDecodeError) as error:
        _fail("agent_agui_python_pin_invalid", f"{path}: {error}")
    return document


def _verify_python_pins(root: Path) -> None:
    pyproject = _load_toml(root / "kokoro-agent/pyproject.toml")
    dependencies = _sequence(
        _mapping(
            pyproject.get("project"),
            code="agent_agui_python_pin_invalid",
            detail="Agent pyproject project table missing",
        ).get("dependencies"),
        code="agent_agui_python_pin_invalid",
        detail="Agent pyproject dependency list missing",
    )
    required_dependency = f"ag-ui-protocol=={AGUI_UPSTREAM_PYTHON_VERSION}"
    if dependencies.count(required_dependency) != 1:
        _fail(
            "agent_agui_python_pin_invalid",
            f"Agent must declare exactly {required_dependency}",
        )

    uv_sources = _mapping(
        _mapping(
            pyproject.get("tool"),
            code="agent_agui_python_pin_invalid",
            detail="Agent pyproject tool table missing",
        ).get("uv"),
        code="agent_agui_python_pin_invalid",
        detail="Agent pyproject tool.uv table missing",
    ).get("sources")
    source = _mapping(
        _mapping(
            uv_sources,
            code="agent_agui_python_pin_invalid",
            detail="Agent pyproject tool.uv.sources table missing",
        ).get("ag-ui-protocol"),
        code="agent_agui_python_pin_invalid",
        detail="Agent ag-ui-protocol source missing",
    )
    if source != {
        "git": AGUI_REPOSITORY,
        "rev": AGUI_UPSTREAM_COMMIT,
        "subdirectory": AGUI_PYTHON_SUBDIRECTORY,
    }:
        _fail("agent_agui_python_pin_invalid", "Agent git source is not exact")

    lock = _load_toml(root / "kokoro-agent/uv.lock")
    packages = _sequence(
        lock.get("package"),
        code="agent_agui_python_pin_invalid",
        detail="Agent lock package list missing",
    )
    locked = [
        package
        for package in packages
        if isinstance(package, Mapping) and package.get("name") == "ag-ui-protocol"
    ]
    expected_git = (
        f"{AGUI_REPOSITORY}?subdirectory=sdks%2Fpython"
        f"&rev={AGUI_UPSTREAM_COMMIT}#{AGUI_UPSTREAM_COMMIT}"
    )
    if len(locked) != 1 or locked[0].get("version") != AGUI_UPSTREAM_PYTHON_VERSION:
        _fail("agent_agui_python_pin_invalid", "Agent lock version is not exact")
    if locked[0].get("source") != {"git": expected_git}:
        _fail("agent_agui_python_pin_invalid", "Agent lock git source is not exact")

    installed_version = importlib.metadata.version("ag-ui-protocol")
    if installed_version != AGUI_UPSTREAM_PYTHON_VERSION:
        _fail(
            "agent_agui_python_pin_invalid",
            f"installed ag-ui-protocol is {installed_version}",
        )

    upstream = _load_json(root / "contract/registry/agui-upstream-profile.yaml")
    python_profile = _mapping(
        upstream.get("python"),
        code="agent_agui_python_pin_invalid",
        detail="Root Python upstream profile missing",
    )
    profile_source = _mapping(
        python_profile.get("source"),
        code="agent_agui_python_pin_invalid",
        detail="Root Python upstream source missing",
    )
    typescript_core = _mapping(
        _mapping(
            upstream.get("typescript"),
            code="agent_agui_python_pin_invalid",
            detail="Root TypeScript upstream profile missing",
        ).get("core"),
        code="agent_agui_python_pin_invalid",
        detail="Root TypeScript core profile missing",
    )
    if (
        python_profile.get("package") != "ag-ui-protocol"
        or python_profile.get("versionAtCommit") != AGUI_UPSTREAM_PYTHON_VERSION
        or profile_source
        != {
            "kind": "git",
            "repository": AGUI_REPOSITORY,
            "subdirectory": AGUI_PYTHON_SUBDIRECTORY,
            "commit": AGUI_UPSTREAM_COMMIT,
        }
        or typescript_core.get("package") != "@ag-ui/core"
        or typescript_core.get("version") != "0.0.57"
        or _mapping(
            upstream.get("upstream"),
            code="agent_agui_python_pin_invalid",
            detail="Root upstream identity missing",
        ).get("commit")
        != AGUI_UPSTREAM_COMMIT
    ):
        _fail("agent_agui_python_pin_invalid", "Root and Agent upstream pins differ")


def validate_corpus(corpus: Mapping[str, Any]) -> int:
    """Rebuild and compare all canonical Agent candidate envelopes."""

    fixtures = _sequence(
        corpus.get("agentSourceFixtures"),
        code="agent_agui_python_source_coverage_invalid",
        detail="agentSourceFixtures missing",
    )
    fixture_sources: dict[str, Mapping[str, Any]] = {}
    for fixture in fixtures:
        fixture_mapping = _mapping(
            fixture,
            code="agent_agui_python_source_coverage_invalid",
            detail="source fixture must be an object",
        )
        source = _mapping(
            fixture_mapping.get("source"),
            code="agent_agui_python_source_coverage_invalid",
            detail="source fixture source missing",
        )
        source_ref = source.get("sourceEventRef")
        if not isinstance(source_ref, str):
            _fail(
                "agent_agui_python_source_coverage_invalid",
                "source fixture refs must be strings",
            )
        if source_ref in fixture_sources:
            _fail(
                "agent_agui_python_source_coverage_invalid",
                "source fixture refs must be unique",
            )
        fixture_sources[source_ref] = source

    cases: list[Any] = []
    for collection_name in (
        "agentCandidateEnvelopeCases",
        "agentCandidateProjectionCases",
    ):
        cases.extend(
            _sequence(
                corpus.get(collection_name),
                code="agent_agui_python_candidate_coverage_invalid",
                detail=f"{collection_name} missing",
            )
        )

    candidate_refs: set[str] = set()
    used_source_refs: set[str] = set()
    for case in cases:
        case_mapping = _mapping(
            case,
            code="agent_agui_python_envelope_invalid",
            detail="candidate case must be an object",
        )
        case_id = case_mapping.get("id")
        envelope = _mapping(
            case_mapping.get("candidateEnvelope"),
            code="agent_agui_python_envelope_invalid",
            detail=f"{case_id}: candidate envelope missing",
        )
        candidate_ref = envelope.get("candidateRef")
        if not isinstance(candidate_ref, str):
            _fail(
                "agent_agui_python_candidate_duplicate",
                f"{case_id}: invalid candidateRef",
            )
        if candidate_ref in candidate_refs:
            _fail(
                "agent_agui_python_candidate_duplicate",
                f"{case_id}: duplicate candidateRef",
            )
        candidate_refs.add(candidate_ref)

        source_document = _mapping(
            envelope.get("source"),
            code="agent_agui_python_envelope_invalid",
            detail=f"{case_id}: source missing",
        )
        source_ref = source_document.get("sourceEventRef")
        if not isinstance(source_ref, str):
            _fail(
                "agent_agui_python_source_coverage_invalid",
                f"{case_id}: envelope source ref is invalid",
            )
        if fixture_sources.get(source_ref) != source_document:
            _fail(
                "agent_agui_python_source_coverage_invalid",
                f"{case_id}: envelope source does not match its Root fixture",
            )
        used_source_refs.add(source_ref)

        event_document = _mapping(
            envelope.get("event"),
            code="agent_agui_python_envelope_invalid",
            detail=f"{case_id}: event missing",
        )
        event_type = event_document.get("type")
        event_model = _EVENT_MODELS.get(event_type) if isinstance(event_type, str) else None
        if event_model is None:
            _fail(
                "agent_agui_python_envelope_invalid",
                f"{case_id}: unsupported official event type",
            )
        try:
            official_event = event_model.model_validate(event_document)
            source = AgentAguiCandidateSource.model_validate(source_document)
            rebuilt = build_agui_candidate(official_event, source=source)
            rebuilt_document = rebuilt.model_dump(
                mode="json", by_alias=True, exclude_none=True
            )
        except Exception as error:
            _fail(
                "agent_agui_python_envelope_invalid",
                f"{case_id}: Python adapter rejected canonical event ({error})",
            )
        if rebuilt_document != envelope:
            _fail(
                "agent_agui_python_envelope_invalid",
                f"{case_id}: Python rebuild differs from Root envelope",
            )

    if len(cases) != EXPECTED_CANDIDATE_COUNT:
        _fail(
            "agent_agui_python_candidate_coverage_invalid",
            f"expected {EXPECTED_CANDIDATE_COUNT} candidates, found {len(cases)}",
        )
    if used_source_refs != set(fixture_sources):
        _fail(
            "agent_agui_python_source_coverage_invalid",
            "Root source fixtures and canonical candidate sources differ",
        )
    return len(cases)


def validate_repository(root: Path) -> int:
    resolved_root = root.resolve()
    _verify_python_pins(resolved_root)
    corpus = _load_json(resolved_root / "contract/corpus/agui-presentation-v1.json")
    return validate_corpus(corpus)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[2])
    args = parser.parse_args()
    count = validate_repository(args.root)
    print(
        "agent_agui_python_parity_ok: "
        f"{count} canonical envelopes, ag-ui-protocol "
        f"{AGUI_UPSTREAM_PYTHON_VERSION} @ {AGUI_UPSTREAM_COMMIT}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
