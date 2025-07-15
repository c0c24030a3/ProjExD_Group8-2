import os
import sys
import pygame
import random
import math
# --- 作業ディレクトリをスクリプトの場所に設定 ---
os.chdir(os.path.dirname(os.path.abspath(__file__)))

# --- 初期化 ---
pygame.init()
WIDTH, HEIGHT = 480, 640
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("縦スクロールシューティング")
clock = pygame.time.Clock()

# --- 色定義 ---
WHITE = (255, 255, 255)
RED = (255, 80, 80)
BLACK = (0, 0, 0)

# --- 画像読み込み ---
bg_img = pygame.image.load("fig/rastboss.jpg")  # 固定背景画像
bg_img = pygame.transform.scale(bg_img, (WIDTH, HEIGHT))
BG_W, BG_H = bg_img.get_size()

f16_img = pygame.transform.rotate(pygame.transform.scale(pygame.image.load("fig/F16.png"), (60, 60)), 180)
sidewinder_img = pygame.transform.rotate(pygame.transform.scale(pygame.image.load("fig/sidewinder.png"), (70, 120)), 180)
beam_img = pygame.transform.scale(pygame.image.load("fig/beam.png"), (10, 20))
explosion_img = pygame.transform.scale(pygame.image.load("fig/explosion.gif"), (60, 60))
rasuboss_img = pygame.transform.scale(pygame.image.load("fig/ぱっちぃ.png"), (120, 120))


# --- フォントとスコア ---
font = pygame.font.SysFont(None, 36)
big_font = pygame.font.SysFont(None, 72)
score = 0

# --- 爆発エフェクト ---
class Explosion(pygame.sprite.Sprite):
    def __init__(self, center):
        super().__init__()
        self.image = explosion_img
        self.rect = self.image.get_rect(center=center)
        self.timer = 15

    def update(self):
        self.timer -= 1
        if self.timer <= 0:
            self.kill()

# --- Playerクラス ---
class Player:
    def __init__(self, char_data):
        self.name = char_data["name"]
        self.hp = char_data["hp"]
        self.speed = char_data["speed"]
        self.shot_speed = char_data["shot_speed"]
        self.image = pygame.transform.flip(pygame.transform.scale(char_data["image"], (40, 40)), True, False)
        self.rect = self.image.get_rect()
        self.rect.x = WIDTH // 2
        self.rect.y = HEIGHT - 60
        self.shot_timer = 0
        self.shots = []

    def move(self, keys):
        if keys[pygame.K_LEFT] and self.rect.x > 0:
            self.rect.x -= self.speed
        if keys[pygame.K_RIGHT] and self.rect.x < WIDTH - self.rect.width:
            self.rect.x += self.speed
        if keys[pygame.K_UP] and self.rect.y > 0:
            self.rect.y -= self.speed
        if keys[pygame.K_DOWN] and self.rect.y < HEIGHT - self.rect.height:
            self.rect.y += self.speed

    def update_shots(self):
        for shot in self.shots[:]:
            shot.move_ip(0, -10)
            if shot.bottom < 0:
                self.shots.remove(shot)

    def shoot(self, keys):
        self.shot_timer += 1
        if keys[pygame.K_SPACE] and self.shot_timer >= 60 / self.shot_speed:
            shot_rect = pygame.Rect(
                self.rect.x + self.rect.width // 2 - beam_img.get_width() // 2,
                self.rect.y,
                beam_img.get_width(),
                beam_img.get_height()
            )
            self.shots.append(shot_rect)
            self.shot_timer = 0

    def draw(self, screen):
        screen.blit(self.image, self.rect)
        for shot in self.shots:
            screen.blit(beam_img, shot)

# --- ミサイルクラス ---
class Sidewinder(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.image = sidewinder_img
        self.rect = self.image.get_rect(center=(x, y))
        self.rect.inflate_ip(-75, -50)
        self.speed = 4

    def update(self):
        self.rect.y += self.speed
        if self.rect.top > HEIGHT:
            self.kill()

# --- 敵クラス ---
class Enemy(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.image = f16_img
        self.rect = self.image.get_rect(center=(random.randint(30, WIDTH - 30), -30))
        self.speed = random.randint(2, 4)
        self.shot_timer = random.randint(30, 60)

    def update(self):
        self.rect.y += self.speed
        self.shot_timer -= 1
        if self.shot_timer <= 0:
            missile = Sidewinder(self.rect.centerx, self.rect.bottom)
            all_sprites.add(missile)
            missiles.add(missile)
            self.shot_timer = random.randint(90, 140)
        if self.rect.top > HEIGHT:
            self.kill()

class BossBullet(pygame.sprite.Sprite):
    def __init__(self, x, y, angle):
        super().__init__()
        self.image = sidewinder_img
        self.rect = self.image.get_rect(center=(x, y))
        self.rect.inflate_ip(-50, -50)
        self.vx = math.cos(angle) * 3
        self.vy = math.sin(angle) * 3

    def update(self):
        self.rect.x += self.vx
        self.rect.y += self.vy
        if (self.rect.right < 0 or self.rect.left > WIDTH or
                self.rect.bottom < 0 or self.rect.top > HEIGHT):
            self.kill()

# --- ラスボス ---
class Rasuboss(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.image = rasuboss_img
        self.rect = self.image.get_rect(center=(WIDTH // 2, 100))
        self.hp = 3000
        self.shot_timer = 0

    def update(self):
        self.shot_timer += 1
        if self.shot_timer % 60 == 0:
            for i in range(12):  # 12方向に発射
                angle = math.radians(i * 30)
                bullet = BossBullet(self.rect.centerx, self.rect.centery, angle)
                all_sprites.add(bullet)
                boss_bullets.add(bullet)

# --- グループ ---
boss_group = pygame.sprite.Group()
boss_bullets = pygame.sprite.Group()

# --- ゲームフラグ ---
game_clear = False
boss_spawned = False

# --- グループ定義 ---
all_sprites = pygame.sprite.Group()
enemies = pygame.sprite.Group()
missiles = pygame.sprite.Group()
explosions = pygame.sprite.Group()

characters = {
    "default": {
        "name": "デフォこうかとん",
        "hp": 10,
        "speed": 5,
        "shot_speed": 10,
        "image": pygame.image.load("fig/3.png")
    }
}

player = Player(characters["default"])
enemy_timer = 0
game_over = False
stage = 4
scroll=0
# --- ゲームループ ---
while True:
    clock.tick(60)

    # 入力イベント
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()

    if not game_over and not game_clear:
        keys = pygame.key.get_pressed()
        player.move(keys)
        player.shoot(keys)
        player.update_shots()

        # 敵出現（スコアが2000未満の場合のみ）
        if score < 100000:
            enemy_timer += 1
            if enemy_timer > 30:
                enemy = Enemy()
                all_sprites.add(enemy)
                enemies.add(enemy)
                enemy_timer = 0

        # スコア2000でラスボス出現
        if score >= 500 and not boss_spawned:
            enemies.empty()
            missiles.empty()
            boss = Rasuboss()
            boss_group.add(boss)
            all_sprites.add(boss)
            boss_spawned = True

        all_sprites.update()
        missiles.update()
        explosions.update()
        boss_bullets.update()

        # 衝突（弾 vs 敵）
        for shot in player.shots[:]:
            for enemy in enemies.sprites():
                if shot.colliderect(enemy.rect):
                    player.shots.remove(shot)
                    enemy.kill()
                    explosion = Explosion(enemy.rect.center)
                    all_sprites.add(explosion)
                    explosions.add(explosion)
                    score += 100
                    break

        # 衝突（弾 vs ラスボス）
        if boss_spawned:
            for shot in player.shots[:]:
                if shot.colliderect(boss.rect):
                    player.shots.remove(shot)
                    boss.hp -= 50
                    if boss.hp <= 0:
                        explosion = Explosion(boss.rect.center)
                        all_sprites.add(explosion)
                        explosions.add(explosion)
                        boss.kill()
                        game_clear = True

        # 衝突（敵・ミサイル・ボス弾 vs プレイヤー）
        if (any(enemy.rect.colliderect(player.rect) for enemy in enemies) or
            any(missile.rect.colliderect(player.rect) for missile in missiles) or
            any(b.rect.colliderect(player.rect) for b in boss_bullets)):
            explosion = Explosion(player.rect.center)
            all_sprites.add(explosion)
            explosions.add(explosion)
            game_over = True

    # --- 描画 ---
    screen.blit(bg_img, (0, 0))

    all_sprites.draw(screen)
    player.draw(screen)
    boss_bullets.draw(screen)

    # スコア
    score_text = font.render(f"Score: {score}", True, WHITE)
    screen.blit(score_text, (10, 10))

    # ラスボスHPバー
    if boss_spawned and boss.alive():
        hp_width = int(boss.hp / 1000 * 200)
        pygame.draw.rect(screen, RED, (WIDTH // 2 - 100, 20, hp_width, 20))
        pygame.draw.rect(screen, WHITE, (WIDTH // 2 - 100, 20, 200, 20), 2)

    # ゲームオーバー表示
    if game_over:
        over_text = big_font.render("GAME OVER", True, RED)
        info_text = font.render("Press any key to exit", True, WHITE)
        screen.blit(over_text, over_text.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 30)))
        screen.blit(info_text, info_text.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 30)))
        pygame.display.flip()
        pygame.time.wait(1000)
        waiting = True
        while waiting:
            for event in pygame.event.get():
                if event.type == pygame.QUIT or event.type == pygame.KEYDOWN:
                    pygame.quit()
                    sys.exit()

    # ゲームクリア表示
    if game_clear:
        clear_text = big_font.render("GAME CLEAR!", True, (100, 255, 100))
        screen.blit(clear_text, clear_text.get_rect(center=(WIDTH // 2, HEIGHT // 2)))
        pygame.display.flip()
        pygame.time.wait(3000)
        pygame.quit()
        sys.exit()

    pygame.display.flip()