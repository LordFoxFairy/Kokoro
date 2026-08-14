#!/usr/bin/env bash
set -euo pipefail

ROOT="$(git rev-parse --show-toplevel)"
cd "$ROOT"

plans=(
  docs/superpowers/plans/2026-08-14-sql-backed-chat-slice-a-master-plan.md
  docs/superpowers/plans/2026-08-14-slice-a-site-iam-model-capability-plan.md
  docs/superpowers/plans/2026-08-14-slice-a-web-e2e-promotion-plan.md
  docs/superpowers/plans/2026-08-14-slice-a-root-database-contracts-plan.md
)

for path in "${plans[@]}"; do
  test -f "$path"
done

python3 - "${plans[@]}" <<'PY'
from __future__ import annotations

from pathlib import Path
import json
import re
import sys
import tempfile

MASTER, OWNER, WEB, ROOT_PLAN = map(Path, sys.argv[1:])
SITE_RETIREMENT_START = "<!-- slice-a-site-contract-retirement:start -->"
SITE_RETIREMENT_END = "<!-- slice-a-site-contract-retirement:end -->"
EXPECTED_SITE_RETIREMENT = """<!-- slice-a-site-contract-retirement:start -->
### Frozen Site contract retirement boundary

The frozen contract source still contains `contract/proto/kokoro/site/v1/site.proto`, consumer key
`kokoro-site` and `SiteService.ResolveSiteByHost`. These are compatibility artifacts only: Slice A does not
materialize them as a runtime repository, process, listener, endpoint, candidate or Root gitlink. Web production
code does not construct the generated client. Removal requires a separate reviewed contract-retirement cut that
updates the manifest, generator, consumer closure, breaking image and every generated output atomically.
<!-- slice-a-site-contract-retirement:end -->"""
CONTAINER_START = "<!-- slice-a-container-delivery:start -->"
CONTAINER_END = "<!-- slice-a-container-delivery:end -->"

SITE_CONTEXT_VARIABLE = re.compile(r"\bKOKORO_SITE_CONTEXT[A-Z0-9_]*\b")
OPERATIONAL_SITE = re.compile(
    r"kokoro[-./]site|kokoro_site(?!_contexts_json)|\bSiteService\b|\bResolveSiteByHost\b|"
    r"\bsite[-_ ]+(?:service|runtime|process|listener|candidate|repository|repo|gitlink|client|endpoint|rpc)\b|"
    r"(?:https?://)?site:7201|\b7201\b|/tmp/kokoro-site-slice-a|"
    r"^\s*(?:[-*]\s*)?site\s*:\s*(?:$|[^/])|"
    r"^\s*\|?\s*site\s*\||\bservices\.site\b|"
    r"[\"']services[\"']\s*:\s*\{[^{}]*[\"']site[\"']\s*:|"
    r"[\"']service[\"']\s*:\s*[\"']site[\"']|^\s*service\s*:\s*site\b",
    re.IGNORECASE | re.MULTILINE,
)
PACKAGING = re.compile(r"\bDockerfile\b|\bdocker\b|\bcompose\b|\bcontainer\b|\bimage-security\b", re.IGNORECASE)
DOCKER_DATABASE_LIFECYCLE = re.compile(r"\bDocker\b|postgres:18|\bcontainer(?:s)?\b|\bvolume(?:s)?\b", re.IGNORECASE)
DOCKER_DATABASE_RUNNER = "run_in_fresh_pg18.py"
NATIVE_DATABASE_RUNNER = "scripts/database/run_in_fresh_pg18_native.py"


def remove_exact_section(text: str, start: str, end: str, expected: str | None) -> tuple[str, str]:
    if text.count(start) != 1 or text.count(end) != 1:
        raise AssertionError(f"expected one structured section: {start}")
    before, rest = text.split(start, 1)
    body, after = rest.split(end, 1)
    actual = start + body + end
    if expected is not None and actual != expected:
        raise AssertionError(f"structured section drift: {start}")
    return before + after, actual


def reject_operational_site(text: str) -> None:
    match = OPERATIONAL_SITE.search(text)
    if match:
        raise AssertionError(f"operational Site surface escaped retirement section: {match.group(0)!r}")
    for match in SITE_CONTEXT_VARIABLE.finditer(text):
        if match.group(0) != "KOKORO_SITE_CONTEXTS_JSON":
            raise AssertionError(f"noncanonical Site context variable is forbidden: {match.group(0)!r}")
    inventory = re.compile(
        r"\b(?:BACKEND|RUNTIME)_(?:PROCESSES|SERVICES)\s*=\s*\{(?P<body>.*?)\}",
        re.IGNORECASE | re.DOTALL,
    )
    for match in inventory.finditer(text):
        if re.search(r"\bsite\b", match.group("body"), re.IGNORECASE):
            raise AssertionError(f"{match.group(0).split('=', 1)[0].strip()} must not contain a Site entry")


def validate_native_start_blocks(text: str) -> None:
    start_blocks = [block for block in re.findall(r"```bash\n(.*?)```", text, re.DOTALL) if "native.py start" in block]
    if len(start_blocks) != 4:
        raise AssertionError(f"expected four native.py start shell blocks, got {len(start_blocks)}")
    for block in start_blocks:
        start = block.index("native.py start")
        cleanup = block.find("cleanup_native", start)
        clear = block.find("trap - EXIT INT TERM", start)
        if 'STATE_PARENT="$(mktemp -d ' not in block:
            raise AssertionError("native start block must allocate STATE_PARENT")
        if 'STATE_DIR="$STATE_PARENT/state"' not in block:
            raise AssertionError("native start block must pass a non-existing STATE_PARENT/state child")
        if 'STATE_DIR="$(mktemp -d ' in block:
            raise AssertionError("native start block must not pre-create STATE_DIR")
        before_start = block[:start]
        if re.search(r"(?:mkdir|install\s+-d|touch)[^\n]*\$\{?STATE_DIR", before_start):
            raise AssertionError("native start block must leave STATE_DIR absent before start")
        trap = block.find("trap cleanup_native EXIT INT TERM")
        if trap < 0 or trap > start:
            raise AssertionError("cleanup trap must be installed before native.py start")
        if cleanup < 0 or clear < cleanup:
            raise AssertionError("success path must explicitly clean and then clear the trap")
        if 'rm -rf -- "$STATE_PARENT"' not in block:
            raise AssertionError("native cleanup must remove STATE_PARENT")
        cleanup_definition = block[block.find("cleanup_native()", 0, trap):trap]
        if 'native.py stop --state-dir "$STATE_DIR" || true' not in cleanup_definition:
            raise AssertionError("native cleanup must attempt to stop the recorded lifecycle")
        if 'cleanup.py --dir "$STATE_DIR" || true' not in cleanup_definition:
            raise AssertionError("native cleanup must remove the marked state child")


def assert_native_block_rejected(block: str) -> None:
    try:
        validate_native_start_blocks(f"```bash\n{block}```\n```bash\n{block}```\n```bash\n{block}```\n```bash\n{block}```")
    except AssertionError:
        return
    raise AssertionError("unsafe native lifecycle fixture unexpectedly passed")


def assert_rejected(text: str, *, structured: bool = False) -> None:
    try:
        candidate = text
        if structured:
            candidate, _ = remove_exact_section(
                candidate, SITE_RETIREMENT_START, SITE_RETIREMENT_END, EXPECTED_SITE_RETIREMENT
            )
        reject_operational_site(candidate)
    except AssertionError:
        return
    raise AssertionError(f"bypass fixture unexpectedly passed: {text!r}")


def run_bypass_self_tests() -> None:
    # Same-line words such as "legacy"/"frozen" never whitelist an operational statement.
    assert_rejected("legacy kokoro-site candidate remains required")
    assert_rejected("frozen SiteService alias is still called")
    assert_rejected("use site service for Host lookup")
    assert_rejected("listen at http://site:7201")
    assert_rejected("listener: 7201")
    assert_rejected('BACKEND_PROCESSES = {"postgres", "site", "iam"}')
    assert_rejected('BACKEND_SERVICES = {"iam", "site"}')
    assert_rejected('RUNTIME_PROCESSES = {"postgres", "site"}')
    assert_rejected('RUNTIME_SERVICES = {"site": "pnpm dev", "iam": "pnpm dev"}')
    assert_rejected("services:\n  site:\n    command: pnpm dev")
    assert_rejected("| Site | 7201 | /ready |")
    assert_rejected("| Site | 8123 | /ready |")
    assert_rejected('{"services": {"site": {"port": 8123}}}')
    assert_rejected("services.site: http://127.0.0.1:8123")
    assert_rejected("export KOKORO_SITE_CONTEXT=/tmp/x")
    assert_rejected("export KOKORO_SITE_CONTEXT_FILE=/tmp/x")
    assert_rejected("export KOKORO_SITE_CONTEXTS_JSON_FILE=/tmp/x")
    assert_rejected("export KOKORO_SITE_CONTEXTS_JSON_V2=/tmp/x")
    assert_rejected(
        EXPECTED_SITE_RETIREMENT + "\nlegacy kokoro-site repo", structured=True
    )
    assert_rejected(
        EXPECTED_SITE_RETIREMENT.replace("compatibility artifacts only", "runtime fallback"),
        structured=True,
    )
    operational, _ = remove_exact_section(
        EXPECTED_SITE_RETIREMENT, SITE_RETIREMENT_START, SITE_RETIREMENT_END, EXPECTED_SITE_RETIREMENT
    )
    reject_operational_site(operational)
    reject_operational_site("KOKORO_SITE_CONTEXTS_JSON is the exact server-only map")

    # Exercise the fixtures through real files so path/encoding behavior cannot bypass the scanner.
    with tempfile.TemporaryDirectory() as raw:
        fixture = Path(raw) / "bypass.md"
        fixture.write_text("frozen SiteService remains operational\n")
        assert_rejected(fixture.read_text())

    safe = '''STATE_PARENT="$(mktemp -d /tmp/native-state.XXXXXX)"
STATE_DIR="$STATE_PARENT/state"
cleanup_native() {
  test ! -e "$STATE_DIR" || native.py stop --state-dir "$STATE_DIR" || true
  test ! -e "$STATE_DIR" || cleanup.py --dir "$STATE_DIR" || true
  rm -rf -- "$STATE_PARENT"
}
trap cleanup_native EXIT INT TERM
native.py start --state-dir "$STATE_DIR"
cleanup_native
trap - EXIT INT TERM
'''
    validate_native_start_blocks("".join(f"```bash\n{safe}```\n" for _ in range(4)))
    assert_native_block_rejected(safe.replace('STATE_DIR="$STATE_PARENT/state"', 'STATE_DIR="$(mktemp -d /tmp/state.XXXXXX)"'))
    assert_native_block_rejected(safe.replace('cleanup_native() {', 'mkdir -p "$STATE_DIR"\ncleanup_native() {'))
    assert_native_block_rejected(safe.replace("trap cleanup_native EXIT INT TERM\n", ""))
    assert_native_block_rejected(safe.replace("trap cleanup_native EXIT INT TERM\n", "").replace("native.py start", "native.py start\ntrap cleanup_native EXIT INT TERM"))
    assert_native_block_rejected(safe.replace('  rm -rf -- "$STATE_PARENT"\n', ""))
    assert_native_block_rejected(safe.replace('  test ! -e "$STATE_DIR" || native.py stop --state-dir "$STATE_DIR" || true\n', ""))
    assert_native_block_rejected(safe.replace('  test ! -e "$STATE_DIR" || cleanup.py --dir "$STATE_DIR" || true\n', ""))
    assert_native_block_rejected(safe.replace("trap - EXIT INT TERM\n", ""))


run_bypass_self_tests()

texts = {path: path.read_text() for path in (MASTER, OWNER, WEB, ROOT_PLAN)}
master_operational, retirement = remove_exact_section(
    texts[MASTER], SITE_RETIREMENT_START, SITE_RETIREMENT_END, EXPECTED_SITE_RETIREMENT
)
assert retirement == EXPECTED_SITE_RETIREMENT
reject_operational_site(master_operational)
for path in (OWNER, WEB, ROOT_PLAN):
    assert SITE_RETIREMENT_START not in texts[path] and SITE_RETIREMENT_END not in texts[path]
    reject_operational_site(texts[path])

for path in (ROOT_PLAN, OWNER, WEB):
    if DOCKER_DATABASE_RUNNER in texts[path]:
        raise AssertionError(f"{path}: current milestone references Docker database runner")
    if NATIVE_DATABASE_RUNNER not in texts[path]:
        raise AssertionError(f"{path}: native PostgreSQL 18 database runner is not required")

# Container delivery is structurally deferred; no current native gate may depend on packaging.
for path in (OWNER, WEB):
    operational, deferred = remove_exact_section(
        texts[path], CONTAINER_START, CONTAINER_END, expected=None
    )
    assert "not a prerequisite" in deferred.lower()
    leaked = PACKAGING.search(operational)
    if leaked:
        raise AssertionError(f"{path}: packaging leaked into current native milestones: {leaked.group(0)!r}")
    if path == WEB:
        assert "native.py start --fresh" in operational
        assert "native.py restart agent|chat" in operational
        assert "repository-native processes" in operational
    else:
        assert "native `pnpm dev`" in operational

root_docker_database = DOCKER_DATABASE_LIFECYCLE.search(texts[ROOT_PLAN])
if root_docker_database:
    raise AssertionError(f"{ROOT_PLAN}: Docker database lifecycle leaked into native milestones: {root_docker_database.group(0)!r}")
validate_native_start_blocks(texts[WEB])

# Exact, machine-reviewable positive architecture facts.
assert "server-bound SiteContext" in texts[MASTER]
assert "The runtime child allowlist is exactly IAM, Model, Capability, Chat, Agent and Web." in texts[OWNER]
assert texts[WEB].count("KOKORO_SITE_CONTEXTS_JSON") >= 2
assert "The exact runtime child allowlist is IAM, Model, Capability, Chat, Agent and Web." in texts[WEB]
assert "IAM does not select a Site" in texts[OWNER]
assert "both `site_*` and `iam_*` to `kokoro-iam`" in texts[ROOT_PLAN]
assert 'RUNTIME_CONSUMERS = {"iam", "chat", "agent", "capability", "model", "web", "root-e2e"}' in texts[ROOT_PLAN]
assert 'assert "site" not in consumer_map' in texts[ROOT_PLAN]
assert 'RUNTIME_CONSUMER_MAP=/tmp/kokoro-slice-a-runtime-consumer-map.json' in texts[ROOT_PLAN]
assert 'json.loads(Path(sys.argv[1]).read_text())' in texts[ROOT_PLAN]
assert 'done < <(python3 - "$RUNTIME_CONSUMER_MAP"' in texts[ROOT_PLAN]
assert "uv run --frozen pytest contract/tests scripts/contract/tests -q" in texts[ROOT_PLAN]
runtime_map_match = re.search(
    r'cat >"\$RUNTIME_CONSUMER_MAP" <<JSON\n(?P<json>\{[^\n]+\})\nJSON', texts[ROOT_PLAN]
)
assert runtime_map_match is not None
runtime_map = json.loads(runtime_map_match.group("json"))
assert set(runtime_map) == {"iam", "chat", "agent", "capability", "model", "web", "root-e2e"}
assert "site" not in runtime_map

print("slice_a_site_context_bypass_self_tests_ok")
print("slice_a_site_context_plan_alignment_ok")
PY

# This alignment cut does not rewrite the already frozen manifest/generator/consumer closure.
git diff --quiet -- \
  contract/slice-a-contract-manifest.yaml \
  contract/consumers.yaml \
  contract/generate.py

printf 'slice_a_site_context_frozen_contract_unchanged\n'
