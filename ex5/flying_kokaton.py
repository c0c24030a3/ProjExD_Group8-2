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


f16_img = pygame.transform.rotate(pygame.transform.scale(pygame.image.load("fig/F16.png"), (60, 60)), 180)
sidewinder_img = pygame.transform.rotate(pygame.transform.scale(pygame.image.load("fig/sidewinder.png"), (70, 120)), 180)
beam_img = pygame.transform.scale(pygame.image.load("fig/beam.png"), (10, 20))
explosion_img = pygame.transform.scale(pygame.image.load("fig/explosion.gif"), (60, 60))

rasuboss_img = pygame.transform.scale(pygame.image.load("fig/ぱっちぃ.png"), (120, 120))
obstacle_img = pygame.transform.scale(pygame.image.load("fig/bakudan.png"), (40, 40)) #障害物画像

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
        beam = power_beam_img if self.powered_up else beam_img
        for shot in self.shots:
            screen.blit(beam, shot)

# 強化ビーム設定(織井)
beam_img = pygame.transform.scale(pygame.image.load("fig/beam.png"), (10, 20))
power_beam_img = pygame.transform.scale(beam_img, (20, 30))
    
# --- 色定義 ---
WHITE = (255, 255, 255)
RED = (255, 80, 80)
BLACK = (0, 0, 0)

# --- 画像読み込み ---



f16_img = pygame.transform.rotate(pygame.transform.scale(pygame.image.load("fig/F16.png"), (60, 60)), 180)
sidewinder_img = pygame.transform.rotate(pygame.transform.scale(pygame.image.load("fig/sidewinder.png"), (70, 120)), 180)
beam_img = pygame.transform.scale(pygame.image.load("fig/beam.png"), (10, 20))  # ここがビーム画像
explosion_img = pygame.transform.scale(pygame.image.load("fig/explosion.gif"), (60, 60))
shield_img = pygame.transform.scale(pygame.image.load("fig/shield.png"), (50, 50))
power_img = pygame.transform.scale(pygame.image.load("fig/chikarakobu.png"), (50, 50))
speed_img = pygame.transform.scale(pygame.image.load("fig/sneaker.png"), (50, 50))
kabe_img = pygame.transform.scale(pygame.image.load("fig/kabe.jpg"), (10, 100))
# --- フォントとスコア ---
font = pygame.font.SysFont(None, 36)
big_font = pygame.font.SysFont(None, 72)

# --- キャラクターデータ ---
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
            missile = Sidewinder(self.rect.centerx,self.rect.bottom) 
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

# --- 障害物クラス ---
class Obstacle(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.image = obstacle_img
        self.rect = self.image.get_rect(center=(random.randint(20, WIDTH - 20), -20))
        self.speed = random.randint(2, 5)

    def update(self):
        self.rect.y += self.speed
        if self.rect.top > HEIGHT:
            self.kill()


# --- グループ ---
boss_group = pygame.sprite.Group()
boss_bullets = pygame.sprite.Group()

# --- ゲームフラグ ---
game_clear = False
boss_spawned = False

# --- Itemクラス ---(織井)
"""プレイヤーが取得できるアイテム3種類を設定
   shield: シールド効果
   power: 攻撃力アップ
   speed: 移動速度アップ

   各アイテムは画面上部から落下し、プレイヤーが取得すると効果を発揮する"""
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
        self.rect.y += 0.8  # アイテムの落下速度
        if self.rect.top > HEIGHT:
            self.kill()

all_sprites = pygame.sprite.Group()
enemies = pygame.sprite.Group()
missiles = pygame.sprite.Group()
explosions = pygame.sprite.Group()
items = pygame.sprite.Group()
obstacles = pygame.sprite.Group()

# キャラクターデータ（画像も渡す）
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

# --- ゲーム管理変数 ---
game_over = False
stage = 100
scroll=0
# --- ゲームループ ---mode = "play"
enemy_timer = 0
stage_timer = 0
stage2_items_generated = False

stage=int(input("あいことばを入力。ステージ1は「2」"))

gamecode=0
if stage==334: #ラスボスステージ
    gamecode=input("呪文を入力")
    if gamecode==3456:
        player.has_shield = True
        print("シールドをゲットした！")
    if gamecode==1836:
        player.powered_up = True
        print("弾が大きくなった！")
    if gamecode==8000:
        player.speed += 2
        print("素早くなった！")
    #呪文を聞く部分(共通)
    bg_img = pygame.image.load("fig/rastboss.jpg")  # 固定背景画像
    bg_img = pygame.transform.scale(bg_img, (WIDTH, HEIGHT))
    BG_W, BG_H = bg_img.get_size()
    while True:
        clock.tick(60)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

        if not game_over and not game_clear:
            keys = pygame.key.get_pressed()
            player.move(keys)
            player.shoot(keys)
            player.update_shots()

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

        # 衝突（敵 or ミサイル vs プレイヤー）
        if any(enemy.rect.colliderect(player.rect) for enemy in enemies) or \
           any(missile.rect.colliderect(player.rect) for missile in missiles):
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
if stage== 111:
    bg_img = pygame.image.load("fig/sky.jpeg") #背景画像
    bg_img = pygame.transform.scale(bg_img, (WIDTH, HEIGHT))
    BG_W, BG_H = bg_img.get_size()
    mode="play"
    gamecode=input("呪文を入力")
    if gamecode==3456:
        player.has_shield = True
        print("シールドをゲットした！")
    if gamecode==1836:
        player.powered_up = True
        print("弾が大きくなった！")
    if gamecode==8000:
        player.speed += 2
        print("素早くなった！")
    #呪文を聞く部分(共通)
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

                # ステージ2へ移行(織井)
                if score >= 200:
                    stage = 3
                    stage_timer = 0
                    player.shots.clear()
                    enemies.empty()
                    missiles.empty()
                    mode = "stage2"
            # --- ステージ2：3レーンアイテム取得（織井） ---
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

                # アイテム取得処理（織井）
                for item in items:
                    if player.rect.colliderect(item.rect):
                        if item.type == "shield":
                            player.has_shield = True
                            print("シールドの呪文「3456」")
                        elif item.type == "power":
                            player.powered_up = True
                            print("火力の呪文「1836」")
                        elif item.type == "speed":
                            player.speed += 2
                            print("素早くなる呪文「8000」")
                        item.kill()
                        #  他のアイテムを消す
                        for other in items:
                            other.kill()

                # ステージ2終了→ステージ3（織井）
                        mode = "stage3"
                        stage2_items_generated = False
                        break
            # ステージ3仮（織井）
            elif mode == "stage3":
                print("ステージ2のあいことばは「777」")
                break

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

        # stage2と表示（織井）
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


if stage==777: #ステージ2
    gamecode=input("呪文を入力")
    if gamecode==3456:
        player.has_shield = True
        print("シールドをゲットした！")
    if gamecode==1836:
        player.powered_up = True
        print("弾が大きくなった！")
    if gamecode==8000:
        player.speed += 2
        print("素早くなった！")
    #呪文を聞く部分(共通)
    bg_img = pygame.image.load("fig/sky.jpeg") #背景画像
    bg_img = pygame.transform.scale(bg_img, (WIDTH, HEIGHT))
    BG_W, BG_H = bg_img.get_size()

    while True:
        clock.tick(60)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

        if not game_over:
            keys = pygame.key.get_pressed()
            player.move(keys)
            player.shoot(keys)
            player.update_shots()

            if random.randint(0, 100) < 1: # 障害物を生成
                obstacle = Obstacle()
                all_sprites.add(obstacle)
                obstacles.add(obstacle)
            
            enemy_timer+=1
            if enemy_timer > 30:
                enemy = Enemy()
                all_sprites.add(enemy)
                enemies.add(enemy)
                enemy_timer = 0

            all_sprites.update()
            missiles.update()
            explosions.update()

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

            
            # 衝突( 障害物　vs プレイヤー）
            if any(ob.rect.colliderect(player.rect) for ob in obstacles):
                explosion = Explosion(player.rect.center)
                all_sprites.add(explosion)
                explosions.add(explosion)
                game_over = True


            if any(enemy.rect.colliderect(player.rect) for enemy in enemies) or \
            any(missile.rect.colliderect(player.rect) for missile in missiles):
                explosion = Explosion(player.rect.center)
                all_sprites.add(explosion)
                explosions.add(explosion)
                game_over = True

        # 背景スクロール（先に描画）
        scroll += 2
        scroll %= BG_H
        for y in range(-scroll, HEIGHT, BG_H):
            for x in range(0, WIDTH, BG_W):
                screen.blit(bg_img, (x, y))

        # 描画
        all_sprites.draw(screen)
        player.draw(screen)

        # スコア表示
        score_text = font.render(f"Score: {score}", True, WHITE)
        screen.blit(score_text, (10, 10))

        if score>=200:#ゲームクリア処理
            print("次のステージの呪文は「292」だよ")#数字変更
            break


        # ゲームオーバー表示
        if game_over:
            over_text = big_font.render("GAME OVER", True, RED)
            info_text = font.render("Press any key to exit", True, WHITE)
            screen.blit(over_text, over_text.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 30)))
            screen.blit(info_text, info_text.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 30)))
            pygame.display.flip()

            waiting = True
            while waiting:
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        pygame.quit()
                        sys.exit()
                    elif event.type == pygame.KEYDOWN:
                        pygame.quit()
                        sys.exit()
                clock.tick(30)
            break

        pygame.display.flip()





else:
    print("正しいステージを選択して下さい")