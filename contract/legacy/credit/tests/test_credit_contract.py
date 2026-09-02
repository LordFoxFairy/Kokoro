from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROTO = ROOT / "proto/kokoro/credit/v1/credit.proto"


def test_credit_first_slice_declares_only_hold_lifecycle_commands() -> None:
    source = PROTO.read_text(encoding="utf-8")
    assert 'package kokoro.credit.v1;' in source
    assert 'service CreditCommandService {' in source
    assert 'rpc CreateHold(CreateHoldRequest)' in source
    assert 'rpc CaptureHold(CaptureHoldRequest)' in source
    assert 'rpc ReleaseHold(ReleaseHoldRequest)' in source
    assert 'string amount_micros = 6;' in source
    assert 'string idempotency_key = 7;' in source
