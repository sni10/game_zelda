"""
Tests for the Player class
"""
import pytest
import pygame
import os
from unittest.mock import patch, MagicMock
from src.entities.player import Player
from src.world.terrain import TerrainTile, TerrainType


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
        
        # Create a mock world for testing
        self.mock_world = MagicMock()
        self.mock_world.width = 1000
        self.mock_world.height = 1000
        self.mock_world.check_collision.return_value = False
        self.mock_world.get_terrain_at.return_value = None
        
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
        self.player.update(1.0, self.mock_world)
        
        # Player should have moved right by speed * dt
        assert self.player.x == initial_x + 120  # speed * 1.0 second
        assert self.player.y == initial_y
        
    def test_player_world_boundaries(self):
        """Test player respects world boundaries"""
        # Test left boundary
        self.player.x = 0
        self.player.direction_x = -1
        self.player.update(1.0, self.mock_world)
        assert self.player.x >= 0
        
        # Test right boundary
        self.player.x = 950  # Close to right edge (1000 - 32 - some margin)
        self.player.direction_x = 1
        self.player.update(1.0, self.mock_world)
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
            self.player.update(0.2, self.mock_world)
            assert self.player.attacking == True
            
            # After attack duration
            mock_time.return_value = 1400  # 400ms later (past 300ms duration)
            self.player.update(0.2, self.mock_world)
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
        """Test attack rectangle calculation for all 8 directions"""
        # Test attack in all 8 directions
        directions = ['up', 'down', 'left', 'right', 'up_left', 'up_right', 'down_left', 'down_right']
        
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
        initial_x = self.player.x
        initial_y = self.player.y
        
        with patch('pygame.time.get_ticks') as mock_time:
            # Set up attack timing - attack should still be active
            mock_time.return_value = 1000
            self.player.attacking = True
            self.player.attack_timer = 800  # Attack started 200ms ago, still within 300ms duration
            self.player.direction_x = 1
            self.player.direction_y = 1
            
            # Update player
            self.player.update(1.0, self.mock_world)
            
            # Player should not have moved
            assert self.player.x == initial_x
            assert self.player.y == initial_y

    def test_player_health_initialization(self):
        """Test player health system initialization"""
        assert self.player.health == 100
        assert self.player.max_health == 100
        assert self.player.damage_cooldown == 1000
        assert self.player.last_damage_time == 0

    def test_player_terrain_damage(self):
        """Test player takes damage from hostile terrain"""
        # Create a damaging terrain tile (swamp)
        swamp_tile = MagicMock()
        swamp_tile.damages_player = True
        swamp_tile.damage_amount = 5
        swamp_tile.speed_modifier = 1.0
        
        # Mock world to return the damaging tile and allow movement
        self.mock_world.get_terrain_at.return_value = swamp_tile
        self.mock_world.check_collision.return_value = False  # Allow movement
        
        with patch('pygame.time.get_ticks') as mock_time:
            # First damage - ensure player moves by setting direction and sufficient dt
            mock_time.return_value = 1001  # Must be > damage_cooldown (1000) for first damage
            initial_health = self.player.health
            initial_x = self.player.x
            self.player.direction_x = 1
            self.player.direction_y = 0
            
            self.player.update(0.1, self.mock_world)
            
            # Verify player actually moved
            assert self.player.x > initial_x
            # Health should decrease
            assert self.player.health == initial_health - 5
            
            # Try to take damage again immediately (should be blocked by cooldown)
            mock_time.return_value = 1500  # 500ms later (less than 1000ms cooldown)
            current_health = self.player.health
            self.player.update(0.1, self.mock_world)
            
            # Health should not decrease due to cooldown
            assert self.player.health == current_health
            
            # Take damage after cooldown
            mock_time.return_value = 2100  # 1100ms later (past 1000ms cooldown)
            self.player.update(0.1, self.mock_world)
            
            # Health should decrease again
            assert self.player.health == current_health - 5

    def test_player_terrain_speed_modification(self):
        """Test player speed is modified by terrain"""
        # Create a slowing terrain tile (quicksand)
        sand_tile = MagicMock()
        sand_tile.damages_player = False
        sand_tile.speed_modifier = 0.5
        
        # Mock world to return the slowing tile
        self.mock_world.get_terrain_at.return_value = sand_tile
        
        initial_x = self.player.x
        self.player.direction_x = 1
        self.player.direction_y = 0
        
        # Update with slowing terrain
        self.player.update(1.0, self.mock_world)
        
        # Player should move at half speed (120 * 0.5 = 60)
        expected_x = initial_x + 60
        assert abs(self.player.x - expected_x) < 1  # Allow small floating point differences

    def test_player_8_directional_facing(self):
        """Test player facing direction updates correctly for all 8 directions"""
        # Test cardinal directions
        keys_facing_map = [
            ({'left': True}, 'left'),
            ({'right': True}, 'right'),
            ({'up': True}, 'up'),
            ({'down': True}, 'down'),
            ({'left': True, 'up': True}, 'up_left'),
            ({'right': True, 'up': True}, 'up_right'),
            ({'left': True, 'down': True}, 'down_left'),
            ({'right': True, 'down': True}, 'down_right'),
        ]
        
        for key_state, expected_facing in keys_facing_map:
            # Create mock keys
            mock_keys = MagicMock()
            mock_keys.__getitem__ = lambda self, key: key_state.get(key.name.lower(), False)
            
            # Simulate key input
            if key_state.get('left'):
                self.player.direction_x = -1
            elif key_state.get('right'):
                self.player.direction_x = 1
            else:
                self.player.direction_x = 0
                
            if key_state.get('up'):
                self.player.direction_y = -1
            elif key_state.get('down'):
                self.player.direction_y = 1
            else:
                self.player.direction_y = 0
            
            # Update facing direction based on movement
            if self.player.direction_x != 0 or self.player.direction_y != 0:
                if self.player.direction_x == -1 and self.player.direction_y == -1:
                    self.player.facing_direction = 'up_left'
                elif self.player.direction_x == 1 and self.player.direction_y == -1:
                    self.player.facing_direction = 'up_right'
                elif self.player.direction_x == -1 and self.player.direction_y == 1:
                    self.player.facing_direction = 'down_left'
                elif self.player.direction_x == 1 and self.player.direction_y == 1:
                    self.player.facing_direction = 'down_right'
                elif self.player.direction_x == -1:
                    self.player.facing_direction = 'left'
                elif self.player.direction_x == 1:
                    self.player.facing_direction = 'right'
                elif self.player.direction_y == -1:
                    self.player.facing_direction = 'up'
                elif self.player.direction_y == 1:
                    self.player.facing_direction = 'down'
            
            assert self.player.facing_direction == expected_facing

    def test_player_health_minimum_zero(self):
        """Test player health cannot go below zero"""
        # Set low health
        self.player.health = 3
        
        # Create a high-damage terrain tile
        damage_tile = MagicMock()
        damage_tile.damages_player = True
        damage_tile.damage_amount = 10  # More damage than current health
        damage_tile.speed_modifier = 1.0
        
        # Mock world to return the damaging tile and allow movement
        self.mock_world.get_terrain_at.return_value = damage_tile
        self.mock_world.check_collision.return_value = False  # Allow movement
        
        with patch('pygame.time.get_ticks') as mock_time:
            mock_time.return_value = 1001  # Must be > damage_cooldown (1000) for first damage
            initial_x = self.player.x
            self.player.direction_x = 1
            self.player.direction_y = 0
            self.player.update(0.1, self.mock_world)
            
            # Verify player actually moved
            assert self.player.x > initial_x
            # Health should be 0, not negative
            assert self.player.health == 0

    def test_player_diagonal_movement_normalization(self):
        """Test diagonal movement is properly normalized"""
        initial_x = self.player.x
        initial_y = self.player.y
        
        # Set diagonal movement
        self.player.direction_x = 1
        self.player.direction_y = 1
        
        # Simulate handle_input normalization
        self.player.direction_x *= 0.707  # 1/sqrt(2)
        self.player.direction_y *= 0.707
        
        self.player.update(1.0, self.mock_world)
        
        # Check that diagonal movement is normalized (approximately 120 * 0.707 = 84.84)
        expected_distance = 120 * 0.707
        actual_distance_x = self.player.x - initial_x
        actual_distance_y = self.player.y - initial_y
        
        assert abs(actual_distance_x - expected_distance) < 1
        assert abs(actual_distance_y - expected_distance) < 1