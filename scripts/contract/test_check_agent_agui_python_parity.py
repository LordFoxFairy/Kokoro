from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any

import pytest

from scripts.contract.check_agent_agui_python_parity import (
    AgentAguiPythonParityError,
    validate_corpus,
    validate_repository,
)


ROOT = Path(__file__).resolve().parents[2]


def _corpus() -> dict[str, Any]:
    return json.loads(
        (ROOT / "contract/corpus/agui-presentation-v1.json").read_text(
            encoding="utf-8"
        )
    )


def test_rebuilds_every_root_candidate_with_pinned_agent_python() -> None:
    assert validate_repository(ROOT) == 6


def test_rejects_root_candidate_digest_drift() -> None:
    corpus = copy.deepcopy(_corpus())
    envelope = corpus["agentCandidateEnvelopeCases"][0]["candidateEnvelope"]
    envelope["eventDigest"] = f"sha256:{'0' * 64}"
    with pytest.raises(
        AgentAguiPythonParityError, match="agent_agui_python_envelope_invalid"
    ):
        validate_corpus(corpus)


def test_rejects_missing_or_duplicate_candidate_coverage() -> None:
    corpus = copy.deepcopy(_corpus())
    corpus["agentCandidateEnvelopeCases"].append(
        copy.deepcopy(corpus["agentCandidateEnvelopeCases"][0])
    )
    with pytest.raises(
        AgentAguiPythonParityError, match="agent_agui_python_candidate_duplicate"
    ):
        validate_corpus(corpus)
