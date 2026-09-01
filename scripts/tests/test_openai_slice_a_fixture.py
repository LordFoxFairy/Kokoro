from __future__ import annotations

import json
import socket
import subprocess
import sys
import time
from pathlib import Path

import httpx

from scripts.fixtures.openai_slice_a import TOOL_ARGUMENTS, _contains_approved_resume


ROOT = Path(__file__).resolve().parents[2]


def test_resume_requires_exact_tool_request_and_approved_result() -> None:
    exact = [
        {"role": "user", "content": "slice-a-hitl"},
        {
            "role": "assistant",
            "tool_calls": [
                {
                    "id": "call_slice_a_approval",
                    "type": "function",
                    "function": {
                        "name": "ask_user_question",
                        "arguments": '{"question":"Approve Slice A?","choices":["Approve","Reject"]}',
                    },
                }
            ],
        },
        {
            "role": "tool",
            "tool_call_id": "call_slice_a_approval",
            "content": "Approve",
        },
    ]
    assert _contains_approved_resume(exact)
    for bad in ("Reject", "", "approved"):
        changed = json.loads(json.dumps(exact))
        changed[-1]["content"] = bad
        assert not _contains_approved_resume(changed)
    changed = json.loads(json.dumps(exact))
    changed[1]["tool_calls"][0]["function"]["arguments"] = "{}"
    assert not _contains_approved_resume(changed)
    changed = json.loads(json.dumps(exact))
    changed[1]["tool_calls"].append(
        {
            "id": "unexpected-call",
            "type": "function",
            "function": {"name": "other_tool", "arguments": "{}"},
        }
    )
    assert not _contains_approved_resume(changed)
    changed = json.loads(json.dumps(exact))
    changed.append(
        {
            "role": "tool",
            "tool_call_id": "unexpected-call",
            "content": "Approve",
        }
    )
    assert not _contains_approved_resume(changed)
    changed = [exact[0], exact[2], exact[1]]
    assert not _contains_approved_resume(changed)
    changed = json.loads(json.dumps(exact))
    changed[1]["role"] = "user"
    assert not _contains_approved_resume(changed)


def test_roadmap_locks_the_exact_reviewed_fixture_contract() -> None:
    roadmap = (
        ROOT / "docs/superpowers/plans/2026-08-14-slice-a-web-e2e-promotion-plan.md"
    ).read_text()
    fixture_section = roadmap.split("`openai_slice_a.py`", 1)[1].split(
        "**JIT cut requirement 3", 1
    )[0]

    assert "`ask_user_question`" in fixture_section
    assert f"JSON arguments `{TOOL_ARGUMENTS}`" in fixture_section
    assert "`request_human`" not in fixture_section


def _free_port() -> int:
    with socket.socket() as probe:
        probe.bind(("127.0.0.1", 0))
        return int(probe.getsockname()[1])


def _wait(port: int) -> None:
    deadline = time.monotonic() + 5
    while time.monotonic() < deadline:
        try:
            response = httpx.get(f"http://127.0.0.1:{port}/healthz", timeout=0.2)
            if response.status_code == 200:
                return
        except httpx.HTTPError:
            pass
        time.sleep(0.05)
    raise AssertionError("OpenAI fixture did not become ready")


def _chunks(response: httpx.Response) -> list[dict[str, object]]:
    return [
        json.loads(line.removeprefix("data: "))
        for line in response.text.splitlines()
        if line.startswith("data: {")
    ]


def test_openai_fixture_drives_ask_user_then_terminal_text() -> None:
    port = _free_port()
    process = subprocess.Popen(
        [
            sys.executable,
            str(ROOT / "scripts/fixtures/openai_slice_a.py"),
            "--host",
            "127.0.0.1",
            "--port",
            str(port),
        ],
        cwd=ROOT,
        start_new_session=True,
    )
    try:
        _wait(port)
        first = httpx.post(
            f"http://127.0.0.1:{port}/v1/chat/completions",
            json={
                "model": "slice-a-fixture",
                "stream": True,
                "stream_options": {"include_usage": True},
                "messages": [{"role": "user", "content": "slice-a-hitl"}],
            },
            timeout=2,
        )
        first.raise_for_status()
        chunks = _chunks(first)
        tool_delta = chunks[0]["choices"][0]["delta"]["tool_calls"][0]
        assert tool_delta == {
            "index": 0,
            "id": "call_slice_a_approval",
            "type": "function",
            "function": {
                "name": "ask_user_question",
                "arguments": '{"question":"Approve Slice A?","choices":["Approve","Reject"]}',
            },
        }
        assert chunks[-1]["usage"] == {
            "prompt_tokens": 11,
            "completion_tokens": 7,
            "total_tokens": 18,
        }

        second = httpx.post(
            f"http://127.0.0.1:{port}/v1/chat/completions",
            json={
                "model": "slice-a-fixture",
                "stream": True,
                "stream_options": {"include_usage": True},
                "messages": [
                    {"role": "user", "content": "slice-a-hitl"},
                    {
                        "role": "assistant",
                        "tool_calls": [
                            {
                                "id": "call_slice_a_approval",
                                "type": "function",
                                "function": {
                                    "name": "ask_user_question",
                                    "arguments": '{"question":"Approve Slice A?","choices":["Approve","Reject"]}',
                                },
                            }
                        ],
                    },
                    {
                        "role": "tool",
                        "tool_call_id": "call_slice_a_approval",
                        "content": "Approve",
                    },
                ],
            },
            timeout=2,
        )
        second.raise_for_status()
        chunks = _chunks(second)
        assert (
            "".join(
                str(chunk["choices"][0]["delta"].get("content", ""))
                for chunk in chunks
                if chunk["choices"]
            )
            == "Slice A approved."
        )
        assert chunks[-1]["usage"] == {
            "prompt_tokens": 19,
            "completion_tokens": 4,
            "total_tokens": 23,
        }

        invalid_resume = httpx.post(
            f"http://127.0.0.1:{port}/v1/chat/completions",
            json={
                "model": "slice-a-fixture",
                "stream": True,
                "messages": [
                    {"role": "user", "content": "slice-a-hitl"},
                    {
                        "role": "assistant",
                        "tool_calls": [
                            {
                                "id": "call_slice_a_approval",
                                "type": "function",
                                "function": {
                                    "name": "ask_user_question",
                                    "arguments": '{"question":"Approve Slice A?","choices":["Approve","Reject"]}',
                                },
                            }
                        ],
                    },
                    {
                        "role": "tool",
                        "tool_call_id": "call_slice_a_approval",
                        "content": "Reject",
                    },
                ],
            },
            timeout=2,
        )
        assert invalid_resume.status_code == 400
        assert (
            invalid_resume.json()["error"]["message"] == "invalid Slice A HITL resume"
        )

        extra_resume = httpx.post(
            f"http://127.0.0.1:{port}/v1/chat/completions",
            json={
                "model": "slice-a-fixture",
                "stream": True,
                "messages": [
                    {"role": "user", "content": "slice-a-hitl"},
                    {
                        "role": "assistant",
                        "tool_calls": [
                            {
                                "id": "call_slice_a_approval",
                                "type": "function",
                                "function": {
                                    "name": "ask_user_question",
                                    "arguments": TOOL_ARGUMENTS,
                                },
                            },
                            {
                                "id": "unexpected-call",
                                "type": "function",
                                "function": {"name": "other_tool", "arguments": "{}"},
                            },
                        ],
                    },
                    {
                        "role": "tool",
                        "tool_call_id": "call_slice_a_approval",
                        "content": "Approve",
                    },
                ],
            },
            timeout=2,
        )
        assert extra_resume.status_code == 400
        assert extra_resume.json()["error"]["message"] == "invalid Slice A HITL resume"
    finally:
        process.terminate()
        process.wait(timeout=5)
