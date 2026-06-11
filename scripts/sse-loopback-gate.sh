#!/usr/bin/env bash
# P0 SSE loopback gate (critic): real agent→session→Redis→session SSE main path,
# scripted assertion of the event sequence. Replaces the manual Playwright e2e as
# a re-runnable gate for ANY stream-pipeline change.
#
# Prereqs (the dev loop this repo already runs): Redis db14 + kokoro-session on
# :3001 + kokoro-agent worker with KOKORO_LOCAL_FAKE_MODEL=1, all on db14.
#   session: KOKORO_STREAM_BACKEND=redis KOKORO_REDIS_URL=redis://127.0.0.1:6379/14 ... bun run src/main.ts
#   worker:  KOKORO_STREAM_BACKEND=redis KOKORO_REDIS_URL=redis://127.0.0.1:6379/14 KOKORO_LOCAL_FAKE_MODEL=1 uv run kokoro-agent-worker
set -uo pipefail
SESSION="${KOKORO_SESSION_URL:-http://127.0.0.1:3001}"
SID="sse_gate_$$_$(date +%s)"

run_json=$(curl -s -X POST "$SESSION/sessions/$SID/runs?conversation_id=$SID&input=ping&execution_style=fast")
run_id=$(printf '%s' "$run_json" | python3 -c "import sys,json;d=json.load(sys.stdin);print(d.get('runId') or d.get('run_id') or '')" 2>/dev/null)
if [ -z "$run_id" ]; then echo "FAIL: POST /runs returned no run_id: $run_json"; exit 1; fi

# /stream is replay-then-live and stays open for the live tail; cap with --max-time.
raw=$(curl -sN --max-time 4 "$SESSION/sessions/$SID/stream")
kinds=$(printf '%s' "$raw" | sed -n 's/^event: *//p' | sort -u)
echo "--- SSE event kinds for $run_id ---"; printf '%s\n' "$kinds" | sed 's/^/  /'

missing=0
# fake-model run normalized to AGUI: session.created(once) + run.created + todo + message + run.completed
for k in session.created run.created todo.updated message.completed run.completed; do
  printf '%s\n' "$kinds" | grep -qx "$k" || { echo "FAIL: missing $k"; missing=1; }
done
[ "$missing" = 0 ] || exit 1

# seq is a first-class envelope field: assert per-runId non-decreasing, and strictly
# increasing once the two run.started-synthesized events (which share one seq) are excluded.
printf '%s' "$raw" | python3 -c '
import sys, json
by_run = {}
for line in sys.stdin:
    line = line.strip()
    if not line.startswith("data:"):
        continue
    try:
        d = json.loads(line[5:].strip())
    except Exception:
        continue
    if "seq" not in d or "run_id" not in d:
        continue
    by_run.setdefault(d["run_id"], []).append((d["seq"], d.get("event")))
ok = True
total = 0
for rid, evs in by_run.items():
    seqs = [s for s, _ in evs]
    total += len(seqs)
    if any(seqs[i] > seqs[i + 1] for i in range(len(seqs) - 1)):
        print(f"FAIL: seq decreased in run {rid}: {seqs}"); ok = False
    ranked = [s for s, e in evs if e not in ("session.created", "run.created")]
    if any(ranked[i] >= ranked[i + 1] for i in range(len(ranked) - 1)):
        print(f"FAIL: ranked seq not strictly increasing in run {rid}: {ranked}"); ok = False
if not ok:
    sys.exit(1)
print(f"PASS: seq per-run non-decreasing + ranked strictly increasing ({total} events, {len(by_run)} run)")
' || exit 1

echo "PASS: SSE loopback intact (run=$run_id)"
