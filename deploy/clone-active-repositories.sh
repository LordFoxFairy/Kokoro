#!/usr/bin/env bash
# Bootstrap the independent Kokoro repositories beside Root.
# This script is additive: it never resets, removes, or overwrites an existing checkout.
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
OWNER="${KOKORO_GITHUB_OWNER:-LordFoxFairy}"

declare -a REPOSITORIES=(
  "kokoro|kokoro-app"
  "kokoro-bff|kokoro-bff"
  "kokoro-iam|kokoro-iam"
  "kokoro-system|kokoro-system"
  "kokoro-model|kokoro-model"
  "kokoro-billing|kokoro-billing"
  "kokoro-capability|kokoro-capability"
  "kokoro-storage|kokoro-storage"
  "kokoro-scheduler|kokoro-scheduler"
)

git -C "$ROOT_DIR" submodule update --init --recursive kokoro-agent

for entry in "${REPOSITORIES[@]}"; do
  local_name="${entry%%|*}"
  repository_name="${entry##*|}"
  destination="$ROOT_DIR/$local_name"
  remote="https://github.com/$OWNER/$repository_name.git"

  if [[ -e "$destination" ]]; then
    top_level="$(git -C "$destination" rev-parse --show-toplevel 2>/dev/null || true)"
    [[ "$top_level" == "$destination" ]] || {
      echo "已有路径不是独立 Git 仓库：$destination" >&2
      exit 1
    }
    actual_remote="$(git -C "$destination" remote get-url origin 2>/dev/null || true)"
    [[ "${actual_remote%.git}" == "${remote%.git}" ]] || {
      echo "已有仓库 remote 不匹配：$destination ($actual_remote)" >&2
      exit 1
    }
    echo "保留现有 checkout：$local_name"
    continue
  fi

  git clone --origin origin "$remote" "$destination"
done

echo "独立 Kokoro 仓库已准备完成；现有 checkout 未被重置或覆盖。"
