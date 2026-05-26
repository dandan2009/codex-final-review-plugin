---
name: final-review
description: Run a final, multi-pass code review workflow for important changes. Use when the user invokes `$final-review`, `$final-review uncommitted`, `$final-review staged`, `$final-review pr xxx`, `$final-review mr xxx`, `$final-review 未提交的代码`, `$final-review 暂存的代码`, `$final-review 这个mr xxx`, `$final-review 这个pr xxx`, or asks to final-review uncommitted changes, staged changes, a merge request, or a pull request. With no explicit scope, default to uncommitted changes. The workflow gathers the requested diff, runs independent review passes when permitted, validates findings, explains whether each issue is real and how it happens, proposes fixes, waits for user confirmation, then fixes only approved issues.
---

# Final Review

## Overview

Run the user's end-of-development review loop without manual copy-paste between sessions. This skill is a workflow controller: gather the right diff, run the Codex review perspective plus real gstack-review when available, validate every finding, then stop before editing code to explain whether each issue exists, how it happens, and the proposed fix. Only after the user confirms the modification plan should the workflow edit files, run checks, perform impact review, and finish with a final full review.

Default invocation means: review uncommitted code and use two independent read-only sub-sessions for cross-review when the active Codex runtime allows it. Treat `$final-review`, `Final Review`, plugin default prompts, and `未提交的代码` prompts as the user's explicit request for this default mode.

Do not ask an extra permission question before opening the two default reviewer sub-sessions. Only avoid sub-sessions when the user explicitly says not to use them, the active Codex runtime/tool rules block them, or subagents are unavailable. In those cases, run the same two review perspectives locally and clearly report that independence was degraded.

## Scope Routing

First resolve what code is being reviewed. Do not ask for scope when the user invokes `$final-review`, clicks a `Final Review` default prompt, or says `未提交的代码`; default to uncommitted changes.

| User command | Review scope |
| --- | --- |
| `$final-review` | Default: all local uncommitted changes, using independent cross-review when allowed. |
| `Final Review` | Default: all local uncommitted changes, using independent cross-review when allowed. |
| `$final-review uncommitted` | All local uncommitted changes: staged, unstaged, and untracked files. |
| `$final-review staged` | Staged changes only. Protect this scope from unstaged/untracked contamination. |
| `$final-review mr xxx` | The specified merge request by URL, number, branch, or identifier. Review the MR diff against its target branch. |
| `$final-review pr xxx` | The specified pull request by URL, number, branch, or identifier. Review the PR diff against its base branch. |
| `$final-review 未提交的代码` | All local uncommitted changes: staged, unstaged, and untracked files. |
| `$final-review 暂存的代码` | Staged changes only. Protect this scope from unstaged/untracked contamination. |
| `$final-review 这个mr xxx` | The specified merge request by URL, number, branch, or identifier. Review the MR diff against its target branch. |
| `$final-review 这个pr xxx` | The specified pull request by URL, number, branch, or identifier. Review the PR diff against its base branch. |

Also treat `pending changes`, `working tree`, `worktree`, `uncommitted`, `default`, `默认`, `未提交`, `未提交的代码`, `未commit的代码`, `cached changes`, `merge request`, `pull request`, `这个MR`, `这个PR`, and `staged changes` as equivalent wording. If the scope is still ambiguous after applying the default, ask one short clarifying question. If the user says only `this mr`, `this pr`, `这个 mr`, or `这个 pr`, first try to discover an open MR/PR for the current branch.

## Diff Collection

### Uncommitted Scope

Collect:

- `git status --short`
- `git diff --stat`
- `git diff`
- `git diff --cached`
- Small untracked source files, excluding ignored files, secrets, generated output, lockfiles unless relevant, and large binaries

Use the combined local worktree as the review target.

### Staged Scope

Collect:

- `git status --short`
- `git diff --cached --stat`
- `git diff --cached`

If unstaged or untracked files exist, report the contamination risk before checks or fixes. Default behavior:

- Review only the staged diff.
- Do not run checks against the dirty worktree as proof that staged-only code passes.
- Prefer a temporary isolated worktree when checks are needed: create it outside the repo, apply the staged patch there, run checks there, and remove it when done.
- If isolated staged-only checks are impractical, mark checks as skipped or contaminated instead of silently trusting them.

Only edit files in the real worktree after a finding is confirmed real and the user approves the modification plan. If the fix modifies staged-scope files, tell the user whether the new fix is staged or unstaged at the end.

### MR/PR Scope

Prefer native repo tooling in this order:

1. URL-specific tool if the URL identifies the host and repo.
2. GitHub CLI for GitHub PRs:
   - `gh pr view <id-or-url> --json number,title,baseRefName,headRefName,headRepository,headRepositoryOwner,url,state,isDraft`
   - `gh pr diff <id-or-url>`
3. GitLab CLI for GitLab MRs:
   - `glab mr view <id-or-url>`
   - `glab mr diff <id-or-url>`
4. GitHub connector, GitLab MCP, or project-native review tooling if available.
5. Current-branch discovery with `gh pr status`, `gh pr view`, `glab mr list`, or `glab mr view`.

For MR/PR review, the selected target is the remote MR/PR diff against its target/base branch, not unrelated local worktree changes. If local checkout is needed to run tests or fix issues, first identify base/head, then work on the corresponding local branch or a temporary worktree. If the MR/PR cannot be resolved uniquely, ask one short clarifying question.

## Baseline Checks

Before review, identify relevant checks from project files and docs:

- Typecheck
- Lint
- Unit or focused tests
- Build/smoke checks for frontend changes

Record the original selected diff and baseline check result before making any fixes. If baseline checks fail:

- Do not fix the failure during the initial review phase.
- Treat this as a candidate finding in the ledger.
- Preserve the original failure and explain whether it is caused by the target diff, unrelated, contaminated, or too expensive to diagnose.
- If the failure is unrelated, contaminated, or expensive to diagnose, include it in the ledger and continue.

## Review Passes

Run two review perspectives over the same selected diff/context.

### Independent Subagents

Use two independent read-only subagents by default when the active tool rules allow it. The default final-review invocation is already authorization for these reviewer subagents; do not ask a separate permission question. Each reviewer must receive the same diff/context, must not see the other reviewer's output, and must not edit target repository files.

Reviewer A: general Codex code review.

Focus on bugs, regressions, edge cases, test gaps, data-flow problems, API contract issues, concurrency/state bugs, and maintainability risks. Ignore style-only nits unless they hide a real defect.

Reviewer B: real gstack-review when available.

Prefer the active gstack `review` / `gstack-review` skill when Codex exposes it and current tool rules allow it. Treat it as the second reviewer from the user's original workflow. gstack may write local state under `~/.gstack`; that is acceptable only when it does not edit the target repository and the active tool rules allow those local side effects.

If real gstack-review is unavailable, blocked, or unsafe under the current tool rules, run this built-in gstack-style structural checklist instead:

- SQL safety, migrations, transactions, and data integrity
- Authorization, tenancy boundaries, and permission checks
- LLM trust boundaries, prompt injection surfaces, and tool/output validation
- Conditional side effects, retries, idempotency, and rollback behavior
- External API contracts, webhooks, queues, and async jobs
- Rollout risks, feature flags, observability, and failure modes
- Tests that would catch the highest-risk failure

When this fallback is used, the final report must include:

```text
Reviewer B: gstack-style fallback, real gstack-review unavailable/not used.
```

### Fallback Without Subagents

If subagents are unavailable or not authorized, run both reviewer perspectives locally as separate passes. Do not pretend they were independent. The final report must include:

```text
Review independence: local two-pass fallback, no independent subagents used.
```

## Finding Format

Require every finding to use this shape:

```text
id:
reviewer: codex | gstack-review | gstack-style | local | check
cycle:
severity: critical | high | medium | low
file:
line:
claim:
mechanism:
evidence:
suggested_fix:
test_needed:
status: needs-evidence | confirmed-real | approved | fixed | rejected | deferred
```

Reject or downgrade findings that lack a concrete file/line, execution path, or violated contract unless the risk is obvious from the diff.

## Ledger Rules

Maintain one ledger in the conversation. If the review spans multiple cycles or context loss is likely, also write a temporary JSON or Markdown ledger under `/tmp`, not inside the repo, unless the user asks for a committed artifact.

Allowed statuses:

- `needs-evidence`: plausible but not proven.
- `confirmed-real`: proven real, explained, and waiting for user approval.
- `approved`: confirmed real and approved by the user for fixing.
- `fixed`: approved and fixed.
- `rejected`: false, unsupported, only stylistic, or not reachable.
- `deferred`: real but outside the requested review/fix scope.

Only `approved` findings may be fixed. Every status transition must keep the reason. Deduplicate by root cause, not by wording.

Cycle rules:

- Cycle 0: baseline check findings before reviewer findings.
- Cycle 1: initial full review, validation, explanation, and modification plan. Stop here and wait for user confirmation before editing files.
- Cycle 2: user-approved fixes, relevant checks, and impact review.
- Cycle 3: final full review. New critical/high findings must be explained with a proposed fix and require user confirmation before editing.
- Stop after cycle 3 unless the user explicitly asks to continue.

Final-review critical/high findings count toward the same three-cycle budget. Medium/low final-review findings should be proposed for fixing only when they are clearly real, low risk to patch, and covered by focused checks; otherwise report them.

## Validate Findings

For each finding, inspect the code and decide whether it is real. A real finding needs at least one of:

- Direct code evidence
- A failing or missing test that demonstrates the risk
- A reachable control/data-flow path
- A violated API, schema, permission, persistence, or security contract

When rejecting a finding, record the reason briefly. Do not argue from intent alone; use code or runtime behavior.

## Explain And Confirm

After reviewer passes and validation, do not edit files yet. Produce a review decision report for the user and wait for confirmation.

For every non-rejected finding, explain:

- Whether the issue truly exists.
- The exact code path, data flow, state transition, permission path, or API contract that makes it happen.
- The user-visible or production impact if it ships unchanged.
- The smallest safe modification plan.
- Which files would be edited.
- Which tests or checks should verify the fix.
- Any tradeoffs or product decisions the user must approve.

Use this status mapping:

- `confirmed-real`: the issue exists and has a proposed fix, but no files may be edited yet.
- `deferred`: the issue exists but is outside the current review/fix scope or needs a broader decision.
- `rejected`: the issue does not exist, lacks evidence, is unreachable, or is only stylistic.

End the initial review phase with a clear confirmation gate. In Chinese conversations, say:

```text
请确认要修复哪些问题。你确认后，我再开始修改代码、运行检查，并做影响面复查。
```

Do not proceed to code edits until the user explicitly confirms the plan, for example `确认修复`, `修复第 1 个`, `按方案修复`, `全部修复`, or an equivalent approval.

## Fix Approved Issues

Batch approved findings by root cause and fix them with the smallest coherent patches. Preserve unrelated user changes and avoid broad refactors. Add or update focused tests when the issue is behavioral, security-sensitive, or likely to regress.

Run relevant checks after each coherent patch batch. If a fix would require a product decision, schema migration, risky architecture change, secret, credential, or production access, stop and report the choice instead of guessing.

## Impact Review

After fixes, review not only the new diff lines but also the affected modules, callers, data flow, permissions, state transitions, and tests. Specifically answer:

- Did the fix change behavior on a path that previously worked?
- Did the fix invalidate any earlier confirmed-real/rejected review conclusion?
- Did the fix introduce a new missing test or contract mismatch?
- Did the selected review scope change because of the fix?

Do not automatically fix real impact-review issues. Explain them with proposed fixes and ask for confirmation before editing, unless they are direct consequences of an already approved fix plan and remain within that approval.

## Final Full Review

Run one final full review over the final selected scope. Prefer the same two-perspective pattern. Use independent subagents only if still allowed by active tool rules and the user's request.

If serious findings remain at the cycle limit, stop with a residual-risk report instead of looping. Any newly found final-review issue requires the same explanation and confirmation gate before fixing.

## Output

Finish with:

- Scope reviewed
- Whether independent subagents were used or local fallback was used
- Checks run and results, including skipped or contaminated checks
- Confirmed-real findings awaiting approval, when in the initial review phase
- Approved findings fixed, when in the fix phase
- Rejected findings and why
- Deferred or remaining risks
- Proposed modification plan and verification plan before any edits
- Files changed by the skill
