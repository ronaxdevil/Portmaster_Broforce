#!/bin/bash
set -euo pipefail

source_dir=$(cd -- "$(dirname -- "$0")" && pwd -P)
bash "$source_dir/fetch-unity-source.sh"
python3 "$source_dir/fetch-artifacts.py"
