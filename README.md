# Pitch Black Theme

True-black (`#000000`) themes for Zed, built for OLED displays.

## Variants

- Pitch Black · Xcode
- Pitch Black · Dark+
- Pitch Black · Oxocarbon I / II / III
- Pitch Black · IBM Carbon
- Pitch Black · Ultraviolet
- Pitch Black · Tokyo Night
- Pitch Black · Catppuccin Mocha
- Pitch Black · Dracula
- Pitch Black · Gruvbox
- Pitch Black · Nord
- Pitch Black · Rosé Pine
- Pitch Black · One Dark
- Pitch Black · Kanagawa
- Pitch Black · Everforest
- Pitch Black · Solarized
- Pitch Black · Monokai Pro
- Pitch Black · Ayu Dark
- Pitch Black · Night Owl
- Pitch Black · GitHub Dark
- Pitch Black · Material
- Pitch Black · Synthwave '84
- Pitch Black · Poimandres
- Pitch Black · Vesper
- Pitch Black · Moonfly
- Pitch Black · Nightfox
- Pitch Black · Oceanic Next
- Pitch Black · Cobalt2
- Pitch Black · Andromeda
- Pitch Black · Horizon
- Pitch Black · Panda
- Pitch Black · Shades of Purple
- Pitch Black · Sonokai
- Pitch Black · Iceberg

## Adding a variant

Add a palette to `PALETTES` in `scripts/generate.py`, then run `python3 scripts/generate.py`.
It reuses the true-black UI from the Xcode variant and regenerates only the palette-based variants.

Every variant also gets readability fixes for pure black (tinted active tab, search vs selection,
terminal bright colours, diff visibility). Change `ACTIVE_TAB_CONTRAST` in the script for a stronger
or subtler active tab. Run `python3 scripts/audit.py` afterwards to check all variants.

## Install locally

1. In Zed, open the Extensions page (`cmd-shift-x`).
2. Click **Install Dev Extension** and select this folder.
3. Open the theme selector (`cmd-k cmd-t`) and pick a Pitch Black variant.
