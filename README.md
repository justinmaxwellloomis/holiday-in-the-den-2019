# Save Christmas — Holiday in the Den 2019

North Paulding High School Computer Science Honor Society

Santa's sleigh is out of control! Up to 8 elves work together to catch the falling
presents (+3) and dodge the ornaments (−1 and a tumble). Grab the gold star for higher
jumps and double speed. Fill the score bar to save Christmas; the elf with the most
points wins.

The same `main.py` runs on a PC and in a web browser.

## Play on a PC

```
pip install pygame-ce        # classic "pygame" 2.x also works
python main.py               # windowed (resizable)
python main.py --fullscreen  # for the event screen
```

`Save_Christmas.py` still works as a launcher too.

## Play in a browser

Build it with [pygbag](https://pypi.org/project/pygbag/):

```
pip install pygbag
pygbag .                     # builds and serves at http://localhost:8000
pygbag --build .             # just builds build/web (index.html + .apk)
```

Or skip the build: zip this folder and upload it on the NPHS Game Design site under
**Instructor Dashboard → Holiday Games**. The site packages it for the browser itself.

## Controls

| | |
|---|---|
| Start / continue | ENTER, SPACE, mouse click, or gamepad START (button 9) |
| Player 1 | A / D move, W jump |
| Player 2 | arrow keys |
| Player 3 | J / L move, I jump |
| Player 4 | numpad 4 / 6 move, 8 jump |
| Gamepads | stick or d-pad to move, any face/shoulder button to jump, SELECT (button 8) to sit out or rejoin |
| PC only | F11 fullscreen, ESC quit |

Each gamepad and each keyboard player gets the next free elf (Blue, Green, Orange,
Pink, Purple, Red, White, Yellow). Gamepads join when connected; keyboard players join
the first time they press one of their keys.

## Project layout

```
main.py              the game (works on PC and in pygbag)
Save_Christmas.py    launcher kept from 2019
assets/images/       sprites, background, signs
assets/sounds/       sound effects and music (.ogg, which browsers need)
```

## What changed from the 2019 version

- **Crash fixed:** `random.randint` was given float limits, which Python 3.12+ rejects,
  so the game crashed when the first present fell.
- **Runs off Windows:** file paths used `\` and file names didn't match their case
  (`sparkle.png` vs `Sparkle.png`, `star.wav` vs `Star.wav`), so the game only loaded on
  Windows.
- **Browser support:** the main loop is `async` and yields every frame, as pygbag requires;
  sounds are `.ogg` (about 1 MB instead of 10 MB of `.wav`).
- **Keyboard players** alongside gamepads; gamepads are tracked as they connect and
  disconnect instead of assuming exactly 8 and reopening them every frame.
- **Safer game flow:** a round can't start with no elves, and returns to the directions
  sign if every player leaves. The score bar can't overflow past full.
- **Refactor:** globals replaced with a `Game` class; presents and ornaments share one
  `Faller` class; physics lives on a shared `Body` base; platforms are built from a
  `platform()` helper. Gameplay constants are unchanged from 2019.
- `SnowTest.py` (an older copy of the game) was removed; it is still in Git history.
