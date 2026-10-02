#!/usr/bin/env python3
"""Two real Product Runs through System, local Ollama and worker-owned delivery.

No infrastructure or model is downloaded. Existing W2 ownership owns all child
processes, PostgreSQL schemas, Redis keys and S3 cleanup, including on failure.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
import hashlib
import http.client
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import os
from pathlib import Path
import re
import secrets
import socket
import subprocess
import sys
from threading import Lock, Thread
from time import monotonic
from urllib.parse import urlsplit
from urllib.request import ProxyHandler, Request, build_opener
from uuid import UUID

if str(Path(__file__).resolve().parent) not in sys.path:
    sys.path.insert(0, str(Path(__file__).resolve().parent))
import run_system_owner_smoke as system
import run_web_project_resource_chromium_smoke as stack

SmokeError = stack.SmokeError
SYSTEM = stack.ROOT / "apps/kokoro-system"
DRIVER = Path(__file__).with_name("web_real_model_worker_chromium.mjs")


@dataclass(frozen=True)
class RealModelConfig:
    endpoint: str
    model: str
    system_sha: str

    def __post_init__(self) -> None:
        p = urlsplit(self.endpoint)
        if (
            p.scheme != "http"
            or p.hostname != "127.0.0.1"
            or p.port != 11434
            or p.path
            or p.query
            or p.fragment
            or p.username
            or p.password
        ):
            raise SmokeError("only existing loopback Ollama 11434 origin is admitted")
        if (
            self.model != "qwen3:8b"
            or re.fullmatch(r"[a-f0-9]{40}", self.system_sha) is None
        ):
            raise SmokeError("explicit real model and exact System source required")


def provider_preflight(config: RealModelConfig) -> dict[str, str]:
    """Read inventory only; never start Ollama or pull a model."""
    try:
        with build_opener(ProxyHandler({})).open(
            Request(config.endpoint + "/api/tags"), timeout=5
        ) as response:
            raw = response.read(1_048_577)
            if response.status != 200 or len(raw) > 1_048_576:
                raise SmokeError("Ollama inventory rejected")
        values = json.loads(raw)["models"]
        selected = [item for item in values if item.get("name") == config.model]
        if (
            len(selected) != 1
            or re.fullmatch(r"[a-f0-9]{64}", selected[0].get("digest", "")) is None
        ):
            raise SmokeError("existing exact Ollama model absent")
        return {
            "endpoint": config.endpoint,
            "model": config.model,
            "digest": selected[0]["digest"],
        }
    except (OSError, ValueError, KeyError, TypeError):
        raise SmokeError("existing Ollama inventory unavailable") from None


def validate_browser_evidence(value: dict[str, object], digest: str) -> None:
    if type(value) is not dict:
        raise SmokeError("real model browser stages incomplete")
    if (
        value.get("browser") != "chromium"
        or value.get("message_post_status") != 202
        or value.get("agui_status") != 200
        or value.get("text_marker_visible") is not True
        or value.get("live_delivery") is not True
        or value.get("reload_card_count") != 1
        or value.get("download_sha256") != digest
        or value.get("member_statuses") != [404, 404, 404]
        or value.get("owner_snapshot_immutable") is not True
        or value.get("completed_reload_content_equal") is not True
        or not isinstance(value.get("assistant_content_sha256"), str)
        or re.fullmatch(r"[a-f0-9]{64}", value["assistant_content_sha256"]) is None
        or any(
            not isinstance(value.get(key), str) or not value[key]
            for key in ("conversation_id", "run_id", "artifact_id", "asset_id")
        )
    ):
        raise SmokeError("real model browser stages incomplete")

    def closed(record, keys):
        return type(record) is dict and set(record) == set(keys.split())

    def identity(item):
        return (
            isinstance(item, str)
            and re.fullmatch(r"[A-Za-z0-9_.:-]{1,191}", item) is not None
        )

    def sha(item):
        return isinstance(item, str) and re.fullmatch(r"[a-f0-9]{64}", item) is not None

    # Every complete fresh journey requires both actual first-login proofs.
    login = value.get("login")
    login_keys = (
        "subject form_status callback_status session_status product_cookie "
        "consent_status consent_post_count consent_post_status consent_decision "
        "native_consent app_status"
    )
    if not closed(login, "owner member"):
        raise SmokeError("real model first-login evidence shape drift")
    for actor in (login["owner"], login["member"]):
        if (
            not closed(actor, login_keys)
            or not identity(actor["subject"])
            or any(
                type(actor[key]) is not int or actor[key] != expected
                for key, expected in (
                    ("form_status", 200),
                    ("callback_status", 303),
                    ("session_status", 200),
                    ("consent_status", 200),
                    ("consent_post_count", 1),
                    ("app_status", 200),
                )
            )
            or type(actor["consent_post_status"]) is not int
            or actor["consent_post_status"] not in (302, 303)
            or actor["consent_decision"] != "agree"
            or actor["native_consent"] is not True
            or actor["product_cookie"] != "HttpOnly+Secure+Lax"
        ):
            raise SmokeError("real model first-login consent evidence incomplete")
    if login["owner"]["subject"] == login["member"]["subject"]:
        raise SmokeError("real model first-login identity drift")

    turns, active = value.get("turns"), value.get("active_reload")
    if (
        type(turns) is not list
        or len(turns) != 2
        or type(value.get("message_post_count")) is not int
        or value["message_post_count"] != 2
        or type(value.get("completed_message_count")) is not int
        or value["completed_message_count"] != 4
        or type(value.get("message_post_statuses")) is not list
        or value["message_post_statuses"] != [202, 202]
        or any(type(status) is not int for status in value["message_post_statuses"])
        or value.get("first_turn_preserved") is not True
    ):
        raise SmokeError("real model two-turn submission evidence incomplete")
    run_ids, message_ids = set(), set()
    for turn in turns:
        if not closed(
            turn,
            "receipt submitted_content_sha256 snapshot_user_content_sha256 event_assistant_content_sha256 snapshot_assistant_content_sha256 start_count finish_count error_count",
        ):
            raise SmokeError("real model turn evidence shape drift")
        receipt = turn["receipt"]
        if not closed(
            receipt, "run_id user_message_id assistant_message_id"
        ) or not all(identity(item) for item in receipt.values()):
            raise SmokeError("real model turn identity drift")
        run_ids.add(receipt["run_id"])
        message_ids.update(
            (receipt["user_message_id"], receipt["assistant_message_id"])
        )
        if (
            any(
                not sha(turn[key])
                for key in (
                    "submitted_content_sha256",
                    "snapshot_user_content_sha256",
                    "event_assistant_content_sha256",
                    "snapshot_assistant_content_sha256",
                )
            )
            or turn["submitted_content_sha256"] != turn["snapshot_user_content_sha256"]
            or turn["event_assistant_content_sha256"]
            != turn["snapshot_assistant_content_sha256"]
            or any(
                type(turn[key]) is not int or turn[key] != expected
                for key, expected in (
                    ("start_count", 1),
                    ("finish_count", 1),
                    ("error_count", 0),
                )
            )
        ):
            raise SmokeError("real model turn text or terminal evidence drift")
    if (
        len(run_ids) != 2
        or len(message_ids) != 4
        or value["run_id"] != turns[1]["receipt"]["run_id"]
    ):
        raise SmokeError("real model turn receipt binding drift")
    if not closed(
        active,
        "run_id state partial_content_length finished_before_reload hydration_watermark sse_last_event_id snapshot_plus_tail_sha256",
    ):
        raise SmokeError("real model active reload evidence shape drift")
    if (
        active["run_id"] != value["run_id"]
        or active["state"] != "active"
        or type(active["partial_content_length"]) is not int
        or not 0 < active["partial_content_length"] <= 8388608
        or active["finished_before_reload"] is not False
        or any(
            not isinstance(active[key], str)
            or not active[key].strip()
            or len(active[key]) > 4096
            or any(ord(char) < 32 or ord(char) == 127 for char in active[key])
            for key in ("hydration_watermark", "sse_last_event_id")
        )
        or active["hydration_watermark"] != active["sse_last_event_id"]
        or not sha(active["snapshot_plus_tail_sha256"])
        or active["snapshot_plus_tail_sha256"]
        != turns[1]["snapshot_assistant_content_sha256"]
        or value["assistant_content_sha256"]
        != turns[1]["snapshot_assistant_content_sha256"]
    ):
        raise SmokeError("real model active reload or reconstruction evidence drift")


def model_stream_evidence(raw: bytes, model: str = "qwen3:8b") -> dict[str, object]:
    """Validate this fixed Ollama stream profile; return actual cumulative usage."""

    def pairs(values):
        result = {}
        for key, value in values:
            if key in result:
                raise ValueError("duplicate JSON key")
            result[key] = value
        return result

    def token(value):
        return type(value) is int and 0 <= value <= 9_223_372_036_854_775_807

    try:
        if len(raw) > 8_388_608:
            raise ValueError("SSE response bound")
        text = (
            raw.decode("utf-8", errors="strict")
            .replace("\r\n", "\n")
            .replace("\r", "\n")
        )
        frames = text.split("\n\n")
        if len(frames) > 65537 or frames[-1].strip():
            raise ValueError("SSE frame bound/EOF")
        done = finished = visible = False
        usage = completion_id = None
        tools = {}
        finish_reason = None
        for frame in frames[:-1]:
            if len(frame.encode()) > 1_048_576:
                raise ValueError("SSE frame bound")
            lines = frame.split("\n")
            if any(
                line.startswith("event:") and line[6:].strip() == "error"
                for line in lines
            ):
                raise ValueError("SSE error event")
            data = "\n".join(
                line[5:].lstrip() for line in lines if line.startswith("data:")
            )
            if not data:
                continue
            if done:
                raise ValueError("data after DONE")
            if data == "[DONE]":
                if not finished or usage is None or not visible:
                    raise ValueError("incomplete stream")
                done = True
                continue
            event = json.loads(
                data,
                object_pairs_hook=pairs,
                parse_constant=lambda value: (_ for _ in ()).throw(
                    ValueError("non-finite JSON")
                ),
            )
            if (
                type(event) is not dict
                or "error" in event
                or event.get("model") != model
                or not isinstance(event.get("id"), str)
                or not 0 < len(event["id"]) <= 191
                or type(event.get("choices")) is not list
                or len(event["choices"]) > 1
            ):
                raise ValueError("model identity/event")
            if completion_id is None:
                completion_id = event["id"]
            if event["id"] != completion_id:
                raise ValueError("completion identity drift")
            if finished and event["choices"]:
                raise ValueError("choice after finish")
            for choice in event["choices"]:
                if (
                    type(choice) is not dict
                    or type(choice.get("index")) is not int
                    or choice["index"] != 0
                    or type(choice.get("delta")) is not dict
                ):
                    raise ValueError("model choice")
                delta = choice["delta"]
                if (
                    delta.get("content") is not None
                    and type(delta["content"]) is not str
                ):
                    raise ValueError("model content")
                if delta.get("content"):
                    visible = True
                calls = delta.get("tool_calls")
                if calls is not None:
                    if type(calls) is not list or not calls:
                        raise ValueError("tool delta")
                    for call in calls:
                        if (
                            type(call) is not dict
                            or type(call.get("index")) is not int
                            or not 0 <= call["index"] < 100
                            or type(call.get("function")) is not dict
                        ):
                            raise ValueError("tool index/function")
                        item = tools.setdefault(
                            call["index"], {"id": "", "name": "", "arguments": ""}
                        )
                        for key, source in (
                            ("id", call),
                            ("name", call["function"]),
                            ("arguments", call["function"]),
                        ):
                            if key in source:
                                if not isinstance(source[key], str):
                                    raise ValueError("tool field")
                                item[key] += source[key]
                        visible = True
                reason = choice.get("finish_reason")
                if reason is not None:
                    if finished or reason not in ("stop", "tool_calls"):
                        raise ValueError("model finish")
                    finish_reason, finished = reason, True
            if event.get("usage") is not None:
                if usage is not None or not finished:
                    raise ValueError("duplicate/early usage")
                usage = event["usage"]
                if (
                    type(usage) is not dict
                    or not all(
                        token(usage.get(key))
                        for key in (
                            "prompt_tokens",
                            "completion_tokens",
                            "total_tokens",
                        )
                    )
                    or usage["prompt_tokens"] == 0
                    or usage["completion_tokens"] == 0
                    or usage["total_tokens"]
                    != usage["prompt_tokens"] + usage["completion_tokens"]
                ):
                    raise ValueError("model usage")
        if not done:
            raise ValueError("missing DONE")
        if finish_reason == "tool_calls":
            if not tools or any(
                not item["id"]
                or not item["name"]
                or type(json.loads(item["arguments"], object_pairs_hook=pairs))
                is not dict
                for item in tools.values()
            ):
                raise ValueError("incomplete tool call")
        elif tools:
            raise ValueError("tool delta without tool finish")
        return {
            "input_tokens": usage["prompt_tokens"],
            "output_tokens": usage["completion_tokens"],
            "completion_id": completion_id,
            "model": model,
            "finish_reason": finish_reason,
            "done_count": 1,
        }
    except (ValueError, TypeError, KeyError, UnicodeError):
        raise SmokeError("actual model SSE evidence rejected") from None


def validate_observed_route(route, seed):
    keys = {
        "model_id",
        "revision_id",
        "revision",
        "digest",
        "generation",
        "tenant_generation",
        "provider_id",
        "provider_model_name",
        "transport",
        "gateway_model_name",
        "label_key",
        "feature_key",
    }
    if type(route) is not dict or set(route) != keys or type(seed) is not dict:
        raise ValueError("System route shape")
    if (
        any(
            not isinstance(route[key], str) or str(UUID(route[key])) != route[key]
            for key in ("model_id", "revision_id", "provider_id")
        )
        or type(route["revision"]) is not int
        or route["revision"] < 1
        or not isinstance(route["digest"], str)
        or re.fullmatch(r"[a-f0-9]{64}", route["digest"]) is None
        or any(
            not isinstance(route[key], str)
            or re.fullmatch(r"[1-9][0-9]*", route[key]) is None
            for key in ("generation", "tenant_generation")
        )
        or route["transport"] != "litellm"
    ):
        raise ValueError("System route values")
    if any(
        route[key] != expected
        for key, expected in (
            ("revision_id", seed["revision_id"]),
            ("provider_id", seed["provider_id"]),
            ("label_key", seed["label_key"]),
            ("feature_key", "chat"),
            ("provider_model_name", seed["model_name"]),
            ("gateway_model_name", seed["model_name"]),
        )
    ):
        raise ValueError("System route source")


def validate_provider_turns(browser, windows, agents) -> None:
    if (
        type(windows) is not list
        or len(windows) != 2
        or type(agents) is not list
        or len(agents) != 2
    ):
        raise SmokeError("per-Run provider observations incomplete")
    request_ids = set()
    call_sequence = 0
    for index, window in enumerate(windows):
        turn = browser["turns"][index]
        if (
            type(window) is not dict
            or set(window) != {"receipt", "system", "model"}
            or window["receipt"] != turn["receipt"]
        ):
            raise SmokeError("per-Run provider receipt binding drift")
        for kind in ("system", "model"):
            observation = window[kind]
            if (
                type(observation) is not dict
                or set(observation)
                != (
                    {
                        "requests",
                        "successes",
                        "response_bytes",
                        "pending",
                        "request_ids",
                        "user_sha256",
                    }
                    | (
                        {"input_tokens", "output_tokens", "calls"}
                        if kind == "model"
                        else {"routes"}
                    )
                )
                or any(
                    type(observation.get(key)) is not int
                    for key in ("requests", "successes", "response_bytes", "pending")
                )
                or observation["pending"] != 0
                or observation["requests"] < 1
                or observation["successes"] != observation["requests"]
                or observation["response_bytes"] <= 0
            ):
                raise SmokeError("per-Run provider incomplete or cross-window request")
            if kind == "system":
                request_id = agents[index].get("request_id")
                if (
                    observation["requests"] != 1
                    or not isinstance(request_id, str)
                    or re.fullmatch(r"[A-Za-z0-9_.:-]{1,128}", request_id) is None
                    or request_id in request_ids
                    or observation["request_ids"] != [request_id]
                    or observation["user_sha256"] != []
                ):
                    raise SmokeError("per-Run System request identity drift")
                routes = observation["routes"]
                if (
                    type(routes) is not list
                    or len(routes) != 1
                    or routes[0] != windows[0]["system"]["routes"][0]
                ):
                    raise SmokeError("per-Run System observed route drift")
                request_ids.add(request_id)
            elif (
                observation["request_ids"] != []
                or observation["user_sha256"]
                != [turn["submitted_content_sha256"]] * observation["requests"]
            ):
                raise SmokeError("per-Run latest user digest drift")
            if kind == "model":
                calls = observation["calls"]
                call_keys = {
                    "sequence",
                    "user_sha256",
                    "model",
                    "completion_id",
                    "finish_reason",
                    "done_count",
                    "input_tokens",
                    "output_tokens",
                    "response_bytes",
                }
                if type(calls) is not list or len(calls) != observation["requests"]:
                    raise SmokeError("per-Run actual model call evidence missing")
                for call in calls:
                    call_sequence += 1
                    if (
                        type(call) is not dict
                        or set(call) != call_keys
                        or type(call["sequence"]) is not int
                        or call["sequence"] != call_sequence
                        or call["user_sha256"] != turn["submitted_content_sha256"]
                        or call["model"] != "qwen3:8b"
                        or not isinstance(call["completion_id"], str)
                        or not 0 < len(call["completion_id"]) <= 191
                        or call["finish_reason"] not in ("stop", "tool_calls")
                        or type(call["done_count"]) is not int
                        or call["done_count"] != 1
                        or any(
                            type(call[key]) is not int or call[key] <= 0
                            for key in (
                                "input_tokens",
                                "output_tokens",
                                "response_bytes",
                            )
                        )
                    ):
                        raise SmokeError("per-Run actual model call drift")
                if any(
                    sum(call[key] for call in calls) != observation[key]
                    for key in ("input_tokens", "output_tokens", "response_bytes")
                ):
                    raise SmokeError("per-Run actual model call totals drift")
            if kind == "model" and (
                any(
                    type(observation.get(key)) is not int or observation[key] <= 0
                    for key in ("input_tokens", "output_tokens")
                )
                or {
                    "input": observation["input_tokens"],
                    "output": observation["output_tokens"],
                }
                != {
                    key: agents[index].get("usage", {}).get(key)
                    for key in ("input", "output")
                }
            ):
                raise SmokeError("per-Run provider/durable usage drift")


class ProviderWindows:
    """Harness-only stdio boundaries before UI POST and after real terminal."""

    def __init__(self, system_proxy, model_proxy):
        self.proxies = {"system": system_proxy, "model": model_proxy}
        self.windows = []
        self.active = None
        self.receipt = None
        self.last = None

    def snapshot(self):
        snapshots = {kind: proxy.snapshot() for kind, proxy in self.proxies.items()}
        if any(value["pending"] or value["errors"] for value in snapshots.values()):
            raise SmokeError("per-Run provider pending/error at boundary")
        return snapshots

    def handle(self, record):
        stage, index = record.get("stage"), record.get("index")
        keys = {"kind", "stage", "index"} | (
            {"receipt"} if stage in ("receipt", "close") else set()
        )
        if (
            set(record) != keys
            or record.get("kind") != "observation-window"
            or type(index) is not int
            or index != len(self.windows)
            or index not in (0, 1)
        ):
            raise SmokeError("provider observation boundary rejected")
        if stage == "open":
            current = self.snapshot()
            if (
                self.active is not None
                or (self.last is not None and current != self.last)
                or (
                    self.last is None
                    and any(
                        value["requests"]
                        or value["successes"]
                        or value["response_bytes"]
                        for value in current.values()
                    )
                )
            ):
                raise SmokeError("provider request outside receipt windows")
            self.active, self.receipt = current, None
        elif stage == "receipt":
            receipt = record["receipt"]
            if (
                self.active is None
                or self.receipt is not None
                or type(receipt) is not dict
                or set(receipt) != {"run_id", "user_message_id", "assistant_message_id"}
                or any(
                    not isinstance(item, str)
                    or re.fullmatch(r"[A-Za-z0-9_.:-]{1,191}", item) is None
                    for item in receipt.values()
                )
            ):
                raise SmokeError("provider receipt boundary rejected")
            self.receipt = receipt
        elif stage == "close":
            if (
                self.active is None
                or self.receipt is None
                or record["receipt"] != self.receipt
            ):
                raise SmokeError("provider terminal boundary rejected")
            current = self.snapshot()
            window = {"receipt": self.receipt}
            for kind, value in current.items():
                base = self.active[kind]
                rows = value["observations"][len(base["observations"]) :]
                window[kind] = {
                    key: value[key] - base[key]
                    for key in ("requests", "successes", "response_bytes")
                }
                if kind == "system":
                    window[kind]["routes"] = [row["route"] for row in rows]
                if kind == "model":
                    window[kind]["calls"] = [
                        {
                            key: row[key]
                            for key in (
                                "sequence",
                                "user_sha256",
                                "model",
                                "completion_id",
                                "finish_reason",
                                "done_count",
                                "input_tokens",
                                "output_tokens",
                                "response_bytes",
                            )
                        }
                        for row in rows
                    ]
                    window[kind].update(
                        input_tokens=sum(row["input_tokens"] for row in rows),
                        output_tokens=sum(row["output_tokens"] for row in rows),
                    )
                window[kind].update(
                    pending=value["pending"],
                    request_ids=[row["request_id"] for row in rows]
                    if kind == "system"
                    else [],
                    user_sha256=[row["user_sha256"] for row in rows]
                    if kind == "model"
                    else [],
                )
            self.windows.append(window)
            self.last, self.active, self.receipt = current, None, None
        else:
            raise SmokeError("provider observation stage rejected")
        return stage != "receipt"

    def finish(self):
        if (
            self.active is not None
            or len(self.windows) != 2
            or self.snapshot() != self.last
        ):
            raise SmokeError("provider observation windows incomplete")
        return self.windows


def read_driver_observations(child, payload, system_proxy, model_proxy, timeout):
    observer = ProviderWindows(system_proxy, model_proxy)
    result, failures, stderr = [], [], []

    def read_errors():
        text = child.stderr.read(4097)
        stderr.append(text[:4096])
        if len(text) > 4096:
            failures.append(SmokeError("browser stderr bound"))

    def read_lines():
        try:
            for count in range(10):
                line = child.stdout.readline(1_048_577)
                if not line:
                    break
                if len(line.encode()) > 1_048_576 or result:
                    raise SmokeError("browser output bound/extra record")
                try:
                    value = json.loads(line)
                except ValueError:
                    raise SmokeError("real model browser evidence malformed") from None
                if type(value) is dict and value.get("kind") == "observation-window":
                    if observer.handle(value):
                        child.stdin.write(
                            json.dumps(
                                {
                                    "kind": "observation-ack",
                                    "stage": value["stage"],
                                    "index": value["index"],
                                }
                            )
                            + "\n"
                        )
                        child.stdin.flush()
                else:
                    result.append(line)
            else:
                raise SmokeError("browser record count bound")
        except (SmokeError, OSError, ValueError) as error:
            failures.append(error)

    child.stdin.write(json.dumps(payload) + "\n")
    child.stdin.flush()
    output_thread, error_thread = (
        Thread(target=read_lines, daemon=True),
        Thread(target=read_errors, daemon=True),
    )
    output_thread.start()
    error_thread.start()
    deadline = monotonic() + timeout
    output_thread.join(timeout)
    if output_thread.is_alive():
        raise subprocess.TimeoutExpired("owned-browser", timeout)
    if failures:
        raise SmokeError("real model browser observation failed") from failures[0]
    child.wait(timeout=max(0.01, deadline - monotonic()))
    error_thread.join(max(0.01, deadline - monotonic()))
    if failures:
        raise SmokeError("real model browser observation failed") from failures[0]
    errors = stderr[0] if stderr else ""
    if child.returncode != 0:
        return "", errors, []
    if not result:
        raise SmokeError("real model browser evidence absent")
    return result[0], errors, observer.finish()


class ObservingProxy(ThreadingHTTPServer):
    """Bounded byte-preserving HTTP observer; never produces successful replies."""

    daemon_threads = True

    def __init__(
        self,
        upstream: str,
        *,
        kind: str,
        token: str,
        tenant: str,
        model: str,
        revision: str,
        timeout: float,
        expected_route: dict | None = None,
    ):
        super().__init__(("127.0.0.1", 0), _ProxyHandler)
        self.upstream = urlsplit(upstream)
        self.kind, self.token, self.tenant = kind, token, tenant
        self.model, self.revision, self.timeout = model, revision, timeout
        self.expected_route = expected_route
        self.requests = self.successes = self.response_bytes = self.pending = 0
        self.lock = Lock()
        self.observations = []
        self.errors: list[str] = []
        self.thread = Thread(target=self.serve_forever, daemon=True)
        self.thread.start()

    def snapshot(self):
        with self.lock:
            return dict(
                requests=self.requests,
                successes=self.successes,
                response_bytes=self.response_bytes,
                pending=self.pending,
                errors=len(self.errors),
                observations=[dict(row) for row in self.observations],
            )

    @property
    def origin(self) -> str:
        return f"http://127.0.0.1:{self.server_port}"

    def close(self) -> None:
        self.shutdown()
        self.server_close()
        self.thread.join(timeout=5)


class _ProxyHandler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def log_message(self, *_args: object) -> None:
        pass

    def do_POST(self) -> None:
        owner = self.server
        assert isinstance(owner, ObservingProxy)
        upstream = None
        counted = False
        try:
            length = int(self.headers.get("content-length", "0"))
            if not 0 < length <= 1_048_576:
                raise ValueError("request size")
            raw = self.rfile.read(length)
            body = json.loads(raw)
            if type(body) is not dict:
                raise ValueError("request object")
            if self.headers.get("authorization") != f"Bearer {owner.token}":
                raise ValueError("credential")
            if owner.kind == "system":
                if (
                    self.path != "/v1/system/model-catalog/resolve"
                    or body != {"feature_key": "chat"}
                    or self.headers.get("x-kokoro-tenant-id") != owner.tenant
                    or self.headers.get("x-kokoro-service") != "kokoro-agent"
                ):
                    raise ValueError("route identity")
            elif (
                self.path != "/v1/chat/completions"
                or body.get("model") != owner.model
                or body.get("stream") is not True
                or type(body.get("stream_options")) is not dict
                or body["stream_options"].get("include_usage") is not True
            ):
                raise ValueError("model stream")
            request_id = self.headers.get("x-request-id")
            user_digest = None
            if owner.kind == "system":
                if (
                    not isinstance(request_id, str)
                    or re.fullmatch(r"[A-Za-z0-9_.:-]{1,128}", request_id) is None
                ):
                    raise ValueError("System request identity")
            else:
                users = [
                    message
                    for message in body.get("messages", [])
                    if type(message) is dict and message.get("role") == "user"
                ]
                if (
                    not users
                    or not isinstance(users[-1].get("content"), str)
                    or not users[-1]["content"]
                ):
                    raise ValueError("latest user content")
                user_digest = hashlib.sha256(users[-1]["content"].encode()).hexdigest()
            with owner.lock:
                if owner.requests >= 100 or (
                    owner.kind == "system"
                    and any(
                        row["request_id"] == request_id for row in owner.observations
                    )
                ):
                    raise ValueError("provider identity/bound")
                owner.requests += 1
                owner.pending += 1
                observation_index = len(owner.observations)
                owner.observations.append(
                    {
                        "sequence": owner.requests,
                        "request_id": request_id if owner.kind == "system" else None,
                        "user_sha256": user_digest,
                    }
                )
                counted = True
            upstream = http.client.HTTPConnection(
                owner.upstream.hostname, owner.upstream.port, timeout=owner.timeout
            )
            headers = {
                key: value
                for key, value in self.headers.items()
                if key.lower() not in {"host", "connection", "transfer-encoding"}
            }
            upstream.request("POST", self.path, raw, headers)
            response = upstream.getresponse()
            self.send_response(response.status)
            self.send_header(
                "content-type",
                response.getheader("content-type", "application/octet-stream"),
            )
            self.send_header("connection", "close")
            self.end_headers()
            total = 0
            if (
                owner.kind == "model"
                and response.getheader("content-type", "").split(";")[0].strip().lower()
                != "text/event-stream"
            ):
                raise ValueError("model media type")
            captured = bytearray()
            while chunk := response.read1(8192):
                total += len(chunk)
                if total > 8_388_608:
                    raise ValueError("response size")
                captured.extend(chunk)
                self.wfile.write(chunk)
                self.wfile.flush()
            with owner.lock:
                owner.response_bytes += total
                owner.observations[observation_index]["response_bytes"] = total
            if response.status != 200:
                raise ValueError("upstream status")
            if owner.kind == "system":
                if response.getheader("x-request-id") != request_id:
                    raise ValueError("System response identity")
                envelope = json.loads(captured)
                if type(envelope) is not dict or set(envelope) != {"data"}:
                    raise ValueError("System envelope")
                route = envelope["data"]
                validate_observed_route(route, owner.expected_route)
                with owner.lock:
                    owner.observations[observation_index]["route"] = route
                if (
                    route["revision_id"] != owner.revision
                    or route["gateway_model_name"] != owner.model
                    or route["feature_key"] != "chat"
                ):
                    raise ValueError("route source")
            else:
                usage = model_stream_evidence(bytes(captured), owner.model)
                with owner.lock:
                    owner.observations[observation_index].update(usage)
            with owner.lock:
                owner.successes += 1
        except (
            OSError,
            ValueError,
            KeyError,
            TypeError,
            SmokeError,
            http.client.HTTPException,
        ):
            with owner.lock:
                owner.errors.append("upstream_observation_failed")
        finally:
            if counted:
                with owner.lock:
                    owner.pending -= 1
            self.close_connection = True
            if upstream is not None:
                upstream.close()


def _query(infra, database_url: str, query: str) -> object:
    return json.loads(
        infra.command(
            ["psql", database_url, "-X", "-v", "ON_ERROR_STOP=1", "-Atc", query]
        ).strip()
    )


def register_owned_worker_runs(infra, database_url: str, ownership) -> None:
    """Validate all isolated journey Runs before granting their cleanup scope."""
    rows = _query(
        infra,
        database_url,
        """SELECT coalesce(json_agg(json_build_object(
          'run',run_id,'session',request_json::jsonb->>'session_id')),
          '[]'::json) FROM kokoro_agent.kokoro_agent_run""",
    )
    if not isinstance(rows, list) or len(rows) > 2:
        raise SmokeError("real model owned Run inventory drift")
    runs: set[str] = set()
    sessions: set[str] = set()
    for row in rows:
        if not isinstance(row, dict) or set(row) != {"session", "run"}:
            raise SmokeError("real model owned Run inventory drift")
        session, run = row["session"], row["run"]
        if not all(
            isinstance(value, str)
            and re.fullmatch(r"[A-Za-z0-9_.:-]{1,191}", value) is not None
            for value in (session, run)
        ):
            raise SmokeError("real model owned Run inventory drift")
        if run in runs or (sessions and session not in sessions):
            raise SmokeError("real model owned Run inventory drift")
        runs.add(run)
        sessions.add(session)
    for row in rows:
        ownership.register_run(row["session"], row["run"])


def worker_owns_lease(owner: object, process_group: int) -> bool:
    if not isinstance(owner, str):
        return False
    prefix = socket.gethostname() + "-"
    if not owner.startswith(prefix) or not owner[len(prefix) :].isdigit():
        return False
    try:
        return os.getpgid(int(owner[len(prefix) :])) == process_group
    except OSError:
        return False


def validate_run_usage(agent):
    usage = agent.get("usage")
    if type(agent.get("generation")) is not int or agent["generation"] < 1:
        raise SmokeError("real model durable usage generation drift")
    if (
        type(usage) is not dict
        or set(usage) != {"input", "output", "segments", "completed"}
        or any(
            type(usage.get(key)) is not int
            or not 0 < usage[key] <= 9_223_372_036_854_775_807
            for key in ("input", "output")
        )
    ):
        raise SmokeError("real model durable usage incomplete")
    segments, completed = usage["segments"], usage["completed"]
    if (
        type(segments) is not list
        or not segments
        or len(segments) > 100
        or type(completed) is not dict
        or set(completed) != {"input_tokens", "output_tokens"}
        or any(
            type(completed[key]) is not int
            or not 0 <= completed[key] <= 9_223_372_036_854_775_807
            for key in completed
        )
    ):
        raise SmokeError("real model durable usage shape drift")
    generations = set()
    for segment in segments:
        if (
            type(segment) is not dict
            or set(segment) != {"generation", "input", "output"}
            or any(type(segment[key]) is not int for key in segment)
            or segment["generation"] < 1
            or segment["generation"] > agent["generation"]
            or segment["generation"] in generations
            or not 0 <= segment["input"] <= 9_223_372_036_854_775_807
            or not 0 <= segment["output"] <= 9_223_372_036_854_775_807
        ):
            raise SmokeError("real model durable usage segment drift")
        generations.add(segment["generation"])
    if agent["generation"] not in generations:
        raise SmokeError("real model durable current usage generation missing")
    if (
        sum(segment["input"] for segment in segments) != usage["input"]
        or sum(segment["output"] for segment in segments) != usage["output"]
        or completed
        != {"input_tokens": usage["input"], "output_tokens": usage["output"]}
    ):
        raise SmokeError("real model durable usage totals drift")


def durable_evidence(
    infra,
    database_url: str,
    browser: dict[str, object],
    tenant: str,
    worker_pid: int,
    digest: str,
) -> dict[str, object]:
    run, conversation, artifact, asset = (
        str(browser[key])
        for key in ("run_id", "conversation_id", "artifact_id", "asset_id")
    )
    if any(
        re.fullmatch(r"[A-Za-z0-9_:-]{1,191}", v) is None
        for v in (run, conversation, artifact, asset, tenant)
    ):
        raise SmokeError("SQL evidence identity rejected")
    validate_browser_evidence(browser, digest)
    runs = [turn["receipt"]["run_id"] for turn in browser["turns"]]
    if any(re.fullmatch(r"[A-Za-z0-9_:-]{1,191}", item) is None for item in runs):
        raise SmokeError("SQL evidence identity rejected")
    # Each query stays in one owner schema. These are read-only test assertions.
    agents = []
    for index, run in enumerate(runs):
        agent = _query(
            infra,
            database_url,
            f"""SELECT json_build_object(
          'terminal',terminal,'generation',lease_generation,'owner',owner,
          'request_id',request_json::jsonb->>'request_id',
          'feature_key',request_json::jsonb->>'feature_key',
          'user_message_id',request_json::jsonb #>> '{{input,message_id}}',
          'input_content',request_json::jsonb #>> '{{input,content}}',
          'durable_counter',durable_counter,
          'terminal_events',(SELECT json_agg(json_build_object('kind',t.kind,'status',t.status,
            'seq',t.durable_seq,'payload',t.payload_json::jsonb) ORDER BY t.durable_seq)
            FROM kokoro_agent.kokoro_agent_run_outbox t WHERE t.run_id=r.run_id
            AND t.kind IN ('run.completed','run.failed')),
          'usage',json_build_object('input',usage_input_total,'output',usage_output_total,
            'segments',(SELECT json_agg(json_build_object('generation',u.lease_generation,
              'input',u.input_tokens,'output',u.output_tokens) ORDER BY u.lease_generation)
              FROM kokoro_agent.kokoro_agent_run_usage_segment u WHERE u.run_id=r.run_id),
            'completed',(SELECT payload_json::jsonb->'token_usage'
              FROM kokoro_agent.kokoro_agent_run_outbox c WHERE c.run_id=r.run_id
              AND c.kind='run.completed' AND c.status='published')),
          'session',request_json::jsonb->>'session_id',
          'run_count',(SELECT count(*) FROM kokoro_agent.kokoro_agent_run x
            WHERE x.tenant_id=r.tenant_id AND x.request_json::jsonb->>'session_id'='{conversation}'),
          'file_writes',(SELECT count(*) FROM kokoro_agent.kokoro_agent_tool_journal w
            WHERE w.run_id=r.run_id AND name='write_file' AND status='succeeded' AND NOT is_error),
          'deliveries',(SELECT count(*) FROM kokoro_agent.kokoro_agent_tool_journal j
            WHERE j.run_id=r.run_id AND name='deliver' AND status='succeeded' AND NOT is_error
            AND result::jsonb->>'artifact_id'='{artifact}' AND result::jsonb->>'asset_id'='{asset}'
            AND result::jsonb->>'content_hash'='{digest}'),
          'events',(SELECT json_agg(kind ORDER BY durable_seq) FROM kokoro_agent.kokoro_agent_run_outbox e
            WHERE e.run_id=r.run_id AND status='published'))
          FROM kokoro_agent.kokoro_agent_run r WHERE run_id='{run}' AND tenant_id='{tenant}'""",
        )
        events = agent.get("events", []) if isinstance(agent, dict) else []
        if (
            not isinstance(agent, dict)
            or agent.get("terminal") is not True
            or type(agent.get("generation")) is not int
            or agent["generation"] < 1
            or not worker_owns_lease(agent.get("owner"), worker_pid)
            or agent.get("session") != conversation
            or type(agent.get("run_count")) is not int
            or agent["run_count"] != 2
            or type(agent.get("file_writes")) is not int
            or agent["file_writes"] < 0
            or type(agent.get("deliveries")) is not int
            or agent["deliveries"] < 0
            or type(events) is not list
            or not all(isinstance(event, str) for event in events)
            or events.count("run.started") != 1
            or events.count("run.completed") != 1
            or events.index("run.started") > events.index("run.completed")
            or "run.failed" in events
            or (
                index == 0
                and (
                    agent.get("file_writes") != 0
                    or agent.get("deliveries") != 0
                    or "delivery.created" in events
                )
            )
            or (
                index == 1
                and (
                    agent.get("file_writes", 0) < 1
                    or agent.get("deliveries") != 1
                    or events.count("delivery.created") != 1
                    or events.index("delivery.created") > events.index("run.completed")
                )
            )
        ):
            raise SmokeError("standard worker lease/journal/terminal evidence drift")
        if (
            not isinstance(agent.get("request_id"), str)
            or re.fullmatch(r"[A-Za-z0-9_.:-]{1,128}", agent["request_id"]) is None
        ):
            raise SmokeError("real model durable request identity drift")
        content = agent.pop("input_content", None)
        if (
            not isinstance(content, str)
            or not content
            or len(content.encode()) > 8_388_608
            or agent.get("feature_key") != "chat"
            or agent.get("user_message_id")
            != browser["turns"][index]["receipt"]["user_message_id"]
        ):
            raise SmokeError("real model durable input identity drift")
        agent["input_content_sha256"] = hashlib.sha256(content.encode()).hexdigest()
        if (
            agent["input_content_sha256"]
            != browser["turns"][index]["submitted_content_sha256"]
        ):
            raise SmokeError("real model durable submitted input drift")
        terminal = agent.get("terminal_events")
        if (
            type(terminal) is not list
            or len(terminal) != 1
            or type(terminal[0]) is not dict
            or set(terminal[0]) != {"kind", "status", "seq", "payload"}
            or terminal[0]["kind"] != "run.completed"
            or terminal[0]["status"] != "published"
            or type(agent.get("durable_counter")) is not int
            or agent["durable_counter"] <= 0
            or type(terminal[0]["seq"]) is not int
            or terminal[0]["seq"] != agent["durable_counter"]
            or type(terminal[0]["payload"]) is not dict
            or set(terminal[0]["payload"]) != {"status", "token_usage"}
            or terminal[0]["payload"]["status"] != "completed"
            or terminal[0]["payload"]["token_usage"]
            != agent.get("usage", {}).get("completed")
        ):
            raise SmokeError("real model durable terminal payload drift")
        validate_run_usage(agent)
        agents.append(agent)
    if agents[0]["request_id"] == agents[1]["request_id"]:
        raise SmokeError("real model durable duplicate request identity")
    run = runs[1]
    storage = _query(
        infra,
        database_url,
        f"""SELECT json_build_object('count',count(*))
      FROM kokoro_storage.storage_artifact a JOIN kokoro_storage.storage_asset s
      ON s.tenant_id=a.tenant_id AND s.asset_id=a.asset_id AND s.scope_id=a.scope_id
      WHERE a.tenant_id='{tenant}' AND a.scope_id='{conversation}' AND a.artifact_id='{artifact}'
      AND a.asset_id='{asset}' AND a.source_run_id='{run}' AND a.state='final'
      AND a.finalized_sha256='{digest}' AND s.scan_state='clean'""",
    )
    if (
        type(storage) is not dict
        or set(storage) != {"count"}
        or type(storage["count"]) is not int
        or storage["count"] != 1
    ):
        raise SmokeError("real worker Storage FINAL CLEAN digest drift")
    return {"agents": agents, "storage": storage}


def real_scenario(config: RealModelConfig, **context) -> dict[str, object]:
    c = context
    source = stack._verify_source(SYSTEM, config.system_sha, "apps/kokoro-system")
    provider = provider_preflight(config)
    directory, log, infra = c["directory"], c["log"], c["infra"]
    node = c["node24"]
    system_root = stack._isolated_owner(SYSTEM, directory, "system")
    system_db = stack._owner_schema_database_url(c["owner_db_url"], "system")
    token = secrets.token_urlsafe(32)
    model_key = secrets.token_urlsafe(32)
    c["credentials"].add(token, model_key)
    port = stack.product.runtime.free_port()
    system_base = f"http://127.0.0.1:{port}"
    env = stack.product.session.node_environment(node, "v24.20.0", c["node"].parent)
    env.update(
        DATABASE_URL=system_db,
        REDIS_URL=c["system_redis_url"],
        KOKORO_SYSTEM_REDIS_NAMESPACE=infra.redis_prefix + "system",
        KOKORO_SYSTEM_HOST="127.0.0.1",
        KOKORO_SYSTEM_PORT=str(port),
        KOKORO_SYSTEM_BFF_SERVICE_TOKEN=token,
        KOKORO_SYSTEM_AGENT_SERVICE_TOKEN=c["agent_secret"],
        KOKORO_SYSTEM_ADMIN_SERVICE_TOKEN=token,
        KOKORO_SYSTEM_MODEL_HEALTH_MAX_AGE_MS="300000",
    )
    env.pop("PGOPTIONS", None)
    for command in (
        [
            str(node),
            str(system_root / "node_modules/tsx/dist/cli.mjs"),
            "scripts/apply-schema.ts",
        ],
        [
            str(node),
            str(system_root / "node_modules/typescript/bin/tsc"),
            "-p",
            "tsconfig.build.json",
        ],
    ):
        stack._run_owner_command(
            command, cwd=system_root, env=env, log=log, timeout=120
        )
    system_process = stack.product.runtime.start_process(node, system_root, env, log)
    c["processes"].append(system_process)
    system.wait_ready(system_base, system_process)
    route = system.seed_control_plane(
        system_base,
        c["ready"].tenant_id,
        token,
        c["run_id"],
        feature_key="chat",
        provider="ollama",
        model_name=config.model,
    )
    system_proxy = ObservingProxy(
        system_base,
        kind="system",
        token=c["agent_secret"],
        tenant=c["ready"].tenant_id,
        model=config.model,
        revision=route["revision_id"],
        timeout=c["timeout"],
        expected_route=route,
    )
    c["proxies"].append(system_proxy)
    model_proxy = ObservingProxy(
        config.endpoint,
        kind="model",
        token=model_key,
        tenant=c["ready"].tenant_id,
        model=config.model,
        revision=route["revision_id"],
        timeout=c["timeout"],
    )
    c["proxies"].append(model_proxy)
    worker_env = {
        **c["agent_env"],
        "KOKORO_SYSTEM_BASE_URL": system_proxy.origin,
        "KOKORO_LITELLM_ENABLED": "1",
        "KOKORO_LITELLM_BASE_URL": model_proxy.origin + "/v1",
        "KOKORO_LITELLM_API_KEY": model_key,
        "KOKORO_DISABLE_STREAMING": "0",
        "KOKORO_STORAGE_BASE_URL": c["storage_base"],
        "KOKORO_STORAGE_OBJECT_ORIGIN": c["object_origin"],
        "KOKORO_STORAGE_SERVICE_SECRET": c["agent_secret"],
        "KOKORO_MCP_EGRESS_MODE": "deny",
    }
    process = subprocess.Popen(
        [
            os.environ.get("KOKORO_W2_UV_BIN", "uv"),
            "run",
            "--frozen",
            "--no-sync",
            "kokoro-agent-worker",
        ],
        cwd=stack.AGENT,
        env=worker_env,
        stdout=log,
        stderr=subprocess.STDOUT,
        stdin=subprocess.DEVNULL,
        start_new_session=True,
    )
    c["processes"].append(process)
    content = f"KOKORO_REAL_MODEL_{c['run_id']}"
    digest = hashlib.sha256(content.encode()).hexdigest()
    payload = {
        "web_origin": c["origin"],
        "web_root": str(stack.WEB),
        "screenshot": str(c["screenshot"]),
        "web_certificate": str(c["certificate"]),
        "owner_email": c["ready"].email,
        "owner_password": c["ready"].password,
        "member_email": c["member"].email,
        "member_password": c["member"].password,
        "marker": content,
        "content_sha256": digest,
        "timeout_ms": int(c["timeout"] * 1000),
    }
    browser_process = subprocess.Popen(
        [str(c["node"]), str(DRIVER)],
        cwd=stack.ROOT,
        text=True,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        start_new_session=True,
    )
    c["processes"].append(browser_process)
    completed = False
    try:
        output, errors, provider_turns = read_driver_observations(
            browser_process, payload, system_proxy, model_proxy, c["timeout"] + 60
        )
        if browser_process.returncode != 0:
            phase = errors.strip()
            if re.fullmatch(r"REAL_MODEL_FAILURE:[a-z0-9-]+", phase) is None:
                phase = "REAL_MODEL_FAILURE:driver"
            raise SmokeError(phase)
        try:
            browser = json.loads(output)
        except ValueError:
            raise SmokeError("real model browser evidence malformed") from None
        validate_browser_evidence(browser, digest)
        durable = durable_evidence(
            infra, c["agent_db_url"], browser, c["ready"].tenant_id, process.pid, digest
        )
        validate_provider_turns(browser, provider_turns, durable["agents"])
        completed = True
    except subprocess.TimeoutExpired:
        raise SmokeError("real model Chromium deadline") from None
    finally:
        if not completed:
            # Quiesce all owned Run producers before taking the final inventory.
            for child in reversed(list(c["processes"])):
                stack.product.runtime.stop_owned_process(child)
                c["processes"].remove(child)
        register_owned_worker_runs(infra, c["agent_db_url"], c["agent_redis"])
    if (
        system_proxy.errors
        or model_proxy.errors
        or system_proxy.requests != 2
        or system_proxy.successes != 2
        or model_proxy.successes < 2
        or model_proxy.requests != model_proxy.successes
        or model_proxy.response_bytes == 0
    ):
        raise SmokeError("actual route/model observations incomplete")
    return {
        **browser,
        "system_source": source,
        "provider": provider,
        "system_route": provider_turns[0]["system"]["routes"][0],
        "system_requests": system_proxy.requests,
        "model_requests": model_proxy.requests,
        "model_successes": model_proxy.successes,
        "model_response_bytes": model_proxy.response_bytes,
        "durable": durable,
        "provider_turns": provider_turns,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--ollama-origin", default="http://127.0.0.1:11434")
    parser.add_argument("--model", default="qwen3:8b")
    parser.add_argument("--expected-system-sha", required=True)
    model_args, rest = parser.parse_known_args(argv)
    config = RealModelConfig(
        model_args.ollama_origin, model_args.model, model_args.expected_system_sha
    )
    args = stack.parse_args(rest)
    env = stack.check_configuration(dict(os.environ))
    if args.check_config:
        print("real model shape valid; no provider contacted")
        return 0
    stack._verify_source(SYSTEM, config.system_sha, "apps/kokoro-system")
    result = stack._run_smoke(
        args, env, real_model_scenario=lambda **kwargs: real_scenario(config, **kwargs)
    )
    print(json.dumps(result, sort_keys=True), flush=True)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except SmokeError as error:
        print(f"Real model smoke failed: {error}", file=sys.stderr)
        raise SystemExit(1) from None
