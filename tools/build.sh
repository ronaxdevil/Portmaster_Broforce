#!/bin/bash
# Build the Broforce release on x86-64 Linux or WSL without system-wide installs.
set -euo pipefail
source_dir=$(cd -- "$(dirname -- "$0")" && pwd -P)
deps="$source_dir/dependencies"
build="$source_dir/.build"

for command in git curl tar xz dpkg-deb python3 gcc g++ make arm-linux-gnueabihf-strip aarch64-linux-gnu-strip docker; do
    command -v "$command" >/dev/null || { echo "Missing prerequisite: $command" >&2; exit 1; }
done
docker info >/dev/null 2>&1 || { echo "Start Docker before building." >&2; exit 1; }
python3 -c 'import sys; assert sys.version_info >= (3, 11), "Python 3.11 or newer is required"'
mkdir -p "$build"
bash "$source_dir/fetch-dependencies.sh"

export CARGO_HOME="$deps/cargo" RUSTUP_HOME="$deps/rustup" RUSTUP_TOOLCHAIN=1.99.1
export DOTNET_ROOT="$deps/dotnet"
export PATH="$deps/cargo/bin:$deps/dotnet:$deps/aarch64-linux-musl-cross/bin:$PATH"
export PMU_TPK="$deps/unitypy/lzma.tpk"
export UNITY_RUNTIME="$deps/portmaster-unity/runtime"
export ZIG="$deps/zig-x86_64-linux-0.15.2/zig"

bash "$source_dir/build-tools.sh"
bash "$source_dir/build-hosts.sh"
bash "$source_dir/build-mono.sh"
python3 "$source_dir/notices.py" "$CARGO_HOME" "$build/notices" \
    --rust-licenses "$(rustc --print sysroot)/share/doc/rust/licenses" \
    --dotnet-runtime "$build/nuget/microsoft.netcore.app.runtime.linux-arm64/8.0.33"
python3 "$source_dir/build.py" --output "${BROFORCE_OUTPUT:-$source_dir/../../output/broforce.zip}"
