#!/bin/bash
XDG_DATA_HOME=${XDG_DATA_HOME:-$HOME/.local/share}

if [ -d "/opt/system/Tools/PortMaster/" ]; then
    controlfolder="/opt/system/Tools/PortMaster"
elif [ -d "/opt/tools/PortMaster/" ]; then
    controlfolder="/opt/tools/PortMaster"
elif [ -d "$XDG_DATA_HOME/PortMaster/" ]; then
    controlfolder="$XDG_DATA_HOME/PortMaster"
else
    controlfolder="/roms/ports/PortMaster"
fi

# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: 2026 Ronax

source $controlfolder/control.txt

[ -f "${controlfolder}/mod_${CFW_NAME}.txt" ] && source "${controlfolder}/mod_${CFW_NAME}.txt"
get_controls

export GAMEDIR="/$directory/ports/broforce"
cd "$GAMEDIR"
> "$GAMEDIR/log.txt" && exec > >(tee "$GAMEDIR/log.txt") 2>&1

if [ -s "$GAMEDIR/game-32/.ready" ] || [ -d "$GAMEDIR/.setup-32" ]; then
    route=32
elif [ -d "$GAMEDIR/game-64" ] || [ -d "$GAMEDIR/.setup-64" ]; then
    route=64
elif [ -e /lib/ld-linux-armhf.so.3 ]; then
    route=32
else
    route=64
fi

if [ "$route" = 32 ] && [ ! -e /lib/ld-linux-armhf.so.3 ]; then
    pm_show_error "The 32-bit ARM loader is missing. Restart the handheld or select the 64-bit route." --title "Broforce"
    pm_finish
    exit 1
fi

host="$GAMEDIR/ua_host64"
if [ "$route" = 32 ]; then
    export PORT_32BIT=Y
    host="$GAMEDIR/ua_host"
fi

export SDL_GAMECONTROLLERCONFIG="${sdl_controllerconfig:-}"
export BROFORCE_SETUP_ROUTE=$route
root="$GAMEDIR/game-$route"

if [ ! -s "$root/.ready" ] && { [ -e "$root" ] || [ -L "$root" ]; }; then
    pm_show_error "The runtime folder is incomplete. Back up game-$route and rename it before retrying." --title "Broforce"
    pm_finish
    exit 1
fi

if [ ! -s "$root/.ready" ]; then
    echo "Preparing Broforce. Supplied game files are removed after successful setup."
    export DEVICE_ARCH controlfolder DISPLAY_WIDTH DISPLAY_HEIGHT
    export PATCHER_FILE="$GAMEDIR/setup/patchscript" PATCHER_QUESTIONS="$GAMEDIR/setup/questions.lua"
    export PATCHER_GAME=Broforce PATCHER_TIME="Several minutes or longer"
    export LD_LIBRARY_PATH="${LD_LIBRARY_PATH:-}"
    if [ -f "$controlfolder/utils/patcher.txt" ] && [ -f "$controlfolder/runtimes/love_11.5/love.txt" ]; then
        ( source "$controlfolder/utils/patcher.txt" )
    else
        "$PATCHER_FILE"
    fi
fi

if [ ! -s "$root/.ready" ] || [ ! -s "$root/Broforce.apk" ] ||
   [ ! -s "$root/android_package.json" ] || [ ! -s "$root/lib/libunity.so" ] ||
   { [ "$route" = 32 ] && [ ! -s "$root/main.1.org.portmaster.broforce.obb" ]; }; then
    if [ -s "$root/.ready" ]; then
        pm_show_error "The installed Broforce runtime is incomplete. Back up game-$route and rename it before retrying." --title "Broforce"
    fi
    pm_finish
    exit 1
fi

sh "$GAMEDIR/setup/cleanup-input" "$GAMEDIR" "$route" || echo "Input cleanup did not complete; see patchlog.txt."

export UA_PAD_NAME="Xbox Wireless Controller"
export UA_DPAD_STICK="auto"
export UA_FPS="10"
buttons=$(cat "$GAMEDIR/buttons.txt" 2>/dev/null)
case "$buttons" in xbox|nintendo) ;; *) buttons=nintendo ;; esac
export BROFORCE_PROMPTS="$buttons"
if [ "$buttons" = nintendo ] && [ ! -f "$root/.prompt-labels" ] && ! ./setup/patch-labels "$root"; then
    pm_show_error "Could not update the button labels. See broforce/log.txt and try launching again." --title "Broforce"
    pm_finish
    exit 1
fi

resolution=$(cat "$GAMEDIR/resolution.txt" 2>/dev/null)
case "$resolution" in device|0.833|0.75|0.5) ;; *) resolution=0.75 ;; esac
unset UA_RENDER_SIZE
if [ "$resolution" != device ]; then
    export UA_RENDER_SCALE="$resolution"
else
    unset UA_RENDER_SCALE
fi
export UA_RENDER_SCALER="gpu"
aspect=$(cat "$GAMEDIR/aspect.txt" 2>/dev/null)
case "$aspect" in
    16:9|4:3|1:1) export UA_ASPECT="$aspect" ;;
    *) unset UA_ASPECT ;;
esac

$GPTOKEYB2 "$(basename "$host")" -c "$GAMEDIR/broforce.ini" 9>&- &
pm_platform_helper "$host"
if [ "$route" = 32 ]; then
    export LD_LIBRARY_PATH="/lib32:/usr/lib32:${LD_LIBRARY_PATH:-}"
fi
"$host" "$root"

pm_finish
