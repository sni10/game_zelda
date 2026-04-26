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

# Новые импорты для системы множественных миров
from src.core.ecs.entity import EntityManager
from src.core.ecs.system import SystemManager, ZTransitionSystem, PortalSystem
from src.core.ecs.component import PositionComponent, RenderLayerComponent, ZLevelComponent, PortalComponent
from src.rendering.layer_renderer import LayerRenderer
from src.world.world_manager import WorldManager
from src.systems.multiworld_save_system import MultiWorldSaveSystem


class Game:
    def __init__(self):
        # Система логирования
        self._setup_logging()

        # Загрузка конфигурации
        self.config = load_config()
        
        # Инициализация Pygame
        pygame.init()
        self.screen = pygame.display.set_mode((get_config('WIDTH'), get_config('HEIGHT')))
        pygame.display.set_caption("Zelda-like Game")
        self.clock = pygame.time.Clock()
        self.running = True
        
        # Состояние игры
        self.state = GameState.MENU
        
        # Главное меню
        self.menu = MainMenu()
        
        # Инициализация ECS системы
        self.entity_manager = EntityManager()
        self.system_manager = SystemManager(self.entity_manager)
        
        # Инициализация системы рендеринга
        self.layer_renderer = LayerRenderer(self.entity_manager, self.screen)
        self.system_manager.add_system(self.layer_renderer)
        
        # Добавляем системы для переходов
        z_transition_system = ZTransitionSystem(self.entity_manager)
        portal_system = PortalSystem(self.entity_manager)
        self.system_manager.add_system(z_transition_system)
        self.system_manager.add_system(portal_system)
        
        # Инициализация менеджера миров
        self.world_manager = WorldManager(
            self.entity_manager,
            self.system_manager,
            self.layer_renderer
        )
        
        # Игровые объекты (инициализируются при начале новой игры)
        self.world = None  # Сохраняем для совместимости
        self.player = None
        self.player_entity = None  # ECS сущность игрока
        self.game_stats = None
        self.game_over_screen = None
        
        # Переменные для отслеживания времени
        self.last_time = pygame.time.get_ticks()
        
        # Отладочная информация
        self.show_debug = False
        
        # Система сохранений (старая и новая)
        self.save_system = SaveSystem()
        self.multiworld_save_system = MultiWorldSaveSystem(self.entity_manager, self.world_manager)
        
        # Словарь для хранения старых миров (совместимость)
        self.legacy_worlds = {}

    def _setup_logging(self):
        """Настройка системы логирования в файлы"""
        # Создаем папку для логов
        log_dir = "logs"
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)

        # Создаем файл лога с текущим временем
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        self.log_filename = os.path.join(log_dir, f"game_session_{timestamp}.log")

        # Открываем файл для записи
        self.log_file = open(self.log_filename, 'w', encoding='utf-8')
        self.log_file.write(f"=== ИГРОВАЯ СЕССИЯ НАЧАЛАСЬ: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ===\n\n")
        self.log_file.flush()

        print(f"📝 Логи записываются в: {self.log_filename}")

    def log(self, message, level="INFO"):
        """Записать сообщение в лог файл"""
        timestamp = datetime.datetime.now().strftime("%H:%M:%S.%f")[:-3]  # Миллисекунды
        log_entry = f"[{timestamp}] [{level}] {message}\n"

        # Записываем в файл
        self.log_file.write(log_entry)
        self.log_file.flush()

        # Дублируем в консоль только важные события
        if level in ["IMPORTANT", "ERROR", "WARNING"]:
            print(f"{message}")

    def _get_or_create_legacy_world(self, world_id: str) -> World:
        """Получить или создать 'старый' мир для рендеринга"""
        if world_id not in self.legacy_worlds:
            map_filename = f"{world_id}.txt"
            map_file_path = os.path.join('data', map_filename)

            # Фоллбэк на основную карту, если файл не найден
            if not os.path.exists(map_file_path):
                self.log(f"Карта '{map_filename}' не найдена, используется 'main_world.txt'", "WARNING")
                map_file_path = os.path.join('data', 'main_world.txt')

            self.log(f"Создание legacy world '{world_id}' из файла '{map_file_path}'")
            self.legacy_worlds[world_id] = World(map_file=map_file_path)

        return self.legacy_worlds[world_id]

    def start_new_game(self):
        """Инициализация новой игры"""
        self.log("=== ЗАПУСК НОВОЙ ИГРЫ ===", "IMPORTANT")

        # Создание старого мира для совместимости
        self.world = self._get_or_create_legacy_world("main_world")
        player_start_x, player_start_y = self.world.get_player_start_position()
        self.log(f"Стартовая позиция игрока: ({player_start_x}, {player_start_y})")

        # Создание множественных миров через WorldManager
        self.log("Создание множественных миров...")

        # Основной мир
        success = self.world_manager.create_world("main", "main_world", 
                                                 (get_config('WORLD_WIDTH'), get_config('WORLD_HEIGHT')))
        if success:
            self.log("✅ Основной мир создан", "IMPORTANT")
        else:
            self.log("❌ Ошибка создания основного мира!", "ERROR")

        # Мир-пещера с тоннелями
        success = self.world_manager.create_world("cave", "cave_world", (800, 600))
        if success:
            self.log("✅ Мир-пещера создан", "IMPORTANT")
        else:
            self.log("❌ Ошибка создания мира-пещеры!", "ERROR")

        # Подземный мир
        success = self.world_manager.create_world("underground", "underground_world", (600, 400))
        if success:
            self.log("✅ Подземный мир создан", "IMPORTANT")
        else:
            self.log("❌ Ошибка создания подземного мира!", "ERROR")

        # Создание старого Player объекта для совместимости.
        # player_start_x/y - это ЦЕНТР стартового тайла (terrain.py: tile_x + 16),
        # а Player(x, y) принимает координаты ЛЕВОГО ВЕРХНЕГО угла rect 32x32.
        # Поэтому смещаем на половину размера игрока, чтобы игрок оказался
        # ровно по центру тайла @, а не пересекал 4 соседних тайла.
        spawn_x = player_start_x - 16  # 16 = PLAYER_SIZE // 2
        spawn_y = player_start_y - 16
        self.player = Player(spawn_x, spawn_y)
        self.log(f"Игрок создан: HP={self.player.health}/{self.player.max_health}")

        # Создание ECS сущности игрока (синхронно с legacy Player - левый верхний угол)
        self.player_entity = self.entity_manager.create_entity()
        self.player_entity.add_component(PositionComponent(spawn_x, spawn_y, 0, "main_world"))
        self.player_entity.add_component(RenderLayerComponent(0))
        self.player_entity.add_component(ZLevelComponent(0))
        self.log(f"ECS сущность игрока создана: ID={id(self.player_entity)}")

        # Переключаемся на основной мир
        self.world_manager.switch_to_world("main_world", self.player_entity)

        current_world = self.world_manager.get_current_world()
        if current_world:
            self.log(f"✅ Активный мир: {current_world.world_id}", "IMPORTANT")
        else:
            self.log("❌ Ошибка: текущий мир не найден!", "ERROR")
        
        # Инициализация статистики игры
        self.game_stats = GameStats()
        
        # Инициализация Game Over экрана
        self.game_over_screen = GameOverScreen(
            get_config('WIDTH'), 
            get_config('HEIGHT'), 
            self.game_stats
        )
        
        print("Игра инициализирована с системой множественных миров!")
        print("Управление: WASD - движение, E - Z-переходы, P - порталы, 1,2,3 - смена миров")
        
        # Переход в игровое состояние
        self.state = GameState.PLAYING

    def handle_events(self):
        """Обработка событий"""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN:
                if self.state == GameState.MENU:
                    # Обработка событий в меню
                    action = self.menu.handle_input(event)
                    if action == "new_game":
                        self.start_new_game()
                    elif action == "continue_game":
                        # Загрузка quicksave
                        self.quickload()
                    elif action == "load_game":
                        # TODO: Реализовать диалог выбора сохранений при реализации Issue #16
                        print("Загрузить игру - функция будет реализована в Issue #16")
                        # Пока что запускаем новую игру
                        self.start_new_game()
                    elif action == "exit":
                        self.running = False
                elif self.state == GameState.PLAYING:
                    # Обработка событий в игре
                    if event.key == pygame.K_F1:
                        self.show_debug = not self.show_debug
                    elif event.key == pygame.K_F5:
                        # Быстрое сохранение
                        self.quicksave()
                    elif event.key == pygame.K_F9:
                        # Быстрая загрузка
                        self.quickload()
                    elif event.key == pygame.K_ESCAPE:
                        self.state = GameState.MENU
                    
                    # Новые клавиши для системы множественных миров.
                    # ВНИМАНИЕ: смена миров перенесена с 1/2/3 на F2/F3/F4,
                    # чтобы освободить цифры под выбор оружия (1..N).
                    elif event.key == pygame.K_e:
                        self.log("⚡ [E] Z-переход", "IMPORTANT")
                        self.handle_z_transition()
                    elif event.key == pygame.K_p:
                        self.log("🌀 [P] Активация портала", "IMPORTANT")
                        self.handle_portal_activation()
                    elif event.key == pygame.K_F2:
                        self.log("🌍 [F2] -> Основной мир", "IMPORTANT")
                        success = self.world_manager.switch_to_world("main_world", self.player_entity)
                        if success:
                            self.world = self._get_or_create_legacy_world("main_world")
                            self.sync_player_position()
                        else:
                            self.log("❌ Ошибка переключения на основной мир!", "ERROR")
                    elif event.key == pygame.K_F3:
                        self.log("🕳️ [F3] -> Мир-пещера", "IMPORTANT")
                        success = self.world_manager.switch_to_world("cave_world", self.player_entity)
                        if success:
                            self.world = self._get_or_create_legacy_world("cave_world")
                            self.sync_player_position()
                        else:
                            self.log("❌ Ошибка переключения на мир-пещеру!", "ERROR")
                    elif event.key == pygame.K_F4:
                        self.log("⛏️ [F4] -> Подземный мир", "IMPORTANT")
                        success = self.world_manager.switch_to_world("underground_world", self.player_entity)
                        if success:
                            self.world = self._get_or_create_legacy_world("underground_world")
                            self.sync_player_position()
                        else:
                            self.log("❌ Ошибка переключения на подземный мир!", "ERROR")

                    # Выбор оружия по цифровым клавишам 1..N (соответствуют
                    # порядку Player.weapons из default_loadout()).
                    elif event.key in (pygame.K_1, pygame.K_2, pygame.K_3,
                                       pygame.K_4, pygame.K_5):
                        if self.player:
                            digit = event.key - pygame.K_1  # K_1 -> 0
                            if self.player.switch_weapon(digit):
                                w = self.player.current_weapon
                                self.log(f"🗡️ [{digit + 1}] Оружие: {w.name} "
                                         f"(reach={w.reach}, dmg={w.damage})",
                                         "IMPORTANT")
                elif self.state == GameState.GAME_OVER:
                    # Обработка событий на экране Game Over
                    if self.game_over_screen:
                        action = self.game_over_screen.handle_input(event)
                        if action == "MENU":
                            self.state = GameState.MENU
                        elif action == "QUIT":
                            self.running = False

    def handle_z_transition(self):
        """Обработка перехода между Z-уровнями"""
        print("   🔍 Проверка наличия ECS сущности игрока...")
        if not self.player_entity:
            print("   ❌ ECS сущность игрока отсутствует!")
            return

        player_pos = self.player_entity.get_component(PositionComponent)
        z_comp = self.player_entity.get_component(ZLevelComponent)

        if not player_pos or not z_comp:
            print("   ❌ Отсутствуют компоненты позиции или Z-уровня!")
            return

        print(f"   📍 Текущая позиция: ({player_pos.x}, {player_pos.y}), Z={player_pos.z}")

        # Простая логика: переключаемся между Z=0 и Z=-1
        current_z = player_pos.z
        target_z = -1 if current_z == 0 else 0
        print(f"   🎯 Попытка перехода Z: {current_z} -> {target_z}")

        # Проверяем, находимся ли мы в мире с тоннелями
        current_world = self.world_manager.get_current_world()
        print(f"   🌍 Текущий мир: {current_world.world_id if current_world else 'None'}")

        if current_world:
            print(f"   ✅ Мир {current_world.world_id} поддерживает Z-переходы, выполняем...")
            # Теперь Z-переходы работают во всех мирах
            success = self.world_manager.handle_z_transition(self.player_entity, target_z)
            if success:
                self.layer_renderer.set_player_z_level(target_z)
                self.sync_player_position()
                print(f"   ✅ Z-переход успешен: {current_z} -> {target_z}")

                # Показываем какой режим рендеринга будет использоваться
                if target_z == -1:
                    print("   🕳️  Переходим в режим рендеринга ПЕЩЕРЫ")
                else:
                    print("   🌍 Переходим в режим рендеринга ПОВЕРХНОСТИ")
            else:
                print("   ❌ Z-переход не удался - ошибка WorldManager")
        else:
            print("   ❌ Текущий мир не найден - Z-переходы невозможны")
            
    def handle_portal_activation(self):
        """Обработка активации портала"""
        if not self.player_entity:
            return
            
        player_pos = self.player_entity.get_component(PositionComponent)
        if not player_pos:
            return
            
        # Ищем ближайший портал
        current_world_entities = self.world_manager.get_current_world_entities()
        
        for entity in current_world_entities:
            if entity.has_component(PortalComponent):
                # Проверяем расстояние до портала
                portal_pos = entity.get_component(PositionComponent)
                if portal_pos:
                    dx = player_pos.x - portal_pos.x
                    dy = player_pos.y - portal_pos.y
                    distance = (dx * dx + dy * dy) ** 0.5
                    
                    if distance <= 64:  # Радиус активации портала
                        success = self.world_manager.handle_portal_activation(entity, self.player_entity)
                        if success:
                            self.sync_player_position()
                            print(f"Портал активирован! Переход в {player_pos.world_id}")
                            return
                            
        print("Поблизости нет портала")
        
    def sync_player_position(self):
        """Синхронизация позиции между старым Player и ECS сущностью"""
        if not self.player or not self.player_entity:
            return
            
        player_pos = self.player_entity.get_component(PositionComponent)
        if player_pos:
            print(f"   🔄 Синхронизация позиции: ECS({player_pos.x}, {player_pos.y}) -> Player({self.player.x}, {self.player.y})")

            # ВАЖНО: Синхронизируем в обе стороны
            # Если ECS позиция (0,0) но Player имеет нормальную позицию, используем Player
            if player_pos.x == 0 and player_pos.y == 0 and (self.player.x != 0 or self.player.y != 0):
                print(f"   ⚠️  ECS сущность в (0,0), восстанавливаем из Player: ({self.player.x}, {self.player.y})")
                player_pos.set_position(self.player.x, self.player.y)
            else:
                # Обычная синхронизация: ECS -> Player
                self.player.x = player_pos.x
                self.player.y = player_pos.y
                self.player.rect.x = int(player_pos.x)
                self.player.rect.y = int(player_pos.y)
            
            # Обновляем камеру
            if self.world:
                self.world.update_camera(
                    self.player.x + self.player.width // 2,
                    self.player.y + self.player.height // 2,
                    get_config('WIDTH'), get_config('HEIGHT')
                )

    def update(self, dt):
        """Обновление игровой логики"""
        if self.state == GameState.PLAYING and self.player and self.world:
            # Проверка смерти игрока
            if self.player.is_dead():
                self.game_stats.record_death()
                self.state = GameState.GAME_OVER
                return
            
            # Получение состояния клавиш
            keys = pygame.key.get_pressed()
            
            # Обработка ввода игрока
            self.player.handle_input(keys)
            
            # Обновление игрока (коллизии теперь проверяются внутри player.update)
            self.player.update(dt, self.world, self.game_stats)
            
            # Синхронизация позиции ECS сущности с Player объектом
            if self.player_entity:
                player_pos = self.player_entity.get_component(PositionComponent)
                if player_pos:
                    player_pos.set_position(self.player.x, self.player.y)
            
            # Обновление WorldManager и ECS систем
            self.world_manager.update(dt)
            self.system_manager.update_all(dt)
            
            # Обновление камеры для LayerRenderer
            if self.player_entity:
                player_pos = self.player_entity.get_component(PositionComponent)
                if player_pos:
                    self.layer_renderer.set_camera(
                        player_pos.x - get_config('WIDTH') // 2,
                        player_pos.y - get_config('HEIGHT') // 2
                    )
            
            # Обновление статистики
            if self.game_stats:
                self.game_stats.update_position(self.player.x, self.player.y)
            
            # Обновление камеры для старого World (для совместимости)
            self.world.update_camera(
                self.player.x + self.player.width // 2,
                self.player.y + self.player.height // 2,
                get_config('WIDTH'), get_config('HEIGHT')
            )

    def draw(self):
        """Отрисовка игры"""
        if self.state == GameState.MENU:
            # Отрисовка меню
            self.menu.draw(self.screen)
        elif self.state == GameState.PLAYING and self.player and self.world:
            # Получаем информацию о текущем состоянии
            player_pos = self.player_entity.get_component(PositionComponent) if self.player_entity else None
            current_world = self.world_manager.get_current_world()

            # Убираем частые логи рендеринга - только при смене режимов
            render_mode = "SURFACE" if (not player_pos or player_pos.z == 0) else "CAVE"

            if not hasattr(self, '_last_render_mode') or self._last_render_mode != render_mode:
                self._last_render_mode = render_mode
                mode_name = "ОБЫЧНЫЙ МИР" if render_mode == "SURFACE" else "ПЕЩЕРА (LayerRenderer)"
                world_name = current_world.world_id if current_world else "None"
                self.log(f"🎨 Смена режима рендеринга: {mode_name}, мир: {world_name}, Z: {player_pos.z if player_pos else 0}", "IMPORTANT")

            # Если игрок НЕ в пещере, рендерим обычный мир
            if not player_pos or player_pos.z == 0:
                # Очищаем экран правильным цветом
                self.screen.fill(get_color('BLACK'))
                # Рендерим основной мир с координатами игрока (земля + фон + миникарта)
                self.world.draw(self.screen, self.player.x, self.player.y)
                # Рендерим игрока ПОВЕРХ земли
                self.player.draw(self.screen, self.world.camera_x, self.world.camera_y)
                # Рендерим overlay-слой (верхушки холмов) ПОВЕРХ игрока,
                # с эффектом полупрозрачности когда игрок под тайлом
                self.world.draw_overlay(self.screen, self.player.rect)
            else:

                # В пещере используем LayerRenderer
                dt = self.clock.get_time() / 1000.0
                self.layer_renderer.update(dt)

                # Дополнительный рендеринг игрока поверх всех слоев
                screen_x = int(player_pos.x - self.layer_renderer.camera_x)
                screen_y = int(player_pos.y - self.layer_renderer.camera_y)

                # Цвет игрока зависит от Z-уровня
                color = (255, 200, 100) if player_pos.z == -1 else (100, 255, 100)

                # Рисуем игрока с улучшенной видимостью
                pygame.draw.circle(self.screen, color, (screen_x, screen_y), 16)
                pygame.draw.circle(self.screen, (255, 255, 255), (screen_x, screen_y), 16, 2)
            
            # Отрисовка UI (полоска здоровья)
            self.draw_health_bar()
            self.draw_weapon_hud()

            # Отладочная информация
            if self.show_debug:
                current_world = self.world_manager.get_current_world()
                world_stats = self.world_manager.get_world_stats()
                player_pos = self.player_entity.get_component(PositionComponent) if self.player_entity else None
                
                debug_info = [
                    f"Player: ({int(self.player.x)}, {int(self.player.y)})",
                    f"World: {player_pos.world_id if player_pos else 'None'}",
                    f"Z-Level: {player_pos.z if player_pos else 0}",
                    f"Camera: ({int(self.layer_renderer.camera_x)}, {int(self.layer_renderer.camera_y)})",
                    f"Direction: {self.player.facing_direction}",
                    f"Attacking: {self.player.attacking}",
                    f"FPS: {int(self.clock.get_fps())}",
                    f"Worlds: {world_stats['total_worlds']} total, {world_stats['loaded_worlds']} loaded",
                    "Controls: WASD - Move, Space - Attack, E - Z-transition, P - Portal",
                    "1..4 - Weapon, F2/F3/F4 - Switch worlds, F1 - Debug, ESC - Menu"
                ]
                
                y_offset = 10
                for info in debug_info:
                    debug(info, y=y_offset)
                    y_offset += 20
            else:
                # Показываем расширенные инструкции
                current_world = self.world_manager.get_current_world()
                world_name = current_world.world_id if current_world else "Unknown"
                player_pos = self.player_entity.get_component(PositionComponent) if self.player_entity else None
                z_level = player_pos.z if player_pos else 0
                
                debug(f"World: {world_name} | Z-Level: {z_level} | F1 - Debug | ESC - Menu", 
                      y=get_config('HEIGHT') - 50)
                debug("E - Z-transition | P - Portal | F2/F3/F4 - Switch worlds | 1..4 - Weapon",
                      y=get_config('HEIGHT') - 30)
        elif self.state == GameState.GAME_OVER:
            # Отрисовка экрана Game Over
            if self.game_over_screen:
                self.game_over_screen.draw(self.screen)
        
        # Обновление дисплея
        pygame.display.flip()

    def draw_health_bar(self):
        """Отрисовка полоски здоровья игрока"""
        # Параметры полоски здоровья
        bar_width = 200
        bar_height = 20
        bar_x = 10
        bar_y = 10
        border_width = 2
        
        # Вычисляем процент здоровья
        health_percentage = self.player.health / self.player.max_health
        health_bar_width = int(bar_width * health_percentage)
        
        # Рисуем фон полоски (темно-серый)
        pygame.draw.rect(self.screen, get_color('DARK_GRAY'), 
                        (bar_x, bar_y, bar_width, bar_height))
        
        # Рисуем полоску здоровья (зеленый)
        if health_bar_width > 0:
            pygame.draw.rect(self.screen, get_color('GREEN'), 
                            (bar_x, bar_y, health_bar_width, bar_height))
        
        # Рисуем тонкую рамочку
        pygame.draw.rect(self.screen, get_color('WHITE'), 
                        (bar_x - border_width, bar_y - border_width, 
                         bar_width + border_width * 2, bar_height + border_width * 2), 
                        border_width)
        
        # Добавляем текст с числовым значением здоровья
        font = pygame.font.Font(None, 24)
        health_text = f"{int(self.player.health)}/{int(self.player.max_health)}"
        text_surface = font.render(health_text, True, get_color('WHITE'))
        text_x = bar_x + bar_width + 10
        text_y = bar_y + (bar_height - text_surface.get_height()) // 2
        self.screen.blit(text_surface, (text_x, text_y))

    def draw_weapon_hud(self):
        """HUD оружий - под полоской здоровья.

        Отображает все слоты оружия (квадратики цвета оружия), цифру
        для переключения и подсвечивает активное оружие белой рамкой.
        Под HUD - имя текущего оружия.
        """
        if not self.player:
            return

        slot_size = 36
        gap = 6
        start_x = 10
        start_y = 40  # под health bar (он на y=10, высотой 20 + рамка)

        font_digit = pygame.font.Font(None, 20)
        font_name = pygame.font.Font(None, 22)

        for i, weapon in enumerate(self.player.weapons):
            slot_x = start_x + i * (slot_size + gap)
            slot_rect = pygame.Rect(slot_x, start_y, slot_size, slot_size)

            # Фон слота - тёмно-серый
            pygame.draw.rect(self.screen, get_color('DARK_GRAY'), slot_rect)
            # Заливка цветом оружия (приглушённая)
            inner = slot_rect.inflate(-8, -8)
            pygame.draw.rect(self.screen, weapon.color, inner)

            # Рамка: белая толстая для активного, тёмная для остальных
            is_active = (i == self.player.current_weapon_index)
            border_color = get_color('WHITE') if is_active else (60, 60, 60)
            border_width = 3 if is_active else 1
            pygame.draw.rect(self.screen, border_color, slot_rect, border_width)

            # Цифра в углу слота
            digit_surf = font_digit.render(str(i + 1), True, get_color('WHITE'))
            self.screen.blit(digit_surf, (slot_x + 3, start_y + 2))

        # Имя активного оружия под слотами
        active = self.player.current_weapon
        name_surf = font_name.render(active.name, True, get_color('WHITE'))
        self.screen.blit(name_surf, (start_x, start_y + slot_size + 4))

    def quicksave(self):
        """Быстрое сохранение игры (F5)"""
        if self.player and self.world:
            success = self.save_system.save_game(self.player, self.world)
            if success:
                # Показываем уведомление об успешном сохранении
                print("Игра сохранена! (F5)")
            else:
                print("Ошибка сохранения!")
        else:
            print("Нет активной игры для сохранения!")

    def quickload(self):
        """Быстрая загрузка игры (F9)"""
        print("\n💾 [F9] Попытка быстрой загрузки игры...")

        if not self.save_system.quicksave_exists():
            print("   ❌ Файл быстрого сохранения не найден!")
            return

        print("   ✅ Файл quicksave.json найден, загружаем данные...")
        save_data = self.save_system.load_game()

        if save_data:
            print(f"   📦 Загруженные данные: {list(save_data.keys())}")

            # Если игра не запущена, создаем новый мир и игрока
            if not self.player or not self.world:
                print("   🏗️  Создание нового мира и игрока для загрузки...")
                self.world = World(width=get_config('WORLD_WIDTH'), height=get_config('WORLD_HEIGHT'))
                # Создаем игрока с временными координатами
                self.player = Player(0, 0)

            # Инициализация статистики игры (если еще не создана)
            if not self.game_stats:
                print("   📊 Создание объекта статистики игры...")
                self.game_stats = GameStats()

            # Инициализация Game Over экрана (если еще не создан)
            if not self.game_over_screen:
                print("   💀 Создание экрана Game Over...")
                self.game_over_screen = GameOverScreen(
                    get_config('WIDTH'), 
                    get_config('HEIGHT'), 
                    self.game_stats
                )

            # Применяем загруженные данные
            print("   🔄 Применение загруженных данных к игроку...")
            self.save_system.apply_save_data_to_player(self.player, save_data)
            print(f"      👤 Позиция игрока: ({self.player.x}, {self.player.y})")
            print(f"      💚 Здоровье: {self.player.health}/{self.player.max_health}")

            print("   🔄 Применение загруженных данных к миру...")
            self.save_system.apply_save_data_to_world(self.world, save_data)

            # Переходим в игровое состояние
            self.state = GameState.PLAYING
            print("   ✅ Игра успешно загружена! (F9)")
        else:
            print("   ❌ Ошибка загрузки - данные сохранения повреждены!")

    def run(self):
        """Основной игровой цикл"""
        while self.running:
            # Вычисление времени кадра
            current_time = pygame.time.get_ticks()
            dt = (current_time - self.last_time) / 1000.0  # Конвертация в секунды
            self.last_time = current_time
            
            # Ограничение dt для стабильности
            dt = min(dt, 1.0 / 30.0)  # Максимум 30 FPS для физики
            
            # Обработка событий
            self.handle_events()
            
            # Обновление игры
            self.update(dt)
            
            # Отрисовка
            self.draw()
            
            # Ограничение FPS
            self.clock.tick(get_config('FPS'))
        
        # Завершение работы
        self.log("=== СЕССИЯ ЗАВЕРШЕНА ===", "IMPORTANT")
        self.log_file.close()
        pygame.quit()
        sys.exit()

