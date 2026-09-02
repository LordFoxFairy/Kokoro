# Kokoro Web Shared Extraction Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Create the independent `kokoro-web-shared` package repository by extracting the existing framework-free web package bootstrap without changing the current `kokoro` product behavior.

**Architecture:** The new repository owns a pnpm workspace containing versioned `@kokoro/*` packages. Product repositories consume package entry points and never import another product's source. The first extraction migrates the existing tested packages; React blocks, data adapters, and runtime blocks remain staged until their public interfaces are stable.

**Tech Stack:** Node.js 22, pnpm 11.2.2, TypeScript 5.9, Vitest 2, ESLint 9, framework-free TypeScript packages.

## Global Constraints

- Shared packages contain no tenant facts, private tokens, provider credentials, database clients, or product page composition.
- `@kokoro/web-core` has no React, CSS, network, or product dependency.
- `@kokoro/i18n` remains framework-free and receives product dictionaries from each consumer.
- Cross-repository consumption uses package versions and lockfiles; no Git submodule and no source-relative imports.
- The current `/Users/nako/WebstormProjects/github/thefoxfairy/Kokoro/kokoro` repository remains buildable and is not rewritten by this extraction.
- Package public APIs use the existing package names: `@kokoro/web-core`, `@kokoro/i18n`, and `@kokoro/tsconfig`.

---

### Task 1: Freeze the extraction inventory

**Files:**
- Read: `/Users/nako/WebstormProjects/github/thefoxfairy/Kokoro/kokoro/packages/README.md`
- Read: `/Users/nako/WebstormProjects/github/thefoxfairy/Kokoro/kokoro/packages/i18n/package.json`
- Read: `/Users/nako/WebstormProjects/github/thefoxfairy/Kokoro/kokoro/packages/web-core/package.json`
- Read: `/Users/nako/WebstormProjects/github/thefoxfairy/Kokoro/kokoro/packages/tsconfig/package.json`
- Create: `/Users/nako/WebstormProjects/github/thefoxfairy/Kokoro/docs/superpowers/specs/2026-09-02-kokoro-web-shared-inventory.md`

**Interfaces:**
- Produces: a file-by-file list of the three packages and an explicit list of files that stay in `kokoro`.

- [ ] **Step 1: Record the current package tree**

```bash
find kokoro/packages -type f -not -path '*/node_modules/*' | sort
```

- [ ] **Step 2: Record package entry points and scripts**

```bash
for f in kokoro/packages/{README.md,i18n/package.json,web-core/package.json,tsconfig/package.json}; do
  echo "### $f"
  sed -n '1,220p' "$f"
done
```

- [ ] **Step 3: Write the inventory with no unresolved entries**

The inventory must list `src`, tests, package metadata, lint/typecheck configuration, and generated files. Generated `*.tsbuildinfo` files are excluded from the new repository.

- [ ] **Step 4: Verify the inventory is clean**

```bash
grep -nE 'TODO|TBD|待定|待确认' docs/superpowers/specs/2026-09-02-kokoro-web-shared-inventory.md
```

Expected: no output and exit status 1.

- [ ] **Step 5: Commit the inventory**

```bash
git add docs/superpowers/specs/2026-09-02-kokoro-web-shared-inventory.md
git commit -m "docs: record shared package extraction inventory"
```

### Task 2: Create the independent shared repository

**Files:**
- Create: `/Users/nako/WebstormProjects/github/thefoxfairy/Kokoro/kokoro-web-shared/.gitignore`
- Create: `/Users/nako/WebstormProjects/github/thefoxfairy/Kokoro/kokoro-web-shared/package.json`
- Create: `/Users/nako/WebstormProjects/github/thefoxfairy/Kokoro/kokoro-web-shared/pnpm-workspace.yaml`
- Create: `/Users/nako/WebstormProjects/github/thefoxfairy/Kokoro/kokoro-web-shared/README.md`
- Copy: `/Users/nako/WebstormProjects/github/thefoxfairy/Kokoro/kokoro/packages/i18n` → `/Users/nako/WebstormProjects/github/thefoxfairy/Kokoro/kokoro-web-shared/packages/i18n`
- Copy: `/Users/nako/WebstormProjects/github/thefoxfairy/Kokoro/kokoro/packages/web-core` → `/Users/nako/WebstormProjects/github/thefoxfairy/Kokoro/kokoro-web-shared/packages/web-core`
- Copy: `/Users/nako/WebstormProjects/github/thefoxfairy/Kokoro/kokoro/packages/tsconfig` → `/Users/nako/WebstormProjects/github/thefoxfairy/Kokoro/kokoro-web-shared/packages/tsconfig`

**Interfaces:**
- Produces: an independent Git repository with the same three public package names and no product import path.

- [ ] **Step 1: Create the repository directory and Git metadata**

```bash
mkdir -p kokoro-web-shared/packages
git init -b main kokoro-web-shared
```

- [ ] **Step 2: Copy only package source and package metadata**

```bash
cp -R kokoro/packages/i18n kokoro-web-shared/packages/i18n
cp -R kokoro/packages/web-core kokoro-web-shared/packages/web-core
cp -R kokoro/packages/tsconfig kokoro-web-shared/packages/tsconfig
find kokoro-web-shared -name '*.tsbuildinfo' -delete
```

- [ ] **Step 3: Add the root workspace contract**

`package.json` must set `private: true`, `packageManager: "pnpm@11.2.2"`, `engines.node: ">=22 <23"`, and scripts for `lint`, `typecheck`, and `test` that run the package-level checks. `pnpm-workspace.yaml` must include only `packages/*`.

- [ ] **Step 4: Add repository boundary documentation**

`README.md` must state that package facts are public browser-safe contracts only; product routes, brand tokens, provider adapters, BFF URLs, and tenant/runtime identity stay in consuming products or service owners.

- [ ] **Step 5: Verify repository isolation**

```bash
git -C kokoro-web-shared status --short
git -C kokoro-web-shared log --oneline -1 || true
grep -RInE 'kokoro/src|/Users/nako|KOKORO_DOMAIN|token|secret' kokoro-web-shared/packages --exclude='*.lock' || true
```

Expected: no source import points into the product and no credential or deployment value is present.

- [ ] **Step 6: Commit the independent repository baseline**

```bash
git -C kokoro-web-shared add .
git -C kokoro-web-shared commit -m "chore: create Kokoro web shared package repository"
```

### Task 3: Validate all extracted packages

**Files:**
- Modify: `/Users/nako/WebstormProjects/github/thefoxfairy/Kokoro/kokoro-web-shared/package.json` only if a check script needs correction
- Test: `/Users/nako/WebstormProjects/github/thefoxfairy/Kokoro/kokoro-web-shared/packages/i18n/test/i18n.test.ts`

**Interfaces:**
- Consumes: package source copied in Task 2.
- Produces: repeatable checks proving the extracted packages can build independently.

- [ ] **Step 1: Install the shared repository dependencies**

```bash
pnpm --dir kokoro-web-shared install
```

- [ ] **Step 2: Run package checks**

```bash
pnpm --dir kokoro-web-shared lint
pnpm --dir kokoro-web-shared typecheck
pnpm --dir kokoro-web-shared test
```

Expected: all commands exit 0; the i18n suite reports interpolation, negotiation, fallback, and translation coverage.

- [ ] **Step 3: Check public package names**

```bash
node -e "for (const p of ['i18n','web-core','tsconfig']) console.log(require('./kokoro-web-shared/packages/'+p+'/package.json').name)"
```

Expected:

```text
@kokoro/i18n
@kokoro/web-core
@kokoro/tsconfig
```

- [ ] **Step 4: Commit the validation metadata**

```bash
git -C kokoro-web-shared add package.json pnpm-workspace.yaml README.md pnpm-lock.yaml
git -C kokoro-web-shared commit -m "test: validate extracted web packages"
```

### Task 4: Keep the original product stable

**Files:**
- Read: `/Users/nako/WebstormProjects/github/thefoxfairy/Kokoro/kokoro/package.json`
- Test: existing `/Users/nako/WebstormProjects/github/thefoxfairy/Kokoro/kokoro` checks

**Interfaces:**
- Consumes: original `kokoro` workspace package bootstrap.
- Produces: evidence that extraction is additive and does not alter the existing product.

- [ ] **Step 1: Confirm original package files are unchanged**

```bash
git -C kokoro diff --exit-code -- packages
```

Expected: exit 0.

- [ ] **Step 2: Run the original package checks**

```bash
pnpm --dir kokoro --filter @kokoro/i18n test
pnpm --dir kokoro --filter @kokoro/web-core typecheck
```

Expected: exit 0.

- [ ] **Step 3: Commit only if the original repository has no extraction edits**

```bash
git -C kokoro status --short -- packages
```

Expected: no output.

