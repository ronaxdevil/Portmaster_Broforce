# Broforce PortMaster build source

`package/` holds the launcher, setup scripts and metadata. `BroforceCompatibility.cs` and `BroforcePrompts.cs` add game-specific patches to the reference assembly patcher. The SHA-256 manifest identifies the accepted Steam Linux depot files. The original desktop game files are needed at installation time.

## Build on Linux or WSL

Use Python 3.11 or later, the .NET 8 SDK, a Rust toolchain with the `aarch64-unknown-linux-musl` target, a host C compiler, and the AArch64 musl GCC cross tools on `PATH`. Install UnityPy 1.25.4 and set `PMU_TPK` to its `resources/lzma.tpk`. Set `CARGO_HOME` to the intended crate cache if you use a portable Rust installation.

PortMaster Unity is an external dependency and is not included in this repository. `dependencies.lock` pins the requested [ronaxdevil/portmaster-unity](https://github.com/ronaxdevil/portmaster-unity) revision; the fetch script checks it out, applies the tracked 200 MB packing-reserve patch, and initializes its submodule. Existing checkouts at a different revision or with conflicting changes are left for manual review. Keep the supplied Cuphead ZIP version `2026.11.01.2` in `../reference zip/cuphead.zip`. The packager checks its SHA-256 and reuses its donor applications and Mono ARM64 bridge with the corresponding notices.

The updated ARM hosts use the same pinned runtime source, including its libhybris submodule at
`7079712a42ea2754adf747e70c6cc75764c8596e`. Set `UNITY_RUNTIME` to the absolute path to that
source tree's `runtime` directory and `ZIG` to Zig 0.15.2. Extract Debian Bookworm's ARM runtime
and development packages into `../work/tools/apt-armhf/root` and `../work/tools/apt-arm64/root`.
Both roots need `libsdl2-dev`, `libvpx-dev`, `libvorbis-dev`, `libogg-dev`, `libopus-dev`,
`libopenh264-dev`, `libegl-dev`, `libgles-dev`, `libgl-dev`, `zlib1g-dev`, and `linux-libc-dev` and
their runtime dependencies. The compiler targets glibc 2.35 for ARMv7 and 2.30 for AArch64.

```bash
bash fetch-dependencies.sh
bash build-tools.sh
bash build-hosts.sh
python3 notices.py "${CARGO_HOME:-$HOME/.cargo}" ../work/notices \
  --rust-licenses "$(rustc --print sysroot)/share/doc/rust/licenses" \
  --dotnet-runtime ../work/tools/nuget/microsoft.netcore.app.runtime.linux-arm64/8.0.33
python3 build.py \
  --pmu ../work/tools/rust-target/aarch64-unknown-linux-musl/release/pmu \
  --asmpatch ../work/tools/asmpatch-arm64/asmpatch \
  --notices ../work/notices
```

This writes the Cuphead-style install archive `broforce.zip` and the PortMaster review tree
`broforce-submission.zip` under `../output`. The submission archive has a top-level README,
artwork, XML and metadata beside the launcher. Both archives use the same payload.

The Broforce port code is MIT-licensed under Copyright (c) 2026 Ronax. The packaged licenses
also credit the upstream authors of the shipped donors, runtime hosts, managed patcher and converter.
The packager selects reference notices by name, and `notices.py` derives the Rust list from the
ARM64 release target. Pass the .NET runtime pack used to publish the patcher when regenerating notices.

The gameplay image uses the RG34XX SP capture `../work/device-level-start.png` at its original
size with 30 pixels of black padding at the top and bottom. The cover uses the title artwork
from `../work/device-full-panel.png`.

The reference's donor apps contain Unity players. Broforce's desktop player binaries, original assemblies, bundles, textures and saves are supplied by the owner and processed locally. Steam returns the normal unavailable result on the port. After successful device setup, unchanged game input files listed in the manifest are removed from `gamedata`; retain an independent backup.

For the supplied ZIP, `pmu` was built with Rust 1.99.1 and the portable AArch64 musl GCC cross toolchain. The current converter handles all serialized files in a UnityFS scene bundle. The reference ZIP's older converter skipped such bundles. The managed patcher was built with .NET SDK 8.0.427 and Mono.Cecil 0.11.6.

The reference projects are [PortMaster Unity](https://github.com/ronaxdevil/portmaster-unity) and [PortMaster Cuphead](https://github.com/wild1walker/portmaster-cuphead).
