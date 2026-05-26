# Usage Guide

Use `final-review` when a change is ready for final review and you want Codex to review, validate, explain, wait for confirmation, then fix and re-check the approved result.

## Commands

### Default

```text
$final-review
```

Reviews all local uncommitted code by default: staged changes, unstaged changes, and small safe untracked source files. It also uses two independent read-only sub-sessions for cross-review when the active Codex runtime allows it, without asking an extra permission question.

### Uncommitted Code

```text
$final-review uncommitted
```

Reviews:

- Staged changes
- Unstaged changes
- Small safe untracked source files

### Staged Code

```text
$final-review staged
```

Reviews only:

- `git diff --cached`

If unstaged or untracked files exist, the workflow reports contamination risk and does not treat dirty-worktree checks as staged-only proof.

### Merge Requests

```text
$final-review mr 123
$final-review mr https://gitlab.example.com/group/project/-/merge_requests/123
```

Uses `glab mr view` and `glab mr diff` when available.

### Pull Requests

```text
$final-review pr 123
$final-review pr https://github.com/owner/repo/pull/123
```

Uses `gh pr view` and `gh pr diff` when available.

## Chinese Aliases

The plugin also supports the original Chinese command aliases:

```text
$final-review 未提交的代码
$final-review 暂存的代码
$final-review 这个mr 123
$final-review 这个pr 123
```

## Review Flow

1. Resolve review scope.
   - If no scope is provided, default to uncommitted code.
2. Collect the selected diff and context.
3. Run safe baseline checks when discoverable.
4. Run two review perspectives:
   - General Codex code review
   - Real gstack-review when available, otherwise the built-in gstack-style structural review fallback
5. Build a finding ledger.
6. Validate each finding with code or runtime evidence.
7. Explain whether each issue exists, how it happens, impact, proposed fix, files to edit, and verification plan.
8. Stop and wait for user confirmation before editing files.
9. Fix only user-approved findings.
10. Run relevant checks.
11. Perform impact review.
12. Run final full review.
13. Report fixed, rejected, deferred, and remaining findings.

## Subagent Behavior

The default `final-review` invocation is treated as permission to use two independent read-only reviewer sub-sessions. The workflow should not ask an extra permission question before opening them.

If subagents are not available or are blocked by the active Codex runtime, Codex runs two local review passes and reports:

```text
Review independence: local two-pass fallback, no independent subagents used.
```

## gstack-review Dependency

For the exact original workflow, install gstack and make sure Codex can see its `review` / `gstack-review` skill. `final-review` treats that as the second reviewer.

If gstack-review is unavailable or blocked by the current Codex environment, the command still runs the second pass with a built-in gstack-style checklist and reports:

```text
Reviewer B: gstack-style fallback, real gstack-review unavailable/not used.
```

## Finding Statuses

The workflow uses a ledger with these statuses:

- `needs-evidence`: plausible but not proven
- `confirmed-real`: proven real, explained, and waiting for user approval
- `approved`: confirmed real and approved by the user for fixing
- `fixed`: approved and fixed
- `rejected`: false, unsupported, style-only, or unreachable
- `deferred`: real but outside the requested review/fix scope

Only `approved` findings may be fixed.

## Cycle Limit

The workflow stops after three cycles unless you explicitly ask it to continue:

- Cycle 0: baseline check findings
- Cycle 1: initial full review, validation, explanation, and modification plan
- Cycle 2: user-approved fixes, relevant checks, and impact review
- Cycle 3: final full review
