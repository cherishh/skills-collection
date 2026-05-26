---
name: check-cherry-pick
description: Compare the latest `release-*` branch with `main` and identify release-only commits that have not been cherry-picked back yet. Use when checking release branch drift, validating hotfix backports, auditing whether release fixes made it back to `main`, or preparing post-release sync work.
---

# Check Cherry Pick

Use this skill to answer one question precisely: which commits exist on the latest release branch but do not yet exist on `main` as equivalent patches.

## Workflow

1. Confirm the repository uses `main` plus `release-*` branches.
2. Detect the latest release branch.
3. Compare the release branch against `main` with patch equivalence, not SHA equality.
4. Report only the commits that are still release-only.
5. Call out any commits that are release tags, release bookkeeping, or intentional non-backports.

## Detect the Latest Release Branch

Prefer the bundled script:

```bash
python3 scripts/report_release_only_commits.py
```

If the user names a branch explicitly, pass it:

```bash
python3 scripts/report_release_only_commits.py --release release-1.20
```

If you need to do it manually, list release branches, normalize away `origin/`, sort by version, and pick the latest one.

## Compare Correctly

Use `git cherry -v main <release-branch>` semantics, not plain `git log main..<release>`.

- `git log main..<release>` shows commits reachable from release and not from `main` by SHA ancestry.
- `git cherry -v main <release>` shows patch equivalence.
- Lines prefixed with `-` are already present on `main` as equivalent patches, usually via cherry-pick.
- Lines prefixed with `+` are still release-only and are the commits you want.

This matters because the same fix usually has different SHAs on `release-*` and `main`.

## Report Format

When summarizing results:

- Name the compared branches.
- Mention the merge base if it is helpful.
- List the release-only commits as `sha subject`.
- Keep the list ordered from oldest to newest unless the user asks otherwise.
- Separate probable product fixes from obvious release bookkeeping when that distinction is useful.

If there are no `+` commits, say explicitly that the latest release branch appears fully backported to `main`.

## Cross-Checks

Use these only when needed:

```bash
git log --oneline main..<release-branch>
git log --oneline <release-branch>..main
git merge-base main <release-branch>
```

Use `git log` to inspect context. Use `git cherry` to decide whether a release commit is still missing from `main`.

## Bundled Script

Use the bundled helper to avoid re-deriving the branch selection and `git cherry` filtering logic:

```bash
python3 scripts/report_release_only_commits.py [--release release-x.y] [--main main]
```

The script:

- auto-detects the latest `release-*` branch when `--release` is omitted
- deduplicates local and `origin/` release branch names
- prints only release-only commits that have not been backported to `main`
- exits successfully with an explicit message when none are pending
