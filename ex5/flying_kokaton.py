# --- 追加インポート ---
import os
import json
import sys
import pygame
import random
import math

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
STATE_SELECT = "select"      # ステージ間（強化選択など）
STATE_CLEAR = "clear"        # クリア画面（任意）

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

rasuboss_img = pygame.transform.scale(pygame.image.load("fig/ぱっちぃ.png"), (120, 120))
obstacle_img = pygame.transform.scale(pygame.image.load("fig/bakudan.png"), (40, 40)) #障害物画像

# --- キャラ定義 ---
CHARACTER_DATA = {
    "default": {"name": "デフォこうかとん", "speed": 7, "shot_speed": 7, "image": pygame.transform.scale(pygame.image.load("fig/3.png"), (40, 40))},
    "power": {"name": "火力こうかとん", "speed": 5, "shot_speed": 10, "image": pygame.transform.scale(pygame.image.load("fig/fireこうかとん.png"),(40,40))},
    "speed": {"name": "素早いこうかとん", "speed": 10, "shot_speed": 5, "image": pygame.transform.scale(pygame.image.load("fig/speedこうかとん.png"),(40,40))}
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


class RasubossBullet(pygame.sprite.Sprite):
    def __init__(self, x, y, angle_deg):
        super().__init__()
        self.image = pygame.Surface((10, 10), pygame.SRCALPHA)
        pygame.draw.circle(self.image, (255, 0, 0), (5, 5), 5)  # 赤い丸の弾
        self.rect = self.image.get_rect(center=(x, y))
        self.speed = 7
        self.angle = math.radians(angle_deg)
        # 弾の速度ベクトル
        self.vx = self.speed * math.cos(self.angle)
        self.vy = self.speed * math.sin(self.angle)

    def update(self):
        self.rect.x += self.vx
        self.rect.y += self.vy
        # 画面外に出たら消す
        if self.rect.top > HEIGHT or self.rect.right < 0 or self.rect.left > WIDTH:
            self.kill()

class Rasuboss(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.image = pygame.transform.scale(rasuboss_img, (120, 120))
        self.rect = self.image.get_rect(center=(WIDTH // 2, 100))
        self.hp = 1000
        self.speed = 2
        self.direction = 1

        self.attack_cooldown = 120  # 攻撃間隔（フレーム数）
        self.attack_timer = 0

        self.bullets_group = pygame.sprite.Group()  # 弾グループ

    def update(self):
        # 左右に移動
        self.rect.x += self.speed * self.direction
        if self.rect.left < 0 or self.rect.right > WIDTH:
            self.direction *= -1

        # 攻撃処理
        self.attack_timer += 1
        if self.attack_timer >= self.attack_cooldown:
            self.attack_timer = 0
            self.fire_bullets()

        # 弾の更新
        self.bullets_group.update()

        # 死亡判定
        if self.hp <= 0:
            self.kill()

    def fire_bullets(self):
        # 5発の角度（度数法）、真下を90度として左右に15度ずつずらす
        angles = [60, 75, 90, 105, 120]
        x = self.rect.centerx
        y = self.rect.bottom
        for angle in angles:
            bullet = RasubossBullet(x, y, angle)
            self.bullets_group.add(bullet)

class SelectScreen:
    def __init__(self, screen, font, clock):
        self.screen = screen
        self.font = font
        self.clock = clock
        self.options = ["shield", "power", "speed"]
        self.selected_index = 0
        self.selected_option = None

    def process_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RIGHT:
                    self.selected_index = (self.selected_index + 1) % len(self.options)
                elif event.key == pygame.K_LEFT:
                    self.selected_index = (self.selected_index - 1) % len(self.options)
                elif event.key == pygame.K_RETURN:
                    self.selected_option = self.options[self.selected_index]

    def update(self):
        self.screen.fill((0, 0, 0))
        for i, option in enumerate(self.options):
            color = (255, 255, 0) if i == self.selected_index else (255, 255, 255)
            text = self.font.render(option, True, color)
            self.screen.blit(text, (100 + i * 150, 300))
        pygame.display.flip()
        self.clock.tick(120)

    def run(self):
        self.selected_option = None
        while self.selected_option is None:
            self.process_events()
            self.update()
        return self.selected_option


class Obstacle(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.image = pygame.image.load("fig/bakudan.png").convert_alpha()
        self.image = pygame.transform.scale(self.image, (40, 40))
        self.rect = self.image.get_rect()
        self.rect.x = random.randint(0, 480 - self.rect.width)  # 画面内でランダムに配置
        self.rect.y = -self.rect.height  # 画面上から出現

        self.speed = random.randint(2, 5)  # ランダムなスピードで落下

    def update(self):
        self.rect.y += self.speed
        if self.rect.top > 640:  # 画面外に出たら削除
            self.kill()

class Game:
    def __init__(self, screen, clock, player, all_sprites, enemies, missiles, explosions, items, obstacles, boss_group,
                 font, big_font, WIDTH, HEIGHT):
        self.screen = screen
        self.clock = clock
        self.player = player
        self.all_sprites = all_sprites
        self.enemies = enemies
        self.missiles = missiles
        self.explosions = explosions
        self.items = items
        self.obstacles = obstacles
        self.boss_group = boss_group
        self.font = font
        self.big_font = big_font
        self.WIDTH = WIDTH
        self.HEIGHT = HEIGHT

        self.game_over = False
        self.game_clear = False
        self.score = 0
        self.stage = 100
        self.scroll = 0
        self.enemy_timer = 0
        self.stage_timer = 0
        self.stage2_items_generated = False
        self.boss_spawned = False

        self.character_data = CHARACTER_DATA
        self.game_over = False
        self.game_clear = False
        self.score = 0
        # 必要な変数もここでセットアップ

    def run(self):
        self.stage = 2  # 初期ステージを0に
        result = None
        while True:
            if self.stage == 0:
                result = self.stage_0()
            elif self.stage == 1:
                result = self.stage_1()
            elif self.stage == 2:
                result = self.stage_2()
            elif self.stage == 3:
                result = self.stage_3()
            elif self.stage == 4:
                result = self.stage_boss()
            else:
                return "game_over"
            
            # ステージ結果に応じて次のステージへ
            if result == "next_stage":
                self.stage += 1
                self.stage_clear = True
                if self.stage > 4:
                    return "game_clear"
                # result = None

            elif result == "game_over":
                return "game_over"
            elif result == "game_clear":
                return "game_clear"
            

            self.clock.tick(60)
            
    def check_quit_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            return event
        return None

    def reset_stage(self):
        self.all_sprites.empty()
        self.enemies.empty()
        self.missiles.empty()
        self.explosions.empty()
        self.items.empty()
        self.obstacles.empty()
        self.boss_group.empty()
        self.player.shots.clear()
        self.game_over = False
        self.game_clear = False
        self.score = 0

    def stage_boss(self):
        self.reset_stage()
        bg_img = pygame.image.load("fig/rastboss.jpg")
        bg_img = pygame.transform.scale(bg_img, (self.WIDTH, self.HEIGHT))
        BG_W, BG_H = bg_img.get_size()
        

        while True:
            self.clock.tick(60)

            event = self.check_quit_events()
            keys = pygame.key.get_pressed()

            if not self.game_over and not self.game_clear:
                self.player.move(keys)
                self.player.shoot(keys)
                self.player.update_shots()

            self.enemy_timer += 1
            if self.enemy_timer > 100:
                enemy = Enemy()
                self.all_sprites.add(enemy)
                self.enemies.add(enemy)
                self.enemy_timer = 0

                # スコア500でラスボス出現
                if self.score >= 1000 and not self.boss_spawned:
                    self.enemies.empty()
                    self.missiles.empty()
                    boss = Rasuboss()
                    self.boss_group.add(boss)
                    self.all_sprites.add(boss)
                    self.boss_spawned = True

            self.all_sprites.update()
            self.missiles.update()
            self.explosions.update()
            self.boss_group.update()

            # 追加：ラスボスの弾も更新
            if self.boss_spawned and boss.alive():
                boss.bullets_group.update()


                # 弾 vs 敵
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
                # 弾 vs ラスボス
            if self.boss_spawned and boss.alive():
                for shot in self.player.shots[:]:
                    if shot.colliderect(boss.rect):
                        self.player.shots.remove(shot)
                        boss.hp -= 50  # 例：ダメージは50
                        if boss.hp <= 0:
                            boss.kill()
                            self.score += 500
                            self.game_clear = True
                            explosion = Explosion(boss.rect.center)
                            self.all_sprites.add(explosion)
                            self.explosions.add(explosion)


            # 敵 or ミサイル vs プレイヤー（バリア・ダメージ処理対応）
            for enemy in self.enemies:
                if enemy.rect.colliderect(self.player.rect):
                    self.player.hit()
                    enemy.kill()
                    break

            for missile in self.missiles:
                if missile.rect.colliderect(self.player.rect):
                    self.player.hit()
                    missile.kill()
                    break

            if self.player.is_dead:
                explosion = Explosion(self.player.rect.center)
                self.all_sprites.add(explosion)
                self.explosions.add(explosion)
                self.game_over = True

                # 追加：ラスボスの弾 vs プレイヤー
            if self.boss_spawned and boss.alive():
                for bullet in boss.bullets_group:
                    if bullet.rect.colliderect(self.player.rect):
                        self.player.hit()
                        bullet.kill()
                        break

            if self.player.is_dead:
                explosion = Explosion(self.player.rect.center)
                self.all_sprites.add(explosion)
                self.explosions.add(explosion)
                self.game_over = True

            # 描画
            self.screen.blit(bg_img, (0, 0))
            self.all_sprites.draw(self.screen)
            self.player.draw(self.screen)
            self.boss_group.draw(self.screen)
            if self.boss_spawned and boss.alive():
                boss.bullets_group.draw(self.screen)

            # スコア表示
            score_text = self.font.render(f"Score: {self.score}", True, (0, 0, 128))
            self.screen.blit(score_text, (10, 10))

            # ラスボスHPバー
            if self.boss_spawned and boss.alive():
                hp_width = int(boss.hp / 1000 * 200)
                pygame.draw.rect(self.screen, (255, 0, 0), (self.WIDTH // 2 - 100, 20, hp_width, 20))
                pygame.draw.rect(self.screen, (255, 255, 255), (self.WIDTH // 2 - 100, 20, 200, 20), 2)

            # ゲームオーバー表示
            if self.game_over:
                over_text = self.big_font.render("GAME OVER", True, (255, 0, 0))
                info_text = self.font.render("Press any key to exit", True, (255, 255, 255))
                self.screen.blit(over_text, over_text.get_rect(center=(self.WIDTH // 2, self.HEIGHT // 2 - 30)))
                self.screen.blit(info_text, info_text.get_rect(center=(self.WIDTH // 2, self.HEIGHT // 2 + 30)))
                pygame.display.flip()
                pygame.time.wait(1000)
                waiting = True
                while waiting:
                    for event in pygame.event.get():
                        if event.type == pygame.QUIT or event.type == pygame.KEYDOWN:
                            pygame.quit()
                            sys.exit()

            # ゲームクリア表示
            if self.game_clear:
                clear_text = self.big_font.render("GAME CLEAR!", True, (100, 255, 100))
                self.screen.blit(clear_text, clear_text.get_rect(center=(self.WIDTH // 2, self.HEIGHT // 2)))
                pygame.display.flip()
                pygame.time.wait(3000)
                pygame.quit()
                sys.exit()

            pygame.display.flip()

    def stage_0(self):
        self.reset_stage()
        bg_img = pygame.image.load("fig/sky.jpeg")  # 適切なファイルパスに置き換えて
        bg_img = pygame.transform.scale(bg_img, (self.WIDTH, self.HEIGHT))

        while True:
            self.clock.tick(60)
            event = self.check_quit_events()
            keys = pygame.key.get_pressed()

            if not self.game_over and not self.game_clear:
                self.player.move(keys)
                self.player.shoot(keys)
                self.player.update_shots()

            self.enemy_timer += 1
            if self.enemy_timer > 120:
                enemy = Enemy()
                self.all_sprites.add(enemy)
                self.enemies.add(enemy)
                self.enemy_timer = 0

            self.all_sprites.update()
            self.missiles.update()
            self.explosions.update()

                # 弾 vs 敵
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

            # 敵 or ミサイル vs プレイヤー
            if any(enemy.rect.colliderect(self.player.rect) for enemy in self.enemies) or \
            any(missile.rect.colliderect(self.player.rect) for missile in self.missiles):
                explosion = Explosion(self.player.rect.center)
                self.all_sprites.add(explosion)
                self.explosions.add(explosion)
                self.game_over = True

            # 描画
            self.screen.blit(pygame.transform.scale(bg_img, (self.WIDTH, self.HEIGHT)), (0, 0))
            self.all_sprites.draw(self.screen)
            self.player.draw(self.screen)
            self.boss_group.draw(self.screen)

            # スコア表示
            score_text = self.font.render(f"Score: {self.score}", True, (0, 0, 128))
            self.screen.blit(score_text, (10, 10))

            # ゲームオーバー表示
            if self.game_over:
                over_text = self.big_font.render("GAME OVER", True, (255, 0, 0))
                info_text = self.font.render("Press any key to exit", True, (255, 255, 255))
                self.screen.blit(over_text, over_text.get_rect(center=(self.WIDTH // 2, self.HEIGHT // 2 - 30)))
                self.screen.blit(info_text, info_text.get_rect(center=(self.WIDTH // 2, self.HEIGHT // 2 + 30)))
                pygame.display.flip()
                pygame.time.wait(1000)
                waiting = True
                while waiting:
                    for event in pygame.event.get():
                        if event.type == pygame.QUIT or event.type == pygame.KEYDOWN:
                            pygame.quit()
                            sys.exit()

            if self.score >= 500:
                self.game_clear = True

                # ステージクリアの表示
                clear_text = self.big_font.render("STAGE1 CLEAR!", True, (255, 255, 0))
                info_text = self.font.render("Press any key to continue", True, (255, 255, 255))
                self.screen.blit(clear_text, clear_text.get_rect(center=(self.WIDTH // 2, self.HEIGHT // 2 - 30)))
                self.screen.blit(info_text, info_text.get_rect(center=(self.WIDTH // 2, self.HEIGHT // 2 + 30)))
                pygame.display.flip()

                # 少し待ってキー入力を待つ
                pygame.time.wait(1000)
                waiting = True
                while waiting:
                    for event in pygame.event.get():
                        if event.type == pygame.QUIT or event.type == pygame.KEYDOWN:
                            waiting = False

                return "next_stage"

            if self.game_over:
                return "game_over"
            pygame.display.flip()

    def stage_1(self):
        self.reset_stage()
        bg_img = pygame.image.load("fig/sky.jpeg")  # 適切なファイルパスに置き換えて
        bg_img = pygame.transform.scale(bg_img, (self.WIDTH, self.HEIGHT))
        buff_selected = False
        self.score = 0
        while True:
            self.clock.tick(60)
            event = self.check_quit_events()
            keys = pygame.key.get_pressed()

            if not self.game_over and not self.game_clear:
                self.player.move(keys)
                self.player.shoot(keys)
                self.player.update_shots()

            self.enemy_timer += 1
            if self.enemy_timer > 120:
                enemy = Enemy()
                self.all_sprites.add(enemy)
                self.enemies.add(enemy)
                self.enemy_timer = 0

            self.all_sprites.update()
            self.missiles.update()
            self.explosions.update()

                # 弾 vs 敵
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

            # 敵 or ミサイル vs プレイヤー
            if any(enemy.rect.colliderect(self.player.rect) for enemy in self.enemies) or \
            any(missile.rect.colliderect(self.player.rect) for missile in self.missiles):
                explosion = Explosion(self.player.rect.center)
                self.all_sprites.add(explosion)
                self.explosions.add(explosion)
                self.game_over = True

            if self.player.hit():
                self.game_over = True

            # 描画
            self.screen.blit(pygame.transform.scale(bg_img, (self.WIDTH, self.HEIGHT)), (0, 0))
            self.all_sprites.draw(self.screen)
            self.player.draw(self.screen)
            self.boss_group.draw(self.screen)

            # スコア表示
            score_text = self.font.render(f"Score: {self.score}", True, (0, 0, 128))            
            self.screen.blit(score_text, (10, 10))

            if self.score >= 500 and not buff_selected:
                # ステージクリア表示
                clear_text = self.big_font.render("STAGE2 CLEAR", True, (255, 255, 0))
                self.screen.blit(clear_text, clear_text.get_rect(center=(self.WIDTH // 2, self.HEIGHT // 2)))
                pygame.display.flip()
                pygame.time.wait(2000)  # 2秒間表示

                select_screen = SelectScreen(self.screen, self.font, self.clock)
                choice = select_screen.run()
                buff_selected = True
                if choice == "shield":
                    self.player.has_shield = True
                    self.player.shield_used = False
                elif choice == "power":
                    self.player.powered_up = True
                elif choice == "speed":
                    self.player.speed_buff = 2  # move()でspeed + speed_buff に反映
                else:
                    # バフなしならspeed_buffは0にするなど初期化
                    self.player.speed_buff = 0
                self.game_clear = True
                return "next_stage"
            
            # ゲームオーバー表示
            if self.game_over:
                over_text = self.big_font.render("GAME OVER", True, (255, 0, 0))
                info_text = self.font.render("Press any key to exit", True, (255, 255, 255))
                self.screen.blit(over_text, over_text.get_rect(center=(self.WIDTH // 2, self.HEIGHT // 2 - 30)))
                self.screen.blit(info_text, info_text.get_rect(center=(self.WIDTH // 2, self.HEIGHT // 2 + 30)))
                pygame.display.flip()
                pygame.time.wait(1000)
                waiting = True
                while waiting:
                    for event in pygame.event.get():
                        if event.type == pygame.QUIT or event.type == pygame.KEYDOWN:
                            waiting = False
                            
                pygame.quit()
                sys.exit()
                return "game_over"   
            
            pygame.display.flip()

    def stage_2(self):
        self.reset_stage()
        self.enemies.empty()
        self.missiles.empty()
        bg_img = pygame.image.load("fig/sky.jpeg")  # 適切なファイルパスに置き換えて
        bg_img = pygame.transform.scale(bg_img, (self.WIDTH, self.HEIGHT))
        buff_selected = False
        self.score = 0
        self.player.is_dead = False
        self.player.invincible_timer = 120  # 2秒間無敵（敵と即衝突しても死なない）
        self.player.shield_used = False  # バリアの使用状態もリセットしたい場合
        dark_overlay_timer = 0 

        while True:
            self.clock.tick(60)
            event = self.check_quit_events()
            keys = pygame.key.get_pressed()

            if not self.game_over and not self.game_clear:
                self.player.move(keys)
                self.player.shoot(keys)
                self.player.update_shots()

            if random.randint(0, 100) < 1:  # 障害物を生成
                obstacle = Obstacle()
                self.all_sprites.add(obstacle)
                self.obstacles.add(obstacle)

            self.enemy_timer += 1
            if self.enemy_timer > 120:
                enemy = Enemy()
                self.all_sprites.add(enemy)
                self.enemies.add(enemy)
                self.enemy_timer = 0

            self.all_sprites.update()
            self.missiles.update()
            self.explosions.update()

                # 弾 vs 敵
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

            # 敵 or ミサイル vs プレイヤー（バリア・ダメージ処理対応）
            for enemy in self.enemies:
                if enemy.rect.colliderect(self.player.rect):
                    self.player.hit()
                    enemy.kill()
                    break

            for missile in self.missiles:
                if missile.rect.colliderect(self.player.rect):
                    self.player.hit()
                    missile.kill()
                    break

            for obstacle in self.obstacles:
                if obstacle.rect.colliderect(self.player.rect):
                    # 暗転開始（まだ暗転中でなければ）
                    if dark_overlay_timer == 0:
                        dark_overlay_timer = 300  # 5秒 × 60fps
                    # 必要に応じて障害物を消す or 残す
                    obstacle.kill()  # 消したければコメント外す
                    break


            if self.player.is_dead:
                explosion = Explosion(self.player.rect.center)
                self.all_sprites.add(explosion)
                self.explosions.add(explosion)
                self.game_over = True

            # 描画
            self.screen.blit(pygame.transform.scale(bg_img, (self.WIDTH, self.HEIGHT)), (0, 0))
            self.all_sprites.draw(self.screen)
            self.player.draw(self.screen)
            self.boss_group.draw(self.screen)

            # スコア表示
            score_text = self.font.render(f"Score: {self.score}", True, (0, 0, 128))            
            self.screen.blit(score_text, (10, 10))

            # 画面暗転処理（残り時間があれば）
            if dark_overlay_timer > 0:
                dark_surface = pygame.Surface((self.WIDTH, self.HEIGHT))
                dark_surface.set_alpha(210)  #暗転の暗さ調節
                dark_surface.fill((0, 0, 0))
                self.screen.blit(dark_surface, (0, 0))
                dark_overlay_timer -= 1


            # ゲームオーバー表示
            if self.game_over:
                over_text = self.big_font.render("GAME OVER", True, (255, 0, 0))
                info_text = self.font.render("Press any key to exit", True, (255, 255, 255))
                self.screen.blit(over_text, over_text.get_rect(center=(self.WIDTH // 2, self.HEIGHT // 2 - 30)))
                self.screen.blit(info_text, info_text.get_rect(center=(self.WIDTH // 2, self.HEIGHT // 2 + 30)))
                pygame.display.flip()
                pygame.time.wait(1000)
                waiting = True
                while waiting:
                    for event in pygame.event.get():
                        if event.type == pygame.QUIT or event.type == pygame.KEYDOWN:
                            pygame.quit()
                            sys.exit()
            

            if self.score >= 1000 and not buff_selected:

                # ステージクリア表示
                clear_text = self.big_font.render("STAGE3 CLEAR", True, (255, 255, 0))
                self.screen.blit(clear_text, clear_text.get_rect(center=(self.WIDTH // 2, self.HEIGHT // 2)))
                pygame.display.flip()
                pygame.time.wait(2000)  # 2秒間表示

                select_screen = SelectScreen(self.screen, self.font, self.clock)
                choice = select_screen.run()
                buff_selected = True
                if choice == "shield":
                    self.player.has_shield = True
                    self.player.shield_used = False
                elif choice == "power":
                    self.player.powered_up = True
                elif choice == "speed":
                    self.player.speed_buff = 2  # move()でspeed + speed_buff に反映
                else:
                    # バフなしならspeed_buffは0にするなど初期化
                    self.player.speed_buff = 0
                self.game_clear = True

                return "next_stage"
            pygame.display.flip()
        
    def stage_3(self):
        self.reset_stage()
        bg_img = pygame.image.load("fig/sky.jpeg")  # 適切なファイルパスに置き換えて
        bg_img = pygame.transform.scale(bg_img, (self.WIDTH, self.HEIGHT))
        buff_selected = False
        self.score = 0
        self.player.is_dead = False
        self.player.invincible_timer = 120  # 2秒間無敵（敵と即衝突しても死なない）
        self.player.shield_used = False  # バリアの使用状態もリセットしたい場合

        while True:
            self.clock.tick(60)
            event = self.check_quit_events()
            keys = pygame.key.get_pressed()

            if not self.game_over and not self.game_clear:
                self.player.move(keys)
                self.player.shoot(keys)
                self.player.update_shots()

            self.enemy_timer += 1
            if self.enemy_timer > 120:
                enemy = Enemy()
                self.all_sprites.add(enemy)
                self.enemies.add(enemy)
                self.enemy_timer = 0
                enemy.shot_interval = 10

            self.all_sprites.update()
            self.missiles.update()
            self.explosions.update()

            # 弾 vs 敵
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


            # 敵 or ミサイル vs プレイヤー（バリア・ダメージ処理対応）
            for enemy in self.enemies:
                if enemy.rect.colliderect(self.player.rect):
                    self.player.hit()
                    enemy.kill()
                    break

            for missile in self.missiles:
                if missile.rect.colliderect(self.player.rect):
                    self.player.hit()
                    missile.kill()
                    break

            if self.player.is_dead:
                explosion = Explosion(self.player.rect.center)
                self.all_sprites.add(explosion)
                self.explosions.add(explosion)
                self.game_over = True

            # 描画
            self.screen.blit(pygame.transform.scale(bg_img, (self.WIDTH, self.HEIGHT)), (0, 0))
            self.all_sprites.draw(self.screen)
            self.player.draw(self.screen)
            self.boss_group.draw(self.screen)

            # スコア表示
            score_text = self.font.render(f"Score: {self.score}", True, (0, 0, 128))            
            self.screen.blit(score_text, (10, 10))

            # ゲームオーバー表示
            if self.game_over:
                over_text = self.big_font.render("GAME OVER", True, (255, 0, 0))
                info_text = self.font.render("Press any key to exit", True, (255, 255, 255))
                self.screen.blit(over_text, over_text.get_rect(center=(self.WIDTH // 2, self.HEIGHT // 2 - 30)))
                self.screen.blit(info_text, info_text.get_rect(center=(self.WIDTH // 2, self.HEIGHT // 2 + 30)))
                pygame.display.flip()
                pygame.time.wait(1000)
                waiting = True
                while waiting:
                    for event in pygame.event.get():
                        if event.type == pygame.QUIT or event.type == pygame.KEYDOWN:
                            pygame.quit()
                            sys.exit()

            if self.score >= 1000 and not buff_selected:
                # ステージクリア表示
                clear_text = self.big_font.render("STAGE4 CLEAR", True, (255, 255, 0))
                self.screen.blit(clear_text, clear_text.get_rect(center=(self.WIDTH // 2, self.HEIGHT // 2)))
                pygame.display.flip()
                pygame.time.wait(2000)  # 2秒間表示

                select_screen = SelectScreen(self.screen, self.font, self.clock)
                choice = select_screen.run()
                buff_selected = True
                if choice == "shield":
                    self.player.has_shield = True
                    self.player.shield_used = False
                elif choice == "power":
                    self.player.powered_up = True
                elif choice == "speed":
                    self.player.speed_buff = 2  # move()でspeed + speed_buff に反映
                else:
                    # バフなしならspeed_buffは0にするなど初期化
                    self.player.speed_buff = 0
                # self.game_clear = True
                return "next_stage"
            
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
        self.has_shield = False
        self.powered_up = False
        self.speed_buff = 0
        self.has_shield = False   # 1回だけ防げるバリア
        self.shield_used = False  # バリアが使われたかどうか
        self.powered_up = False   # 弾拡散フラグ
        self.shield_effect_timer = 0  # ← 消えるアニメーション用のタイマー
        self.is_dead = False  # プレイヤーがやられたかどうか
        self.invincible_timer = 0  # 無敵タイマー（フレーム数）

    # Player.move() 修正例
    def move(self, keys):
        effective_speed = self.speed + self.speed_buff
        if keys[pygame.K_LEFT] and self.rect.x > 0:
            self.rect.x -= effective_speed
        if keys[pygame.K_RIGHT] and self.rect.x < WIDTH - self.rect.width:
            self.rect.x += effective_speed
        if keys[pygame.K_UP] and self.rect.y > 0:
            self.rect.y -= effective_speed
        if keys[pygame.K_DOWN] and self.rect.y < HEIGHT - self.rect.height:
            self.rect.y += effective_speed


    def shoot(self, keys):
        self.shot_timer += 1
        if keys[pygame.K_SPACE] and self.shot_timer >= 60 / self.shot_speed:
            shot_rect = pygame.Rect(self.rect.x + self.rect.width // 2 - beam_img.get_width() // 2, self.rect.y, beam_img.get_width(), beam_img.get_height())
            self.shots.append(shot_rect)

        # powerアップ状態なら拡散弾も追加（左右に1つずつずらして2発追加）
            center_x = self.rect.x + self.rect.width // 2 - beam_img.get_width() // 2
            if self.powered_up:
                left_shot = pygame.Rect(center_x - 20, self.rect.y, beam_img.get_width(), beam_img.get_height())
                right_shot = pygame.Rect(center_x + 20, self.rect.y, beam_img.get_width(), beam_img.get_height())
                self.shots.append(left_shot)
                self.shots.append(right_shot)

            self.shot_timer = 0
    def hit(self):
        if self.invincible_timer > 0:
            # 無敵中はダメージ無効
            return

        if self.has_shield and not self.shield_used:
            self.shield_used = True  # バリアを消費
            self.has_shield = False
            self.shield_effect_timer = 30
            self.invincible_timer = 60  # バリア消費後、1秒間（60フレーム）無敵
        else:
            self.is_dead = True

    def update_shots(self):
        for shot in self.shots[:]:
            shot.move_ip(0, -10)
            if shot.bottom < 0:
                self.shots.remove(shot)

    def draw(self, screen):
        screen.blit(self.image, self.rect)
        for shot in self.shots:
            screen.blit(beam_img, shot)   # 矩形ではなく画像を描画
        # バリアがあるけどまだ使っていないならバリアを描画（例：青い円など）
        if self.has_shield and not self.shield_used:
            pygame.draw.circle(screen, (0, 0, 255), self.rect.center, max(self.rect.width, self.rect.height), 3)
        # バリアが使われた直後 → エフェクト表示（青→白→消える）
        if self.shield_effect_timer > 0:
            color = (0, 0, 255) if self.shield_effect_timer > 20 else (150, 150, 255)
            pygame.draw.circle(screen, color, self.rect.center, max(self.rect.width, self.rect.height) + 5, 4)
            self.shield_effect_timer -= 1
        if self.invincible_timer > 0:
            self.invincible_timer -= 1


# --- ミサイルクラス（直進） ---
class Sidewinder(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.image = sidewinder_img
        self.rect = self.image.get_rect(center=(x, y))
        self.rect.inflate_ip(-30, 0)  # 当たり判定調整
        self.speed = 8
        self.speed = 8 if game.stage != 3 else 14 

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
            # ステージによって発射頻度変更（ステージ3だけ速く）
            if game.stage == 3:
                self.shot_timer = random.randint(45, 70)  # 高速発射
            else:
                self.shot_timer = random.randint(90, 140)  # 通常速度

        if self.rect.top > HEIGHT:
            self.kill()


def main():
    ui = UIManager()
    global game

    # Gameに渡す共通オブジェクトを準備
    player = Player(CHARACTER_DATA[ui.selected_char])
    all_sprites = pygame.sprite.Group()
    enemies = pygame.sprite.Group()
    missiles = pygame.sprite.Group()
    explosions = pygame.sprite.Group()
    items = pygame.sprite.Group()
    obstacles = pygame.sprite.Group()
    boss_group = pygame.sprite.Group()
    
    game = Game(
        screen,
        clock,
        player,
        all_sprites,
        enemies,
        missiles,
        explosions,
        items,
        obstacles,
        boss_group,
        font,
        big_font,
        WIDTH,
        HEIGHT
    )
   

    game = None

    while True:
        clock.tick(60)
        

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            if ui.state != STATE_GAME:
                ui.handle_event(event)
        
        if ui.state == STATE_HOME:
            ui.draw_home()

        elif ui.state == STATE_CHAR_SELECT:
            ui.draw_char_select()

        elif ui.state == STATE_GAME:
            if game is None:
                # 初回起動時のみ生成
                player = Player(CHARACTER_DATA[ui.selected_char])
                all_sprites = pygame.sprite.Group()
                enemies = pygame.sprite.Group()
                missiles = pygame.sprite.Group()
                explosions = pygame.sprite.Group()
                items = pygame.sprite.Group()
                obstacles = pygame.sprite.Group()
                boss_group = pygame.sprite.Group()

                game = Game(
                    screen,
                    clock,
                    player,
                    all_sprites,
                    enemies,
                    missiles,
                    explosions,
                    items,
                    obstacles,
                    boss_group,
                    font,
                    big_font,
                    WIDTH,
                    HEIGHT
                )
                game.stage = ui.stage

            result = game.run()
            if result == "next_stage":
                ui.stage += 1
                game = None  # 新しいステージのためにリセット
            elif result in ("game_over", "game_clear"):
                ui.state = STATE_HOME
                ui.stage = 0
                game = None

        pygame.display.flip()


if __name__ == "__main__":
    pygame.init()
    main()
    pygame.quit()
    sys.exit()