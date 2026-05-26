#!/usr/bin/env python3

import argparse
import re
import subprocess
import sys
from typing import Iterable


def run_git(args: list[str]) -> str:
    result = subprocess.run(['git', *args], capture_output=True, text=True)
    if result.returncode != 0:
        message = result.stderr.strip() or result.stdout.strip() or f"git {' '.join(args)} failed"
        raise RuntimeError(message)
    return result.stdout.strip()


def normalize_release_branch(ref: str) -> str:
    return re.sub(r'^origin/', '', ref.strip())


def version_key(branch: str) -> list[object]:
    parts = re.split(r'(\d+)', branch)
    key: list[object] = []
    for part in parts:
        if not part:
            continue
        key.append(int(part) if part.isdigit() else part)
    return key


def detect_latest_release_branch() -> str:
    raw_refs = run_git(['for-each-ref', '--format=%(refname:short)', 'refs/heads/release-*', 'refs/remotes/origin/release-*'])
    refs = [normalize_release_branch(ref) for ref in raw_refs.splitlines() if ref.strip()]
    branches = sorted({ref for ref in refs if ref.startswith('release-')}, key=version_key)
    if not branches:
        raise RuntimeError('No release-* branches found locally or under origin/.')
    return branches[-1]


def parse_cherry_output(lines: Iterable[str]) -> list[str]:
    commits: list[str] = []
    for line in lines:
        if line.startswith('+ '):
            commits.append(line[2:])
    return commits


def main() -> int:
    parser = argparse.ArgumentParser(
        description='List commits that exist on a release branch but are not yet cherry-picked back to main.'
    )
    parser.add_argument('--release', help='Release branch to compare, for example release-1.20')
    parser.add_argument('--main', default='main', help='Main branch name (default: main)')
    args = parser.parse_args()

    try:
      release_branch = args.release or detect_latest_release_branch()
      merge_base = run_git(['merge-base', args.main, release_branch])
      cherry_output = run_git(['cherry', '-v', args.main, release_branch])
    except RuntimeError as error:
      print(f'Error: {error}', file=sys.stderr)
      return 1

    commits = parse_cherry_output(cherry_output.splitlines())

    print(f'Main branch: {args.main}')
    print(f'Release branch: {release_branch}')
    print(f'Merge base: {merge_base}')
    print()

    if not commits:
        print('No release-only commits are pending cherry-pick back to main.')
        return 0

    print('Release-only commits not yet backported to main:')
    for commit in commits:
        print(commit)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
