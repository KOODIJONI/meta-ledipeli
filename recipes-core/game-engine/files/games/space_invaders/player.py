from .projectile import Projectile

class Player:
    def __init__(self, startpos,size):
        self.x, self.y = startpos
        self.size_x, self.size_y = size
        self.projectile_count = 1
        self.pool = [Projectile(0.0, 0.0, active=False) for _ in range(self.projectile_count)]
        self.color = (255, 0, 0)
        self.bullet_speed= -60
    def move_x(self,pos_x):
        self.x =pos_x

    def bounds(self):
        return self.x, self.y, self.x+self.size_x, self.y+self.size_y

    def shoot(self) -> Projectile | None:
        print("sho")
        for proj in self.pool:
            if not proj.active:
                proj.x = float(self.x + self.size_x / 2.0)
                proj.y = float(self.y - 2)
                proj.vx = 0.0
                proj.vy = self.bullet_speed
                proj.owner = "player"
                proj.color = (255, 255, 80)
                proj.length = 2
                proj.active = True
                return proj
        return None

    def update_projectiles(self, dt: float, rows: int, cols: int) -> None:
        for proj in self.pool:
            if proj.active:
                proj.update(dt, rows, cols)

    def draw_projectiles(self, game) -> None:
        for proj in self.pool:
            if proj.active:
                proj.draw(game)

    def draw(self, game) -> None:


        x1, y1, x2, y2 = self.bounds()
        r, g, b = self.color
        game.fill_rect(x1, y1, x2, y2, r, g, b)
        game.set_led_pixel(x1,y1,0,0,0)
        game.set_led_pixel(self.x+self.size_x,y1,0,0,0)

    def draw_lifes(self, game) -> None:
        rows = game.rows
        max_lives = max(3, int(getattr(game, "max_lives", 3)))
        lives = max(0, int(getattr(game, "lives", 0)))
        y = rows - 2

        for heart in range(max_lives):
            x = 2 + heart * 5
            if heart < lives:
                # Active life: bright red/pink
                color = (255, 60, 80)
            else:
                # Lost life: dim dark red/gray
                color = (45, 10, 15)

            game.set_led_pixel(x, y, color[0], color[1], color[2])