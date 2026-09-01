from __future__ import annotations

import argparse
import json
import time
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import TypeAlias


JsonValue: TypeAlias = (
    None | bool | int | float | str | list["JsonValue"] | dict[str, "JsonValue"]
)


MODEL = "slice-a-fixture"
TOOL_ID = "call_slice_a_approval"
TOOL_ARGUMENTS = '{"question":"Approve Slice A?","choices":["Approve","Reject"]}'


def _contains_text(value: JsonValue, expected: str) -> bool:
    if isinstance(value, str):
        return expected in value
    if isinstance(value, list):
        return any(_contains_text(item, expected) for item in value)
    if isinstance(value, dict):
        return any(_contains_text(item, expected) for item in value.values())
    return False


def _contains_approved_resume(messages: JsonValue) -> bool:
    if not isinstance(messages, list):
        return False
    if any(
        not isinstance(message, dict)
        or ("tool_calls" in message and not isinstance(message["tool_calls"], list))
        or ("tool_calls" in message and message.get("role") != "assistant")
        for message in messages
    ):
        return False
    requests = [
        (index, call)
        for index, message in enumerate(messages)
        if isinstance(message, dict) and isinstance(message.get("tool_calls"), list)
        for call in message.get("tool_calls", [])
    ]
    results = [
        (index, message)
        for index, message in enumerate(messages)
        if isinstance(message, dict) and message.get("role") == "tool"
    ]
    return (
        len(requests) == len(results) == 1
        and requests[0][0] < results[0][0]
        and requests[0][1]
        == {
            "id": TOOL_ID,
            "type": "function",
            "function": {
                "name": "ask_user_question",
                "arguments": TOOL_ARGUMENTS,
            },
        }
        and results[0][1]
        == {
            "role": "tool",
            "tool_call_id": TOOL_ID,
            "content": "Approve",
        }
    )


def _chunk(*, choices: JsonValue, usage: JsonValue | None = None) -> bytes:
    payload: dict[str, JsonValue] = {
        "id": "chatcmpl-slice-a",
        "object": "chat.completion.chunk",
        "created": int(time.time()),
        "model": MODEL,
        "choices": choices,
    }
    if usage is not None:
        payload["usage"] = usage
    return f"data: {json.dumps(payload, separators=(',', ':'))}\n\n".encode()


class FixtureHandler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def log_message(self, format: str, *args: object) -> None:
        del format, args

    def do_GET(self) -> None:  # noqa: N802
        if self.path != "/healthz":
            self.send_error(HTTPStatus.NOT_FOUND)
            return
        body = b'{"status":"ok"}'
        self.send_response(HTTPStatus.OK)
        self.send_header("content-type", "application/json")
        self.send_header("content-length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_POST(self) -> None:  # noqa: N802
        if self.path not in {"/v1/chat/completions", "/chat/completions"}:
            self.send_error(HTTPStatus.NOT_FOUND)
            return
        try:
            length = int(self.headers.get("content-length", "0"))
            raw = json.loads(self.rfile.read(length))
        except (ValueError, json.JSONDecodeError):
            self._json_error("invalid JSON")
            return
        if not isinstance(raw, dict) or raw.get("model") != MODEL:
            self._json_error("unsupported model")
            return
        messages = raw.get("messages")
        if not _contains_text(messages, "slice-a-hitl"):
            self._json_error("unsupported prompt")
            return
        if raw.get("stream") is not True:
            self._json_error("fixture requires streaming")
            return
        has_tool_result = (
            any(
                isinstance(message, dict) and message.get("role") == "tool"
                for message in messages
            )
            if isinstance(messages, list)
            else False
        )
        resumed = _contains_approved_resume(messages)
        if has_tool_result and not resumed:
            self._json_error("invalid Slice A HITL resume")
            return
        chunks = self._completion_chunks(resumed)
        body = b"".join(chunks) + b"data: [DONE]\n\n"
        self.send_response(HTTPStatus.OK)
        self.send_header("content-type", "text/event-stream")
        self.send_header("cache-control", "no-cache")
        self.send_header("connection", "close")
        self.send_header("content-length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _completion_chunks(self, resumed: bool) -> list[bytes]:
        if resumed:
            return [
                _chunk(
                    choices=[
                        {
                            "index": 0,
                            "delta": {
                                "role": "assistant",
                                "content": "Slice A approved.",
                            },
                            "finish_reason": None,
                        }
                    ]
                ),
                _chunk(choices=[{"index": 0, "delta": {}, "finish_reason": "stop"}]),
                _chunk(
                    choices=[],
                    usage={
                        "prompt_tokens": 19,
                        "completion_tokens": 4,
                        "total_tokens": 23,
                    },
                ),
            ]
        return [
            _chunk(
                choices=[
                    {
                        "index": 0,
                        "delta": {
                            "role": "assistant",
                            "tool_calls": [
                                {
                                    "index": 0,
                                    "id": TOOL_ID,
                                    "type": "function",
                                    "function": {
                                        "name": "ask_user_question",
                                        "arguments": TOOL_ARGUMENTS,
                                    },
                                }
                            ],
                        },
                        "finish_reason": None,
                    }
                ]
            ),
            _chunk(choices=[{"index": 0, "delta": {}, "finish_reason": "tool_calls"}]),
            _chunk(
                choices=[],
                usage={"prompt_tokens": 11, "completion_tokens": 7, "total_tokens": 18},
            ),
        ]

    def _json_error(self, message: str) -> None:
        body = json.dumps(
            {"error": {"message": message, "type": "invalid_request_error"}}
        ).encode()
        self.send_response(HTTPStatus.BAD_REQUEST)
        self.send_header("content-type", "application/json")
        self.send_header("content-length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Deterministic OpenAI-compatible Slice A fixture"
    )
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, required=True)
    args = parser.parse_args()
    server = ThreadingHTTPServer((args.host, args.port), FixtureHandler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
