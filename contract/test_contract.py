"""events 契约守卫的测试：drift 检测逻辑、yaml 派生、端到端 verify/generate（此前零测试）。

contract/ 无专属 venv——脚本走系统 python3（pytest 9 + pyyaml 均在）。
运行：python3 -m pytest contract/test_contract.py
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

import verify  # contract/verify.py（pytest 把 test 所在目录加入 sys.path）

_ROOT = Path(__file__).resolve().parent.parent


# ── Report.compare：drift 检测逻辑（证明守卫不是恒绿空操作）──────────────────


def test_compare_clean_when_identical() -> None:
    rep = verify.Report()
    rep.compare("f", "v", {"a": {"x", "y"}}, {"a": {"x", "y"}})
    assert rep.problems == []


def test_compare_detects_missing_kind() -> None:
    rep = verify.Report()
    rep.compare("f", "v", {"a": set(), "b": set()}, {"a": set()})
    assert any("missing kind/event 'b'" in p.detail for p in rep.problems)


def test_compare_detects_unexpected_kind() -> None:
    rep = verify.Report()
    rep.compare("f", "v", {"a": set()}, {"a": set(), "b": set()})
    assert any("unexpected kind/event 'b'" in p.detail for p in rep.problems)


def test_compare_detects_missing_payload_field() -> None:
    rep = verify.Report()
    rep.compare("f", "v", {"a": {"x", "y"}}, {"a": {"x"}})
    assert any("missing payload field 'y'" in p.detail for p in rep.problems)


def test_compare_detects_unexpected_payload_field() -> None:
    rep = verify.Report()
    rep.compare("f", "v", {"a": {"x"}}, {"a": {"x", "z"}})
    assert any("unexpected payload field 'z'" in p.detail for p in rep.problems)


def test_compare_allow_extra_tolerates_field() -> None:
    rep = verify.Report()
    rep.compare("f", "v", {"a": {"x"}}, {"a": {"x", "z"}}, allow_extra={"a": {"z"}})
    assert rep.problems == []


# ── yaml 派生：expected_* 从真实 spec 推导出非空、结构自洽 ───────────────────


def test_expected_agui_out_derives_nonempty_and_web_superset() -> None:
    spec = verify.load_spec()
    strict = verify.expected_agui_out(spec, with_web_extra=False)
    web = verify.expected_agui_out(spec, with_web_extra=True)
    assert strict
    assert set(strict) == set(web)  # web 容忍只加可选字段、不增 kind
    for kind in strict:
        assert strict[kind] <= web[kind]


def test_expected_render_derives_nonempty() -> None:
    assert verify.expected_render(verify.load_spec())


# ── 端到端守卫：当前仓库 in-sync（任何漂移都会让这两条变红）──────────────────


def test_verify_passes_on_current_repo() -> None:
    result = subprocess.run(
        [sys.executable, "contract/verify.py"],
        cwd=_ROOT,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stdout + result.stderr


def test_generate_check_passes_on_current_repo() -> None:
    result = subprocess.run(
        [sys.executable, "contract/generate.py", "--check"],
        cwd=_ROOT,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stdout + result.stderr


# ── 端到端：守卫真的拦得住漂移（把一个 mirror 指向被掏空的副本，不碰任何已提交文件）──


def test_verify_main_returns_nonzero_on_drifted_mirror(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    empty_union = tmp_path / "session-event.ts"
    empty_union.write_text("const sessionEventSchema = z.union([])\n")
    monkeypatch.setattr(verify, "SESSION_EVENT_TS", empty_union)
    # 掏空的 mirror → 所有 agui-out kind 都缺失 → main() 必须报漂移返回 1（守卫拦得住）。
    assert verify.main() == 1
