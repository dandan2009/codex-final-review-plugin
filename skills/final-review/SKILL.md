---
name: final-review
description: Run a final, multi-pass code review workflow for important changes. Use when the user invokes `$final-review uncommitted`, `$final-review staged`, `$final-review pr xxx`, `$final-review mr xxx`, `$final-review 未提交的代码`, `$final-review 暂存的代码`, `$final-review 这个mr xxx`, `$final-review 这个pr xxx`, or asks to final-review uncommitted changes, staged changes, a merge request, or a pull request. The workflow gathers the requested diff, runs independent review passes when permitted, validates findings, fixes true issues, reruns relevant tests, performs impact review, and finishes with a final full review.
---

# Final Review

## Overview

Run the user's end-of-development review loop without manual copy-paste between sessions. This skill is a workflow controller: gather the right diff, run two review perspectives, validate every finding, fix only true issues, and finish with an impact review plus final full review.

Do not let this skill text override active tool rules. If the current Codex runtime requires the user to explicitly authorize subagents and the user's request did not already include wording such as `subagent`, `sub-session`, `independent reviewer`, `子会话`, `子 agent`, `独立 reviewer`, or equivalent, ask one short permission question before review. Ask in the user's language; default to English:

```text
May I open two independent read-only sub-sessions for this final-review?
```

If the user grants permission, spawn the two read-only reviewer subagents. If the user declines, cannot answer, or subagents are unavailable, run the same two review perspectives locally and clearly report that independence was degraded.

## Scope Routing

First resolve what code is being reviewed.

| User command | Review scope |
| --- | --- |
| `$final-review uncommitted` | All local uncommitted changes: staged, unstaged, and untracked files. |
| `$final-review staged` | Staged changes only. Protect this scope from unstaged/untracked contamination. |
| `$final-review mr xxx` | The specified merge request by URL, number, branch, or identifier. Review the MR diff against its target branch. |
| `$final-review pr xxx` | The specified pull request by URL, number, branch, or identifier. Review the PR diff against its base branch. |
| `$final-review 未提交的代码` | All local uncommitted changes: staged, unstaged, and untracked files. |
| `$final-review 暂存的代码` | Staged changes only. Protect this scope from unstaged/untracked contamination. |
| `$final-review 这个mr xxx` | The specified merge request by URL, number, branch, or identifier. Review the MR diff against its target branch. |
| `$final-review 这个pr xxx` | The specified pull request by URL, number, branch, or identifier. Review the PR diff against its base branch. |

Also treat `pending changes`, `working tree`, `worktree`, `cached changes`, `merge request`, `pull request`, `这个MR`, `这个PR`, `staged changes`, and `未commit的代码` as equivalent wording. If the scope is ambiguous, ask one short clarifying question. If the user says only `this mr`, `this pr`, `这个 mr`, or `这个 pr`, first try to discover an open MR/PR for the current branch.

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

Only edit files in the real worktree after a finding is accepted. If the fix modifies staged-scope files, tell the user whether the new fix is staged or unstaged at the end.

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

- Fix immediately only when the failure is clearly caused by the target diff and the fix is small.
- Treat this as cycle 0 in the ledger.
- Preserve the original failure, the fix, and the post-fix check result for reviewers.
- If the failure is unrelated, contaminated, or expensive to diagnose, include it in the ledger and continue.

## Review Passes

Run two review perspectives over the same selected diff/context.

### Independent Subagents

Use two independent read-only subagents only when the active tool rules allow it. If authorization is missing but can be requested, ask the one-line permission question from the Overview before starting reviewer passes. Each reviewer must receive the same diff/context, must not see the other reviewer's output, and must not edit files.

Reviewer A: general Codex code review.

Focus on bugs, regressions, edge cases, test gaps, data-flow problems, API contract issues, concurrency/state bugs, and maintainability risks. Ignore style-only nits unless they hide a real defect.

Reviewer B: gstack-style structural review.

Do not invoke the real gstack `review` skill inside a read-only subagent by default, because it may write session/config/analytics files or prompt repository changes. Instead, use this checklist:

- SQL safety, migrations, transactions, and data integrity
- Authorization, tenancy boundaries, and permission checks
- LLM trust boundaries, prompt injection surfaces, and tool/output validation
- Conditional side effects, retries, idempotency, and rollback behavior
- External API contracts, webhooks, queues, and async jobs
- Rollout risks, feature flags, observability, and failure modes
- Tests that would catch the highest-risk failure

Only run the real gstack `review` skill if the user explicitly asks for real gstack-review and accepts its side effects. Keep that execution out of read-only reviewer subagents.

### Fallback Without Subagents

If subagents are unavailable or not authorized, run both reviewer perspectives locally as separate passes. Do not pretend they were independent. The final report must include:

```text
Review independence: local two-pass fallback, no independent subagents used.
```

## Finding Format

Require every finding to use this shape:

```text
id:
reviewer: codex | gstack-style | local | check
cycle:
severity: critical | high | medium | low
file:
line:
claim:
mechanism:
evidence:
suggested_fix:
test_needed:
status: needs-evidence
```

Reject or downgrade findings that lack a concrete file/line, execution path, or violated contract unless the risk is obvious from the diff.

## Ledger Rules

Maintain one ledger in the conversation. If the review spans multiple cycles or context loss is likely, also write a temporary JSON or Markdown ledger under `/tmp`, not inside the repo, unless the user asks for a committed artifact.

Allowed statuses:

- `needs-evidence`: plausible but not proven.
- `accepted`: proven real and eligible for fixing.
- `fixed`: accepted and fixed.
- `rejected`: false, unsupported, only stylistic, or not reachable.
- `deferred`: real but outside the requested review/fix scope.

Only `accepted` findings with concrete evidence may be fixed. Every status transition must keep the reason. Deduplicate by root cause, not by wording.

Cycle rules:

- Cycle 0: baseline check fixes before reviewer findings.
- Cycle 1: initial full review and fixes.
- Cycle 2: impact review and fixes.
- Cycle 3: final full review and only critical/high fixes by default.
- Stop after cycle 3 unless the user explicitly asks to continue.

Final-review critical/high findings count toward the same three-cycle budget. Medium/low final-review findings should be fixed only when they are clearly real, low risk to patch, and covered by focused checks; otherwise report them.

## Validate Findings

For each finding, inspect the code and decide whether it is real. A real finding needs at least one of:

- Direct code evidence
- A failing or missing test that demonstrates the risk
- A reachable control/data-flow path
- A violated API, schema, permission, persistence, or security contract

When rejecting a finding, record the reason briefly. Do not argue from intent alone; use code or runtime behavior.

## Fix True Issues

Batch accepted findings by root cause and fix them with the smallest coherent patches. Preserve unrelated user changes and avoid broad refactors. Add or update focused tests when the issue is behavioral, security-sensitive, or likely to regress.

Run relevant checks after each coherent patch batch. If a fix would require a product decision, schema migration, risky architecture change, secret, credential, or production access, stop and report the choice instead of guessing.

## Impact Review

After fixes, review not only the new diff lines but also the affected modules, callers, data flow, permissions, state transitions, and tests. Specifically answer:

- Did the fix change behavior on a path that previously worked?
- Did the fix invalidate any earlier accepted/rejected review conclusion?
- Did the fix introduce a new missing test or contract mismatch?
- Did the selected review scope change because of the fix?

Fix real impact-review issues before final review when still inside the cycle budget.

## Final Full Review

Run one final full review over the final selected scope. Prefer the same two-perspective pattern. Use independent subagents only if still allowed by active tool rules and the user's request.

If serious findings remain at the cycle limit, stop with a residual-risk report instead of looping.

## Output

Finish with:

- Scope reviewed
- Whether independent subagents were used or local fallback was used
- Checks run and results, including skipped or contaminated checks
- Accepted findings fixed
- Rejected findings and why
- Deferred or remaining risks
- Files changed by the skill
