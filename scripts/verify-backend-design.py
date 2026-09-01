#!/usr/bin/env python3
"""Verify the current backend design against the DeepAgents-first boundary."""
from __future__ import annotations
import ast
import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "docs/kokoro-handbook/technical/backend-design/backend-design-manifest.json"
CARDS = MANIFEST.parent
AGENT_CARD = CARDS / "09-agent.md"
AGENT_PACKAGE = ROOT / "kokoro-agent"
AGENT_SRC = AGENT_PACKAGE / "src/kokoro_agent"
CURRENT_DOCS = (
    ROOT / "docs/kokoro-handbook/technical/42-ga-core-architecture.md",
    ROOT / "docs/kokoro-handbook/technical/36-ga-final-agent-technical-plan.md",
    ROOT / "docs/kokoro-handbook/technical/43-ga-clean-build-slices.md",
    AGENT_CARD,
    AGENT_PACKAGE / "docs/agent/architecture.md",
    AGENT_PACKAGE / "docs/agent/technical-plan.md",
    AGENT_PACKAGE / "docs/agent/current-boundary.md",
)
REQUIRED_AGENT_CARD_SECTIONS = (
    "## 定位", "## 架构等级", "## 核心闭环与外部边界",
    "## 数据 owner 与不负责项", "## Sandbox workspace 与 S3-compatible 配置",
    "## 可执行目录与语义拓扑", "## 依赖规则与可自动化门禁",
    "## 公开契约", "## 100 分证据", "## 当前源码审计与首发前置条件",
)
REQUIRED_AGENT_PACKAGE_SECTIONS = (
    "## 1. 目标链路", "## 2. 对象与命名", "## 3. 两条构造路径",
    "## 4. 目录与依赖", "## 5. 状态、Session 与身份",
    "## 6. 能力和外部服务", "## 7. 事件、聊天与计费",
    "## 8. 实施顺序", "## 9. 验收标准",
)
EXPECTED_SOURCE_PATHS = (
    "agents", "features", "agent_factory.py", "swarm.py", "execution", "worker",
    "tools", "skills", "clients", "sandbox", "storage", "mcp", "model", "prompts",
)
FORBIDDEN_SOURCE_PATHS = (
    "ga", "factory", "framework", "compiler", "runtime", "ports", "deepagents.py",
    "graph.py", "flow.py", "state.py", "agent.py",
)
FORBIDDEN_SHADOW_NAMES = {
    "DeepAgentState", "KokoroAgentState", "CompiledGraph", "ConversationState",
    "Workflow", "BusinessOrchestration",
}
FORBIDDEN_PUBLIC_FIELDS = {
    "namespace", "thread_id", "agent", "agents", "member", "members", "graph",
    "skill", "skills", "mcp", "deps", "binding", "release", "version",
}
STALE_CURRENT_DOC_PATTERNS = (
    re.compile(r"WorkflowCatalog"),
    re.compile(r"CompiledGraphRegistry"),
    re.compile(r"Feature\s*->\s*Workflow"),
    re.compile(r"WorkflowCompiler"),
    re.compile(r"当前源码正在从.*迁移", re.S),
    re.compile(r"迁移中的旧文件"),
)

def py_files():
    return tuple(sorted(AGENT_SRC.rglob("*.py")))

def rel(path):
    return str(path.relative_to(AGENT_SRC))

def imports(path):
    tree = ast.parse(path.read_text(encoding="utf-8"))
    out = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            out.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            out.add(node.module)
    return out

def defined(path):
    tree = ast.parse(path.read_text(encoding="utf-8"))
    return {node.name for node in ast.walk(tree)
            if isinstance(node, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef))}

def markers(errors, path, values):
    if not path.is_file():
        errors.append(f"missing architecture document: {path.relative_to(ROOT)}")
        return
    text = path.read_text(encoding="utf-8")
    missing = [value for value in values if value not in text]
    if missing:
        errors.append(f"{path.relative_to(ROOT)}: missing markers {missing}")

def links(errors, path):
    if not path.is_file():
        return
    in_fence = False
    fence = chr(96) * 3
    for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if line.strip().startswith(fence):
            in_fence = not in_fence
            continue
        if not in_fence and line.count(chr(96)) % 2:
            errors.append(f"{path.relative_to(ROOT)}:{number}: unmatched inline backtick")

def check_manifest(errors):
    if not MANIFEST.is_file():
        errors.append(f"missing manifest: {MANIFEST.relative_to(ROOT)}")
        return
    data = json.loads(MANIFEST.read_text(encoding="utf-8"))
    repos = data.get("repositories")
    if not isinstance(repos, list) or not repos:
        errors.append("backend design manifest has no repositories")
        return
    names = [repo.get("name") for repo in repos]
    if len(names) != len(set(names)):
        errors.append("backend design manifest contains duplicate repository names")
    required = {"name", "kind", "complexity", "designScore", "designCard", "owns", "doesNotOwn", "currentEvidence"}
    for repo in repos:
        missing = required - repo.keys()
        if missing:
            errors.append(f"{repo.get('name', '<unknown>')}: missing fields {sorted(missing)}")
        card = CARDS / str(repo.get("designCard", ""))
        if not card.is_file():
            errors.append(f"{repo.get('name', '<unknown>')}: missing design card {card.relative_to(ROOT)}")
        if repo.get("designScore") != 100:
            errors.append(f"{repo.get('name', '<unknown>')}: designScore must be 100")
        if not repo.get("owns") or not repo.get("doesNotOwn"):
            errors.append(f"{repo.get('name', '<unknown>')}: owns/doesNotOwn must be non-empty")
    capability = next((repo for repo in repos if repo.get("name") == "kokoro-capability"), None)
    if capability is None:
        errors.append("backend design manifest is missing kokoro-capability")
    elif any("snapshot" in item or "version" in item for item in capability.get("owns", ())):
        errors.append("Capability must own logical paths/CRUD, not runtime snapshots or versions")

def check_source(errors, allow_missing=False):
    files = py_files()
    if not files:
        if allow_missing and not AGENT_SRC.exists():
            return
        errors.append("kokoro-agent source tree is empty")
        return
    for expected in EXPECTED_SOURCE_PATHS:
        if not (AGENT_SRC / expected).exists():
            errors.append(f"missing expected Agent path: {expected}")
    for forbidden in FORBIDDEN_SOURCE_PATHS:
        path = AGENT_SRC / forbidden
        if path.is_dir() or path.is_file():
            errors.append(f"forbidden shadow-runtime path exists: {rel(path)}")
    framework_users = []
    for path in files:
        name = rel(path)
        modules = imports(path)
        if "deepagents" in modules:
            framework_users.append(name)
        shadow = defined(path) & FORBIDDEN_SHADOW_NAMES
        if shadow:
            errors.append(f"{name}: defines shadow framework names {sorted(shadow)}")
        text = path.read_text(encoding="utf-8")
        if "type: ignore" in text or "TYPE_CHECKING" in text:
            errors.append(f"{name}: contains a type-checking escape hatch")
        if "os.environ" in text and name != "worker/main.py":
            errors.append(f"{name}: reads os.environ outside worker/main.py")
        if any(module.startswith("kokoro_agent.worker") and module != "kokoro_agent.worker.services" for module in modules) and not name.startswith("worker/"):
            errors.append(f"{name}: core code imports worker transport")
    if framework_users != ["agent_factory.py"]:
        errors.append("DeepAgents import boundary drifted; expected only agent_factory.py, found " + str(framework_users))
    if any("create_deep_agent" in defined(path) for path in files):
        errors.append("GA defines a create_deep_agent shadow constructor")
    for path in files:
        if not rel(path).startswith("contract/"):
            continue
        offenders = {module for module in imports(path)
                     if module.startswith("kokoro_agent") and not module.startswith("kokoro_agent.contract")}
        if offenders:
            errors.append(f"{rel(path)}: contract imports inward modules {sorted(offenders)}")

def check_public_shapes(errors):
    control = AGENT_SRC / "contract/control.py"
    if control.is_file():
        tree = ast.parse(control.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if not isinstance(node, ast.ClassDef) or node.name not in {"RunRequest", "RunInput"}:
                continue
            fields = {statement.target.id for statement in node.body
                      if isinstance(statement, ast.AnnAssign) and isinstance(statement.target, ast.Name)}
            forbidden = fields & FORBIDDEN_PUBLIC_FIELDS
            if forbidden:
                errors.append(f"contract.{node.name} exposes forbidden selectors {sorted(forbidden)}")
    for path in (AGENT_SRC / "agents/definition.py", AGENT_SRC / "features/definition.py"):
        if not path.is_file():
            continue
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if not isinstance(node, ast.ClassDef) or node.name not in {"Agent", "Feature"}:
                continue
            fields = {statement.target.id for statement in node.body
                      if isinstance(statement, ast.AnnAssign) and isinstance(statement.target, ast.Name)}
            forbidden = fields & {"namespace", "thread_id", "deps", "binding", "release", "version"}
            if forbidden:
                errors.append(f"{path.relative_to(ROOT)}:{node.name} exposes runtime fields {sorted(forbidden)}")

def main(argv: list[str] | None = None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--manifest-only",
        action="store_true",
        help="validate Root-owned design artifacts when the private Agent checkout is not loaded",
    )
    args = parser.parse_args(argv)
    errors = []
    check_manifest(errors)
    check_source(errors, allow_missing=args.manifest_only)
    check_public_shapes(errors)
    markers(errors, AGENT_CARD, REQUIRED_AGENT_CARD_SECTIONS)
    markers(errors, AGENT_PACKAGE / "docs/agent/architecture.md",
            ("DeepAgents 是执行底座", "AgentFactory", "Feature", "create_deep_agent", "langgraph-swarm"))
    if AGENT_PACKAGE.joinpath("docs/agent/technical-plan.md").is_file():
        markers(errors, AGENT_PACKAGE / "docs/agent/technical-plan.md",
                ("严格以 DeepAgents 为 Agent runtime", "create_deep_agent", "AgentFactory", "DeepAgents 是唯一 Agent loop"))
        markers(errors, AGENT_PACKAGE / "docs/agent/technical-plan.md", REQUIRED_AGENT_PACKAGE_SECTIONS)
    elif not args.manifest_only:
        markers(errors, AGENT_PACKAGE / "docs/agent/technical-plan.md", REQUIRED_AGENT_PACKAGE_SECTIONS)
    for path in CURRENT_DOCS:
        links(errors, path)
        if not path.is_file():
            continue
        text = path.read_text(encoding="utf-8")
        for pattern in STALE_CURRENT_DOC_PATTERNS:
            match = pattern.search(text)
            if match:
                errors.append(f"{path.relative_to(ROOT)}: stale architecture wording {match.group(0)!r}")
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1
    print("backend design: DeepAgents-first architecture verified")
    print("Feature -> AgentFactory -> create_deep_agent / official Swarm")
    print("source tree, public shapes, manifest, and current documents: verified")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
