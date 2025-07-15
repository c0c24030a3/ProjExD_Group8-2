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

# --- Playerクラス ---　#  織井
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
        self.has_shield = False
        self.powered_up = False

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

    def shoot(self, keys): #  織井
        self.shot_timer += 1
        if keys[pygame.K_SPACE] and self.shot_timer >= 60 / self.shot_speed:
            beam = power_beam_img if self.powered_up else beam_img
            shot_rect = pygame.Rect(self.rect.centerx - beam.get_width() // 2, self.rect.y, beam.get_width(), beam.get_height())
            self.shots.append(shot_rect)
            self.shot_timer = 0

    def draw(self, screen):
        screen.blit(self.image, self.rect)
        beam = power_beam_img if self.powered_up else beam_img
        for shot in self.shots:
            screen.blit(beam, shot)

#  織井
beam_img = pygame.transform.scale(pygame.image.load("fig/beam.png"), (10, 20))
power_beam_img = pygame.transform.scale(beam_img, (20, 30))  # 強化ビーム
    
# --- 色定義 ---
WHITE = (255, 255, 255)
RED = (255, 80, 80)
BLACK = (0, 0, 0)

# --- 画像読み込み ---
bg_img = pygame.image.load("fig/sky.jpeg") #背景画像
BG_W, BG_H = bg_img.get_size()

f16_img = pygame.transform.rotate(pygame.transform.scale(pygame.image.load("fig/F16.png"), (60, 60)), 180)
sidewinder_img = pygame.transform.rotate(
    pygame.transform.scale(pygame.image.load("fig/sidewinder.png"), (70, 120)), 180)
beam_img = pygame.transform.scale(pygame.image.load("fig/beam.png"), (10, 20))  # ここがビーム画像
explosion_img = pygame.transform.scale(pygame.image.load("fig/explosion.gif"), (60, 60))
shield_img = pygame.transform.scale(pygame.image.load("fig/shield.png"), (50, 50))
power_img = pygame.transform.scale(pygame.image.load("fig/chikarakobu.png"), (50, 50))
speed_img = pygame.transform.scale(pygame.image.load("fig/sneaker.png"), (50, 50))
kabe_img = pygame.transform.scale(pygame.image.load("fig/kabe.jpg"), (10, 100))
# --- フォントとスコア ---
font = pygame.font.SysFont(None, 36)
big_font = pygame.font.SysFont(None, 72)

# --- キャラクターデータ ---　織井
characters = {
    "default": {
        "name": "デフォこうかとん",
        "hp": 10,
        "speed": 5,
        "shot_speed": 10,
        "image": pygame.image.load("fig/3.png")
    }
}

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

# --- ミサイルクラス（敵が発射） ---
class Sidewinder(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.image = sidewinder_img
        self.rect = self.image.get_rect(center=(x, y))
        self.rect.inflate_ip(-30, 0)
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
            missile = Sidewinder(self.rect.centerx,self.rect.bottom) 
            all_sprites.add(missile)
            missiles.add(missile)
            self.shot_timer = random.randint(90, 140)
        if self.rect.top > HEIGHT:
            self.kill()

# --- Itemクラス ---
class Item(pygame.sprite.Sprite):
    def __init__(self, x, y, type):
        super().__init__()
        self.type = type      
        self.image = pygame.Surface((50, 50))

        if type == "shield":
            self.image = shield_img
        elif type == "power":
            self.image = power_img
        elif type == "speed":
            self.image = speed_img
        self.rect = self.image.get_rect(center=(x, y))

    def update(self):
        self.rect.y += 0.8
        if self.rect.top > HEIGHT:
            self.kill()

all_sprites = pygame.sprite.Group()
enemies = pygame.sprite.Group()
missiles = pygame.sprite.Group()
explosions = pygame.sprite.Group()
items = pygame.sprite.Group()
player = Player(characters["default"])


# --- ゲーム管理変数 ---
score = 0
scroll = 0
game_over = False
mode = "play"
enemy_timer = 0
stage_timer = 0
stage2_items_generated = False

while True:
    clock.tick(60)

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()

    keys = pygame.key.get_pressed()

    # --- スクロール背景 ---
    scroll += 2
    scroll %= BG_H
    for y in range(-scroll, HEIGHT, BG_H):
        for x in range(0, WIDTH, BG_W):
            screen.blit(bg_img, (x, y))

    if not game_over:
        player.move(keys)
        player.shoot(keys)
        player.update_shots()

        all_sprites.update()
        missiles.update()
        explosions.update()
        items.update()

# --- ステージ1（通常プレイ） ---
        if mode == "play":
            enemy_timer += 1
            if enemy_timer > 30:
                enemy = Enemy()
                all_sprites.add(enemy)
                enemies.add(enemy)
                enemy_timer = 0

            # ステージ2へ移行
            if score >= 2000:
                mode = "stage2"
                stage_timer = 0
                player.shots.clear()
                enemies.empty()
                missiles.empty()

        # --- ステージ2：3レーンアイテム取得 ---
        elif mode == "stage2":
            stage_timer += 1

            if not stage2_items_generated:
                lane_x = [WIDTH // 4, WIDTH // 2, WIDTH * 3 // 4]
                item_types = ["shield", "power", "speed"]
                for x, t in zip(lane_x, item_types):
                    item = Item(x, -80, t)
                    all_sprites.add(item)
                    items.add(item)

                stage2_items_generated = True

            # アイテム取得処理
            for item in items:
                if player.rect.colliderect(item.rect):
                    if item.type == "shield":
                        player.has_shield = True
                    elif item.type == "power":
                        player.powered_up = True
                    elif item.type == "speed":
                        player.speed += 2
                    item.kill()
                    #  他のアイテムを消す
                    for other in items:
                        other.kill()

            # ステージ2終了→ステージ1再開
                    mode = "stage3"
                    stage2_items_generated = False
                    break
        # ステージ3 (仮)
        elif mode == "stage3":
            enemy_timer += 1
            if enemy_timer > 20:
                enemy = Enemy()
                all_sprites.add(enemy)
                enemies.add(enemy)
                enemy_timer = 0

        # --- 弾と敵の衝突判定 ---
        for shot in player.shots[:]:
            for enemy in enemies:
                if shot.colliderect(enemy.rect):
                    player.shots.remove(shot)
                    enemy.kill()
                    explosion = Explosion(enemy.rect.center)
                    all_sprites.add(explosion)
                    explosions.add(explosion)
                    score += 100
                    break

        # --- プレイヤー被弾 ---
        hit = any(enemy.rect.colliderect(player.rect) for enemy in enemies) or any(missile.rect.colliderect(player.rect) for missile in missiles)
        if hit:
            if player.has_shield:
                player.has_shield = False
                enemies.empty()
                missiles.empty()
            else:
                explosion = Explosion(player.rect.center)
                all_sprites.add(explosion)
                explosions.add(explosion)
                game_over = True

    # 描画
    all_sprites.draw(screen)
    items.draw(screen)
    player.draw(screen)

    # スコア表示
    screen.blit(font.render(f"Score: {score}", True, WHITE), (10, 10))

    if mode == "stage2" and stage_timer < 120:
        stage2_text = big_font.render("STAGE 2", True, WHITE)
        screen.blit(stage2_text, stage2_text.get_rect(center=(WIDTH // 2, HEIGHT // 2)))

    if game_over:
        over_text = big_font.render("GAME OVER", True, RED)
        info_text = font.render("Press any key to exit", True, WHITE)
        screen.blit(over_text, over_text.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 30)))
        screen.blit(info_text, info_text.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 30)))
        pygame.display.flip()
        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT or event.type == pygame.KEYDOWN:
                    pygame.quit()
                    sys.exit()
            clock.tick(30)

    pygame.display.flip()

