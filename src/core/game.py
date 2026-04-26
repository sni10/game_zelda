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

from src.core.config_loader import load_config, get_config, get_color
from src.core.game_states import GameState
from src.core.game_stats import GameStats
from src.ui.menu import MainMenu
from src.ui.game_over import GameOverScreen
from src.ui.hud import HUD
from src.ui.save_load_menu import SaveLoadMenu
from src.utils.debug import debug
from src.utils.session_logger import SessionLogger
from src.entities.player import Player
from src.world.world import World
from src.systems.save_system import SaveSystem
from src.systems.pickup_manager import PickupManager


# Размер игрока (32x32) - используется для центрирования в стартовом тайле.
# В будущем стоит вынести в config.ini.
_PLAYER_HALF = 16


class Game:
    def __init__(self):
        self.logger = SessionLogger()

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
        self.hud: HUD = None
        self.pickup_manager: PickupManager = None

        # Тайминги игрового цикла
        self.last_time = pygame.time.get_ticks()

        # Отладочная информация
        self.show_debug = False

        # Система сохранений
        self.save_system = SaveSystem()

        # Меню слотов сохранений (load/save) — создаётся лениво, чтобы не
        # инициализировать pygame.font раньше чем это понадобится. См. v0.3.2.
        self.save_load_menu: SaveLoadMenu = None
        # Куда возвращаться из SAVE_MENU: PLAYING (если открыт по F6) или MENU.
        self._save_menu_return_state = GameState.PLAYING

    # --- Логирование -------------------------------------------------------

    def log(self, message, level="INFO"):
        """Прокси к SessionLogger (сохранён ради обратной совместимости вызовов self.log)."""
        self.logger.log(message, level)

    # --- Жизненный цикл игры ----------------------------------------------

    def start_new_game(self):
        """Начать новую игру: создать мир, игрока, статистику."""
        self.log("=== ЗАПУСК НОВОЙ ИГРЫ ===", "IMPORTANT")

        # Загружаем основной (и единственный) мир
        self.world = World(map_file=os.path.join('data', 'main_world.txt'))
        start_x, start_y = self.world.get_player_start_position()
        self.log(f"Стартовая позиция (центр тайла @): ({start_x}, {start_y})")

        # PickupManager — система дропа/сбора пикапов
        self.pickup_manager = PickupManager()
        self.world.enemy_manager.pickup_manager = self.pickup_manager

        # Игрок спавнится центрированно в тайле, чтобы не пересекать
        # соседние клетки и не застревать у стенок.
        self.player = Player(start_x - _PLAYER_HALF, start_y - _PLAYER_HALF)
        self.log(
            f"Игрок создан: HP={self.player.health}/{self.player.max_health}, "
            f"оружие='{self.player.current_weapon.name}'"
        )

        # Спавн врагов вне зоны видимости игрока
        spawned = self.world.enemy_manager.spawn_initial(
            self.player.x, self.player.y
        )
        self.log(f"Заспавнено врагов: {spawned} "
                 f"(по типам: {self.world.enemy_manager.alive_by_type()})",
                 "IMPORTANT")

        # Статистика и Game Over экран
        self.game_stats = GameStats()
        self.game_over_screen = GameOverScreen(
            get_config('WIDTH'), get_config('HEIGHT'), self.game_stats
        )
        self.hud = HUD()

        print("Игра запущена. WASD/стрелки - движение, Space - атака, "
              "1..4 - оружие, F1 - debug, F5 - quicksave, F6 - save menu, "
              "F9 - quickload, ESC - меню")
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
            elif self.state in (GameState.LOAD_MENU, GameState.SAVE_MENU):
                self._handle_save_load_menu_key(event)

    def _handle_menu_key(self, event):
        action = self.menu.handle_input(event)
        if action == "new_game":
            self.start_new_game()
        elif action == "continue_game":
            self.quickload()
        elif action == "load_game":
            # v0.3.2 — открываем полноценное меню слотов
            self._open_load_menu()
        elif action == "exit":
            self.running = False

    def _handle_playing_key(self, event):
        if event.key == pygame.K_F1:
            self.show_debug = not self.show_debug
        elif event.key == pygame.K_F5:
            self.quicksave()
        elif event.key == pygame.K_F6:
            # v0.3.2 — выбор manual-слота для сохранения
            self._open_save_menu()
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

    def _ensure_save_load_menu(self, mode):
        """Создать или переинициализировать SaveLoadMenu в нужном режиме."""
        if self.save_load_menu is None:
            self.save_load_menu = SaveLoadMenu(self.save_system, mode=mode)
        else:
            self.save_load_menu.set_mode(mode)
        self.save_load_menu.refresh()

    def _open_load_menu(self):
        """Открыть меню загрузки. Доступно из главного меню."""
        self._ensure_save_load_menu(SaveLoadMenu.MODE_LOAD)
        # Из LOAD_MENU всегда возвращаемся в главное меню
        self.state = GameState.LOAD_MENU

    def _open_save_menu(self):
        """Открыть меню сохранения (F6). Только во время игры."""
        if not self.player or not self.world:
            print("Нет активной игры для сохранения!")
            return
        self._ensure_save_load_menu(SaveLoadMenu.MODE_SAVE)
        self._save_menu_return_state = GameState.PLAYING
        self.state = GameState.SAVE_MENU

    def _handle_save_load_menu_key(self, event):
        if self.save_load_menu is None:
            self.state = GameState.MENU
            return
        action = self.save_load_menu.handle_input(event)
        if action is None:
            return

        atype = action.get("type")
        if atype == "back":
            if self.state == GameState.SAVE_MENU:
                self.state = self._save_menu_return_state
            else:
                self.state = GameState.MENU
            return

        if atype == "load_quicksave":
            self.quickload()
            return

        if atype == "load_slot":
            slot_id = action["slot_id"]
            save_data = self.save_system.load_from_slot(slot_id)
            if save_data is None:
                print(f"   ❌ Слот {slot_id}: ошибка загрузки")
                self.save_load_menu.refresh()
                return
            self._apply_loaded_save_data(save_data)
            print(f"   ✅ Загружен слот {slot_id}")
            return

        if atype == "save_slot":
            slot_id = action["slot_id"]
            ok = self.save_system.save_to_slot(
                slot_id,
                self.player,
                self.world,
                game_stats=self.game_stats,
                pickup_manager=self.pickup_manager,
                enemy_manager=self.world.enemy_manager,
            )
            print(f"   ✅ Сохранено в слот {slot_id}" if ok
                  else f"   ❌ Ошибка сохранения в слот {slot_id}")
            self.save_load_menu.refresh()
            return

        if atype == "delete_slot":
            ok = self.save_system.delete_slot(action["slot_id"])
            print(f"   🗑 Слот {action['slot_id']} удалён" if ok
                  else f"   ❌ Не удалось удалить слот {action['slot_id']}")
            self.save_load_menu.refresh()
            return

    def _apply_loaded_save_data(self, save_data):
        """Применить уже загруженные save_data к текущему состоянию игры.

        Та же логика, что и в quickload(), но без чтения файла.
        """
        if not self.player or not self.world:
            self.world = World(map_file=os.path.join('data', 'main_world.txt'))
            self.player = Player(0, 0)
        if not self.pickup_manager:
            self.pickup_manager = PickupManager()
            self.world.enemy_manager.pickup_manager = self.pickup_manager
        if not self.game_stats:
            self.game_stats = GameStats()
        if not self.game_over_screen:
            self.game_over_screen = GameOverScreen(
                get_config('WIDTH'), get_config('HEIGHT'), self.game_stats
            )
        if not self.hud:
            self.hud = HUD()

        self.save_system.apply_save_data_to_player(self.player, save_data)
        self.save_system.apply_save_data_to_world(self.world, save_data)
        self.save_system.apply_save_data_to_enemies(
            self.world.enemy_manager, save_data
        )
        self.save_system.apply_save_data_to_pickups(
            self.pickup_manager, save_data
        )
        self.save_system.apply_save_data_to_game_stats(
            self.game_stats, save_data
        )
        self.state = GameState.PLAYING

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

        # Враги патрулируют свои зоны + авто-респавн при удалении игрока
        self.world.enemy_manager.update(
            dt, self.player.x, self.player.y, player=self.player
        )

        # Если игрок атакует - применяем урон врагам.
        # apply_player_attack использует attack_id, чтобы 1 атака
        # = 1 урон каждому затронутому врагу (даже если зона держится
        # 200-400мс на нём).
        if self.player.attacking:
            weapon = self.player.current_weapon
            hits, kills = self.world.enemy_manager.apply_player_attack(
                self.player.attack_id,
                self.player.get_attack_rects(),
                weapon.damage + self.player.damage_bonus,
                player=self.player,
            )
            if kills > 0 and self.game_stats:
                for _ in range(kills):
                    self.game_stats.record_enemy_kill(weapon.damage)
            elif hits > 0 and self.game_stats:
                self.game_stats.record_attack(weapon.damage * hits)

        if self.game_stats:
            self.game_stats.update_position(self.player.x, self.player.y)

        # Контактный урон от врагов (враг касается игрока = дамаг)
        self.world.enemy_manager.apply_contact_damage(self.player)

        # Обновление пикапов (магнит + сбор)
        if self.pickup_manager:
            self.pickup_manager.update(dt, self.player)

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
            # 2) Пикапы поверх земли (но под врагами)
            if self.pickup_manager:
                self.pickup_manager.draw(
                    self.screen, self.world.camera_x, self.world.camera_y
                )
            # 3) Враги поверх земли (но под игроком)
            self.world.enemy_manager.draw(
                self.screen, self.world.camera_x, self.world.camera_y
            )
            # 4) Игрок поверх врагов
            self.player.draw(self.screen, self.world.camera_x, self.world.camera_y)
            # 5) Overlay (крыши/холм) поверх игрока с эффектом прозрачности
            self.world.draw_overlay(self.screen, self.player.rect)
            # 6) HUD
            if self.hud:
                self.hud.draw(self.screen, self.player)

            if self.show_debug:
                self._draw_debug_info()
            else:
                debug(
                    "WASD | Shift | Space | 1..4 | F1 - Debug | "
                    "F5 - Quicksave | F6 - Save menu | F9 - Quickload | ESC - Menu",
                    y=get_config('HEIGHT') - 30,
                )

        elif self.state == GameState.GAME_OVER and self.game_over_screen:
            self.game_over_screen.draw(self.screen)

        elif self.state in (GameState.LOAD_MENU, GameState.SAVE_MENU) \
                and self.save_load_menu is not None:
            self.save_load_menu.draw(self.screen)

        pygame.display.flip()

    def _draw_debug_info(self):
        info = [
            f"Player: ({int(self.player.x)}, {int(self.player.y)})",
            f"HP: {self.player.health}/{self.player.max_health}"
            f" | Lv.{self.player.level}"
            f" | XP: {self.player.xp}/{self.player.stats.xp_to_next_level}"
            f" | Coins: {self.player.coins}",
            f"Direction: {self.player.facing_direction}",
            f"Sprint: {self.player.is_sprinting} (x{self.player.sprint_multiplier})",
            f"Weapon: {self.player.current_weapon.name} (dmg={self.player.current_weapon.damage}+{self.player.damage_bonus})",
            f"Attacking: {self.player.attacking} (id={self.player.attack_id})",
            f"Enemies alive: {self.world.enemy_manager.alive_count()} "
            f"({self.world.enemy_manager.alive_by_type()})",
            f"Pickups: {self.pickup_manager.count() if self.pickup_manager else 0}",
            f"Kills: {self.game_stats.enemies_killed if self.game_stats else 0}",
            f"FPS: {int(self.clock.get_fps())}",
            "Controls: WASD - Move, Shift - Sprint, Space - Attack, 1..4 - Weapon",
            "F1 - Debug, F5 - Quicksave, F6 - Save menu, F9 - Quickload, ESC - Menu",
        ]
        y = 10
        for line in info:
            debug(line, y=y)
            y += 20

    # --- Сохранения --------------------------------------------------------

    def quicksave(self):
        if self.player and self.world:
            ok = self.save_system.save_game(
                self.player,
                self.world,
                game_stats=self.game_stats,
                pickup_manager=self.pickup_manager,
                enemy_manager=self.world.enemy_manager,
            )
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
        if not self.pickup_manager:
            self.pickup_manager = PickupManager()
            self.world.enemy_manager.pickup_manager = self.pickup_manager
        if not self.game_stats:
            self.game_stats = GameStats()
        if not self.game_over_screen:
            self.game_over_screen = GameOverScreen(
                get_config('WIDTH'), get_config('HEIGHT'), self.game_stats
            )
        if not self.hud:
            self.hud = HUD()

        self.save_system.apply_save_data_to_player(self.player, save_data)
        self.save_system.apply_save_data_to_world(self.world, save_data)
        self.save_system.apply_save_data_to_enemies(
            self.world.enemy_manager, save_data
        )
        self.save_system.apply_save_data_to_pickups(
            self.pickup_manager, save_data
        )
        self.save_system.apply_save_data_to_game_stats(
            self.game_stats, save_data
        )
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
        self.logger.close()
        pygame.quit()
        sys.exit()

