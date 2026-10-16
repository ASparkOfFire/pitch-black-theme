"""Generate extra Pitch Black variants from palettes.

Uses "Pitch Black · Xcode" as the structural template: every black/neutral
surface key is kept, every hue-bearing key is rebuilt from the palette.
Re-running replaces previously generated variants, so it is idempotent.

Every variant (original and generated) also goes through `polish()`, which
fixes readability issues on pure black and fills keys Zed would otherwise
take from its built-in default theme.

    python3 scripts/generate.py
    python3 scripts/audit.py
"""

import colorsys
import copy
import json
import math
from pathlib import Path

THEME_FILE = Path(__file__).resolve().parent.parent / "themes" / "pitch-black.json"
TEMPLATE = "Pitch Black · Xcode"

# Contrast (vs #000000) the active tab tint must reach; raise to make it stronger.
ACTIVE_TAB_CONTRAST = 1.3

# Alpha for error / conflict / info backgrounds (diagnostic popovers, banners).
STATUS_BG_ALPHA = "33"

# ui: fg, muted, comment, accent, red, green, yellow, blue, magenta, cyan, orange, purple
# syn: keyword, string, function, type, number, constant, property, operator,
#      punct, tag, attribute, builtin, escape, preproc, variant, link, special
PALETTES = {
    "Tokyo Night": dict(
        fg="#c0caf5", muted="#737aa2", comment="#565f89", accent="#7aa2f7",
        red="#f7768e", green="#9ece6a", yellow="#e0af68", blue="#7aa2f7",
        magenta="#bb9af7", cyan="#7dcfff", orange="#ff9e64", purple="#9d7cd8",
        keyword="#bb9af7", string="#9ece6a", function="#7aa2f7", type="#2ac3de",
        number="#ff9e64", constant="#ff9e64", property="#73daca", operator="#89ddff",
        punct="#a9b1d6", tag="#f7768e", attribute="#e0af68", builtin="#2ac3de",
        escape="#89ddff", preproc="#7dcfff", variant="#ff9e64", link="#73daca",
        special="#f7768e",
    ),
    "Catppuccin Mocha": dict(
        fg="#cdd6f4", muted="#9399b2", comment="#7f849c", accent="#cba6f7",
        red="#f38ba8", green="#a6e3a1", yellow="#f9e2af", blue="#89b4fa",
        magenta="#f5c2e7", cyan="#94e2d5", orange="#fab387", purple="#cba6f7",
        keyword="#cba6f7", string="#a6e3a1", function="#89b4fa", type="#f9e2af",
        number="#fab387", constant="#fab387", property="#b4befe", operator="#89dceb",
        punct="#9399b2", tag="#89b4fa", attribute="#f9e2af", builtin="#f38ba8",
        escape="#f5c2e7", preproc="#f5c2e7", variant="#74c7ec", link="#89b4fa",
        special="#f38ba8",
    ),
    "Dracula": dict(
        fg="#f8f8f2", muted="#8c94b8", comment="#6272a4", accent="#bd93f9",
        red="#ff5555", green="#50fa7b", yellow="#f1fa8c", blue="#8be9fd",
        magenta="#ff79c6", cyan="#8be9fd", orange="#ffb86c", purple="#bd93f9",
        keyword="#ff79c6", string="#f1fa8c", function="#50fa7b", type="#8be9fd",
        number="#bd93f9", constant="#bd93f9", property="#f8f8f2", operator="#ff79c6",
        punct="#f8f8f2", tag="#ff79c6", attribute="#50fa7b", builtin="#8be9fd",
        escape="#ff79c6", preproc="#ff79c6", variant="#bd93f9", link="#8be9fd",
        special="#ffb86c",
    ),
    "Gruvbox": dict(
        fg="#ebdbb2", muted="#a89984", comment="#928374", accent="#fabd2f",
        red="#fb4934", green="#b8bb26", yellow="#fabd2f", blue="#83a598",
        magenta="#d3869b", cyan="#8ec07c", orange="#fe8019", purple="#d3869b",
        keyword="#fb4934", string="#b8bb26", function="#8ec07c", type="#fabd2f",
        number="#d3869b", constant="#d3869b", property="#83a598", operator="#ebdbb2",
        punct="#a89984", tag="#fb4934", attribute="#fabd2f", builtin="#fe8019",
        escape="#fe8019", preproc="#8ec07c", variant="#d3869b", link="#83a598",
        special="#fe8019",
    ),
    "Nord": dict(
        fg="#d8dee9", muted="#8a93a5", comment="#616e88", accent="#88c0d0",
        red="#bf616a", green="#a3be8c", yellow="#ebcb8b", blue="#81a1c1",
        magenta="#b48ead", cyan="#88c0d0", orange="#d08770", purple="#b48ead",
        keyword="#81a1c1", string="#a3be8c", function="#88c0d0", type="#8fbcbb",
        number="#b48ead", constant="#b48ead", property="#d8dee9", operator="#81a1c1",
        punct="#eceff4", tag="#81a1c1", attribute="#8fbcbb", builtin="#81a1c1",
        escape="#ebcb8b", preproc="#5e81ac", variant="#b48ead", link="#88c0d0",
        special="#d08770",
    ),
    "Rosé Pine": dict(
        fg="#e0def4", muted="#908caa", comment="#6e6a86", accent="#c4a7e7",
        red="#eb6f92", green="#9ccfd8", yellow="#f6c177", blue="#31748f",
        magenta="#ebbcba", cyan="#9ccfd8", orange="#f6c177", purple="#c4a7e7",
        keyword="#3e8fb0", string="#f6c177", function="#ebbcba", type="#9ccfd8",
        number="#f6c177", constant="#f6c177", property="#c4a7e7", operator="#908caa",
        punct="#908caa", tag="#9ccfd8", attribute="#c4a7e7", builtin="#eb6f92",
        escape="#3e8fb0", preproc="#c4a7e7", variant="#ebbcba", link="#c4a7e7",
        special="#eb6f92",
    ),
    "One Dark": dict(
        fg="#abb2bf", muted="#828997", comment="#5c6370", accent="#61afef",
        red="#e06c75", green="#98c379", yellow="#e5c07b", blue="#61afef",
        magenta="#c678dd", cyan="#56b6c2", orange="#d19a66", purple="#c678dd",
        keyword="#c678dd", string="#98c379", function="#61afef", type="#e5c07b",
        number="#d19a66", constant="#d19a66", property="#e06c75", operator="#56b6c2",
        punct="#abb2bf", tag="#e06c75", attribute="#d19a66", builtin="#56b6c2",
        escape="#56b6c2", preproc="#c678dd", variant="#d19a66", link="#61afef",
        special="#e06c75",
    ),
    "Kanagawa": dict(
        fg="#dcd7ba", muted="#9a9a8a", comment="#727169", accent="#7e9cd8",
        red="#e46876", green="#98bb6c", yellow="#e6c384", blue="#7e9cd8",
        magenta="#d27e99", cyan="#7fb4ca", orange="#ffa066", purple="#957fb8",
        keyword="#957fb8", string="#98bb6c", function="#7e9cd8", type="#7aa89f",
        number="#d27e99", constant="#ffa066", property="#e6c384", operator="#c0a36e",
        punct="#9cabca", tag="#e6c384", attribute="#e6c384", builtin="#7fb4ca",
        escape="#ffa066", preproc="#e46876", variant="#ffa066", link="#7fb4ca",
        special="#e46876",
    ),
    "Everforest": dict(
        fg="#d3c6aa", muted="#9da9a0", comment="#7a8478", accent="#a7c080",
        red="#e67e80", green="#a7c080", yellow="#dbbc7f", blue="#7fbbb3",
        magenta="#d699b6", cyan="#83c092", orange="#e69875", purple="#d699b6",
        keyword="#e67e80", string="#83c092", function="#a7c080", type="#dbbc7f",
        number="#d699b6", constant="#d699b6", property="#7fbbb3", operator="#e69875",
        punct="#9da9a0", tag="#e69875", attribute="#dbbc7f", builtin="#7fbbb3",
        escape="#e69875", preproc="#d699b6", variant="#83c092", link="#7fbbb3",
        special="#e69875",
    ),
    "Solarized": dict(
        fg="#93a1a1", muted="#839496", comment="#586e75", accent="#268bd2",
        red="#dc322f", green="#859900", yellow="#b58900", blue="#268bd2",
        magenta="#d33682", cyan="#2aa198", orange="#cb4b16", purple="#6c71c4",
        keyword="#859900", string="#2aa198", function="#268bd2", type="#b58900",
        number="#d33682", constant="#2aa198", property="#6c71c4", operator="#859900",
        punct="#839496", tag="#268bd2", attribute="#b58900", builtin="#cb4b16",
        escape="#dc322f", preproc="#cb4b16", variant="#6c71c4", link="#268bd2",
        special="#dc322f",
    ),
    "Monokai Pro": dict(
        fg="#fcfcfa", muted="#939293", comment="#727072", accent="#ffd866",
        red="#ff6188", green="#a9dc76", yellow="#ffd866", blue="#78dce8",
        magenta="#ff6188", cyan="#78dce8", orange="#fc9867", purple="#ab9df2",
        keyword="#ff6188", string="#ffd866", function="#a9dc76", type="#78dce8",
        number="#ab9df2", constant="#ab9df2", property="#fcfcfa", operator="#ff6188",
        punct="#939293", tag="#ff6188", attribute="#78dce8", builtin="#78dce8",
        escape="#ab9df2", preproc="#ff6188", variant="#ab9df2", link="#78dce8",
        special="#fc9867",
    ),
    "Ayu Dark": dict(
        fg="#bfbdb6", muted="#8a8986", comment="#646b73", accent="#e6b450",
        red="#f07178", green="#aad94c", yellow="#e6b450", blue="#59c2ff",
        magenta="#d2a6ff", cyan="#95e6cb", orange="#ff8f40", purple="#d2a6ff",
        keyword="#ff8f40", string="#aad94c", function="#ffb454", type="#59c2ff",
        number="#d2a6ff", constant="#d2a6ff", property="#39bae6", operator="#f29668",
        punct="#bfbdb6", tag="#39bae6", attribute="#ffb454", builtin="#f07178",
        escape="#95e6cb", preproc="#e6b673", variant="#d2a6ff", link="#39bae6",
        special="#e6b673",
    ),
    "Night Owl": dict(
        fg="#d6deeb", muted="#8badc1", comment="#637777", accent="#82aaff",
        red="#ef5350", green="#addb67", yellow="#ecc48d", blue="#82aaff",
        magenta="#c792ea", cyan="#7fdbca", orange="#f78c6c", purple="#c792ea",
        keyword="#c792ea", string="#ecc48d", function="#82aaff", type="#ffcb8b",
        number="#f78c6c", constant="#f78c6c", property="#7fdbca", operator="#7fdbca",
        punct="#d6deeb", tag="#7fdbca", attribute="#addb67", builtin="#addb67",
        escape="#f78c6c", preproc="#c792ea", variant="#82aaff", link="#80cbc4",
        special="#ff5874",
    ),
    "GitHub Dark": dict(
        fg="#e6edf3", muted="#8b949e", comment="#8b949e", accent="#58a6ff",
        red="#ff7b72", green="#3fb950", yellow="#d29922", blue="#58a6ff",
        magenta="#bc8cff", cyan="#39c5cf", orange="#ffa657", purple="#d2a8ff",
        keyword="#ff7b72", string="#a5d6ff", function="#d2a8ff", type="#ffa657",
        number="#79c0ff", constant="#79c0ff", property="#79c0ff", operator="#ff7b72",
        punct="#e6edf3", tag="#7ee787", attribute="#79c0ff", builtin="#ffa657",
        escape="#79c0ff", preproc="#ff7b72", variant="#79c0ff", link="#a5d6ff",
        special="#ffa657",
    ),
    "Material": dict(
        fg="#eeffff", muted="#8a9ba8", comment="#546e7a", accent="#80cbc4",
        red="#f07178", green="#c3e88d", yellow="#ffcb6b", blue="#82aaff",
        magenta="#c792ea", cyan="#89ddff", orange="#f78c6c", purple="#c792ea",
        keyword="#c792ea", string="#c3e88d", function="#82aaff", type="#ffcb6b",
        number="#f78c6c", constant="#f78c6c", property="#b2ccd6", operator="#89ddff",
        punct="#89ddff", tag="#f07178", attribute="#ffcb6b", builtin="#89ddff",
        escape="#89ddff", preproc="#c792ea", variant="#f78c6c", link="#80cbc4",
        special="#f07178",
    ),
    "Synthwave '84": dict(
        fg="#f0eff1", muted="#a8a4c4", comment="#848bbd", accent="#ff7edb",
        red="#fe4450", green="#72f1b8", yellow="#fede5d", blue="#2ee2fa",
        magenta="#ff7edb", cyan="#36f9f6", orange="#ff8b39", purple="#b893ce",
        keyword="#fede5d", string="#ff8b39", function="#36f9f6", type="#fe4450",
        number="#f97e72", constant="#f97e72", property="#ff7edb", operator="#fede5d",
        punct="#b6b1b1", tag="#72f1b8", attribute="#fede5d", builtin="#fe4450",
        escape="#f97e72", preproc="#72f1b8", variant="#f97e72", link="#36f9f6",
        special="#ff7edb",
    ),
    "Poimandres": dict(
        fg="#e4f0fb", muted="#a6accd", comment="#767c9d", accent="#5de4c7",
        red="#d0679d", green="#5de4c7", yellow="#fffac2", blue="#89ddff",
        magenta="#fcc5e9", cyan="#add7ff", orange="#fffac2", purple="#91b4d5",
        keyword="#91b4d5", string="#5de4c7", function="#add7ff", type="#a6accd",
        number="#5de4c7", constant="#add7ff", property="#e4f0fb", operator="#91b4d5",
        punct="#a6accd", tag="#5de4c7", attribute="#91b4d5", builtin="#5fb3a1",
        escape="#fcc5e9", preproc="#d0679d", variant="#5fb3a1", link="#add7ff",
        special="#fcc5e9",
    ),
    "Vesper": dict(
        fg="#ffffff", muted="#a0a0a0", comment="#6c6c6c", accent="#ffc799",
        red="#ff8080", green="#99ffe4", yellow="#ffc799", blue="#a0a0a0",
        magenta="#ff8080", cyan="#99ffe4", orange="#ffc799", purple="#a0a0a0",
        keyword="#a0a0a0", string="#99ffe4", function="#ffc799", type="#ffc799",
        number="#ffc799", constant="#ffc799", property="#ffffff", operator="#a0a0a0",
        punct="#a0a0a0", tag="#a0a0a0", attribute="#ffc799", builtin="#ffc799",
        escape="#99ffe4", preproc="#a0a0a0", variant="#ffc799", link="#99ffe4",
        special="#ff8080",
    ),
    "Moonfly": dict(
        fg="#bdbdbd", muted="#9e9e9e", comment="#808080", accent="#74b2ff",
        red="#ff5d5d", green="#8cc85f", yellow="#e3c78a", blue="#80a0ff",
        magenta="#cf87e8", cyan="#79dac8", orange="#de935f", purple="#ae81ff",
        keyword="#cf87e8", string="#c6c684", function="#74b2ff", type="#36c692",
        number="#f09479", constant="#f09479", property="#85dc85", operator="#e65e72",
        punct="#9e9e9e", tag="#80a0ff", attribute="#79dac8", builtin="#36c692",
        escape="#e3c78a", preproc="#ff5189", variant="#f09479", link="#79dac8",
        special="#ff5189",
    ),
    "Nightfox": dict(
        fg="#cdcecf", muted="#aeafb0", comment="#738091", accent="#719cd6",
        red="#c94f6d", green="#81b29a", yellow="#dbc074", blue="#719cd6",
        magenta="#d67ad2", cyan="#63cdcf", orange="#f4a261", purple="#9d79d6",
        keyword="#9d79d6", string="#81b29a", function="#719cd6", type="#dbc074",
        number="#f4a261", constant="#f4a261", property="#63cdcf", operator="#aeafb0",
        punct="#aeafb0", tag="#c94f6d", attribute="#dbc074", builtin="#c94f6d",
        escape="#d67ad2", preproc="#d67ad2", variant="#f4a261", link="#63cdcf",
        special="#d67ad2",
    ),
    "Oceanic Next": dict(
        fg="#c0c5ce", muted="#a7adba", comment="#65737e", accent="#6699cc",
        red="#ec5f67", green="#99c794", yellow="#fac863", blue="#6699cc",
        magenta="#c594c5", cyan="#5fb3b3", orange="#f99157", purple="#c594c5",
        keyword="#c594c5", string="#99c794", function="#6699cc", type="#fac863",
        number="#f99157", constant="#f99157", property="#ec5f67", operator="#5fb3b3",
        punct="#5fb3b3", tag="#ec5f67", attribute="#fac863", builtin="#5fb3b3",
        escape="#ab7967", preproc="#c594c5", variant="#f99157", link="#6699cc",
        special="#ab7967",
    ),
    "Cobalt2": dict(
        fg="#ffffff", muted="#a0a8b8", comment="#0088ff", accent="#ffc600",
        red="#ff628c", green="#3ad900", yellow="#ffc600", blue="#0088ff",
        magenta="#fb94ff", cyan="#9effff", orange="#ff9d00", purple="#fb94ff",
        keyword="#ff9d00", string="#3ad900", function="#ffc600", type="#80ffbb",
        number="#ff628c", constant="#ff628c", property="#9effff", operator="#ff9d00",
        punct="#e1efff", tag="#9effff", attribute="#ffc600", builtin="#fb94ff",
        escape="#ff628c", preproc="#ff9d00", variant="#ff628c", link="#9effff",
        special="#fb94ff",
    ),
    "Andromeda": dict(
        fg="#d5ced9", muted="#a0a1a7", comment="#757888", accent="#00e8c6",
        red="#ee5d43", green="#96e072", yellow="#ffe66d", blue="#7cb7ff",
        magenta="#ff00aa", cyan="#00e8c6", orange="#f39c12", purple="#c74ded",
        keyword="#c74ded", string="#96e072", function="#ffe66d", type="#f39c12",
        number="#f39c12", constant="#ee5d43", property="#00e8c6", operator="#ee5d43",
        punct="#d5ced9", tag="#ff00aa", attribute="#ffe66d", builtin="#7cb7ff",
        escape="#00e8c6", preproc="#c74ded", variant="#f39c12", link="#7cb7ff",
        special="#ff00aa",
    ),
    "Horizon": dict(
        fg="#d5d8da", muted="#9da0a2", comment="#6c6f93", accent="#e95678",
        red="#e95678", green="#29d398", yellow="#fab795", blue="#26bbd9",
        magenta="#ee64ac", cyan="#59e1e3", orange="#f09483", purple="#b877db",
        keyword="#b877db", string="#fab795", function="#25b0bc", type="#fac29a",
        number="#f09483", constant="#f09483", property="#e95678", operator="#b877db",
        punct="#9da0a2", tag="#e95678", attribute="#fab795", builtin="#25b0bc",
        escape="#59e1e3", preproc="#ee64ac", variant="#f09483", link="#59e1e3",
        special="#ee64ac",
    ),
    "Panda": dict(
        fg="#e6e6e6", muted="#a0a4ae", comment="#676b79", accent="#ff75b5",
        red="#ff2c6d", green="#19f9d8", yellow="#ffcc95", blue="#45a9f9",
        magenta="#ff75b5", cyan="#19f9d8", orange="#ffb86c", purple="#b084eb",
        keyword="#ff75b5", string="#19f9d8", function="#6fc1ff", type="#ffb86c",
        number="#ffb86c", constant="#ffb86c", property="#b084eb", operator="#f3f3f3",
        punct="#e6e6e6", tag="#ff75b5", attribute="#ffb86c", builtin="#b084eb",
        escape="#ff9ac1", preproc="#ff75b5", variant="#ffb86c", link="#45a9f9",
        special="#ff9ac1",
    ),
    "Shades of Purple": dict(
        fg="#ffffff", muted="#a599e9", comment="#b362ff", accent="#fad000",
        red="#ec3a37", green="#a5ff90", yellow="#fad000", blue="#7f6bff",
        magenta="#ff628c", cyan="#80fcff", orange="#ff9d00", purple="#b362ff",
        keyword="#ff9d00", string="#a5ff90", function="#fad000", type="#fb94ff",
        number="#ff628c", constant="#ff628c", property="#9effff", operator="#ff9d00",
        punct="#e1efff", tag="#9effff", attribute="#fad000", builtin="#fb94ff",
        escape="#ff628c", preproc="#ff9d00", variant="#ff628c", link="#80fcff",
        special="#fb94ff",
    ),
    "Sonokai": dict(
        fg="#e2e2e3", muted="#a0a4ad", comment="#7f8490", accent="#76cce0",
        red="#fc5d7c", green="#9ed072", yellow="#e7c664", blue="#76cce0",
        magenta="#b39df3", cyan="#76cce0", orange="#f39660", purple="#b39df3",
        keyword="#fc5d7c", string="#e7c664", function="#9ed072", type="#76cce0",
        number="#b39df3", constant="#f39660", property="#f39660", operator="#fc5d7c",
        punct="#a0a4ad", tag="#fc5d7c", attribute="#e7c664", builtin="#76cce0",
        escape="#b39df3", preproc="#fc5d7c", variant="#b39df3", link="#76cce0",
        special="#f39660",
    ),
    "Iceberg": dict(
        fg="#c6c8d1", muted="#9a9ca5", comment="#6b7089", accent="#84a0c6",
        red="#e27878", green="#b4be82", yellow="#e2a478", blue="#84a0c6",
        magenta="#a093c7", cyan="#89b8c2", orange="#e2a478", purple="#a093c7",
        keyword="#84a0c6", string="#89b8c2", function="#e2a478", type="#b4be82",
        number="#a093c7", constant="#a093c7", property="#c6c8d1", operator="#84a0c6",
        punct="#9a9ca5", tag="#84a0c6", attribute="#b4be82", builtin="#89b8c2",
        escape="#e27878", preproc="#b4be82", variant="#a093c7", link="#89b8c2",
        special="#e27878",
    ),
}


def rgb(h):
    h = h.lstrip("#")
    return [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]


def alpha(h):
    h = h.lstrip("#")
    return int(h[6:8], 16) / 255 if len(h) == 8 else 1.0


def to_hex(c):
    return "#" + "".join(f"{round(max(0.0, min(1.0, x)) * 255):02x}" for x in c)


def mix(a, b, t):
    """Opaque blend of hex a toward hex b by t (0..1)."""
    return to_hex([x + (y - x) * t for x, y in zip(rgb(a), rgb(b))])


def over_black(h):
    return [x * alpha(h) for x in rgb(h)]


def _linear(x):
    return x / 12.92 if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4


def luminance(c):
    r, g, b = map(_linear, c)
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def contrast(fg, bg="#000000"):
    a, b = luminance(over_black(fg)), luminance(over_black(bg))
    return (max(a, b) + 0.05) / (min(a, b) + 0.05)


def delta_e(a, b):
    """CIE76 colour difference, both colours composited over black."""
    def lab(c):
        r, g, b_ = map(_linear, c)
        x = (0.4124 * r + 0.3576 * g + 0.1805 * b_) / 0.95047
        y = 0.2126 * r + 0.7152 * g + 0.0722 * b_
        z = (0.0193 * r + 0.1192 * g + 0.9505 * b_) / 1.08883
        f = lambda t: t ** (1 / 3) if t > 0.008856 else 7.787 * t + 16 / 116
        return 116 * f(y) - 16, 500 * (f(x) - f(y)), 200 * (f(y) - f(z))
    return math.dist(lab(over_black(a)), lab(over_black(b)))


def grey_like(h):
    """Neutral grey with the same luminance as h."""
    y = luminance(rgb(h))
    v = y * 12.92 if y <= 0.0031308 else 1.055 * y ** (1 / 2.4) - 0.055
    return to_hex([v, v, v])


def tint(h, target):
    """Darkest opaque blend of h over black that reaches `target` contrast."""
    for step in range(5, 41):
        c = mix("#000000", h[:7], step / 100)
        if contrast(c) >= target:
            return c
    return mix("#000000", h[:7], 0.4)


def with_alpha_for(h, target):
    """Raise h's alpha (never lower it) until it reaches `target` contrast over black."""
    if contrast(h) >= target:
        return h
    for a in range(round(alpha(h) * 255), 0x100):
        if contrast(h[:7] + f"{a:02x}") >= target:
            return h[:7] + f"{a:02x}"
    return h[:7] + "ff"


def lift(h, target):
    """Mix h toward white until it reaches `target` contrast over black."""
    if contrast(h) >= target:
        return h
    for step in range(1, 101):
        c = mix(h[:7], "#ffffff", step / 100)
        if contrast(c) >= target:
            return c
    return "#ffffff"


def distinct(colors, pool, min_de=12):
    """Swap near-duplicate colours for unused pool colours, else a hue rotation."""
    out = []
    ok = lambda c: all(delta_e(c, o) >= min_de for o in out)
    for c in colors:
        if ok(c):
            out.append(c)
            continue
        pick = next((p for p in pool if ok(p)), None)
        if pick is None:
            h, l, s = colorsys.rgb_to_hls(*rgb(c))
            rotations = (to_hex(colorsys.hls_to_rgb((h + i / 12) % 1, l, max(s, 0.5))) for i in range(1, 12))
            pick = next((r for r in rotations if ok(r)), c)
        out.append(pick)
    return out


def derive(s):
    """Approximate palette roles for a hand-written variant."""
    ansi = lambda k: s[f"terminal.ansi.{k}"]
    return dict(accent=s["text.accent"], red=ansi("red"), green=ansi("green"),
                yellow=ansi("yellow"), blue=ansi("blue"), magenta=ansi("magenta"),
                cyan=ansi("cyan"), orange=ansi("yellow"))


def polish(s, c):
    """Readability fixes and extra keys shared by every variant."""
    # Active tab: accent tint, so the current file stands out from black inactive tabs.
    s["tab.active_background"] = tint(c["accent"], ACTIVE_TAB_CONTRAST)
    for key in ("error", "conflict", "info"):
        s[f"{key}.background"] = s[key][:7] + STATUS_BG_ALPHA

    # Selection must be visible on black, and line numbers readable.
    main = s["players"][0]
    main["selection"] = with_alpha_for(main["selection"], 1.5)
    s["editor.line_number"] = lift(s["editor.line_number"], 3.0)

    # Search hits need their own hue, not the selection's.
    if delta_e(s["search.match_background"], main["selection"]) < 15:
        hues = [c["yellow"], c["orange"], c["cyan"], c["green"], c["magenta"]]
        s["search.match_background"] = max(hues, key=lambda h: delta_e(h, c["accent"]))[:7] + "55"
    # Current match: as strong as possible while text on it stays readable.
    hue = s["search.match_background"][:7]
    active = next((a for a in range(0x8c, 0x60, -1) if contrast(s["text"], f"{hue}{a:02x}") >= 3.5), 0x60)
    s["search.active_match_background"] = f"{hue}{active:02x}"

    for kind in ("added", "deleted"):
        key = f"editor.diff_hunk.{kind}.background"
        s[key] = with_alpha_for(s[key], 1.25)
        s[f"editor.diff_hunk.{kind}.hollow_background"] = s[key][:7] + "0f"
        s[f"editor.diff_hunk.{kind}.hollow_border"] = s[key][:7] + "5c"
    s["version_control.word_added"] = s["editor.diff_hunk.added.background"][:7] + "59"
    s["version_control.word_deleted"] = s["editor.diff_hunk.deleted.background"][:7] + "59"

    # Keys Zed would otherwise fill from its default (grey/blue) dark theme.
    s.update({
        "element.selection_background": c["accent"][:7] + "40",
        "panel.overlay_background": s["panel.background"],
        "panel.overlay_hover": s["element.hover"],
        "panel.indent_guide": s["editor.indent_guide"],
        "panel.indent_guide_hover": s["editor.indent_guide_active"],
        "panel.indent_guide_active": s["editor.indent_guide_active"],
        "editor.hover_line_number": s["text.muted"],
        "editor.debugger_active_line.background": c["yellow"][:7] + "1f",
        "scrollbar.thumb.active_background": "#ffffff66",
        "drop_target.border": c["accent"][:7],
        "minimap.thumb.border": "#00000000",
        "version_control.conflict_marker.ours": c["green"][:7] + "33",
        "version_control.conflict_marker.theirs": c["blue"][:7] + "33",
    })


def build_style(template, p):
    s = copy.deepcopy(template)
    pool = [p[k] for k in ("red", "keyword", "string", "function", "type", "number", "property",
                           "attribute", "builtin", "tag", "special", "escape", "preproc", "link")]
    # "renamed" must not read as created (green), modified (yellow) or deleted (red).
    renamed = next((h for h in (p["cyan"], p["blue"], p["purple"], p["magenta"])
                    if min(delta_e(h, p[k]) for k in ("green", "yellow", "red")) >= 20), p["cyan"])

    def status(key, color):
        s[key] = color
        s[f"{key}.background"] = color + "1f"
        s[f"{key}.border"] = color + "66"

    s.update({
        "pane.focused_border": p["accent"] + "66",
        "panel.focused_border": p["accent"] + "66",
        "element.active": p["accent"] + "40",
        "ghost_element.active": p["accent"] + "40",
        "drop_target.background": p["accent"] + "33",
        "search.match_background": p["yellow"] + "55",
        "editor.document_highlight.read_background": p["comment"] + "40",
        "editor.document_highlight.write_background": p["comment"] + "66",
        "editor.document_highlight.bracket_background": p["comment"] + "40",
        "text": p["fg"],
        "text.muted": p["muted"],
        "text.placeholder": p["muted"],
        "text.accent": p["accent"],
        "icon": p["fg"],
        "icon.muted": p["muted"],
        "icon.placeholder": p["muted"],
        "icon.accent": p["accent"],
        "editor.foreground": p["fg"],
        "editor.line_number": p["comment"],
        "editor.active_line_number": p["fg"],
        "link_text.hover": p["link"],
        "hint": p["comment"],
        "predictive": p["muted"],
        "hidden": p["muted"],
        "accents": distinct([p["accent"], p["magenta"], p["green"], p["yellow"],
                             p["purple"], p["cyan"], p["orange"]], pool),
        "editor.diff_hunk.added.background": p["green"] + "33",
        "editor.diff_hunk.deleted.background": p["red"] + "33",
        "version_control.added": p["green"],
        "version_control.modified": p["yellow"],
        "version_control.deleted": p["red"],
        "version_control.renamed": renamed,
        "version_control.conflict": p["orange"],
        "terminal.foreground": p["fg"],
        "terminal.dim_foreground": p["muted"],
        "terminal.ansi.bright_black": grey_like(p["comment"]),
        "terminal.ansi.white": p["fg"],
    })
    status("error", p["red"])
    status("warning", p["yellow"])
    status("info", p["blue"])
    status("success", p["green"])
    status("conflict", p["orange"])
    status("created", p["green"])
    status("modified", p["yellow"])
    status("deleted", p["red"])
    status("renamed", renamed)
    status("unreachable", p["comment"])
    s["hint.background"] = p["comment"] + "1f"

    for name in ("red", "green", "yellow", "blue", "magenta", "cyan"):
        s[f"terminal.ansi.{name}"] = p[name]
        s[f"terminal.ansi.bright_{name}"] = mix(p[name], "#ffffff", 0.25)
        s[f"terminal.ansi.dim_{name}"] = p[name] + "99"
    s["terminal.ansi.dim_white"] = p["fg"] + "99"

    others = distinct([p["fg"], p["blue"], p["magenta"], p["green"], p["yellow"],
                       p["purple"], p["cyan"], p["orange"]], pool)[1:]
    s["players"] = [{"cursor": p["fg"], "background": p["fg"], "selection": p["accent"] + "40"}] + [
        {"cursor": c, "background": c, "selection": c + "40"} for c in others
    ]

    roles = {
        "attribute": "attribute", "boolean": "constant", "comment": "comment",
        "comment.doc": "comment", "constant": "constant", "constructor": "type",
        "embedded": "fg", "emphasis": "fg", "emphasis.strong": "fg", "enum": "type",
        "function": "function", "function.builtin": "builtin", "keyword": "keyword",
        "label": "keyword", "link_text": "link", "link_uri": "link", "number": "number",
        "operator": "operator", "preproc": "preproc", "property": "property",
        "punctuation": "punct", "punctuation.bracket": "punct",
        "punctuation.delimiter": "punct", "punctuation.list_marker": "keyword",
        "punctuation.special": "special", "string": "string", "string.escape": "escape",
        "string.regex": "escape", "string.special": "special",
        "string.special.symbol": "constant", "tag": "tag", "text.literal": "string",
        "title": "function", "type": "type", "type.builtin": "builtin",
        "variable": "fg", "variable.special": "special", "variant": "variant",
    }
    syntax = s["syntax"]
    for key, role in roles.items():
        syntax.setdefault(key, {})
        syntax[key]["color"] = p[role]
    syntax["comment"]["font_style"] = "italic"
    syntax["comment.doc"]["font_style"] = "italic"
    polish(s, p)
    return s


def main():
    family = json.loads(THEME_FILE.read_text())
    template = next(t for t in family["themes"] if t["name"] == TEMPLATE)
    generated = {f"Pitch Black · {name}" for name in PALETTES}
    family["themes"] = [t for t in family["themes"] if t["name"] not in generated]
    for theme in family["themes"]:
        polish(theme["style"], derive(theme["style"]))
    for name, palette in PALETTES.items():
        family["themes"].append({
            "name": f"Pitch Black · {name}",
            "appearance": "dark",
            "style": build_style(template["style"], palette),
        })
    THEME_FILE.write_text(json.dumps(family, indent=2, ensure_ascii=False) + "\n")
    print(f"wrote {len(family['themes'])} themes to {THEME_FILE}")


if __name__ == "__main__":
    main()
