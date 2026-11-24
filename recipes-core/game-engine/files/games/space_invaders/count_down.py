from __future__ import annotations

from dataclasses import dataclass, field


# 3x5 pixel glyphs for digits 0-9
DIGITS_3X5: dict[str, tuple[str, ...]] = {
    "0": (
        "###",
        "#.#",
        "#.#",
        "#.#",
        "###",
    ),
    "1": (
        ".#.",
        "##.",
        ".#.",
        ".#.",
        "###",
    ),
    "2": (
        "###",
        "..#",
        "###",
        "#..",
        "###",
    ),
    "3": (
        "###",
        "..#",
        "###",
        "..#",
        "###",
    ),
    "4": (
        "#.#",
        "#.#",
        "###",
        "..#",
        "..#",
    ),
    "5": (
        "###",
        "#..",
        "###",
        "..#",
        "###",
    ),
    "6": (
        "###",
        "#..",
        "###",
        "#.#",
        "###",
    ),
    "7": (
        "###",
        "..#",
        "..#",
        ".#.",
        ".#.",
    ),
    "8": (
        "###",
        "#.#",
        "###",
        "#.#",
        "###",
    ),
    "9": (
        "###",
        "#.#",
        "###",
        "..#",
        "###",
    ),
}


@dataclass
class Countdown:
    seconds: float = 3.0
    scale: int = 3  # 3x5 glyph * scale 3 = 9x15 grid pixels per digit
    color: tuple[int, int, int] = (255, 220, 60)
    remaining: float = field(init=False)
    active: bool = field(init=False, default=False)

    def __post_init__(self) -> None:
        self.remaining = max(float(self.seconds), 0.0)

    def start(self, seconds: float | None = None) -> None:
        """Start or restart the countdown."""
        if seconds is not None:
            self.seconds = max(float(seconds), 0.0)
        self.remaining = self.seconds
        self.active = self.remaining > 0.0

    def stop(self) -> None:
        """Cancel/finish the countdown immediately."""
        self.remaining = 0.0
        self.active = False

    @property
    def current_number(self) -> int:
        """Integer number to display (e.g., 3, 2, 1)."""
        if not self.active or self.remaining <= 0.0:
            return 0
        return max(1, int(self.remaining + 0.999))

    @property
    def finished(self) -> bool:
        """True once the countdown has completed."""
        return not self.active and self.remaining <= 0.0

    def update(self, dt: float) -> bool:
        """
        Advance countdown by `dt` (in seconds).
        Returns True while still counting down, False when finished.
        """
        if not self.active:
            return False

        self.remaining = max(0.0, self.remaining - max(float(dt), 0.0))
        if self.remaining <= 0.0:
            self.active = False
            return False
        return True

    def draw(self, game) -> None:
        """Draw the current countdown digit centered on `game`'s matrix."""
        if not self.active:
            return

        text = str(self.current_number)
        glyph_w = 3
        glyph_h = 5
        gap = 1

        total_glyph_cols = len(text) * glyph_w + max(len(text) - 1, 0) * gap
        pixel_w = total_glyph_cols * self.scale
        pixel_h = glyph_h * self.scale

        start_x = (game.cols - pixel_w) // 2
        start_y = (game.rows - pixel_h) // 2
        r, g, b = self.color

        cursor_x = start_x
        for ch in text:
            rows = DIGITS_3X5.get(ch)
            if rows is None:
                continue
            for row_idx, pattern in enumerate(rows):
                for col_idx, cell in enumerate(pattern):
                    if cell == "#":
                        x1 = cursor_x + col_idx * self.scale
                        y1 = start_y + row_idx * self.scale
                        x2 = x1 + self.scale - 1
                        y2 = y1 + self.scale - 1
                        game.fill_rect(x1, y1, x2, y2, r, g, b)
            cursor_x += (glyph_w + gap) * self.scale