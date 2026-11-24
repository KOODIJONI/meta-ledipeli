from __future__ import annotations

from base_game.base_game import BaseGame, Gesture
from .player import Player
from .enemyformation import EnemyFormation
from .collisions import check_collisions
from .projectile import Projectile
from .count_down import Countdown
from base_game.text_renderer import draw_text_centered
import time

class space_invaders(BaseGame):
    def __init__(
            self,
            socket_path=None,
            config=None,
            mqtt_client=None,
            mqtt_broker=None,
            state_prefix: str = "game",
            tracker=None,
        ):
        super().__init__(
            socket_path=socket_path,
            config=config,
            mqtt_client=mqtt_client,
            mqtt_broker=mqtt_broker,
            state_prefix=state_prefix,
            tracker=tracker,
        )
    
        self.cursor_x = self.cols // 2
        self.cursor_y = self.rows // 2
        self.target_x = (self.cols * 3) // 4
        self.target_y = self.rows // 2
        self.trail: set[tuple[int, int]] = set()
        self.gesture = Gesture.UNKNOWN
        self.palette = [
            (0, 220, 255),  
            (255, 200, 0),  
            (80, 255, 120), 
            (255, 80, 180), 
        ]
        self.color_idx = 0
        self._prev_gesture = Gesture.UNKNOWN
        self.player = Player((32,40),(4,2))
        self.lives = 3
        self.count_down = True

        self.formation = EnemyFormation(
            cols_grid=self.cols,
            rows_grid=self.rows,
            formation_cols=7,
            formation_rows=3,
        )
        self.enemy_bullets: list = []
        self.score = 0
        self.countdown = Countdown(seconds=3.0, scale=3, color=(255, 220, 60))
        self._game_over_time = 0.0
        self._title_duration = 3.0
        self._title_start = 0.0
        self.reset_game(start_countdown=False)
        self._show_title()  
                
    def _show_title(self):
        self.state = "title"
        self._title_start = time.monotonic()

    def handle_input(self, hand_state):
        pos = self.get_hand_position(hand_state, index=0)
        if pos is not None:
            norm_x, norm_y = pos
            self.cursor_x = min(max(int(norm_x * self.cols), 0), self.cols - 1 - self.player.size_x)
            self.cursor_y = min(max(int(norm_y * self.rows), 0), self.rows - 1)

        gesture = self.get_hand_gesture(hand_state, index=0)

        if self.state == "playing" and gesture == Gesture.POINTING:
            self.player.shoot()

        elif self.state == "game_over" and time.monotonic() - self._game_over_time > 1.0:
            self.reset_game(start_countdown=True)

        self._prev_gesture = gesture
    def update(self):

        if self.state == "title":
            if time.monotonic() - self._title_start >= self._title_duration:
                self.countdown.start(3.0)
                self.state = "countdown"
            return
        if self.state == "game_over":
            return

        if self.state == "countdown":
            if not self.countdown.update(0.0167):
                self.state = "playing"
            return

        self.player.move_x(self.cursor_x)
        self.player.update_projectiles(0.0167, self.rows, self.cols)
        self.formation.update(0.0167, on_enemy_shoot=self._spawn_enemy_bullet)

        if self.formation.all_cleared:
            self.formation.spawn()

        if self.formation.has_reached_row(self.player.y):
            self._trigger_game_over()          # was reset_game(...)
            return

        for bullet in self.enemy_bullets:
            bullet.update(0.0167, self.rows, self.cols)
        self.enemy_bullets = [b for b in self.enemy_bullets if b.active]

        active_player_shots = [p for p in self.player.pool if p.active]
        self.score += check_collisions(
            player=self.player,
            enemies=self.formation.alive_enemies,
            player_projectiles=active_player_shots,
            enemy_projectiles=self.enemy_bullets,
            on_player_hit=self._on_player_hit,
        )

    def _spawn_enemy_bullet(self, x: float, y: float) -> None:

        self.enemy_bullets.append(
            Projectile(
                x=x,
                y=y,
                vx=0.0,
                vy=16.0,       # positive moves downward toward the player
                owner="alien",
                color=(255, 70, 70),
                length=2,
                active=True,
            )
        )
    def render(self):
        
        if self.state == "title":
            self._render_game_name()
            return

        if self.state == "game_over":
            self._render_game_over()
            return

        self.player.draw(self)
        self.player.draw_projectiles(self)
        self.formation.draw(self)
        for bullet in self.enemy_bullets:
            bullet.draw(self)
        self.player.draw_lifes(self)
        if self.state == "countdown":
            self.countdown.draw(self)
            

    def reset_game(self, start_countdown: bool = False) -> None:
        self.score = 0
        self.lives = 3
        self.enemy_bullets = []
        self.player.x = max(0, min(self.cols // 2, self.cols - 1 - self.player.size_x))
        for proj in self.player.pool:
            proj.active = False
        self.formation.spawn()

        if start_countdown:
            self.countdown.start(3.0)
            self.state = "countdown"
        else:
            self.countdown.stop()
            self.state = "playing"

    def _on_player_hit(self, player, proj):
        self.lives -= 1
        if self.lives <= 0:
            self._trigger_game_over()

    def _trigger_game_over(self):
        self.state = "game_over"
        self._game_over_time = time.monotonic()

    def _render_game_name(self):
        draw_text_centered(self, "SPACE", 3,  (255, 60, 60), scale=2)
        draw_text_centered(self, "INVADERS", 21, (255, 60, 60), scale=1)
        draw_text_centered(self, str(self.score), 40, (255, 220, 60)) 

    def _render_game_over(self):
        draw_text_centered(self, "GAME", 3,  (255, 60, 60), scale=3)
        draw_text_centered(self, "OVER", 21, (255, 60, 60), scale=3)
        draw_text_centered(self, str(self.score), 40, (255, 220, 60)) 
