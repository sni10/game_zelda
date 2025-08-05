import unittest
import pygame
import os
import tempfile
import shutil
from unittest.mock import patch, MagicMock
from src.core.game_states import GameState
from src.ui.menu import MainMenu


class TestGameState(unittest.TestCase):
    """Тесты для перечисления GameState"""
    
    def test_game_state_values(self):
        """Тест значений состояний игры"""
        self.assertEqual(GameState.MENU.value, "menu")
        self.assertEqual(GameState.PLAYING.value, "playing")
        self.assertEqual(GameState.GAME_OVER.value, "game_over")
    
    def test_game_state_enum_members(self):
        """Тест наличия всех членов перечисления"""
        expected_states = {"MENU", "PLAYING", "GAME_OVER"}
        actual_states = {state.name for state in GameState}
        self.assertEqual(expected_states, actual_states)


class TestMainMenu(unittest.TestCase):
    """Тесты для класса MainMenu"""
    
    def setUp(self):
        """Настройка перед каждым тестом"""
        # Инициализация pygame для тестов
        pygame.init()
        pygame.display.set_mode((800, 600))
        
        # Создаем временную директорию для тестов сохранений
        self.test_saves_dir = tempfile.mkdtemp()
        self.original_cwd = os.getcwd()
        
        # Патчим проверку файлов сохранений
        self.saves_patcher = patch('src.ui.menu.os.path.exists')
        self.listdir_patcher = patch('src.ui.menu.os.listdir')
        
        self.mock_exists = self.saves_patcher.start()
        self.mock_listdir = self.listdir_patcher.start()
        
        # По умолчанию нет сохранений
        self.mock_exists.return_value = False
        self.mock_listdir.return_value = []
    
    def tearDown(self):
        """Очистка после каждого теста"""
        self.saves_patcher.stop()
        self.listdir_patcher.stop()
        
        # Удаляем временную директорию
        shutil.rmtree(self.test_saves_dir, ignore_errors=True)
        
        pygame.quit()
    
    def test_menu_initialization_no_saves(self):
        """Тест инициализации меню без сохранений"""
        menu = MainMenu()
        expected_items = ["Новая игра", "Выход"]
        self.assertEqual(menu.menu_items, expected_items)
        self.assertEqual(menu.selected_index, 0)
    
    def test_menu_initialization_with_quicksave(self):
        """Тест инициализации меню с quicksave"""
        # Настраиваем мок для наличия quicksave
        def mock_exists_side_effect(path):
            if path == "saves/quicksave.json":
                return True
            elif path == "saves":
                return True
            return False
        
        self.mock_exists.side_effect = mock_exists_side_effect
        self.mock_listdir.return_value = ["quicksave.json"]
        
        menu = MainMenu()
        expected_items = ["Новая игра", "Продолжить игру", "Загрузить игру", "Выход"]
        self.assertEqual(menu.menu_items, expected_items)
    
    def test_menu_initialization_with_saves_no_quicksave(self):
        """Тест инициализации меню с сохранениями но без quicksave"""
        def mock_exists_side_effect(path):
            if path == "saves/quicksave.json":
                return False
            elif path == "saves":
                return True
            return False
        
        self.mock_exists.side_effect = mock_exists_side_effect
        self.mock_listdir.return_value = ["save1.json", "save2.json"]
        
        menu = MainMenu()
        expected_items = ["Новая игра", "Загрузить игру", "Выход"]
        self.assertEqual(menu.menu_items, expected_items)
    
    def test_navigation_up(self):
        """Тест навигации вверх по меню"""
        menu = MainMenu()
        initial_index = menu.selected_index
        
        # Создаем событие нажатия стрелки вверх
        event = MagicMock()
        event.type = pygame.KEYDOWN
        event.key = pygame.K_UP
        
        menu.handle_input(event)
        
        # Должен перейти к последнему элементу (циклическая навигация)
        expected_index = len(menu.menu_items) - 1
        self.assertEqual(menu.selected_index, expected_index)
    
    def test_navigation_down(self):
        """Тест навигации вниз по меню"""
        menu = MainMenu()
        initial_index = menu.selected_index
        
        # Создаем событие нажатия стрелки вниз
        event = MagicMock()
        event.type = pygame.KEYDOWN
        event.key = pygame.K_DOWN
        
        menu.handle_input(event)
        
        # Должен перейти к следующему элементу
        expected_index = (initial_index + 1) % len(menu.menu_items)
        self.assertEqual(menu.selected_index, expected_index)
    
    def test_menu_selection_new_game(self):
        """Тест выбора пункта 'Новая игра'"""
        menu = MainMenu()
        menu.selected_index = 0  # "Новая игра"
        
        # Создаем событие нажатия Enter
        event = MagicMock()
        event.type = pygame.KEYDOWN
        event.key = pygame.K_RETURN
        
        action = menu.handle_input(event)
        self.assertEqual(action, "new_game")
    
    def test_menu_selection_exit(self):
        """Тест выбора пункта 'Выход'"""
        menu = MainMenu()
        # Устанавливаем индекс на "Выход" (последний элемент)
        menu.selected_index = len(menu.menu_items) - 1
        
        # Создаем событие нажатия Enter
        event = MagicMock()
        event.type = pygame.KEYDOWN
        event.key = pygame.K_RETURN
        
        action = menu.handle_input(event)
        self.assertEqual(action, "exit")
    
    def test_menu_selection_continue_game(self):
        """Тест выбора пункта 'Продолжить игру'"""
        # Настраиваем мок для наличия quicksave
        def mock_exists_side_effect(path):
            if path == "saves/quicksave.json":
                return True
            elif path == "saves":
                return True
            return False
        
        self.mock_exists.side_effect = mock_exists_side_effect
        self.mock_listdir.return_value = ["quicksave.json"]
        
        menu = MainMenu()
        # Находим индекс "Продолжить игру"
        continue_index = menu.menu_items.index("Продолжить игру")
        menu.selected_index = continue_index
        
        # Создаем событие нажатия Enter
        event = MagicMock()
        event.type = pygame.KEYDOWN
        event.key = pygame.K_RETURN
        
        action = menu.handle_input(event)
        self.assertEqual(action, "continue_game")
    
    def test_menu_selection_load_game(self):
        """Тест выбора пункта 'Загрузить игру'"""
        # Настраиваем мок для наличия сохранений
        def mock_exists_side_effect(path):
            if path == "saves/quicksave.json":
                return True
            elif path == "saves":
                return True
            return False
        
        self.mock_exists.side_effect = mock_exists_side_effect
        self.mock_listdir.return_value = ["quicksave.json", "save1.json"]
        
        menu = MainMenu()
        # Находим индекс "Загрузить игру"
        load_index = menu.menu_items.index("Загрузить игру")
        menu.selected_index = load_index
        
        # Создаем событие нажатия Enter
        event = MagicMock()
        event.type = pygame.KEYDOWN
        event.key = pygame.K_RETURN
        
        action = menu.handle_input(event)
        self.assertEqual(action, "load_game")
    
    def test_invalid_event_handling(self):
        """Тест обработки неподдерживаемых событий"""
        menu = MainMenu()
        
        # Тест события не KEYDOWN
        event = MagicMock()
        event.type = pygame.KEYUP
        action = menu.handle_input(event)
        self.assertIsNone(action)
        
        # Тест неподдерживаемой клавиши
        event = MagicMock()
        event.type = pygame.KEYDOWN
        event.key = pygame.K_SPACE
        action = menu.handle_input(event)
        self.assertIsNone(action)
    
    def test_menu_update_on_draw(self):
        """Тест обновления меню при отрисовке"""
        menu = MainMenu()
        initial_items = menu.menu_items.copy()
        
        # Создаем реальный pygame Surface для тестов
        screen = pygame.Surface((800, 600))
        
        # Патчим get_config и get_color для тестов
        with patch('src.ui.menu.get_config') as mock_get_config, \
             patch('src.ui.menu.get_color') as mock_get_color, \
             patch('pygame.draw.rect') as mock_draw_rect:
            
            mock_get_config.side_effect = lambda key: {'WIDTH': 800, 'HEIGHT': 600}.get(key, 0)
            mock_get_color.side_effect = lambda color: (255, 255, 255)  # Белый цвет
            
            # Изменяем состояние сохранений
            def mock_exists_side_effect(path):
                if path == "saves/quicksave.json":
                    return True
                elif path == "saves":
                    return True
                return False
            
            self.mock_exists.side_effect = mock_exists_side_effect
            self.mock_listdir.return_value = ["quicksave.json"]
            
            # Вызываем отрисовку, которая должна обновить меню
            menu.draw(screen)
            
            # Проверяем, что меню обновилось
            expected_items = ["Новая игра", "Продолжить игру", "Загрузить игру", "Выход"]
            self.assertEqual(menu.menu_items, expected_items)
    
    def test_has_saves_method(self):
        """Тест метода has_saves"""
        menu = MainMenu()
        
        # Тест когда папки saves нет
        self.mock_exists.return_value = False
        self.assertFalse(menu.has_saves())
        
        # Тест когда папка есть, но файлов нет
        def mock_exists_side_effect(path):
            return path == "saves"
        
        self.mock_exists.side_effect = mock_exists_side_effect
        self.mock_listdir.return_value = []
        self.assertFalse(menu.has_saves())
        
        # Тест когда есть json файлы
        self.mock_listdir.return_value = ["save1.json", "save2.txt", "save3.json"]
        self.assertTrue(menu.has_saves())
    
    def test_has_quicksave_method(self):
        """Тест метода has_quicksave"""
        menu = MainMenu()
        
        # Тест когда quicksave нет
        self.mock_exists.return_value = False
        self.assertFalse(menu.has_quicksave())
        
        # Тест когда quicksave есть
        def mock_exists_side_effect(path):
            return path == "saves/quicksave.json"
        
        self.mock_exists.side_effect = mock_exists_side_effect
        self.assertTrue(menu.has_quicksave())


if __name__ == '__main__':
    unittest.main()