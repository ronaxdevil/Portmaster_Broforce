#!/usr/bin/env python3
"""Generate pinned ARM sysroot package metadata from Debian package indexes."""
import json
import lzma
from pathlib import Path

source = Path(__file__).resolve().parent
names = set('''libsdl2-dev libsdl2-2.0-0 libvpx-dev libvpx7 libvorbis-dev libvorbis0a
libogg-dev libogg0 libopus-dev libopus0 libopenh264-dev libopenh264-7 libegl-dev
libgles-dev libgl-dev libglvnd-dev libglx-dev libdrm-dev libwayland-dev zlib1g-dev
zlib1g linux-libc-dev'''.split())
result = {}
for arch in ('arm64', 'armhf'):
    packages = {}
    with lzma.open(source / 'dependencies' / f'Packages-{arch}.xz', 'rt', encoding='utf-8') as stream:
        record = {}
        for line in stream:
            if line == '\n':
                if record.get('Package') in names:
                    packages[record['Package']] = {key: record[key] for key in ('Version', 'Filename', 'SHA256')}
                record = {}
            elif not line.startswith(' ') and ': ' in line:
                key, value = line.rstrip('\n').split(': ', 1)
                record[key] = value
    missing = names - packages.keys()
    if missing:
        raise SystemExit(f'Missing {arch} packages: {sorted(missing)}')
    result[arch] = dict(sorted(packages.items()))
(source / 'sysroots.lock.json').write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
