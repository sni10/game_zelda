"""
Tests for the GameOverScreen class
"""
import pytest
import pygame
import os
from unittest.mock import MagicMock, patch
from src.ui.game_over import GameOverScreen
from src.core.game_stats import GameStats


class TestGameOverScreen:
    """Test cases for GameOverScreen class"""
    
    @classmethod
    def setup_class(cls):
        """Set up pygame for testing"""
        os.environ['SDL_VIDEODRIVER'] = 'dummy'
        pygame.init()
    
    def setup_method(self):
        """Set up test fixtures"""
        self.screen_width = 800
        self.screen_height = 600
        self.game_stats = GameStats()
        self.game_over_screen = GameOverScreen(
            self.screen_width, 
            self.screen_height, 
            self.game_stats
        )
    
    def test_game_over_screen_initialization(self):
        """Test GameOverScreen initialization"""
        assert self.game_over_screen.screen_width == self.screen_width
        assert self.game_over_screen.screen_height == self.screen_height
        assert self.game_over_screen.game_stats == self.game_stats
        assert self.game_over_screen.selected_option == 0
        assert len(self.game_over_screen.options) == 2
        assert "Вернуться в меню" in self.game_over_screen.options
        assert "Выйти из игры" in self.game_over_screen.options
    
    def test_game_over_screen_without_stats(self):
        """Test GameOverScreen initialization without stats"""
        screen = GameOverScreen(self.screen_width, self.screen_height, None)
        assert screen.game_stats is None
    
    def test_handle_input_navigation_up(self):
        """Test navigation up in game over screen"""
        # Start at option 0, go up should wrap to last option
        self.game_over_screen.selected_option = 0
        
        event = MagicMock()
        event.type = pygame.KEYDOWN
        event.key = pygame.K_UP
        
        result = self.game_over_screen.handle_input(event)
        assert result is None
        assert self.game_over_screen.selected_option == 1
    
    def test_handle_input_navigation_down(self):
        """Test navigation down in game over screen"""
        # Start at last option, go down should wrap to first option
        self.game_over_screen.selected_option = 1
        
        event = MagicMock()
        event.type = pygame.KEYDOWN
        event.key = pygame.K_DOWN
        
        result = self.game_over_screen.handle_input(event)
        assert result is None
        assert self.game_over_screen.selected_option == 0
    
    def test_handle_input_wasd_navigation(self):
        """Test WASD navigation"""
        # Test W key (up)
        event = MagicMock()
        event.type = pygame.KEYDOWN
        event.key = pygame.K_w
        
        self.game_over_screen.selected_option = 1
        result = self.game_over_screen.handle_input(event)
        assert result is None
        assert self.game_over_screen.selected_option == 0
        
        # Test S key (down)
        event.key = pygame.K_s
        result = self.game_over_screen.handle_input(event)
        assert result is None
        assert self.game_over_screen.selected_option == 1
    
    def test_handle_input_select_menu(self):
        """Test selecting menu option"""
        self.game_over_screen.selected_option = 0  # "Вернуться в меню"
        
        # Test Enter key
        event = MagicMock()
        event.type = pygame.KEYDOWN
        event.key = pygame.K_RETURN
        
        result = self.game_over_screen.handle_input(event)
        assert result == "MENU"
        
        # Test Space key
        event.key = pygame.K_SPACE
        result = self.game_over_screen.handle_input(event)
        assert result == "MENU"
    
    def test_handle_input_select_quit(self):
        """Test selecting quit option"""
        self.game_over_screen.selected_option = 1  # "Выйти из игры"
        
        # Test Enter key
        event = MagicMock()
        event.type = pygame.KEYDOWN
        event.key = pygame.K_RETURN
        
        result = self.game_over_screen.handle_input(event)
        assert result == "QUIT"
        
        # Test Space key
        event.key = pygame.K_SPACE
        result = self.game_over_screen.handle_input(event)
        assert result == "QUIT"
    
    def test_handle_input_non_keydown_event(self):
        """Test handling non-keydown events"""
        event = MagicMock()
        event.type = pygame.KEYUP  # Not KEYDOWN
        
        result = self.game_over_screen.handle_input(event)
        assert result is None
        assert self.game_over_screen.selected_option == 0  # Should not change
    
    def test_handle_input_other_keys(self):
        """Test handling other keys"""
        event = MagicMock()
        event.type = pygame.KEYDOWN
        event.key = pygame.K_a  # Random key
        
        result = self.game_over_screen.handle_input(event)
        assert result is None
        assert self.game_over_screen.selected_option == 0  # Should not change
    
    @patch('pygame.display.flip')
    @patch('pygame.font.Font')
    def test_draw_method(self, mock_font, mock_flip):
        """Test draw method doesn't crash"""
        # Mock font objects
        mock_font_obj = MagicMock()
        mock_font_obj.render.return_value = MagicMock()
        mock_font_obj.render.return_value.get_rect.return_value = MagicMock()
        mock_font.return_value = mock_font_obj
        
        # Create a mock screen
        screen = MagicMock()
        screen.get_width.return_value = self.screen_width
        screen.get_height.return_value = self.screen_height
        
        # This should not raise an exception
        try:
            self.game_over_screen.draw(screen)
        except Exception as e:
            pytest.fail(f"draw() method raised an exception: {e}")
    
    def test_options_wrapping(self):
        """Test that option selection wraps correctly"""
        # Test wrapping from 0 to last option
        self.game_over_screen.selected_option = 0
        
        event = MagicMock()
        event.type = pygame.KEYDOWN
        event.key = pygame.K_UP
        
        self.game_over_screen.handle_input(event)
        assert self.game_over_screen.selected_option == len(self.game_over_screen.options) - 1
        
        # Test wrapping from last option to 0
        event.key = pygame.K_DOWN
        self.game_over_screen.handle_input(event)
        assert self.game_over_screen.selected_option == 0