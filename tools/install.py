#!/usr/bin/env python3
"""Install only this skill. No network, credential access, or configuration edits."""
import argparse
from datetime import datetime, timezone
import os
from pathlib import Path
import shutil
import tempfile


def install(dest, upgrade=False):
    source = Path(__file__).resolve().parents[1] / 'skills/astra-jev-team'
    dest = Path(dest).expanduser()
    if dest.is_symlink():
        raise ValueError('Refusing to replace a symlink destination')
    if dest.exists() and not upgrade:
        raise ValueError('Already installed; use --upgrade to back up and replace it')
    dest.parent.mkdir(parents=True, exist_ok=True)
    if source == dest.resolve() or source in dest.resolve().parents:
        raise ValueError('Destination must be outside the source skill')
    backup = None
    with tempfile.TemporaryDirectory(dir=dest.parent, prefix='.jev-install-') as temp:
        staged = Path(temp) / 'skill'
        shutil.copytree(source, staged, ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))
        if dest.exists():
            backup_root = dest.parent.parent / 'skill-backups'
            backup_root.mkdir(exist_ok=True)
            stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
            backup = backup_root / (dest.name + '-' + stamp)
            dest.rename(backup)
        try:
            staged.rename(dest)
        except OSError:
            if backup is not None:
                backup.rename(dest)
            raise
    return dest, backup


def main():
    p = argparse.ArgumentParser(description=__doc__)
    default = Path(os.environ.get('CODEX_HOME', str(Path.home()/'.codex'))) / 'skills/astra-jev-team'
    p.add_argument('--dest', type=Path, default=default, help='Full destination skill directory')
    p.add_argument('--upgrade', action='store_true', help='Back up an existing installation before replacing')
    args = p.parse_args()
    try:
        dest, backup = install(args.dest, args.upgrade)
    except (OSError, ValueError) as exc:
        p.exit(1, str(exc) + '\n')
    print('Installed: ' + str(dest))
    if backup:
        print('Previous version backed up: ' + str(backup))
    print('Available on your next Codex turn. Invoke $astra-jev-team.')


if __name__ == '__main__':
    main()
