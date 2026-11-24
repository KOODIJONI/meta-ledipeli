from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Enemy:
    x: float
    y: float
    size_x: int = 3
    size_y: int = 2
    color: tuple[int, int, int] = (0, 255, 120)
    points: int = 10
    hp: int = 1
    alive: bool = True
    anim_frame: int = 0
    _anim_timer: float = 0.0
    anim_interval: float = 0.4  # seconds per animation frame
    hit_flash_duration: float = 0.15  # seconds to fade from white back to original color
    _hit_flash_timer: float = 0.0

    def move(self, dx: float, dy: float = 0.0) -> None:
        """Shift enemy position in grid coordinates."""
        if not self.alive:
            return
        self.x += dx
        self.y += dy

    def update(self, dt: float) -> None:
        """Advance enemy animation timer (dt in seconds)."""
        if not self.alive:
            return
        self._anim_timer += dt

        if self._hit_flash_timer > 0.0:
            self._hit_flash_timer = max(0.0, self._hit_flash_timer - max(float(dt), 0.0))

        if self._anim_timer >= self.anim_interval:
            self._anim_timer -= self.anim_interval
            self.anim_frame = 1 - self.anim_frame

    def take_damage(self, amount: int = 1) -> bool:
        """Apply damage; returns True if the enemy is defeated by this hit."""
        if not self.alive:
            return False
        self.hp -= amount

        if self.hit_flash_duration > 0.0:
            self._hit_flash_timer = self.hit_flash_duration

        if self.hp <= 0:
            self.hp = 0
            self.alive = False
            return True
        return False
    
    def _current_color(self) -> tuple[int, int, int]:
        """Interpolate from white (255, 255, 255) back toward `self.color`."""
        br, bg, bb = self.color
        if self._hit_flash_timer <= 0.0 or self.hit_flash_duration <= 0.0:
            return (br, bg, bb)

        t = max(0.0, min(1.0, self._hit_flash_timer / self.hit_flash_duration))
        r = int(round(br + (255 - br) * t))
        g = int(round(bg + (255 - bg) * t))
        b = int(round(bb + (255 - bb) * t))
        return (r, g, b)
    def bounds(self) -> tuple[int, int, int, int]:
        """Return (x1, y1, x2, y2) inclusive grid bounds for collision and drawing."""
        x1 = int(round(self.x))
        y1 = int(round(self.y))
        x2 = int(round(self.x + self.size_x - 1))
        y2 = int(round(self.y + self.size_y - 1))
        return (x1, y1, x2, y2)

    def draw(self, game) -> None:
        """Draw the enemy onto a BaseGame CLI matrix."""
        if not self.alive:
            return

        x1, y1, x2, y2 = self.bounds()
        r, g, b = self._current_color()
        game.fill_rect(x1, y1, x2, y2, r, g, b)

        if self.size_x >= 3 and self.size_y >= 2:
            if self.anim_frame == 0:
                game.set_led_pixel(x1, y2, 0, 0, 0)
                game.set_led_pixel(x2, y2, 0, 0, 0)
            else:
                game.set_led_pixel(x1 + 1, y2, 0, 0, 0)
                if x2 - 1 > x1 + 1:
                    game.set_led_pixel(x2 - 1, y2, 0, 0, 0)
@dataclass
class SquidEnemy(Enemy):
    color: tuple[int, int, int] = (255, 80, 180)
    points: int = 30


@dataclass
class CrabEnemy(Enemy):
    color: tuple[int, int, int] = (0, 220, 255)
    points: int = 20


@dataclass
class TankEnemy(Enemy):
    color: tuple[int, int, int] = (255, 170, 0)
    points: int = 50
    hp: int = 2