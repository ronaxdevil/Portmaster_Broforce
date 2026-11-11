#!/bin/bash
# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: 2026 Ronax
set -euo pipefail

source_dir=$(cd -- "$(dirname -- "$0")" && pwd -P)
work_dir=$(cd -- "$source_dir/../work" && pwd -P)
: "${UNITY_RUNTIME:?Set UNITY_RUNTIME to the pinned runtime source with libhybris populated}"
: "${ZIG:?Set ZIG to the path to Zig 0.15.2}"
export ZIG_GLOBAL_CACHE_DIR="$work_dir/tools/zig-cache"
export ZIG_LOCAL_CACHE_DIR="$work_dir/tools/zig-local"
cd "$UNITY_RUNTIME"

build_host() (
    local arch=$1 target=$2 multi=$3 name=$4
    shift 4
    local sysroot="$work_dir/tools/apt-$arch/root"
    local lib="$sysroot/usr/lib/$multi"
    local out="$work_dir/hosts/$arch"
    local hybris=thirdparty/libhybris/hybris
    local flags=(-target "$target" "$@" -O2 -D_GNU_SOURCE -fPIC -I jni -I jni/include
        -isystem "$sysroot/usr/include/$multi" -isystem "$sysroot/usr/include")
    local media_flags=(-D_FILE_OFFSET_BITS=64 -DUM_HAVE_VPX -DUM_HAVE_VORBIS -DUM_HAVE_OPUS
        -DUM_HAVE_MP4 -DUM_HAVE_FFMPEG -DUM_HAVE_H264)
    local hybris_flags=(-D_LARGEFILE64_SOURCE -I loader/hybris -I "$hybris/include" -I "$hybris/common")
    local objects=()
    mkdir -p "$out"

    compile() {
        local compiler=$1 src=$2 obj
        shift 2
        obj="$out/${src//\//_}.o"
        "$ZIG" "$compiler" "${flags[@]}" "$@" -c "$src" -o "$obj"
        objects+=("$obj")
    }
    for f in loader/{so_loader,softfp,fastclock}.c loader/bionic_setjmp.S; do compile cc "$f"; done
    compile cc loader/hybris_compat.c "${hybris_flags[@]}" -D_FORTIFY_SOURCE=2
    for f in sysconf hooks_shm logging strlcpy strlcat legacy_properties/{properties,cache,runtime_cache}; do
        compile cc "$hybris/common/$f.c" "${hybris_flags[@]}"
    done
    compile cc "$hybris/properties/hybris_properties.c" "${hybris_flags[@]}"
    compile c++ "$hybris/common/dso_handle_counters.cpp" "${hybris_flags[@]}"
    for f in log_shim native_window asset_manager looper_input_sensor choreographer ndk_newer opensles media_ndk egl_glue shim_tables; do
        compile cc "android/$f.c" -D_FILE_OFFSET_BITS=64
    done
    for f in fakejni unityplayer up_android up_input up_softinput up_media up_tls up_fmod up_http up_unity6 up_legacy; do
        compile cc "jni/$f.c"
    done
    for f in um_format um_extractor um_webm um_mp4 um_codec um_surface um_vpx um_audio um_h264 um_ffmpeg um_pmhwdec um_stubs um_compat; do
        compile cc "media/$f.c" "${media_flags[@]}"
    done
    for f in ua_host input pointer osk frames framerate gcbudget uinav monoinvoke jitlog jitwarm monoaot quality \
        glhooks hitches prof threads futex gltrace glfill gltexdump monodump glopt glpersist glstate glarena \
        glpresent glmemo gpuidle glpass glspec glrename glrec glrec_fg glmerge msaafix display display_sdl fbdev \
        steamstub plugins plugstubs wwise desktopenv mono64 unityhooks unitypool unityverts unitymath wwplay; do
        compile cc "host/$f.c" -ffp-contract=off
    done
    compile cc host/wwise_tramp.S
    compile cc host/wwplay_vorbis.c -O3 -ffast-math

    "$ZIG" c++ -target "$target" "$@" -rdynamic -o "$out/$name" "${objects[@]}" \
        "$lib"/lib{vpx,vorbis,ogg,opus,openh264}.a \
        "$lib/libSDL2-2.0.so.0" "$sysroot/lib/$multi/libz.so.1" -ldl -lpthread -lm -lrt
)

build_host armhf arm-linux-gnueabihf.2.35 arm-linux-gnueabihf ua_host -mcpu=cortex_a7 -funwind-tables &
pid32=$!
build_host arm64 aarch64-linux-gnu.2.30 aarch64-linux-gnu ua_host64 &
pid64=$!
status=0
wait "$pid32" || status=1
wait "$pid64" || status=1
exit "$status"
