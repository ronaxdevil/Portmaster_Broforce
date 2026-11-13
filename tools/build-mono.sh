#!/bin/bash
# Build the ARM64 Mono bridge, runtime, and class libraries from source.
set -euo pipefail
source_dir=$(cd -- "$(dirname -- "$0")" && pwd -P)
source "$source_dir/dependencies.lock"
build_tools="$source_dir/dependencies"
unity="$build_tools/portmaster-unity"
mono="$build_tools/mono64"
mkdir -p "$mono/runtime-cache" "$mono/classlib-cache"
command -v docker >/dev/null || { echo "Docker is required to build Mono." >&2; exit 1; }
docker info >/dev/null 2>&1 || { echo "Start Docker before building Mono." >&2; exit 1; }
export MONO_REF="$MONO_REVISION"
export MONO64_RUNTIME_VOLUME="$mono/runtime-cache"
export MONO64_CL_VOLUME="$mono/classlib-cache"
for marker in "$mono/src/unity-2017.4-mbe/.fetched" "$mono/classlib-cache/src/.fetched"; do
    if [ -f "$marker" ] && ! grep -Fq "$MONO_REF" "$marker"; then
        echo "Existing Mono build cache does not match the pinned revision: $marker" >&2
        exit 1
    fi
done
bash "$unity/runtime/mono64/build.sh"
bash "$unity/tools/mono64/build-mono.sh" 2017.4 "$mono"
bash "$unity/tools/mono64/build-classlibs.sh" 2017.4 "$mono"
grep -Fq "$MONO_REF" "$mono/out/unity-2017.4-mbe/SOURCE.txt"
grep -Fq "$MONO_REF" "$mono/out/unity-2017.4-mbe/classlibs/SOURCE.txt"
