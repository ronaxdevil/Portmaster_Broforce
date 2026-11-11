## Notes

Thanks to [Free Lives](https://freelives.net/) for Broforce, and to wild1walker for the Unity porting tools.

Requires **Broforce for Linux from Steam**. Open Steam's console with `steam://open/console` and enter
`download_depot 274190 274193`. Copy the downloaded `depot_274193` folder into
`ports/broforce/gamedata/`. You can also copy the Linux `Broforce_Data` folder directly into
`gamedata/`. The port verifies the files before setup.

Install the port with PortMaster and start **Broforce** from Ports. The first launch builds the game
on the handheld and needs at least **4.5 GB** free on the card. The first setup can take 20 minutes
or longer. It works offline. Keep a separate backup of your game files: after setup succeeds, the
verified input files in `gamedata/` are removed. Other files are retained. If setup is interrupted,
launch Broforce again to resume. See `ports/broforce/patchlog.txt` for setup details and
`ports/broforce/log.txt` for launcher and game output.

Setup asks about ASTC texture compression quality, picture shape, render resolution, and face-button
labels in the Controls menu. **75%** render resolution is the default. **50%** reduces the work for
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
