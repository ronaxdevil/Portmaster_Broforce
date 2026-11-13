# Broforce PortMaster build source

Build the BYO-data Broforce port on x86-64 Linux or Windows with WSL. The build produces `../output/broforce.zip` and an unpacked PortMaster submission staging folder. It does not require a copy of Broforce: the player supplies the supported Steam Linux game files when installing the port.

## Build

Install Git, curl, tar, xz, dpkg-deb, Python 3.11 or newer, GCC, G++, Make, and Docker with ARM64 container support. Start Docker before building. On Debian or Ubuntu, the non-Docker tools can be installed with:

```bash
sudo apt install git curl tar xz-utils dpkg-dev python3 build-essential
```

From this directory, run:

```bash
bash build.sh
```

The first build downloads its pinned dependencies and may take substantial time and disk space. Downloads are stored in `dependencies/`; generated objects and the unpacked submission staging folder are in `.build/`. Both folders are ignored by Git. The resulting port ZIP contains the files needed for offline setup on a handheld.

The build fetches [ronaxdevil/portmaster-unity](https://github.com/ronaxdevil/portmaster-unity) at the revision in `dependencies.lock`, initializes its libhybris submodule, and applies the tracked packaging-space and Mono build patches. Existing conflicting checkouts are not reset. `sysroots.lock.json` pins the Debian ARM packages; the fetcher checks the downloaded archives against their hashes.

The Unity Android players are carried in small donor APKs built using the corresponding Unity editor versions, rather than downloaded as standalone APKs from Unity. For now, the build downloads the published [Cuphead 2026.11.01.2 release](https://github.com/wild1walker/portmaster-cuphead/releases/tag/2026.11.01.2), verifies its SHA-256, and takes only the three donor APKs from it. Those donors match the files used by the tested Broforce release. No Cuphead or Broforce game data is included.

The 64-bit bridge is built from the pinned PortMaster Unity source. The Mono runtime and class libraries are built from Unity's MIT-licensed Mono source at the revision in `dependencies.lock`. The ARM64 Docker builds fetch their source dependencies into the ignored `dependencies/mono64/` directory; Docker also downloads its build images. ARM64 emulation makes this substantially slower on an x86-64 machine.

The build downloads pinned versions of Rust, the ARM musl cross-compiler, Zig, .NET, UnityPy's class database, and the two ARM sysroots into `dependencies/`. The Git source includes the Broforce compatibility and button-label patches, launcher, setup scripts, metadata, artwork, and licenses.

## Installation notes

The player supplies the exact Steam Linux data identified by `package/broforce/setup/linux.sha256`. After successful device setup, unchanged game-input files listed in that manifest are removed from `gamedata`; keep an independent backup. Saves are stored in the built game directory. See the port README packaged in the ZIP for installation and controls.

Broforce port code is MIT licensed under Copyright (c) 2026 Ronax. The port also includes the relevant upstream component notices.
