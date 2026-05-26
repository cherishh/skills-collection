---
name: cp
description: Commit all current changes, push the current branch, and for release-* branches ask whether to cherry-pick the new commit back to main.
---

# CP

Use this skill when the user asks to run `cp`, commit and push all current changes, or perform the commit-push workflow with optional release-to-main cherry-pick.

## Workflow

1. Inspect the working tree with `git status --short` and the current branch with `git branch --show-current`.
2. Stage all current changes with `git add -A`.
3. Commit the staged changes. Choose a specific commit message that names both the affected area and the concrete outcome if the user did not provide one.
   - Use Conventional Commit style with one of these prefixes: `feat`, `fix`, `chore`, `refactor`, `docs`, `ci`, `test`, `perf`, or `build`.
   - Prefer scoped messages in the form `type(scope): outcome`, for example `fix(kb): restore local file path lookup after Electron upgrade`.
   - The scope should be the smallest meaningful product, module, workflow, or infrastructure area, such as `kb`, `attachments`, `settings`, `auth`, `i18n`, `build`, `release`, etc. (No need to limit to these illustrated examples.)
   - Do not use a bare prefix such as `feat: ...` or `fix: ...` when a reasonable scope can be inferred from the diff. Allow bare prefixes as a fallback when the affected area is not clear or the user explicitly asks for a terse message.
   - Avoid terse messages like `fix bug` or `update files`; the message should make the user-facing or technical result clear.
4. Capture the new commit SHA with `git rev-parse HEAD`.
5. Push the current branch with `git push origin <current-branch>`.
6. If the current branch name matches `release-*`, ask the user exactly:

   `当前在 release 分支，是否要 cherry-pick 这个 commit 到 main？`

7. If the user agrees:
   - Switch to `main`.
   - Pull the latest `main`.
   - Cherry-pick the captured commit SHA.
   - Push `main`.
   - Switch back to the original release branch.
8. If the user refuses, stop after the release branch push.
9. If the current branch is `main`, starts with `feat/`, starts with `fix/`, or is any other non-`release-*` branch, do not ask the cherry-pick question and stop after pushing.

## Guardrails

- Do not run destructive git commands such as `git reset --hard` or `git checkout --` unless the user explicitly asks.
- If there are no staged or unstaged changes, do not create an empty commit unless the user explicitly asks.
- If commit, push, pull, or cherry-pick fails, stop and report the failure with the current branch and relevant git status.
- If cherry-pick creates conflicts, stop on `main`, report the conflicted files, and do not switch back until the conflict is resolved or the user gives instructions.
