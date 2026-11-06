#!/usr/bin/env python3
"""Restore original ROS 2 SQLite bags from compressed Git LFS files."""

import argparse
import gzip
import hashlib
import json
from pathlib import Path


def checksum(path):
    digest = hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(4 * 1024 * 1024), b''):
            digest.update(chunk)
    return digest.hexdigest()


def restore(root, name, entry):
    target = root / name / entry['filename']
    if target.exists():
        if checksum(target) != entry['sha256']:
            raise ValueError(f'{target}: existing file has a different checksum')
        print(f'{name}: already restored and verified')
        return

    source = target.with_name(target.name + '.gz')
    with source.open('rb') as stream:
        if stream.read(2) != b'\x1f\x8b':
            raise ValueError(f'{source}: run git lfs pull to download the bag')

    partial = target.with_name(target.name + '.partial')
    output = partial.open('xb')
    digest = hashlib.sha256()
    size = 0
    try:
        with output, gzip.open(source, 'rb') as compressed:
            for chunk in iter(lambda: compressed.read(4 * 1024 * 1024), b''):
                output.write(chunk)
                digest.update(chunk)
                size += len(chunk)
        if digest.hexdigest() != entry['sha256'] or size != entry['size_bytes']:
            raise ValueError(f'{name}: restored bag failed verification')
        partial.rename(target)
    except Exception:
        partial.unlink(missing_ok=True)
        raise
    print(f'{name}: restored and verified {target.name}')


def main():
    root = Path(__file__).resolve().parents[1] / 'rosbags'
    manifest = json.loads((root / 'manifest.json').read_text())
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('bags', nargs='*', help='Bags to restore (default: both)')
    args = parser.parse_args()
    for name in args.bags or manifest:
        if name not in manifest:
            parser.error(f'unknown bag {name!r}; choose from {", ".join(manifest)}')
        restore(root, name, manifest[name])


if __name__ == '__main__':
    main()
