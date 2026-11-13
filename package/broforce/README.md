## Notes

Thanks to [Free Lives](https://freelives.net/) for Broforce, and to wild1walker for the Unity porting tools.

## Get Steam data

Requires **Broforce for Linux from Steam**.

1. Open Steam's console with `steam://open/console` and enter:

   ```text
   download_depot 274190 274193
   ```

2. Copy the downloaded `depot_274193` folder into `ports/broforce/gamedata/`.
   Alternatively, copy its Linux `Broforce_Data` folder directly into `gamedata/`.
3. The port verifies the game files before setup.

## Setup

Install the port with PortMaster and start **Broforce** from Ports. First launch builds the game
on the handheld and needs at least **4.5 GB** free on the card. Setup can take 20 minutes or longer.
It works offline. Keep a separate backup of your game files: after setup succeeds, all files and
subfolders inside `gamedata/` are removed, and that folder is left empty. If setup is interrupted,
the supplied files remain in place; launch Broforce again to resume. See
`ports/broforce/patchlog.txt` for setup details and `ports/broforce/log.txt` for launcher and game
output.

Setup asks about ASTC texture compression quality, picture shape, render resolution, and face-button
labels in the Controls menu. General artwork uses ASTC 6×6; texture atlases named `Font Texture`
use ASTC 4×4 to preserve glyph edges. The current Linux game data contains only empty 0×0
`Font Texture` placeholders, so the converter skips them; pre-rendered text artwork stays on the
general 6×6 setting. **75%** render resolution is the default. **50%** reduces the work for
the GPU further. The picture fills the screen by default, with fixed aspect ratios available if
you prefer black bars. Physical controls work by position in either button-label mode.

You can edit these text files in `ports/broforce/` after setup.

| File | Values |
| --- | --- |
| `resolution.txt` | `0.75`, `0.5`, `0.833`, or `device` |
| `aspect.txt` | `fill`, `16:9`, `4:3`, or `1:1` |
| `buttons.txt` | `nintendo` or `xbox` |

The port runs on 64-bit ARM firmware with SDL2, OpenGL ES 3, and ASTC support. It uses the ARMv7
player when the firmware provides armhf libraries and the AArch64 player otherwise. This port
supports offline play.

Saves and settings are in `ports/broforce/game-32/` or `ports/broforce/game-64/`. Back up that
folder before reinstalling or removing the port.

## Controls

| Control | Action |
| --- | --- |
| D-pad / left stick | Move |
| A | Confirm / Jump |
| B | Back / Grenade |
| X | Join / Fire |
| Y | Melee |
| Start | Pause |
| Select + Start | Quit |

On the Xbox layout, A and B are reversed, as are X and Y.

The port targets 64-bit ARM firmware. Its optional 32-bit ARMv7 Unity Mono route is included for
lower memory use and better overall performance on low-memory RG-XX devices.
It runs on AArch64 firmware that provides armhf userland. The launcher uses the AArch64 Unity
runtime when armhf userland is absent or its glibc is older than 2.35. Both routes use the same
Steam Linux game files; the ARM32 route does not support 32-bit-only handhelds.

## Compile

### 1. Install build tools

Build on x86-64 Linux, or on Windows through Ubuntu in WSL2. Install Git, curl, tar, xz, dpkg-deb,
Python 3.11 or newer, GCC, G++, Make,
ARM cross-binutils, and Docker. On Ubuntu or Debian Linux:

```bash
sudo apt update
sudo apt install git curl tar xz-utils dpkg-dev python3 build-essential \
  binutils-arm-linux-gnueabihf binutils-aarch64-linux-gnu
```

On Windows, install Ubuntu with WSL2 and Docker Desktop, then enable Docker Desktop's WSL
integration for Ubuntu. Start Docker before building.

### 2. Clone the source

```bash
git clone https://github.com/ronaxdevil/Portmaster_Broforce.git
cd Portmaster_Broforce
```

The individual stage commands below assume the pinned dependencies have been fetched and the build
environment is configured as in the source repository's `README.md`. Run these commands from the
cloned repository root. For a fresh checkout, `bash tools/build.sh` performs setup and runs
every stage in order.

### 3. Build the Mono runtime

```bash
bash tools/build-mono.sh
```

This builds the ARM64 Mono bridge, runtime, and class libraries from the pinned source revisions.

### 4. Build the Unity host runtimes

```bash
bash tools/build-hosts.sh
```

This builds both `ua_host` (ARM32/armhf) and `ua_host64` (AArch64).

### 5. Package the port

```bash
python3 tools/build.py
```

The packager strips unneeded symbols, adds the runtime and compatibility tools, and writes
`output/broforce.zip`. To fetch pinned tools and dependencies, initialize the build environment,
and run every stage in order with one command instead, use:

```bash
bash tools/build.sh
```
