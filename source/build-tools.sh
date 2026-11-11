#!/bin/bash
# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: 2026 Ronax
set -euo pipefail

source_dir=$(cd -- "$(dirname -- "$0")" && pwd -P)
work_dir=$(cd -- "$source_dir/../work" && pwd -P)
upstream="$source_dir/portmaster-unity"
revision=ed3d8ccaa941a14ef958872cc8094d56ad2b8fb5
[[ "$(git -C "$upstream" rev-parse HEAD)" == "$revision" ]]

: "${PMU_TPK:?Set PMU_TPK to UnityPy 1.25.4 resources/lzma.tpk}"
export PMU_TPK
export CARGO_TARGET_DIR="${CARGO_TARGET_DIR:-$work_dir/tools/rust-target}"
export CARGO_TARGET_AARCH64_UNKNOWN_LINUX_MUSL_LINKER=aarch64-linux-musl-gcc
export CC_aarch64_unknown_linux_musl=aarch64-linux-musl-gcc
export CXX_aarch64_unknown_linux_musl=aarch64-linux-musl-g++
export AR_aarch64_unknown_linux_musl=aarch64-linux-musl-ar
export TC_CXX=aarch64-linux-musl-g++
export CFLAGS_aarch64_unknown_linux_musl="-ffile-prefix-map=$upstream/setup-rs=/src/setup-rs"
export CXXFLAGS_aarch64_unknown_linux_musl="$CFLAGS_aarch64_unknown_linux_musl"
export RUSTFLAGS="--remap-path-prefix=$upstream/setup-rs=/src/setup-rs --remap-path-prefix=$work_dir=/build"
(cd "$upstream/setup-rs" && cargo build --locked --release --target aarch64-unknown-linux-musl -p pmu)

export DOTNET_CLI_HOME="$work_dir/tools" DOTNET_CLI_TELEMETRY_OPTOUT=1
export DOTNET_SYSTEM_GLOBALIZATION_INVARIANT=1 DOTNET_GENERATE_ASPNET_CERTIFICATE=false
export NUGET_PACKAGES="$work_dir/tools/nuget"
mkdir -p "$work_dir/tools/patcher-source"
git -C "$upstream" archive "$revision" tools/asmpatch | tar -x -C "$work_dir/tools/patcher-source"
patcher="$work_dir/tools/patcher-source/tools/asmpatch"
cp "$source_dir"/Broforce{Compatibility,Prompts}.cs "$patcher/src/Patches/"
sed -i '/new RewiredAndroid(),/a\        new BroforceCompatibility(),\n        new BroforcePrompts(),' "$patcher/src/Patch.cs"
dotnet publish "$patcher/asmpatch.csproj" -c Release -r linux-arm64 --self-contained \
    -p:PublishSingleFile=true -p:PublishTrimmed=true -p:InvariantGlobalization=true \
    -p:DebugType=none -p:TrimmerRemoveSymbols=true -p:ContinuousIntegrationBuild=true \
    -p:PathMap="$patcher=/src/asmpatch" -o "$work_dir/tools/asmpatch-arm64"
