#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: 2026 Ronax
"""Package the source, public compatibility tools, and the reference's donor apps."""

import argparse
import hashlib
import io
from pathlib import Path
import stat
import zipfile


SOURCE = Path(__file__).resolve().parent
PROJECT = SOURCE.parent
REFERENCE_HASH = "b9594262cce9cccd9d27bceae9cde75a3bccbbe3759b5ee459850e1fe240fce7"
DONORS = (
    "donor-2017.4.9f1-mono-armv7.apk",
    "donor-2017.4.40f1-mono-armv7.apk",
    "donor-2017.4.40f1-il2cpp-arm64.apk",
)
REFERENCE_NOTICES = (
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
    parser.add_argument("--reference", type=Path, default=PROJECT / "reference zip/cuphead.zip")
    parser.add_argument("--pmu", type=Path, required=True)
    parser.add_argument("--asmpatch", type=Path, required=True)
    parser.add_argument("--hosts", type=Path, default=PROJECT / "work/hosts")
    parser.add_argument("--notices", type=Path, required=True)
    parser.add_argument("--output", type=Path, default=PROJECT / "output/broforce.zip")
    parser.add_argument("--submission", type=Path, default=PROJECT / "output/broforce-submission.zip")
    args = parser.parse_args()

    with args.reference.open("rb") as reference:
        if hashlib.file_digest(reference, "sha256").hexdigest() != REFERENCE_HASH:
            parser.error("the Cuphead reference ZIP does not match the pinned 2026.11.01.2 build")
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
        (SOURCE / "portmaster-unity/LICENSE").read_bytes(), False
    )
    for host, arch, machine in (("ua_host", "armhf", 40), ("ua_host64", "arm64", 183)):
        binary = (args.hosts / arch / host).read_bytes()
        if not arm_elf(binary, machine) or b"UA_ASPECT\0" not in binary:
            parser.error(f"invalid host or missing picture-shape support: {host}")
        entries[f"broforce/{host}"] = (binary, True)
    with zipfile.ZipFile(args.reference) as ref:
        for name in DONORS:
            entries[f"broforce/donor/{name}"] = (ref.read(f"cuphead/donor/{name}"), False)
        for name in REFERENCE_NOTICES:
            entries[f"broforce/licenses/{name}"] = (ref.read(f"cuphead/licenses/{name}"), False)
        donor_notice = ref.read("cuphead/licenses/LICENSE.unity-donor.txt")
        entries["broforce/licenses/LICENSE.unity-donor.txt"] = (
            donor_notice.replace(b"for this port: a game of pong", b"by the PortMaster Unity project: a game of pong")
            .replace(b"run the player's own copy of Cuphead", b"run the player's own copy of Broforce"),
            False,
        )
        with zipfile.ZipFile(io.BytesIO(ref.read("cuphead/setup64/setup64.zip"))) as mono:
            for name in sorted(mono.namelist()):
                if name.startswith("mono64/") and not name.endswith("/"):
                    entries[f"broforce/setup64/{name}"] = (mono.read(name), False)
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
    write_package(args.submission, submission)


if __name__ == "__main__":
    main()
