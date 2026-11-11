# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: 2026 Ronax
"""Gather notices for the ARM64 converter and managed patcher."""

import argparse
import os
from pathlib import Path
import re
import subprocess
import tomllib


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("cargo_home", type=Path)
    parser.add_argument("out", type=Path)
    parser.add_argument("--rust-licenses", type=Path)
    parser.add_argument("--dotnet-runtime", type=Path, required=True)
    args = parser.parse_args()
    rust = Path(__file__).resolve().parent / "portmaster-unity/setup-rs"
    locked = tomllib.loads((rust / "Cargo.lock").read_text(encoding="utf-8"))["package"]
    tree = subprocess.check_output(
        ["cargo", "tree", "--offline", "--locked", "-p", "pmu", "--target",
         "aarch64-unknown-linux-musl", "-e", "normal,no-proc-macro", "--prefix", "none"],
        cwd=rust,
        env={**os.environ, "CARGO_HOME": str(args.cargo_home.resolve())},
        text=True,
    )
    target_crates = set(re.findall(r"^([\w-]+) v(\S+)", tree, re.MULTILINE))
    args.out.mkdir(parents=True, exist_ok=True)
    registry = args.cargo_home / "registry/src"
    with (args.out / "LICENSE.rust-crates.txt").open("w", encoding="utf-8") as output:
        output.write("License notices for the ARM64 converter's Rust dependencies.\n")
        if args.rust_licenses:
            output.write("\nRust standard library\n")
            for name in ("MIT.txt", "Apache-2.0.txt"):
                path = args.rust_licenses / name
                if path.is_file():
                    output.write(path.read_text(encoding="utf-8") + "\n")
        for package in locked:
            if not package.get("source", "").startswith("registry+") or (
                package["name"], package["version"]
            ) not in target_crates:
                continue
            name = f"{package['name']}-{package['version']}"
            directory = next(registry.glob(f"*/{name}"), None)
            if directory is None:
                raise FileNotFoundError(f"Cargo source required for notices: {name}")
            output.write(f"\n\n{name}\n")
            matches = sorted(
                file for file in directory.iterdir()
                if file.is_file() and file.name.upper().startswith(
                    ("LICEN", "COPYING", "UNLICENSE", "NOTICE")
                )
            )
            for file in matches:
                output.write(f"\n{file.name}\n{file.read_text(encoding='utf-8', errors='replace')}\n")
            if not matches:
                metadata = tomllib.loads((directory / "Cargo.toml").read_text(encoding="utf-8"))
                output.write(f"{metadata['package'].get('license', 'See crate sources')}\n")
            for component in ("src/zlib/LICENSE", "liblz4/lib/LICENSE"):
                license_file = directory / component
                if license_file.is_file():
                    output.write(f"\n{component}\n{license_file.read_text(encoding='utf-8')}\n")

    vendors = {
        "ww2ogg": "ww2ogg/LICENSE",
        "libvpx": "libvpx/LICENSE",
    }
    for name, license_file in vendors.items():
        license_text = (rust / "vendor" / license_file).read_text(encoding="utf-8")
        if name == "libvpx":
            license_text += "\n\n" + (rust / "vendor/libvpx/PATENTS").read_text(encoding="utf-8")
        (args.out / f"LICENSE.{name}.txt").write_text(license_text, encoding="utf-8")
    for upstream, name in (
        ("LICENSE.TXT", "LICENSE.dotnet-runtime.txt"),
        ("THIRD-PARTY-NOTICES.TXT", "LICENSE.dotnet-third-party.txt"),
    ):
        (args.out / name).write_bytes((args.dotnet_runtime / upstream).read_bytes())


if __name__ == "__main__":
    main()
