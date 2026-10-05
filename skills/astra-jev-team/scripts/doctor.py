#!/usr/bin/env python3
"""Offline dependency presence check; never prints credentials or calls a service."""
import json
import os
from pathlib import Path
import sys


def main():
    checks = {'python_3_9_or_newer': sys.version_info >= (3, 9),
              'jev_cli_present': (Path.home()/'.local/bin/jev-decide').is_file(),
              'jev_skill_present': any((base/'jev/SKILL.md').is_file() for base in (Path(__file__).resolve().parents[2], Path(os.environ.get('CODEX_HOME', str(Path.home()/'.codex')))/'skills')),
              'typesafe_key_present': bool(os.environ.get('TYPESAFE_API_KEY')),
              'network_called': False,
              'note': 'Presence only: authentication, model access and accuracy are not checked.'}
    print(json.dumps(checks, indent=2))
    return 0 if all(checks[k] for k in ('python_3_9_or_newer', 'jev_cli_present', 'jev_skill_present', 'typesafe_key_present')) else 2


if __name__ == '__main__':
    raise SystemExit(main())
