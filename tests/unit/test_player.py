"""
Tests for the Player class
"""
import pytest
import pygame
import os
from unittest.mock import patch, MagicMock
from src.entities.player import Player


class TestPlayer:
    """Test cases for Player class"""
    
    @classmethod
    def setup_class(cls):
        """Set up pygame for testing"""
        os.environ['SDL_VIDEODRIVER'] = 'dummy'
        pygame.init()
        
    @classmethod
    def teardown_class(cls):
        """Clean up pygame"""
        pygame.quit()
        
    def setup_method(self):
        """Set up test fixtures"""
        self.player = Player(100, 100)
        
    def test_player_initialization(self):
        """Test player initializes with correct values"""
        assert self.player.x == 100
        assert self.player.y == 100
        assert self.player.width == 32
        assert self.player.height == 32
        assert self.player.speed == 120
        assert self.player.facing_direction == 'down'
        assert self.player.attacking == False
        assert isinstance(self.player.rect, pygame.Rect)
        
    def test_player_movement_input(self):
        """Test player handles movement input correctly"""
        # Mock keys pressed
        keys = {
            pygame.K_LEFT: False,
            pygame.K_RIGHT: True,
            pygame.K_UP: False,
            pygame.K_DOWN: False,
            pygame.K_a: False,
            pygame.K_d: False,
            pygame.K_w: False,
            pygame.K_s: False,
            pygame.K_SPACE: False
        }
        
        self.player.handle_input(keys)
        
        assert self.player.direction_x == 1
        assert self.player.direction_y == 0
        assert self.player.facing_direction == 'right'
        
    def test_player_diagonal_movement(self):
        """Test player diagonal movement normalization"""
        keys = {
            pygame.K_LEFT: False,
            pygame.K_RIGHT: True,
            pygame.K_UP: True,
            pygame.K_DOWN: False,
            pygame.K_a: False,
            pygame.K_d: False,
            pygame.K_w: False,
            pygame.K_s: False,
            pygame.K_SPACE: False
        }
        
        self.player.handle_input(keys)
        
        # Check diagonal movement is normalized
        assert abs(self.player.direction_x - 0.707) < 0.01
        assert abs(self.player.direction_y - (-0.707)) < 0.01
        
    def test_player_attack_input(self):
        """Test player attack input"""
        keys = {
            pygame.K_LEFT: False,
            pygame.K_RIGHT: False,
            pygame.K_UP: False,
            pygame.K_DOWN: False,
            pygame.K_a: False,
            pygame.K_d: False,
            pygame.K_w: False,
            pygame.K_s: False,
            pygame.K_SPACE: True
        }
        
        with patch('pygame.time.get_ticks', return_value=1000):
            self.player.handle_input(keys)
            
        assert self.player.attacking == True
        
    def test_player_update_movement(self):
        """Test player position updates correctly"""
        initial_x = self.player.x
        initial_y = self.player.y
        
        # Set movement direction
        self.player.direction_x = 1
        self.player.direction_y = 0
        
        # Update with 1 second delta time
        self.player.update(1.0, 1000, 1000)
        
        # Player should have moved right by speed * dt
        assert self.player.x == initial_x + 120  # speed * 1.0 second
        assert self.player.y == initial_y
        
    def test_player_world_boundaries(self):
        """Test player respects world boundaries"""
        # Test left boundary
        self.player.x = 0
        self.player.direction_x = -1
        self.player.update(1.0, 1000, 1000)
        assert self.player.x >= 0
        
        # Test right boundary
        self.player.x = 950  # Close to right edge (1000 - 32 - some margin)
        self.player.direction_x = 1
        self.player.update(1.0, 1000, 1000)
        assert self.player.x <= 1000 - self.player.width
        
    def test_player_attack_duration(self):
        """Test attack duration and cooldown"""
        with patch('pygame.time.get_ticks') as mock_time:
            # Start attack
            mock_time.return_value = 1000
            self.player.try_attack()
            assert self.player.attacking == True
            
            # During attack
            mock_time.return_value = 1200  # 200ms later
            self.player.update(0.2, 1000, 1000)
            assert self.player.attacking == True
            
            # After attack duration
            mock_time.return_value = 1400  # 400ms later (past 300ms duration)
            self.player.update(0.2, 1000, 1000)
            assert self.player.attacking == False
            
    def test_player_attack_cooldown(self):
        """Test attack cooldown prevents rapid attacks"""
        with patch('pygame.time.get_ticks') as mock_time:
            # First attack
            mock_time.return_value = 1000
            self.player.try_attack()
            assert self.player.attacking == True
            
            # Try to attack again immediately (should fail due to cooldown)
            mock_time.return_value = 1050  # 50ms later (less than 100ms cooldown)
            self.player.attacking = False  # Reset attacking state
            self.player.try_attack()
            assert self.player.attacking == False
            
            # Try to attack after cooldown
            mock_time.return_value = 1150  # 150ms later (past 100ms cooldown)
            self.player.try_attack()
            assert self.player.attacking == True
            
    def test_player_get_attack_rect(self):
        """Test attack rectangle calculation"""
        # Test attack in different directions
        directions = ['up', 'down', 'left', 'right']
        
        for direction in directions:
            self.player.facing_direction = direction
            self.player.attacking = True
            
            attack_rect = self.player.get_attack_rect()
            assert isinstance(attack_rect, pygame.Rect)
            assert attack_rect.width == 30
            assert attack_rect.height == 30
            
        # Test no attack rect when not attacking
        self.player.attacking = False
        attack_rect = self.player.get_attack_rect()
        assert attack_rect is None
        
    def test_player_draw(self):
        """Test player drawing doesn't crash"""
        # Create a dummy surface
        surface = pygame.Surface((800, 600))
        
        # Test drawing without attacking
        self.player.draw(surface, 0, 0)
        
        # Test drawing while attacking
        self.player.attacking = True
        self.player.draw(surface, 0, 0)
        
        # Should not raise any exceptions
        assert True
        
    def test_player_no_movement_during_attack(self):
        """Test player cannot move while attacking"""
        with patch('pygame.time.get_ticks') as mock_time:
            initial_x = self.player.x
            initial_y = self.player.y
            
            # Properly initiate attack
            mock_time.return_value = 1000
            self.player.try_attack()
            assert self.player.attacking == True
            
            # Set movement direction
            self.player.direction_x = 1
            self.player.direction_y = 1
            
            # Update player while still in attack duration (200ms < 300ms)
            mock_time.return_value = 1200  # 200ms later, still attacking
            self.player.update(1.0, 1000, 1000)
            
            # Player should not have moved during attack
            assert self.player.x == initial_x
            assert self.player.y == initial_y
            assert self.player.attacking == True  # Still attacking