# Usage Guide

Use `final-review` when a change is ready for final review and you want Codex to review, validate, fix, and re-check the result.

## Commands

### Uncommitted Code

```text
$final-review 未提交的代码
```

Reviews:

- Staged changes
- Unstaged changes
- Small safe untracked source files

### Staged Code

```text
$final-review 暂存的代码
```

Reviews only:

- `git diff --cached`

If unstaged or untracked files exist, the workflow reports contamination risk and does not treat dirty-worktree checks as staged-only proof.

### Merge Requests

```text
$final-review 这个mr 123
$final-review 这个mr https://gitlab.example.com/group/project/-/merge_requests/123
```

Uses `glab mr view` and `glab mr diff` when available.

### Pull Requests

```text
$final-review 这个pr 123
$final-review 这个pr https://github.com/owner/repo/pull/123
```

Uses `gh pr view` and `gh pr diff` when available.

## Review Flow

1. Resolve review scope.
2. Collect the selected diff and context.
3. Run safe baseline checks when discoverable.
4. Run two review perspectives:
   - General Codex code review
   - gstack-style structural review
5. Build a finding ledger.
6. Validate each finding with code or runtime evidence.
7. Fix only accepted findings.
8. Run relevant checks.
9. Perform impact review.
10. Run final full review.
11. Report fixed, rejected, deferred, and remaining findings.

## Subagent Permission

Codex tool rules may require explicit permission before opening subagents. When needed, the workflow asks:

```text
允许我为这次 final-review 开两个独立只读子会话做 review 吗？
```

Answer `允许` to use independent reviewers.

If you answer `不允许`, or subagents are not available, Codex runs two local review passes and reports:

```text
Review independence: local two-pass fallback, no independent subagents used.
```

## Finding Statuses

The workflow uses a ledger with these statuses:

- `needs-evidence`: plausible but not proven
- `accepted`: proven real and eligible for fixing
- `fixed`: accepted and fixed
- `rejected`: false, unsupported, style-only, or unreachable
- `deferred`: real but outside the requested review/fix scope

Only `accepted` findings with concrete evidence may be fixed.

## Cycle Limit

The workflow stops after three cycles unless you explicitly ask it to continue:

- Cycle 0: baseline check fixes
- Cycle 1: initial full review
- Cycle 2: impact review
- Cycle 3: final full review

