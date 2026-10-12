#!/usr/bin/env python3
"""Select a pinned local Scientist/Brain pair without upgrading user records."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import subprocess
import sys
import tempfile

TIMEOUT = 120
PAIR_KEYS = {"scientist", "brain"}


def plain(path):
    path = Path(os.path.abspath(path))
    if any(p.is_symlink() for p in (path, *path.parents)):
        raise ValueError(f"symlink paths are not supported: {path}")
    return path


def git(root, *args):
    try:
        return subprocess.check_output(["git", "-C", str(root), *args], text=True,
                                       stderr=subprocess.PIPE, timeout=30).strip()
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as exc:
        raise ValueError(f"cannot inspect Git checkout: {root}") from exc


def pin(root, kind):
    root = plain(root)
    if Path(git(root, "rev-parse", "--show-toplevel")) != root:
        raise ValueError("framework path must be a Git checkout root")
    if git(root, "status", "--porcelain", "--untracked-files=all"):
        raise ValueError(f"framework checkout is dirty: {root}")
    required = {"scientist": ["scripts/organism_board.py"],
                "brain": ["board/_theme.py", "board/_state.py"]}[kind]
    for name in required:
        path = plain(root / name)
        if not path.is_file() or not git(root, "ls-files", "--", name):
            raise ValueError(f"missing tracked {kind} entry point: {name}")
    return {"path": str(root), "revision": git(root, "rev-parse", "HEAD")}


def verify_pair(pair):
    if not isinstance(pair, dict) or set(pair) != PAIR_KEYS:
        raise ValueError("runtime must pin Scientist and Brain")
    for kind, expected in pair.items():
        if (not isinstance(expected, dict) or set(expected) != {"path", "revision"}
                or not isinstance(expected["path"], str) or not Path(expected["path"]).is_absolute()
                or not isinstance(expected["revision"], str)
                or not re.fullmatch(r"[0-9a-f]{40,64}", expected["revision"])):
            raise ValueError("invalid framework pin")
        if pin(expected["path"], kind) != expected:
            raise ValueError(f"{kind} revision changed; review before selecting it again")


def load(manifest):
    manifest = plain(manifest)
    data = json.loads(manifest.read_bytes())
    fields = {"schema_version", "instance", "repos", "protected", "current", "previous"}
    if not isinstance(data, dict) or set(data) != fields or type(data["schema_version"]) is not int or data["schema_version"] != 1:
        raise ValueError("invalid runtime manifest schema")
    for key in ("instance", "repos"):
        if not isinstance(data[key], str) or not Path(data[key]).is_absolute() or not plain(data[key]).is_file():
            raise ValueError(f"runtime {key} must name an existing absolute file")
    protected = data["protected"]
    if (not isinstance(protected, list) or not protected or
            any(not isinstance(p, str) or not Path(p).is_absolute() for p in protected)):
        raise ValueError("invalid protected paths")
    if str(Path(data["instance"]).parent) not in protected or data["repos"] not in protected:
        raise ValueError("profile directory and canonical map must remain protected")
    if manifest == Path(data['instance']) or manifest == Path(data['repos']):
        raise ValueError("manifest must be separate from user configuration")
    return data


def fingerprints(paths, exclude=()):
    """Hash regular files and directory modes; reject links and special files.

    Git metadata alone is excluded. No scientific/data directory is implicitly
    skipped, and exclusions are limited to this tool's manifest/temporary file.
    """
    excluded = {Path(p) for p in exclude}
    result = {}

    def visit(path):
        if path in excluded or path.name == ".git":
            return
        if path.is_symlink():
            raise ValueError(f"protected symlink is unsupported: {path}")
        mode = path.stat().st_mode
        if stat.S_ISDIR(mode):
            result[str(path)] = ("directory", stat.S_IMODE(mode))
            for child in sorted(path.iterdir()):
                visit(child)
        elif stat.S_ISREG(mode):
            digest = hashlib.sha256()
            with path.open('rb') as stream:
                for chunk in iter(lambda: stream.read(1024 * 1024), b''):
                    digest.update(chunk)
            result[str(path)] = (digest.hexdigest(), stat.S_IMODE(mode))
        else:
            raise ValueError(f"protected path must be a regular file or directory: {path}")

    for path in paths:
        visit(plain(path))
    return result


def boundaries(data, manifest, pair):
    for kind in PAIR_KEYS:
        code = Path(pair[kind]["path"])
        if manifest == code or code in manifest.parents:
            raise ValueError("runtime manifest must live outside framework checkouts")
        for value in data["protected"]:
            record = Path(value)
            if record == code or code in record.parents or record in code.parents:
                raise ValueError("protected data and framework checkouts must be separate")


def execute(data, pair, render=False):
    verify_pair(pair)
    args = [sys.executable, '-B', str(Path(pair['scientist']['path']) / 'scripts/organism_board.py'),
            '--instance', data['instance'], '--repos', data['repos'],
            '--html' if render else '--check-instance']
    env = dict(os.environ, PYAUTO_BRAIN=pair['brain']['path'], PYTHONDONTWRITEBYTECODE='1')
    try:
        result = subprocess.run(args, cwd=pair['scientist']['path'], env=env,
                                capture_output=True, text=True, timeout=TIMEOUT)
    except subprocess.TimeoutExpired as exc:
        raise ValueError("selected runtime timed out") from exc
    if result.returncode:
        raise ValueError("selected runtime failed: " + (result.stderr or result.stdout)[-4000:])
    return result.stdout


def observe(data, manifest, pair, *, render=False):
    boundaries(data, manifest, pair)
    before = fingerprints(data['protected'], [manifest])
    original_manifest = manifest.read_bytes() if manifest.exists() else None
    try:
        output = execute(data, pair, render)
    finally:
        if (manifest.read_bytes() if manifest.exists() else None) != original_manifest:
            raise ValueError("runtime manifest changed during execution; inspect manually")
        if fingerprints(data['protected'], [manifest]) != before:
            raise ValueError("protected records changed during runtime execution; inspect manually (no restore attempted)")
    verify_pair(pair)
    return before, output


def prepare(action, manifest, *, instance=None, repos=None, scientist=None, brain=None, protect=()):
    manifest = plain(manifest)
    if not manifest.parent.is_dir():
        raise ValueError("manifest parent directory must exist")
    original = manifest.read_bytes() if manifest.exists() else None
    if action == 'initialize':
        if original is not None:
            raise ValueError("runtime manifest exists; use upgrade or check")
        instance, repos = plain(instance), plain(repos)
        if not instance.is_file() or not repos.is_file() or manifest in (instance, repos):
            raise ValueError("profile/map must exist separately from the manifest")
        data = {"schema_version": 1, "instance": str(instance), "repos": str(repos),
                "protected": sorted({str(instance.parent), str(repos), *(str(plain(p)) for p in protect)}),
                "current": None, "previous": None}
    else:
        if original is None:
            raise ValueError("runtime manifest is missing")
        data = load(manifest)
    if action in ('initialize', 'upgrade'):
        candidate = {"scientist": pin(scientist, 'scientist'), "brain": pin(brain, 'brain')}
    elif action == 'rollback':
        candidate = data['previous']
        if candidate is None:
            raise ValueError("no previous runtime is recorded")
        verify_pair(candidate)
    else:
        raise ValueError("unknown runtime transition")
    # An upgrade must retain a usable current pair as the recovery target.
    # Rollback may recover from a missing or broken current pair.
    if action == 'upgrade':
        verify_pair(data['current'])
    before, output = observe(data, manifest, candidate)
    unchanged = (manifest.read_bytes() if manifest.exists() else None) == original
    if not unchanged:
        raise ValueError("manifest changed during validation; rerun preview")
    changed = candidate != data['current']
    if changed:
        data['previous'], data['current'] = data['current'], candidate
    return {"manifest": manifest, "original": original, "data": data,
            "records": before, "changed": changed, "validation": output,
            "recovery": data['previous'] if action == 'upgrade' and changed else None}


def apply(prepared):
    path, data = prepared['manifest'], prepared['data']

    def unchanged(extra=()):
        plain(path)
        if (path.read_bytes() if path.exists() else None) != prepared['original']:
            raise ValueError("manifest changed; rerun preview")
        if fingerprints(data['protected'], [path, *extra]) != prepared['records']:
            raise ValueError("protected records changed; rerun preview")
        verify_pair(data['current'])
        if prepared['recovery'] is not None:
            verify_pair(prepared['recovery'])

    unchanged()
    if not prepared['changed']:
        return False
    temporary = None
    try:
        fd, name = tempfile.mkstemp(prefix='.scientist-runtime-', dir=path.parent)
        temporary = Path(name)
        with os.fdopen(fd, 'w') as stream:
            if prepared['original'] is not None:
                os.fchmod(stream.fileno(), stat.S_IMODE(path.stat().st_mode))
            json.dump(data, stream, indent=2); stream.write('\n')
            stream.flush(); os.fsync(stream.fileno())
        unchanged([temporary])
        if prepared['original'] is None:
            os.link(temporary, path)  # never replace a competing initializer
        else:
            os.replace(temporary, path)
        return True
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=['initialize', 'upgrade', 'rollback', 'check', 'render'])
    parser.add_argument('--manifest', type=Path, required=True)
    parser.add_argument('--instance', type=Path)
    parser.add_argument('--repos', type=Path)
    parser.add_argument('--scientist', type=Path)
    parser.add_argument('--brain', type=Path)
    parser.add_argument('--protect', type=Path, action='append', default=[])
    parser.add_argument('--apply', action='store_true')
    args = parser.parse_args(argv)
    if args.action == 'initialize' and (args.instance is None or args.repos is None):
        parser.error('initialize requires --instance and --repos')
    if args.action in ('initialize', 'upgrade') and (args.scientist is None or args.brain is None):
        parser.error('initialize/upgrade require --scientist and --brain')
    if args.action != 'initialize' and (args.instance or args.repos or args.protect):
        parser.error('profile, map and protected paths are selected at initialization')
    if args.action not in ('initialize', 'upgrade') and (args.scientist or args.brain):
        parser.error('this action uses the recorded framework selection')
    if args.action in ('check', 'render') and args.apply:
        parser.error('check/render do not accept --apply')
    try:
        if args.action in ('check', 'render'):
            data = load(args.manifest)
            _, output = observe(data, plain(args.manifest), data['current'], render=args.action == 'render')
            print(output, end='')
        else:
            prepared = prepare(args.action, args.manifest, instance=args.instance, repos=args.repos,
                               scientist=args.scientist, brain=args.brain, protect=args.protect)
            print(json.dumps(prepared['data'], indent=2))
            print(prepared['validation'], end='')
            if args.apply:
                print('Selected runtime updated' if apply(prepared) else 'Selection unchanged')
            else:
                print('Preview only; pass --apply to select this runtime')
    except (OSError, ValueError, TypeError) as exc:
        parser.exit(2, f'instance-runtime: {exc}\n')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
