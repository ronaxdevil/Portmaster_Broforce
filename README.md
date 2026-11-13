# Broforce PortMaster build source

Build the BYO-data Broforce port on x86-64 Linux or Windows with WSL. The build produces `../output/broforce.zip` and an unpacked PortMaster submission staging folder. It does not require a copy of Broforce: the player supplies the supported Steam Linux game files when installing the port.

The current package version is **0.2.4**.

## Build

Install Git, curl, tar, xz, dpkg-deb, Python 3.11 or newer, GCC, G++, Make, ARM cross-binutils, and Docker with ARM64 container support. Start Docker before building. On Debian or Ubuntu, the non-Docker tools can be installed with:

```bash
sudo apt install git curl tar xz-utils dpkg-dev python3 build-essential binutils-arm-linux-gnueabihf binutils-aarch64-linux-gnu
```

From the cloned repository root, run:

```bash
bash tools/build.sh
```

The build scripts, dependency locks, and build notices helper are in `tools/`. The first build downloads its pinned dependencies into `tools/dependencies/`; generated objects and the unpacked submission staging folder are in `tools/.build/`. Both generated folders are ignored by Git. The resulting port ZIP is written to `output/broforce.zip` and contains the files needed for offline setup on a handheld.

The build fetches [ronaxdevil/portmaster-unity](https://github.com/ronaxdevil/portmaster-unity) at the revision in `tools/dependencies.lock`, initializes its libhybris submodule, and applies the tracked packaging-space and Mono build patches. Existing conflicting checkouts are not reset. `tools/sysroots.lock.json` pins the Debian ARM packages; the fetcher checks the downloaded archives against their hashes.

The Unity Android players are carried in small donor APKs built using the corresponding Unity editor versions, rather than downloaded as standalone APKs from Unity. For now, the build downloads the published [Cuphead 2026.11.01.2 release](https://github.com/wild1walker/portmaster-cuphead/releases/tag/2026.11.01.2), verifies its SHA-256, and takes only the three donor APKs from it. Those donors match the files used by the tested Broforce release. No Cuphead or Broforce game data is included.

The 64-bit bridge is built from the pinned PortMaster Unity source. The Mono runtime and class libraries are built from Unity's MIT-licensed Mono source at the revision in `tools/dependencies.lock`. The ARM64 Docker builds fetch their source dependencies into the ignored `tools/dependencies/mono64/` directory; Docker also downloads its build images. ARM64 emulation makes this substantially slower on an x86-64 machine.

The build downloads pinned versions of Rust, the ARM musl cross-compiler, Zig, .NET, UnityPy's class database, the Cuphead donor package, and the two ARM sysroots into `tools/dependencies/`. The Git source includes the Broforce compatibility and button-label patches, launcher, setup scripts, metadata, artwork, and licenses. At first launch, the port copies PortMaster's installed patcher to a private working directory and changes its hard-coded dialogue speaker from Cybion to Ronax, leaving PortMaster's shared patcher untouched.

## Installation notes

### Get Steam data

Requires **Broforce for Linux from Steam**.

1. Open Steam's console with `steam://open/console` and enter:

   ```text
   download_depot 274190 274193
   ```

2. Copy the downloaded `depot_274193` folder into `ports/broforce/gamedata/`. Alternatively, copy
   its Linux `Broforce_Data` folder directly into `gamedata/`.
3. Setup verifies the files against `package/broforce/setup/linux.sha256` before conversion.

### Setup

Install the port with PortMaster and start **Broforce** from Ports. First launch builds the game
on the handheld and needs at least **4.5 GB** free on the card. Setup can take 20 minutes or longer
and works offline. Keep an independent backup of your game files: after successful setup, unchanged
verified input files in `gamedata/` are removed; other files are retained. If setup is interrupted,
launch Broforce again to resume. Setup logs are in `ports/broforce/patchlog.txt`; launcher and game
output is in `ports/broforce/log.txt`.

### Runtime, settings, and controls

The port targets 64-bit ARM firmware with SDL2, OpenGL ES 3, and ASTC support. The optional 32-bit
ARMv7 Unity Mono route is included for lower memory use and better overall performance on low-memory
RG-XX devices. It runs when AArch64 firmware has armhf userland; otherwise, or when armhf glibc is
older than 2.35, the launcher uses the AArch64 Unity runtime. Both routes use the same Steam Linux
game files. This ARM32 process route does not support 32-bit-only handhelds.

The setup questions select ASTC texture compression quality, picture shape, render resolution, and
the button labels shown in the Controls menu. General artwork uses ASTC 6×6; texture atlases named
`Font Texture` use ASTC 4×4 to preserve glyph edges. The supplied Linux game data has only empty
0×0 `Font Texture` placeholders, which the converter skips; pre-rendered text artwork uses the
general 6×6 setting. Render resolution defaults to **75%**; **50%** reduces GPU work further. The
picture fills the screen by default, with fixed aspect ratios available.

| Setting file | Values |
| --- | --- |
| `resolution.txt` | `0.75`, `0.5`, `0.833`, or `device` |
| `aspect.txt` | `fill`, `16:9`, `4:3`, or `1:1` |
| `buttons.txt` | `nintendo` or `xbox` |

Saves and settings are stored in `ports/broforce/game-32/` or `ports/broforce/game-64/`. Back up
that folder before reinstalling or removing the port. Select + Start quits the game.

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

Broforce port code is MIT licensed under Copyright (c) 2026 Ronax. The port also includes the relevant upstream component notices.

Thanks to [Free Lives](https://freelives.net/) for Broforce, and to wild1walker for the Unity porting tools.
