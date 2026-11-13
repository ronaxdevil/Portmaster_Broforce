#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: 2026 Ronax
"""Package the built port, source-built Mono, and temporarily supplied donor apps."""

import argparse
import hashlib
from pathlib import Path
import shutil
import stat
import subprocess
import tempfile
import zipfile


SOURCE = Path(__file__).resolve().parent
PROJECT = SOURCE.parent
REFERENCE_HASH = "8b7737101a423ad658c12855a67e4407492a79f3af5fb72b2674fcaa9fa0be4d"
DONORS = (
    "donor-2017.4.9f1-mono-armv7.apk",
    "donor-2017.4.40f1-mono-armv7.apk",
    "donor-2017.4.40f1-il2cpp-arm64.apk",
)
COMPONENT_NOTICES = (
    "LICENSE.astc-encoder.txt",
    "LICENSE.bdwgc.txt",
    "LICENSE.libhybris.txt",
    "LICENSE.mono-cecil.txt",
    "LICENSE.mono-class-libraries.txt",
    "LICENSE.mono.txt",
    "LICENSE.musl.txt",
    "LICENSE.optimized-routines.txt",
    "LICENSE.pillow.txt",
    "LICENSE.texture2ddecoder.txt",
    "LICENSE.unitypy.txt",
    "LICENSE.unity-donor.txt",
)
MONO_CLASSLIBS = (
    "mscorlib.dll", "System.dll", "System.Core.dll", "System.Xml.dll",
    "Mono.Security.dll", "System.Configuration.dll", "System.Security.dll", "Mono.Posix.dll",
)
GENERATED_NOTICES = (
    "LICENSE.dotnet-runtime.txt",
    "LICENSE.dotnet-third-party.txt",
    "LICENSE.libvpx.txt",
    "LICENSE.rust-crates.txt",
    "LICENSE.ww2ogg.txt",
)
SUBMISSION_METADATA = {
    "broforce/port.json": "port.json",
    "broforce/README.md": "README.md",
    "broforce/gameinfo.xml": "gameinfo.xml",
    "broforce/cover.png": "cover.png",
    "broforce/screenshot.png": "screenshot.png",
}


def arm_elf(data, machine):
    return data.startswith(b"\x7fELF") and int.from_bytes(data[18:20], "little") == machine


def add(archive, name, data, executable=False):
    info = zipfile.ZipInfo(name, (2026, 11, 10, 0, 0, 0))
    info.create_system = 3
    info.external_attr = (stat.S_IFREG | (0o755 if executable else 0o644)) << 16
    archive.writestr(info, data, compress_type=zipfile.ZIP_DEFLATED, compresslevel=6)


def write_package(destination, entries):
    destination.parent.mkdir(parents=True, exist_ok=True)
    partial = destination.with_suffix(".zip.partial")
    with zipfile.ZipFile(partial, "w") as archive:
        for name, (data, executable) in sorted(entries.items()):
            add(archive, name, data, executable)
    with zipfile.ZipFile(partial) as archive:
        damaged = archive.testzip()
        if damaged is not None:
            raise ValueError(f"corrupt package entry: {damaged}")
    partial.replace(destination)
    with destination.open("rb") as archive:
        print(f"{hashlib.file_digest(archive, 'sha256').hexdigest()}  {destination.name}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--reference", type=Path, default=SOURCE / "dependencies/cuphead-2026.11.01.2.zip")
    parser.add_argument("--pmu", type=Path, default=SOURCE / ".build/rust-target/aarch64-unknown-linux-musl/release/pmu")
    parser.add_argument("--asmpatch", type=Path, default=SOURCE / ".build/asmpatch-arm64/asmpatch")
    parser.add_argument("--hosts", type=Path, default=SOURCE / ".build/hosts")
    parser.add_argument("--strip-armhf", default="arm-linux-gnueabihf-strip")
    parser.add_argument("--strip-arm64", default="aarch64-linux-gnu-strip")
    parser.add_argument("--notices", type=Path, default=SOURCE / ".build/notices")
    parser.add_argument("--mono", type=Path, default=SOURCE / "dependencies/mono64/out/unity-2017.4-mbe")
    parser.add_argument("--mono-bridge", type=Path, default=SOURCE / "dependencies/portmaster-unity/runtime/mono64/out/arm64/libil2cpp_mono.so")
    parser.add_argument("--output", type=Path, default=PROJECT / "output/broforce.zip")
    parser.add_argument("--submission", type=Path, default=SOURCE / ".build/submission")
    args = parser.parse_args()

    with args.reference.open("rb") as reference:
        if hashlib.file_digest(reference, "sha256").hexdigest() != REFERENCE_HASH:
            parser.error("the Cuphead dependency does not match the pinned official 2026.11.01.2 release")
    pmu = args.pmu.read_bytes()
    asmpatch = args.asmpatch.read_bytes()
    if not arm_elf(pmu, 183) or not arm_elf(asmpatch, 183):
        parser.error("pmu and asmpatch must be Linux AArch64 ELF executables")
    notices = [args.notices / name for name in GENERATED_NOTICES]
    missing = [path.name for path in notices if not path.is_file() or not path.stat().st_size]
    if missing:
        parser.error("generate the required dependency notices with notices.py: " + ", ".join(missing))

    entries = {}
    for path in sorted((SOURCE / "package").rglob("*")):
        if path.is_file():
            name = path.relative_to(SOURCE / "package").as_posix()
            executable = name in ("Broforce.sh", "broforce/setup/patchscript", "broforce/setup/patch-labels", "broforce/setup/cleanup-input")
            entries[name] = (path.read_bytes(), executable)
    entries["broforce/setup/pmu"] = (pmu, True)
    entries["broforce/setup/asmpatch"] = (asmpatch, True)
    entries["broforce/licenses/LICENSE.broforce-port.txt"] = ((SOURCE / "LICENSE").read_bytes(), False)
    entries["broforce/licenses/LICENSE.portmaster-unity.txt"] = (
        (SOURCE / "dependencies/portmaster-unity/LICENSE").read_bytes(), False
    )
    for host, arch, machine in (("ua_host", "armhf", 40), ("ua_host64", "arm64", 183)):
        source_binary = args.hosts / arch / host
        binary = source_binary.read_bytes()
        if not arm_elf(binary, machine) or b"UA_ASPECT\0" not in binary:
            parser.error(f"invalid host or missing picture-shape support: {host}")
        strip_tool = args.strip_armhf if arch == "armhf" else args.strip_arm64
        if shutil.which(strip_tool) is None:
            parser.error(f"missing cross-binutils strip tool: {strip_tool}")
        with tempfile.TemporaryDirectory(prefix="broforce-strip-", dir=SOURCE / ".build") as temp_dir:
            stripped_binary = Path(temp_dir) / host
            stripped_binary.write_bytes(binary)
            subprocess.run([strip_tool, "--strip-debug", str(stripped_binary)], check=True)
            binary = stripped_binary.read_bytes()
        if len(binary) >= source_binary.stat().st_size:
            parser.error(f"debug stripping did not reduce {host}")
        entries[f"broforce/{host}"] = (binary, True)
    with zipfile.ZipFile(args.reference) as ref:
        for name in DONORS:
            entries[f"broforce/donor/{name}"] = (ref.read(f"cuphead/donor/{name}"), False)
    for name in COMPONENT_NOTICES:
        entries[f"broforce/licenses/{name}"] = ((SOURCE / "component-licenses" / name).read_bytes(), False)
    for source_path, name in (
        (args.mono_bridge, "libil2cpp.so"),
        (args.mono / "libmonobdwgc-2.0.so", "libmonobdwgc-2.0.so"),
        (args.mono / "libMonoPosixHelper.so", "libMonoPosixHelper.so"),
    ):
        data = source_path.read_bytes()
        if not arm_elf(data, 183):
            parser.error(f"invalid ARM64 Mono library: {source_path}")
        entries[f"broforce/setup64/mono64/{name}"] = (data, False)
    for name in MONO_CLASSLIBS:
        path = args.mono / "classlibs" / name
        entries[f"broforce/setup64/mono64/classlibs/{name}"] = (path.read_bytes(), False)
    for name in ("mono/config", "mono/4.5/machine.config"):
        path = args.mono / "classlibs/etc" / name
        entries[f"broforce/setup64/mono64/etc/{name}"] = (path.read_bytes(), False)
    for path in notices:
        entries[f"broforce/licenses/{path.name}"] = (path.read_bytes(), False)
    for path in sorted((SOURCE / "host-licenses").glob("LICENSE.*.txt")):
        entries[f"broforce/licenses/{path.name}"] = (path.read_bytes(), False)

    write_package(args.output, entries)
    submission = {
        "port/broforce/" + SUBMISSION_METADATA.get(name, name): entry
        for name, entry in entries.items()
    }
    submission["port/broforce/testing_thread.txt"] = (
        (SOURCE / "testing_thread.txt").read_bytes(), False
    )
    args.submission.mkdir(parents=True, exist_ok=True)
    staging = Path(tempfile.mkdtemp(prefix="staging-", dir=args.submission))
    for name, (data, executable) in submission.items():
        target = staging / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
        target.chmod(0o755 if executable else 0o644)
    print(f"Submission staging: {staging / 'port/broforce'}")


if __name__ == "__main__":
    main()
