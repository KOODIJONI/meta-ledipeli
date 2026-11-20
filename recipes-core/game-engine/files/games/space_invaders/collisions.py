from __future__ import annotations

from typing import Iterable


Rect = tuple[int | float, int | float, int | float, int | float]


def rects_overlap(a: Rect, b: Rect) -> bool:
    """Return True if two inclusive axis-aligned boxes (x1, y1, x2, y2) overlap."""
    ax1, ay1, ax2, ay2 = a
    bx1, by1, bx2, by2 = b
    return ax1 <= bx2 and ax2 >= bx1 and ay1 <= by2 and ay2 >= by1


def check_collisions(
    player,
    enemies: Iterable,
    player_projectiles: Iterable,
    enemy_projectiles: Iterable = (),
    on_enemy_defeated=None,
    on_player_hit=None,
) -> int:
    """
    Check collisions for active projectiles and return points earned this tick.

    - `player_projectiles` with `owner == "player"` (or any active shot) vs alive `enemies`.
    - `enemy_projectiles` with `owner == "alien"` (or any active shot) vs `player`.
    """
    points_earned = 0
    player_bounds = player.bounds() if player is not None else None

    for proj in player_projectiles:
        if not getattr(proj, "active", False):
            continue
        if getattr(proj, "owner", "player") != "player":
            continue

        p_bounds = proj.bounds()
        for enemy in enemies:
            if not getattr(enemy, "alive", False):
                continue

            if rects_overlap(p_bounds, enemy.bounds()):
                proj.active = False
                defeated = enemy.take_damage(1)
                if defeated:
                    pts = int(getattr(enemy, "points", 0))
                    points_earned += pts
                    if callable(on_enemy_defeated):
                        on_enemy_defeated(enemy, pts)
                break  # one projectile hits one enemy

    if player_bounds is not None:
        for proj in enemy_projectiles:
            if not getattr(proj, "active", False):
                continue
            if getattr(proj, "owner", "alien") == "player":
                continue

            if rects_overlap(proj.bounds(), player_bounds):
                proj.active = False
                if callable(on_player_hit):
                    on_player_hit(player, proj)

    return points_earned