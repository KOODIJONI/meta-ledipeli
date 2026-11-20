from __future__ import annotations

import random

from .enemy import CrabEnemy, Enemy, SquidEnemy, TankEnemy


class EnemyFormation:
    def __init__(
        self,
        cols_grid: int = 48,
        rows_grid: int = 48,
        formation_cols: int = 7,
        formation_rows: int = 3,
        start_x: float = 4.0,
        start_y: float = 3.0,
        spacing_x: float = 5.0,
        spacing_y: float = 4.0,
        base_speed: float = 8.0,      # grid columns per second
        speed_boost: float = 12.0,    # extra speed when few enemies remain
        drop_step: float = 2.0,       # rows dropped when hitting an edge
        left_margin: int = 1,
        right_margin: int = 1,
    ):
        self.cols_grid = cols_grid
        self.rows_grid = rows_grid
        self.formation_cols = formation_cols
        self.formation_rows = formation_rows
        self.start_x = start_x
        self.start_y = start_y
        self.spacing_x = spacing_x
        self.spacing_y = spacing_y

        self.base_speed = base_speed
        self.speed_boost = speed_boost
        self.drop_step = drop_step
        self.left_margin = left_margin
        self.right_margin = right_margin

        self.direction: int = 1  # 1 = right, -1 = left
        self.enemies: list[Enemy] = []
        self._fire_timer: float = 1.2
        self.fire_interval: float = 1.4

        self.spawn()

    def spawn(self) -> None:
        """Create a fresh formation of enemies across rows and columns."""
        self.enemies.clear()
        self.direction = 1
        self._fire_timer = self.fire_interval

        for r in range(self.formation_rows):
            for c in range(self.formation_cols):
                x = self.start_x + c * self.spacing_x
                y = self.start_y + r * self.spacing_y

                if r == 0:
                    enemy: Enemy = SquidEnemy(x=x, y=y)
                elif r == 1:
                    enemy = CrabEnemy(x=x, y=y)
                else:
                    enemy = TankEnemy(x=x, y=y)

                self.enemies.append(enemy)

    @property
    def alive_enemies(self) -> list[Enemy]:
        """Return all currently living enemies."""
        return [e for e in self.enemies if e.alive]

    @property
    def all_cleared(self) -> bool:
        """True when every enemy in the formation has been defeated."""
        return len(self.alive_enemies) == 0

    def _current_speed(self) -> float:
        """Scale speed up as fewer enemies remain."""
        total = max(len(self.enemies), 1)
        alive = len(self.alive_enemies)
        defeated_ratio = 1.0 - (alive / total)
        return self.base_speed + self.speed_boost * defeated_ratio

    def update(self, dt: float, on_enemy_shoot=None) -> None:
        """Advance enemy animations, formation movement, and optional enemy firing."""
        living = self.alive_enemies
        if not living:
            return

        for enemy in living:
            enemy.update(dt)

        dx = self.direction * self._current_speed() * dt
        hit_edge = False

        for enemy in living:
            x1, _, x2, _ = enemy.bounds()
            next_x1 = x1 + dx
            next_x2 = x2 + dx
            if next_x1 < self.left_margin or next_x2 >= self.cols_grid - self.right_margin:
                hit_edge = True
                break

        if hit_edge:
            self.direction *= -1
            for enemy in living:
                enemy.move(0.0, self.drop_step)
        else:
            for enemy in living:
                enemy.move(dx, 0.0)

        # Optional periodic shot from a random living enemy
        if callable(on_enemy_shoot):
            self._fire_timer -= dt
            if self._fire_timer <= 0.0:
                self._fire_timer = self.fire_interval
                shooter = random.choice(living)
                sx = shooter.x + shooter.size_x / 2.0
                sy = shooter.y + shooter.size_y
                on_enemy_shoot(sx, sy)

    def draw(self, game) -> None:
        """Draw all living enemies onto the game CLI matrix."""
        for enemy in self.alive_enemies:
            enemy.draw(game)
            
    def has_reached_row(self, target_y: float) -> bool:
        """Return True if any living enemy has reached or passed `target_y`."""
        for enemy in self.alive_enemies:
            _, _, _, y2 = enemy.bounds()
            if y2 >= round(target_y):
                return True
        return False