# --- 追加インポート ---
import os
import json
import sys
import pygame
import random
import math
import pygame as pg

# --- 作業ディレクトリをスクリプトの場所に設定 ---
os.chdir(os.path.dirname(os.path.abspath(__file__)))

# --- 定数定義 ---
WIDTH, HEIGHT = 480, 640
WHITE = (255, 255, 255)
RED = (255, 80, 80)
BLACK = (0, 0, 0)
FPS = 60
STATE_HOME = "home"
STATE_CHAR_SELECT = "char_select"
STATE_GAME = "game"

# --- 初期化 ---
pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("縦スクロールシューティング")
clock = pygame.time.Clock()
font = pygame.font.SysFont(None, 30)
big_font = pygame.font.SysFont(None, 72)

# --- 画像読み込み ---
bg_img = pygame.image.load("fig/sky.jpeg")
BG_W, BG_H = bg_img.get_size()
beam_img = pygame.transform.scale(pygame.image.load("fig/beam.png"), (10, 20))
f16_img = pygame.transform.rotate(pygame.transform.scale(pygame.image.load("fig/F16.png"), (60, 60)), 180)
sidewinder_img = pygame.transform.rotate(pygame.transform.scale(pygame.image.load("fig/sidewinder.png"), (70, 120)), 180)
explosion_img = pygame.transform.scale(pygame.image.load("fig/explosion.gif"), (60, 60))

# --- キャラ定義 ---
CHARACTER_DATA = {
    "default": {"name": "デフォこうかとん", "speed": 10, "shot_speed": 10, "image": pygame.transform.scale(pygame.image.load("fig/3.png"), (40, 40))},
    "power": {"name": "火力こうかとん", "speed": 5, "shot_speed": 15, "image": pygame.transform.scale(pygame.image.load("fig/fireこうかとん.png"),(40,40))},
    "speed": {"name": "素早いこうかとん", "speed": 15, "shot_speed": 5, "image": pygame.transform.scale(pygame.image.load("fig/speedこうかとん.png"),(40,40))}
}

class UIManager:
    def __init__(self):
        self.state = STATE_HOME
        self.selected_char = "default"
        self.score = 0
        self.stage = 1  # 1: ステージ1, 2: ステージ2 ...

    def draw_home(self):
        screen.fill(BLACK)  # 背景を黒にする
        title = big_font.render("Koukaton Shooting", True, WHITE)
        screen.blit(title, title.get_rect(center=(WIDTH//2, 100)))  # タイトル表示
        options = [
            "S: Start Game",
            "C: Character Select"
        ]
        for i, text in enumerate(options):
            txt = font.render(text, True, WHITE)
            screen.blit(txt, (100, 250 + i * 50))  # メニュー選択肢の表示
        pygame.display.flip()

    def draw_char_select(self):
        screen.fill(BLACK)
        y = 100
        for key, ch in CHARACTER_DATA.items():
            line = f"{key.upper()} - Speed:{ch['speed']} Rate:{ch['shot_speed']}"
            txt = font.render(line, True, WHITE)
            screen.blit(txt, (50, y))   # テキスト情報を表示
            screen.blit(ch["image"],(0,y))  # キャラの画像を表示
            y += 50
        info = font.render("Press D/P/S to select or B to go back", True, WHITE)
        screen.blit(info, (50, HEIGHT - 100))   # 操作案内
        pygame.display.flip()

    def handle_event(self, event):
        if self.state == STATE_HOME and event.type == pygame.KEYDOWN:
            if event.key == pygame.K_s:
                self.state = STATE_GAME  # ゲーム開始
            elif event.key == pygame.K_c:
                self.state = STATE_CHAR_SELECT  # キャラ選択へ
            elif event.key == pygame.K_l:
                self.load()  # セーブデータ読み込み
        elif self.state == STATE_CHAR_SELECT and event.type == pygame.KEYDOWN:
            if event.key == pygame.K_d:
                self.selected_char = "default"
            elif event.key == pygame.K_p:
                self.selected_char = "power"
            elif event.key == pygame.K_s:
                self.selected_char = "speed"
            elif event.key == pygame.K_b:
                self.state = STATE_HOME  # 戻る
            if event.key in [pygame.K_d, pygame.K_p, pygame.K_s]:
                self.state = STATE_HOME  # キャラ選択したらホームに戻る

class Game:
    def __init__(self, player_data):
        self.player_data = player_data  #キャラ性能
        self.score = 0
        self.scroll = 0  #背景のスクロール位置
        self.running = True  #ゲームを続けるかのフラグ
        self.all_sprites = pygame.sprite.Group()  #全スプライト
        self.enemies = pygame.sprite.Group()  #敵キャラグループ
        self.missiles = pygame.sprite.Group()  #敵のミサイルグループ
        self.explosions = pygame.sprite.Group()  #爆発アニメグループ
        self.enemy_timer = 0  #敵の出現タイマー
        self.player = Player(player_data)  #プレイヤーオブジェクト

    def run(self):
        while self.running:
            clock.tick(FPS)
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()

            keys = pygame.key.get_pressed()
            self.player.move(keys)
            self.player.shoot(keys)
            self.player.update_shots()

            self.enemy_timer += 1
            if self.enemy_timer > 30:
                enemy = Enemy()
                self.all_sprites.add(enemy)
                self.enemies.add(enemy)
                self.enemy_timer = 0

            self.all_sprites.update()
            self.missiles.update()
            self.explosions.update()

            if self.score >= 1000:  # 例えば1000点
                self.running = False
                return "next_stage"  # ← run()の戻り値で判定

            # 弾と敵の当たり判定
            for shot in self.player.shots[:]:
                for enemy in self.enemies.sprites():
                    if shot.colliderect(enemy.rect):
                        self.player.shots.remove(shot)
                        enemy.kill()
                        explosion = Explosion(enemy.rect.center)
                        self.all_sprites.add(explosion)
                        self.explosions.add(explosion)
                        self.score += 100
                        break

            # プレイヤー被弾
            if any(enemy.rect.colliderect(self.player.rect) for enemy in self.enemies) or \
               any(missile.rect.colliderect(self.player.rect) for missile in self.missiles):
                explosion = Explosion(self.player.rect.center)
                self.all_sprites.add(explosion)
                self.explosions.add(explosion)
                self.running = False

            #背景スクロール処理
            self.scroll += 2
            self.scroll %= BG_H
            for y in range(-self.scroll, HEIGHT, BG_H):
                for x in range(0, WIDTH, BG_W):
                    screen.blit(bg_img, (x, y))

            #スプライトとスコア表示
            self.all_sprites.draw(screen)
            self.player.draw(screen)
            score_text = font.render(f"Score: {self.score}", True, WHITE)
            screen.blit(score_text, (10, 10))

            #ゲームオーバー画面
            if not self.running:
                over_text = big_font.render("GAME OVER", True, RED)
                info_text = font.render("Press any key to exit", True, WHITE)
                screen.blit(over_text, over_text.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 30)))
                screen.blit(info_text, info_text.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 30)))
                pygame.display.flip()
                waiting = True
                while waiting:
                    for event in pygame.event.get():
                        if event.type == pygame.QUIT or event.type == pygame.KEYDOWN:
                            waiting = False
                pygame.quit()
                sys.exit()

            #画面更新
            pygame.display.flip()


#--- フォントとスコア ---
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
        self.speed = char_data["speed"]
        self.shot_speed = char_data["shot_speed"]  # 連射速度（回/秒）
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

    def shoot(self, keys):
        self.shot_timer += 1
        if keys[pygame.K_SPACE] and self.shot_timer >= 60 / self.shot_speed:
            shot_rect = pygame.Rect(self.rect.x + self.rect.width // 2 - beam_img.get_width() // 2, self.rect.y, beam_img.get_width(), beam_img.get_height())
            self.shots.append(shot_rect)
            self.shot_timer = 0

    def update_shots(self):
        for shot in self.shots[:]:
            shot.move_ip(0, -10)
            if shot.bottom < 0:
                self.shots.remove(shot)

    def draw(self, screen):
        screen.blit(self.image, self.rect)
        for shot in self.shots:
            screen.blit(beam_img, shot)   # 矩形ではなく画像を描画


# --- ミサイルクラス（直進） ---
class Sidewinder(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.image = sidewinder_img
        self.rect = self.image.get_rect(center=(x, y))
        self.rect.inflate_ip(-30, 0)  # 当たり判定調整
        self.speed = 4

    def update(self):
        self.rect.y += self.speed
        if self.rect.top > HEIGHT:
            self.kill()


# --- 敵クラス（F16） ---
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
            game.missiles.add(missile)
            game.all_sprites.add(missile)
            self.shot_timer = random.randint(90, 140)
        if self.rect.top > HEIGHT:
            self.kill()


def main():
    ui = UIManager()
    global game

    while True:
        clock.tick(FPS)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            ui.handle_event(event)

        if ui.state == STATE_HOME:
            ui.draw_home()
        elif ui.state == STATE_CHAR_SELECT:
            ui.draw_char_select()
        elif ui.state in [STATE_GAME]:
            game = Game(CHARACTER_DATA[ui.selected_char])
            result = game.run()
            if result == "next_stage":
                ui.stage += 1  # ステージ進行
                ui.state = STATE_GAME  # もう一度 Game に進む
            else:
                ui.state = STATE_HOME  # 通常のゲームオーバーならタイトルへ戻る

if __name__ == "__main__":
    pg.init()
    main()
    pg.quit()
    sys.exit()
 