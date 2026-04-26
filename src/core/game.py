"""
Game - основной класс игрового цикла.

Простая single-world игра в стиле Zelda. Без мульти-миров, ECS,
порталов и подземных Z-переходов - всё это было оверинжинирингом
для текущего этапа разработки. При необходимости вернётся отдельной
веткой когда базовые механики (комбат, враги, инвентарь) будут готовы.
"""
import pygame
import sys
import os
import datetime

from src.core.config_loader import load_config, get_config, get_color
from src.core.game_states import GameState
from src.core.game_stats import GameStats
from src.ui.menu import MainMenu
from src.ui.game_over import GameOverScreen
from src.utils.debug import debug
from src.entities.player import Player
from src.world.world import World
from src.systems.save_system import SaveSystem


# Размер игрока (32x32) - используется для центрирования в стартовом тайле.
# В будущем стоит вынести в config.ini.
_PLAYER_HALF = 16


class Game:
    def __init__(self):
        self._setup_logging()

        # Загрузка конфигурации
        self.config = load_config()

        # Инициализация Pygame
        pygame.init()
        self.screen = pygame.display.set_mode(
            (get_config('WIDTH'), get_config('HEIGHT'))
        )
        pygame.display.set_caption("Zelda-like Game")
        self.clock = pygame.time.Clock()
        self.running = True

        # Состояние игры
        self.state = GameState.MENU

        # Главное меню
        self.menu = MainMenu()

        # Игровые объекты (инициализируются при начале новой игры)
        self.world: World = None
        self.player: Player = None
        self.game_stats: GameStats = None
        self.game_over_screen: GameOverScreen = None

        # Тайминги игрового цикла
        self.last_time = pygame.time.get_ticks()

        # Отладочная информация
        self.show_debug = False

        # Система сохранений
        self.save_system = SaveSystem()

    # --- Логирование -------------------------------------------------------

    def _setup_logging(self):
        """Настройка логирования каждой сессии в отдельный файл."""
        log_dir = "logs"
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)

        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        self.log_filename = os.path.join(log_dir, f"game_session_{timestamp}.log")

        self.log_file = open(self.log_filename, 'w', encoding='utf-8')
        self.log_file.write(
            f"=== ИГРОВАЯ СЕССИЯ НАЧАЛАСЬ: "
            f"{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ===\n\n"
        )
        self.log_file.flush()
        print(f"📝 Логи записываются в: {self.log_filename}")

    def log(self, message, level="INFO"):
        """Записать сообщение в лог. INFO в файл, важное также в консоль."""
        timestamp = datetime.datetime.now().strftime("%H:%M:%S.%f")[:-3]
        log_entry = f"[{timestamp}] [{level}] {message}\n"

        self.log_file.write(log_entry)
        self.log_file.flush()

        if level in ("IMPORTANT", "ERROR", "WARNING"):
            print(message)

    # --- Жизненный цикл игры ----------------------------------------------

    def start_new_game(self):
        """Начать новую игру: создать мир, игрока, статистику."""
        self.log("=== ЗАПУСК НОВОЙ ИГРЫ ===", "IMPORTANT")

        # Загружаем основной (и единственный) мир
        self.world = World(map_file=os.path.join('data', 'main_world.txt'))
        start_x, start_y = self.world.get_player_start_position()
        self.log(f"Стартовая позиция (центр тайла @): ({start_x}, {start_y})")

        # Игрок спавнится центрированно в тайле, чтобы не пересекать
        # соседние клетки и не застревать у стенок.
        self.player = Player(start_x - _PLAYER_HALF, start_y - _PLAYER_HALF)
        self.log(
            f"Игрок создан: HP={self.player.health}/{self.player.max_health}, "
            f"оружие='{self.player.current_weapon.name}'"
        )

        # Статистика и Game Over экран
        self.game_stats = GameStats()
        self.game_over_screen = GameOverScreen(
            get_config('WIDTH'), get_config('HEIGHT'), self.game_stats
        )

        print("Игра запущена. WASD/стрелки - движение, Space - атака, "
              "1..4 - оружие, F1 - debug, F5/F9 - save/load, ESC - меню")
        self.state = GameState.PLAYING

    # --- Обработка событий -------------------------------------------------

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
                continue

            if event.type != pygame.KEYDOWN:
                continue

            if self.state == GameState.MENU:
                self._handle_menu_key(event)
            elif self.state == GameState.PLAYING:
                self._handle_playing_key(event)
            elif self.state == GameState.GAME_OVER:
                self._handle_game_over_key(event)

    def _handle_menu_key(self, event):
        action = self.menu.handle_input(event)
        if action == "new_game":
            self.start_new_game()
        elif action == "continue_game":
            self.quickload()
        elif action == "load_game":
            print("Load game - функция будет реализована позже")
            self.start_new_game()
        elif action == "exit":
            self.running = False

    def _handle_playing_key(self, event):
        if event.key == pygame.K_F1:
            self.show_debug = not self.show_debug
        elif event.key == pygame.K_F5:
            self.quicksave()
        elif event.key == pygame.K_F9:
            self.quickload()
        elif event.key == pygame.K_ESCAPE:
            self.state = GameState.MENU
        # Выбор оружия по 1..5 (соответствует Player.weapons)
        elif event.key in (pygame.K_1, pygame.K_2, pygame.K_3,
                           pygame.K_4, pygame.K_5):
            if self.player:
                idx = event.key - pygame.K_1
                if self.player.switch_weapon(idx):
                    w = self.player.current_weapon
                    self.log(
                        f"🗡️ [{idx + 1}] Оружие: {w.name} "
                        f"(reach={w.reach}, dmg={w.damage})",
                        "IMPORTANT",
                    )

    def _handle_game_over_key(self, event):
        if not self.game_over_screen:
            return
        action = self.game_over_screen.handle_input(event)
        if action == "MENU":
            self.state = GameState.MENU
        elif action == "QUIT":
            self.running = False

    # --- Обновление --------------------------------------------------------

    def update(self, dt):
        if self.state != GameState.PLAYING or not self.player or not self.world:
            return

        # Смерть игрока
        if self.player.is_dead():
            self.game_stats.record_death()
            self.state = GameState.GAME_OVER
            return

        keys = pygame.key.get_pressed()
        self.player.handle_input(keys)
        self.player.update(dt, self.world, self.game_stats)

        if self.game_stats:
            self.game_stats.update_position(self.player.x, self.player.y)

        # Камера следует за игроком
        self.world.update_camera(
            self.player.x + self.player.width // 2,
            self.player.y + self.player.height // 2,
            get_config('WIDTH'), get_config('HEIGHT'),
        )

    # --- Отрисовка ---------------------------------------------------------

    def draw(self):
        if self.state == GameState.MENU:
            self.menu.draw(self.screen)

        elif self.state == GameState.PLAYING and self.player and self.world:
            self.screen.fill(get_color('BLACK'))
            # 1) Земля + миникарта
            self.world.draw(self.screen, self.player.x, self.player.y)
            # 2) Игрок поверх земли
            self.player.draw(self.screen, self.world.camera_x, self.world.camera_y)
            # 3) Overlay (крыши/холм) поверх игрока с эффектом прозрачности
            self.world.draw_overlay(self.screen, self.player.rect)
            # 4) HUD
            self.draw_health_bar()
            self.draw_weapon_hud()

            if self.show_debug:
                self._draw_debug_info()
            else:
                debug(
                    "WASD - Move | Space - Attack | 1..4 - Weapon | "
                    "F1 - Debug | F5/F9 - Save/Load | ESC - Menu",
                    y=get_config('HEIGHT') - 30,
                )

        elif self.state == GameState.GAME_OVER and self.game_over_screen:
            self.game_over_screen.draw(self.screen)

        pygame.display.flip()

    def _draw_debug_info(self):
        info = [
            f"Player: ({int(self.player.x)}, {int(self.player.y)})",
            f"Direction: {self.player.facing_direction}",
            f"Weapon: {self.player.current_weapon.name}",
            f"Attacking: {self.player.attacking}",
            f"FPS: {int(self.clock.get_fps())}",
            "Controls: WASD - Move, Space - Attack, 1..4 - Weapon",
            "F1 - Debug, F5 - Save, F9 - Load, ESC - Menu",
        ]
        y = 10
        for line in info:
            debug(line, y=y)
            y += 20

    def draw_health_bar(self):
        """Полоска здоровья игрока в верхнем-левом углу."""
        bar_width, bar_height = 200, 20
        bar_x, bar_y = 10, 10
        border_width = 2

        pct = self.player.health / self.player.max_health
        health_w = int(bar_width * pct)

        # Фон
        pygame.draw.rect(self.screen, get_color('DARK_GRAY'),
                         (bar_x, bar_y, bar_width, bar_height))
        # Заливка
        if health_w > 0:
            pygame.draw.rect(self.screen, get_color('GREEN'),
                             (bar_x, bar_y, health_w, bar_height))
        # Рамка
        pygame.draw.rect(
            self.screen, get_color('WHITE'),
            (bar_x - border_width, bar_y - border_width,
             bar_width + border_width * 2, bar_height + border_width * 2),
            border_width,
        )
        # Текст
        font = pygame.font.Font(None, 24)
        text = f"{int(self.player.health)}/{int(self.player.max_health)}"
        text_surf = font.render(text, True, get_color('WHITE'))
        self.screen.blit(
            text_surf,
            (bar_x + bar_width + 10,
             bar_y + (bar_height - text_surf.get_height()) // 2),
        )

    def draw_weapon_hud(self):
        """Слоты оружий с подсветкой активного - под полоской здоровья."""
        if not self.player:
            return

        slot_size, gap = 36, 6
        start_x, start_y = 10, 40

        font_digit = pygame.font.Font(None, 20)
        font_name = pygame.font.Font(None, 22)

        for i, weapon in enumerate(self.player.weapons):
            slot_x = start_x + i * (slot_size + gap)
            slot_rect = pygame.Rect(slot_x, start_y, slot_size, slot_size)

            pygame.draw.rect(self.screen, get_color('DARK_GRAY'), slot_rect)
            inner = slot_rect.inflate(-8, -8)
            pygame.draw.rect(self.screen, weapon.color, inner)

            is_active = (i == self.player.current_weapon_index)
            border_color = get_color('WHITE') if is_active else (60, 60, 60)
            border_w = 3 if is_active else 1
            pygame.draw.rect(self.screen, border_color, slot_rect, border_w)

            digit_surf = font_digit.render(str(i + 1), True, get_color('WHITE'))
            self.screen.blit(digit_surf, (slot_x + 3, start_y + 2))

        # Имя активного оружия под слотами
        active = self.player.current_weapon
        name_surf = font_name.render(active.name, True, get_color('WHITE'))
        self.screen.blit(name_surf, (start_x, start_y + slot_size + 4))

    # --- Сохранения --------------------------------------------------------

    def quicksave(self):
        if self.player and self.world:
            ok = self.save_system.save_game(self.player, self.world)
            print("Игра сохранена! (F5)" if ok else "Ошибка сохранения!")
        else:
            print("Нет активной игры для сохранения!")

    def quickload(self):
        print("\n💾 [F9] Попытка быстрой загрузки...")
        if not self.save_system.quicksave_exists():
            print("   ❌ Файл сохранения не найден")
            return

        save_data = self.save_system.load_game()
        if not save_data:
            print("   ❌ Ошибка - данные повреждены")
            return

        # Создаём мир/игрока, если игра ещё не запущена
        if not self.player or not self.world:
            self.world = World(map_file=os.path.join('data', 'main_world.txt'))
            self.player = Player(0, 0)
        if not self.game_stats:
            self.game_stats = GameStats()
        if not self.game_over_screen:
            self.game_over_screen = GameOverScreen(
                get_config('WIDTH'), get_config('HEIGHT'), self.game_stats
            )

        self.save_system.apply_save_data_to_player(self.player, save_data)
        self.save_system.apply_save_data_to_world(self.world, save_data)
        self.state = GameState.PLAYING
        print("   ✅ Игра загружена! (F9)")

    # --- Главный цикл ------------------------------------------------------

    def run(self):
        while self.running:
            current_time = pygame.time.get_ticks()
            dt = (current_time - self.last_time) / 1000.0
            self.last_time = current_time
            dt = min(dt, 1.0 / 30.0)  # capping для физической стабильности

            self.handle_events()
            self.update(dt)
            self.draw()

            self.clock.tick(get_config('FPS'))

        self.log("=== СЕССИЯ ЗАВЕРШЕНА ===", "IMPORTANT")
        self.log_file.close()
        pygame.quit()
        sys.exit()

