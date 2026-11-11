#!/bin/bash
set -euo pipefail

source_dir=$(cd -- "$(dirname -- "$0")" && pwd -P)
source "$source_dir/dependencies.lock"
checkout="$source_dir/portmaster-unity"
patch="$source_dir/$PORTMASTER_UNITY_PATCH"

if [ ! -e "$checkout" ]; then
    git clone --no-checkout "$PORTMASTER_UNITY_URL" "$checkout"
    git -C "$checkout" checkout --detach "$PORTMASTER_UNITY_REVISION"
fi
if [ "$(git -C "$checkout" rev-parse HEAD)" != "$PORTMASTER_UNITY_REVISION" ]; then
    echo "PortMaster Unity is not at the pinned revision; preserve your changes and check it out separately." >&2
    exit 1
fi
if git -C "$checkout" apply --reverse --check "$patch" 2>/dev/null; then
    echo "Broforce's 200 MB reserve patch is already applied."
elif git -C "$checkout" apply --check "$patch"; then
    git -C "$checkout" apply "$patch"
    echo "Applied Broforce's 200 MB reserve patch."
else
    echo "Cannot apply Broforce's patch cleanly; the existing checkout was not changed." >&2
    exit 1
fi
git -C "$checkout" submodule update --init --recursive
echo "PortMaster Unity is ready at $PORTMASTER_UNITY_REVISION."
