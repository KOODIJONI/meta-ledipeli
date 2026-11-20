"""3x5 pixel-font text renderer for LED-matrix games.

Drop this in `base_game/text_renderer.py`. It only needs the game object to
provide `fill_rect(x1, y1, x2, y2, r, g, b)`, `cols` and `rows`
(which BaseGame already does).
"""
from __future__ import annotations

GLYPH_W = 3
GLYPH_H = 5

FONT: dict[str, tuple[str, ...]] = {
    # digits
    "0": ("###", "#.#", "#.#", "#.#", "###"),
    "1": (".#.", "##.", ".#.", ".#.", "###"),
    "2": ("###", "..#", "###", "#..", "###"),
    "3": ("###", "..#", "###", "..#", "###"),
    "4": ("#.#", "#.#", "###", "..#", "..#"),
    "5": ("###", "#..", "###", "..#", "###"),
    "6": ("###", "#..", "###", "#.#", "###"),
    "7": ("###", "..#", "..#", ".#.", ".#."),
    "8": ("###", "#.#", "###", "#.#", "###"),
    "9": ("###", "#.#", "###", "..#", "###"),
    # letters
    "A": (".#.", "#.#", "###", "#.#", "#.#"),
    "B": ("##.", "#.#", "##.", "#.#", "##."),
    "C": (".##", "#..", "#..", "#..", ".##"),
    "D": ("##.", "#.#", "#.#", "#.#", "##."),
    "E": ("###", "#..", "##.", "#..", "###"),
    "F": ("###", "#..", "##.", "#..", "#.."),
    "G": (".##", "#..", "#.#", "#.#", ".##"),
    "H": ("#.#", "#.#", "###", "#.#", "#.#"),
    "I": ("###", ".#.", ".#.", ".#.", "###"),
    "J": ("..#", "..#", "..#", "#.#", ".#."),
    "K": ("#.#", "#.#", "##.", "#.#", "#.#"),
    "L": ("#..", "#..", "#..", "#..", "###"),
    "M": ("#.#", "###", "###", "#.#", "#.#"),
    "N": ("###", "#.#", "#.#", "#.#", "#.#"),
    "O": ("###", "#.#", "#.#", "#.#", "###"),
    "P": ("###", "#.#", "###", "#..", "#.."),
    "Q": ("###", "#.#", "#.#", "###", "..#"),
    "R": ("##.", "#.#", "##.", "#.#", "#.#"),
    "S": (".##", "#..", ".#.", "..#", "##."),
    "T": ("###", ".#.", ".#.", ".#.", ".#."),
    "U": ("#.#", "#.#", "#.#", "#.#", "###"),
    "V": ("#.#", "#.#", "#.#", "#.#", ".#."),
    "W": ("#.#", "#.#", "###", "###", "#.#"),
    "X": ("#.#", "#.#", ".#.", "#.#", "#.#"),
    "Y": ("#.#", "#.#", ".#.", ".#.", ".#."),
    "Z": ("###", "..#", ".#.", "#..", "###"),
    # punctuation
    " ": ("...", "...", "...", "...", "..."),
    "!": (".#.", ".#.", ".#.", "...", ".#."),
    "?": ("###", "..#", ".##", "...", ".#."),
    ".": ("...", "...", "...", "...", ".#."),
    ":": ("...", ".#.", "...", ".#.", "..."),
    "-": ("...", "...", "###", "...", "..."),
    "+": ("...", ".#.", "###", ".#.", "..."),
    "/": ("..#", "..#", ".#.", "#..", "#.."),
}

Color = tuple[int, int, int]


def _glyph(ch: str) -> tuple[str, ...]:
    return FONT.get(ch.upper(), FONT["?"])


def text_width(text: str, scale: int = 1, spacing: int = 1) -> int:
    """Width in matrix pixels. `spacing` is the gap between letters in glyph pixels."""
    if not text:
        return 0
    return (len(text) * GLYPH_W + (len(text) - 1) * spacing) * scale


def text_height(scale: int = 1) -> int:
    return GLYPH_H * scale


def fit_scale(text: str, max_width: int, max_scale: int = 4, spacing: int = 1) -> int:
    """Largest integer scale (>= 1) at which `text` fits within `max_width`."""
    scale = max_scale
    while scale > 1 and text_width(text, scale, spacing) > max_width:
        scale -= 1
    return scale


def draw_text(
    game,
    text: str,
    x: int,
    y: int,
    color: Color = (255, 255, 255),
    scale: int = 1,
    spacing: int = 1,
) -> int:
    """Draw `text` with its top-left corner at (x, y). Returns the pixel width drawn.

    Horizontal runs of lit pixels are merged into a single fill_rect call, which
    keeps the number of C-driver calls low. Everything is clipped to the matrix.
    """
    r, g, b = color
    cols, rows = game.cols, game.rows
    scale = max(1, int(scale))
    cursor_x = int(x)

    for ch in text:
        glyph = _glyph(ch)
        for row_idx, pattern in enumerate(glyph):
            py1 = y + row_idx * scale
            py2 = py1 + scale - 1
            if py2 < 0 or py1 >= rows:
                continue
            py1, py2 = max(py1, 0), min(py2, rows - 1)

            col = 0
            while col < GLYPH_W:
                if pattern[col] != "#":
                    col += 1
                    continue
                start = col
                while col < GLYPH_W and pattern[col] == "#":
                    col += 1
                px1 = cursor_x + start * scale
                px2 = cursor_x + col * scale - 1
                if px2 < 0 or px1 >= cols:
                    continue
                game.fill_rect(max(px1, 0), py1, min(px2, cols - 1), py2, r, g, b)

        cursor_x += (GLYPH_W + spacing) * scale

    return text_width(text, scale, spacing)


def draw_text_centered(
    game,
    text: str,
    y: int,
    color: Color = (255, 255, 255),
    scale: int = 1,
    spacing: int = 1,
) -> int:
    """Draw `text` horizontally centered on the matrix, top edge at `y`."""
    x = (game.cols - text_width(text, scale, spacing)) // 2
    return draw_text(game, text, x, y, color, scale, spacing)


def draw_text_block(
    game,
    lines: list[str],
    y: int,
    color: Color = (255, 255, 255),
    scale: int = 1,
    line_gap: int = 2,
    spacing: int = 1,
) -> int:
    """Draw several centered lines top to bottom. Returns the y below the last line."""
    for line in lines:
        draw_text_centered(game, line, y, color, scale, spacing)
        y += text_height(scale) + line_gap
    return y
