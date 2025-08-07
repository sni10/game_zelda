"""
Демонстрационный скрипт для тестирования системы множественных миров и Z-координат
"""
import pygame
import sys
import os

# Добавляем путь к проекту
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.core.ecs.entity import EntityManager
from src.core.ecs.system import SystemManager
from src.core.ecs.component import PositionComponent, RenderLayerComponent, ZLevelComponent
from src.rendering.layer_renderer import LayerRenderer
from src.world.world_manager import WorldManager
from src.factories.world_factory import WorldFactoryRegistry


class MultiWorldDemo:
    """Демонстрация системы множественных миров и Z-координат"""
    
    def __init__(self):
        # Инициализация Pygame
        pygame.init()
        self.screen = pygame.display.set_mode((1024, 768))
        pygame.display.set_caption("Multi-World Z-Coordinate System Demo")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.Font(None, 24)
        
        # Инициализация ECS
        self.entity_manager = EntityManager()
        self.system_manager = SystemManager(self.entity_manager)
        
        # Инициализация рендерера
        self.layer_renderer = LayerRenderer(self.entity_manager, self.screen)
        self.system_manager.add_system(self.layer_renderer)
        
        # Инициализация менеджера миров
        self.world_manager = WorldManager(
            self.entity_manager, 
            self.system_manager, 
            self.layer_renderer
        )
        
        # Создание игрока
        self.player = self.create_player()
        
        # Создание миров
        self.create_demo_worlds()
        
        # Состояние демо
        self.running = True
        self.current_info_mode = 0  # 0: основная информация, 1: статистика миров, 2: помощь
        self.show_debug = True
        
        print("Multi-World Z-Coordinate Demo initialized!")
        print("Controls:")
        print("  WASD - Move player")
        print("  E - Enter/Exit tunnel/cave (Z-level transition)")
        print("  P - Activate portal (world transition)")
        print("  1,2,3,4 - Switch worlds directly")
        print("  TAB - Toggle info display")
        print("  F1 - Toggle debug info")
        print("  ESC - Exit")
        
    def create_player(self):
        """Создать игрока"""
        player = self.entity_manager.create_entity()
        player.add_component(PositionComponent(400, 300, 0, "main_world"))
        player.add_component(RenderLayerComponent(0))
        player.add_component(ZLevelComponent(0))
        return player
        
    def create_demo_worlds(self):
        """Создать демонстрационные миры"""
        # Основной мир
        success = self.world_manager.create_world("main", "main_world", (800, 600))
        if success:
            print("✓ Created main world")
            
        # Второй обычный мир с пещерами
        success = self.world_manager.create_world("second", "second_world", (800, 600))
        if success:
            print("✓ Created second world with caves")
            
        # Мир-пещера с тоннелями
        success = self.world_manager.create_world("cave", "cave_world", (800, 600))
        if success:
            print("✓ Created cave world with tunnels")
            
        # Подземный мир
        success = self.world_manager.create_world("underground", "underground_world", (600, 400))
        if success:
            print("✓ Created underground world")
            
        # Переключаемся на основной мир
        self.world_manager.switch_to_world("main_world", self.player)
        
    def handle_events(self):
        """Обработка событий"""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
                
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.running = False
                    
                elif event.key == pygame.K_TAB:
                    self.current_info_mode = (self.current_info_mode + 1) % 3
                    
                elif event.key == pygame.K_F1:
                    self.show_debug = not self.show_debug
                    
                elif event.key == pygame.K_e:
                    self.handle_z_transition()
                    
                elif event.key == pygame.K_p:
                    self.handle_portal_activation()
                    
                elif event.key == pygame.K_1:
                    self.world_manager.switch_to_world("main_world", self.player)
                    
                elif event.key == pygame.K_2:
                    self.world_manager.switch_to_world("cave_world", self.player)
                    
                elif event.key == pygame.K_3:
                    self.world_manager.switch_to_world("underground_world", self.player)
                    
                elif event.key == pygame.K_4:
                    self.world_manager.switch_to_world("second_world", self.player)
                    
    def handle_input(self):
        """Обработка ввода для движения игрока"""
        keys = pygame.key.get_pressed()
        player_pos = self.player.get_component(PositionComponent)
        
        if not player_pos:
            return
            
        # Скорость движения
        speed = 200  # пикселей в секунду
        dt = self.clock.get_time() / 1000.0  # время в секундах
        
        # Движение
        dx, dy = 0, 0
        if keys[pygame.K_a] or keys[pygame.K_LEFT]:
            dx = -speed * dt
        if keys[pygame.K_d] or keys[pygame.K_RIGHT]:
            dx = speed * dt
        if keys[pygame.K_w] or keys[pygame.K_UP]:
            dy = -speed * dt
        if keys[pygame.K_s] or keys[pygame.K_DOWN]:
            dy = speed * dt
            
        # Обновляем позицию игрока
        if dx != 0 or dy != 0:
            new_x = max(32, min(player_pos.x + dx, 768))  # Ограничиваем границами
            new_y = max(32, min(player_pos.y + dy, 536))
            player_pos.set_position(new_x, new_y)
            
    def handle_z_transition(self):
        """Обработка перехода между Z-уровнями"""
        player_pos = self.player.get_component(PositionComponent)
        z_comp = self.player.get_component(ZLevelComponent)
        
        if not player_pos or not z_comp:
            return
            
        # Простая логика: переключаемся между Z=0 и Z=-1
        current_z = player_pos.z
        target_z = -1 if current_z == 0 else 0
        
        # Проверяем, находимся ли мы в мире с тоннелями или пещерами
        current_world = self.world_manager.get_current_world()
        if current_world and (current_world.world_id == "cave_world" or current_world.world_id == "second_world"):
            # В мире-пещере или втором мире можем переходить между уровнями
            success = self.world_manager.handle_z_transition(self.player, target_z)
            if success:
                self.layer_renderer.set_player_z_level(target_z)
                world_name = "Cave World" if current_world.world_id == "cave_world" else "Second World"
                print(f"Z-transition in {world_name}: {current_z} -> {target_z}")
            else:
                print("Z-transition failed")
        else:
            print("Z-transitions only available in Cave World and Second World")
            
    def handle_portal_activation(self):
        """Обработка активации портала"""
        player_pos = self.player.get_component(PositionComponent)
        if not player_pos:
            return
            
        # Ищем ближайший портал
        current_world_entities = self.world_manager.get_current_world_entities()
        
        from src.core.ecs.component import PortalComponent
        for entity in current_world_entities:
            if entity.has_component(PortalComponent):
                # Проверяем расстояние до портала
                portal_pos = entity.get_component(PositionComponent)
                if portal_pos:
                    dx = player_pos.x - portal_pos.x
                    dy = player_pos.y - portal_pos.y
                    distance = (dx * dx + dy * dy) ** 0.5
                    
                    if distance <= 64:  # Радиус активации портала
                        success = self.world_manager.handle_portal_activation(entity, self.player)
                        if success:
                            print(f"Portal activated! Traveled to {player_pos.world_id}")
                            return
                            
        print("No portal nearby")
        
    def update(self):
        """Обновление логики"""
        dt = self.clock.get_time() / 1000.0
        
        # Обновляем менеджер миров
        self.world_manager.update(dt)
        
        # Обновляем все системы
        self.system_manager.update_all(dt)
        
        # Обновляем камеру
        player_pos = self.player.get_component(PositionComponent)
        if player_pos:
            self.layer_renderer.set_camera(
                player_pos.x - self.screen.get_width() // 2,
                player_pos.y - self.screen.get_height() // 2
            )
            
    def render(self):
        """Рендеринг"""
        # Очищаем экран правильным цветом
        self.screen.fill((20, 20, 40))  # Темно-синий фон

        # НЕ вызываем LayerRenderer.update() - он очищает экран черным
        # self.layer_renderer.update() - УБРАНО

        # Рендерим игрока напрямую
        self.render_player()
        
        # Рендерим UI
        self.render_ui()
        
        # Обновляем экран
        pygame.display.flip()
        

    def render_player(self):
        """Рендеринг игрока"""
        player_pos = self.player.get_component(PositionComponent)
        if not player_pos:
            return
            
        # Позиция на экране
        screen_x = int(player_pos.x - self.layer_renderer.camera_x)
        screen_y = int(player_pos.y - self.layer_renderer.camera_y)
        
        # Цвет игрока зависит от Z-уровня
        if player_pos.z == -1:
            color = (255, 200, 100)  # Оранжевый в тоннеле
        elif player_pos.z == 1:
            color = (200, 200, 255)  # Голубой на высоте
        else:
            color = (100, 255, 100)  # Зеленый на поверхности
            
        # Рисуем игрока
        pygame.draw.circle(self.screen, color, (screen_x, screen_y), 16)
        pygame.draw.circle(self.screen, (255, 255, 255), (screen_x, screen_y), 16, 2)
        
    def render_ui(self):
        """Рендеринг пользовательского интерфейса"""
        if self.current_info_mode == 0:
            self.render_basic_info()
        elif self.current_info_mode == 1:
            self.render_world_stats()
        elif self.current_info_mode == 2:
            self.render_help()
            
        if self.show_debug:
            self.render_debug_info()
            
    def render_basic_info(self):
        """Рендеринг основной информации"""
        player_pos = self.player.get_component(PositionComponent)
        if not player_pos:
            return
            
        info_lines = [
            f"World: {player_pos.world_id}",
            f"Position: ({int(player_pos.x)}, {int(player_pos.y)})",
            f"Z-Level: {player_pos.z}",
            f"FPS: {int(self.clock.get_fps())}",
            "",
            "Controls: WASD=Move, E=Z-transition, P=Portal",
            "1,2,3,4=Switch worlds, TAB=Info, F1=Debug"
        ]
        
        y_offset = 10
        for line in info_lines:
            if line:  # Пропускаем пустые строки
                text = self.font.render(line, True, (255, 255, 255))
                self.screen.blit(text, (10, y_offset))
            y_offset += 25
            
    def render_world_stats(self):
        """Рендеринг статистики миров"""
        stats = self.world_manager.get_world_stats()
        
        info_lines = [
            "=== WORLD STATISTICS ===",
            f"Total Worlds: {stats['total_worlds']}",
            f"Loaded Worlds: {stats['loaded_worlds']}",
            f"Active World: {stats['active_world']}",
            "",
            "World Details:"
        ]
        
        for world_id, world_info in stats['worlds'].items():
            status = "ACTIVE" if world_info['active'] else ("LOADED" if world_info['loaded'] else "UNLOADED")
            info_lines.append(f"  {world_id}: {status} ({world_info['entity_count']} entities)")
            
        y_offset = 10
        for line in info_lines:
            color = (255, 255, 100) if line.startswith("===") else (255, 255, 255)
            text = self.font.render(line, True, color)
            self.screen.blit(text, (10, y_offset))
            y_offset += 25
            
    def render_help(self):
        """Рендеринг справки"""
        help_lines = [
            "=== HELP ===",
            "",
            "Movement:",
            "  WASD / Arrow Keys - Move player",
            "",
            "World Navigation:",
            "  E - Enter/Exit tunnels/caves (Z-level transition)",
            "  P - Activate nearby portals",
            "  1 - Switch to Main World",
            "  2 - Switch to Cave World (has tunnels)",
            "  3 - Switch to Underground World",
            "  4 - Switch to Second World (has caves)",
            "",
            "Interface:",
            "  TAB - Cycle info displays",
            "  F1 - Toggle debug information",
            "  ESC - Exit demo",
            "",
            "Features to test:",
            "  • Multiple worlds with different layouts",
            "  • Z-level tunnels in Cave World",
            "  • Portal teleportation between worlds",
            "  • Layer rendering with overlay effects"
        ]
        
        y_offset = 10
        for line in help_lines:
            if line.startswith("==="):
                color = (255, 255, 100)
            elif line.startswith("  "):
                color = (200, 200, 200)
            elif line.endswith(":"):
                color = (100, 255, 100)
            else:
                color = (255, 255, 255)
                
            text = self.font.render(line, True, color)
            self.screen.blit(text, (10, y_offset))
            y_offset += 20
            
    def render_debug_info(self):
        """Рендеринг отладочной информации"""
        # Рендерим статистику рендеринга
        render_stats = self.layer_renderer.get_render_stats()
        
        debug_lines = [
            "=== DEBUG INFO ===",
            f"Entities: {render_stats['total_entities']}",
            f"Underground: {render_stats['underground_entities']}",
            f"Surface: {render_stats['surface_entities']}",
            f"Elevated: {render_stats['elevated_entities']}",
            f"Player Z: {render_stats['player_z_level']}",
            f"Cache Dirty: {render_stats['cache_dirty']}"
        ]
        
        x_offset = self.screen.get_width() - 250
        y_offset = 10
        
        for line in debug_lines:
            color = (255, 255, 100) if line.startswith("===") else (255, 200, 200)
            text = self.font.render(line, True, color)
            self.screen.blit(text, (x_offset, y_offset))
            y_offset += 20
            
    def run(self):
        """Главный цикл демонстрации"""
        while self.running:
            # Обработка событий
            self.handle_events()
            
            # Обработка ввода
            self.handle_input()
            
            # Обновление логики
            self.update()
            
            # Рендеринг
            self.render()
            
            # Ограничение FPS
            self.clock.tick(60)
            
        pygame.quit()
        print("Demo finished!")


def main():
    """Запуск демонстрации"""
    try:
        demo = MultiWorldDemo()
        demo.run()
    except Exception as e:
        print(f"Error running demo: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()