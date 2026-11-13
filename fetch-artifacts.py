#!/usr/bin/env python3
"""Fetch and verify the pinned build tools and redistributable port components."""
import concurrent.futures
import hashlib
import json
import os
from pathlib import Path
import platform
import subprocess
import tarfile

ROOT = Path(__file__).resolve().parent
DEPS = ROOT / 'dependencies'
DEPS.mkdir(exist_ok=True)

ARTIFACTS = {
    'cuphead-2026.11.01.2.zip': ('https://github.com/wild1walker/portmaster-cuphead/releases/download/2026.11.01.2/cuphead.zip', 'sha256', '8b7737101a423ad658c12855a67e4407492a79f3af5fb72b2674fcaa9fa0be4d'),
    'unitypy-1.25.4.tar.gz': ('https://files.pythonhosted.org/packages/10/a4/5b1c786cae645d30c882eac7933ab7c8916e13f1a571bf7d0f2cdc942a52/unitypy-1.25.4.tar.gz', 'sha256', '91d6169d73db8eb5f11fd6531b4e5e980f53dae00d5e3cbab827bbf4765de6d3'),
    'zig-0.15.2.tar.xz': ('https://ziglang.org/download/0.15.2/zig-x86_64-linux-0.15.2.tar.xz', 'sha256', '02aa270f183da276e5b5920b1dac44a63f1a49e55050ebde3aecc9eb82f93239'),
    'dotnet-sdk-8.0.427.tar.gz': ('https://builds.dotnet.microsoft.com/dotnet/Sdk/8.0.427/dotnet-sdk-8.0.427-linux-x64.tar.gz', 'sha512', '85725692f465f5024b9b42a159a29d9f73e8c57ad9e8bfe1e7028a505d18031d68931e8aa3f9de44145b08170dde897c8a78e1aa18d4219698b6891af7095d39'),
    'aarch64-linux-musl-cross.tgz': ('https://musl.cc/aarch64-linux-musl-cross.tgz', 'sha256', 'c909817856d6ceda86aa510894fa3527eac7989f0ef6e87b5721c58737a06c38'),
    'rustup-init': ('https://static.rust-lang.org/rustup/archive/1.28.2/x86_64-unknown-linux-gnu/rustup-init', 'sha256', '20a06e644b0d9bd2fbdbfd52d42540bdde820ea7df86e92e533c073da0cdd43c'),
}

def digest(path, algorithm):
    h = hashlib.new(algorithm)
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()

def fetch(name, url, algorithm, expected):
    path = DEPS / name
    if path.is_file() and digest(path, algorithm) == expected:
        return path
    part = DEPS / (name + '.partial')
    print(f'Downloading {name}', flush=True)
    subprocess.run(['curl', '-fL', '--retry', '3', '--silent', '--show-error', '-o', str(part), url], check=True)
    if digest(part, algorithm) != expected:
        raise SystemExit(f'Checksum mismatch for {name}; the existing dependency was not replaced.')
    os.replace(part, path)
    return path

def fetch_package(item):
    arch, name, metadata = item
    filename = metadata['Filename']
    local = f'deb-{arch}-{Path(filename).name}'
    return arch, name, metadata['SHA256'], fetch(local, 'https://deb.debian.org/debian/' + filename, 'sha256', metadata['SHA256'])

def extract(archive, destination, marker):
    stamp = DEPS / (archive.name + '.extracted')
    if stamp.is_file() and marker.is_file():
        return
    destination.mkdir(parents=True, exist_ok=True)
    subprocess.run(['tar', '-xf', str(archive), '-C', str(destination)], check=True)
    if not marker.is_file():
        raise SystemExit(f'Missing expected file after extracting {archive.name}: {marker}')
    stamp.touch()

def main():
    if platform.system() != 'Linux' or platform.machine() not in ('x86_64', 'amd64'):
        raise SystemExit('This automated build currently requires x86-64 Linux or WSL.')
    for name, (url, algorithm, checksum) in ARTIFACTS.items():
        fetch(name, url, algorithm, checksum)
    extract(DEPS / 'zig-0.15.2.tar.xz', DEPS, DEPS / 'zig-x86_64-linux-0.15.2/zig')
    extract(DEPS / 'aarch64-linux-musl-cross.tgz', DEPS, DEPS / 'aarch64-linux-musl-cross/bin/aarch64-linux-musl-gcc')
    extract(DEPS / 'dotnet-sdk-8.0.427.tar.gz', DEPS / 'dotnet', DEPS / 'dotnet/dotnet')
    unity = DEPS / 'unitypy/lzma.tpk'
    unity.parent.mkdir(exist_ok=True)
    with tarfile.open(DEPS / 'unitypy-1.25.4.tar.gz', 'r:gz') as archive:
        data = archive.extractfile('unitypy-1.25.4/UnityPy/resources/lzma.tpk').read()
    if hashlib.sha256(data).hexdigest() != '16f1f8b809d1cd3bc3aeebf0cd43ecd3690b326a7a88b2273e57bcd83f5df608':
        raise SystemExit('UnityPy class database checksum mismatch')
    unity.write_bytes(data)

    lock = json.loads((ROOT / 'sysroots.lock.json').read_text(encoding='utf-8'))
    items = [(arch, name, meta) for arch, packages in lock.items() for name, meta in packages.items()]
    with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:
        downloaded = list(pool.map(fetch_package, items))
    for arch, name, checksum, path in downloaded:
        target = DEPS / 'sysroots' / arch
        target.mkdir(parents=True, exist_ok=True)
        marker = target / ('.package-' + name + '-' + checksum[:16])
        if not marker.exists():
            subprocess.run(['dpkg-deb', '-x', str(path), str(target)], check=True)
            marker.touch()

    env = dict(os.environ, CARGO_HOME=str(DEPS / 'cargo'), RUSTUP_HOME=str(DEPS / 'rustup'))
    rustup = DEPS / 'cargo/bin/rustup'
    if not rustup.is_file():
        installer = DEPS / 'rustup-init'
        installer.chmod(0o755)
        subprocess.run([str(installer), '-y', '--no-modify-path', '--profile', 'minimal', '--default-toolchain', '1.99.1', '--target', 'aarch64-unknown-linux-musl'], env=env, check=True)
    else:
        subprocess.run([str(rustup), 'toolchain', 'install', '1.99.1', '--profile', 'minimal', '--target', 'aarch64-unknown-linux-musl'], env=env, check=True)
    print('Pinned build dependencies are ready.')

if __name__ == '__main__':
    main()
