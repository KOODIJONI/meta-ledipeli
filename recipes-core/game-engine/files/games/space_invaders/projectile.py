from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Projectile:
    x: float
    y: float
    vx: float = 0.0
    vy: float = -24.0
    owner: str = "player"
    color: tuple[int, int, int] = (255, 255, 80)
    length: int = 2
    active: bool = False

    def activate(
        self,
        x: float,
        y: float,
        vy: float = -24.0,
        vx: float = 0.0,
        owner: str = "player",
        color: tuple[int, int, int] = (255, 255, 80),
        length: int = 2,
    ) -> None:
        self.x = x
        self.y = y
        self.vx = vx
        self.vy = vy
        self.owner = owner
        self.color = color
        self.length = length
        self.active = True

    def update(self, dt: float, rows: int, cols: int) -> None:
        if not self.active:
            return

        self.x += self.vx * dt
        self.y += self.vy * dt

        if self.x < 0 or self.x >= cols or self.y + self.length < 0 or self.y >= rows:
            self.active = False

    def bounds(self) -> tuple[int, int, int, int]:
        x1 = int(round(self.x))
        y1 = int(round(self.y))
        x2 = x1
        y2 = int(round(self.y + self.length - 1))
        return (min(x1, x2), min(y1, y2), max(x1, x2), max(y1, y2))

    def draw(self, game) -> None:
        if not self.active:
            return

        x1, y1, x2, y2 = self.bounds()
        r, g, b = self.color
        game.fill_rect(x1, y1, x2, y2, r, g, b)