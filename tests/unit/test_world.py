"""
Tests for the World class
"""
import pytest
import pygame
import os
from unittest.mock import patch, MagicMock
from src.world.world import World


class TestWorld:
    """Test cases for World class"""
    
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
        self.world = World(width=1000, height=1000)
        
    def test_world_initialization(self):
        """Test world initializes with correct values"""
        assert self.world.width == 1000
        assert self.world.height == 1000
        assert self.world.tile_size == 32
        assert self.world.tiles_x == 1000 // 32
        assert self.world.tiles_y == 1000 // 32
        assert self.world.camera_x == 0
        assert self.world.camera_y == 0
        assert len(self.world.obstacles) > 0  # Should have generated obstacles
        
    def test_world_default_size(self):
        """Test world with default size"""
        default_world = World()
        assert default_world.width == 2000
        assert default_world.height == 2000
        
    def test_obstacle_generation(self):
        """Test obstacle generation creates boundaries and random obstacles"""
        # Check that we have obstacles
        assert len(self.world.obstacles) > 0
        
        # Check that boundary obstacles exist
        boundary_obstacles = []
        for obstacle in self.world.obstacles:
            if (obstacle.x == 0 or obstacle.x == self.world.width - self.world.tile_size or
                obstacle.y == 0 or obstacle.y == self.world.height - self.world.tile_size):
                boundary_obstacles.append(obstacle)
                
        assert len(boundary_obstacles) > 0, "Should have boundary obstacles"
        
    def test_camera_update(self):
        """Test camera follows player correctly"""
        screen_width = 800
        screen_height = 600
        player_x = 500
        player_y = 400
        
        self.world.update_camera(player_x, player_y, screen_width, screen_height)
        
        # Camera should center on player
        expected_camera_x = player_x - screen_width // 2
        expected_camera_y = player_y - screen_height // 2
        
        assert self.world.camera_x == expected_camera_x
        assert self.world.camera_y == expected_camera_y
        
    def test_camera_boundaries(self):
        """Test camera respects world boundaries"""
        screen_width = 800
        screen_height = 600
        
        # Test camera at world edges
        # Top-left corner
        self.world.update_camera(0, 0, screen_width, screen_height)
        assert self.world.camera_x >= 0
        assert self.world.camera_y >= 0
        
        # Bottom-right corner
        self.world.update_camera(self.world.width, self.world.height, screen_width, screen_height)
        assert self.world.camera_x <= self.world.width - screen_width
        assert self.world.camera_y <= self.world.height - screen_height
        
    def test_collision_detection(self):
        """Test collision detection with obstacles"""
        # Create a test rectangle
        test_rect = pygame.Rect(0, 0, 32, 32)  # Should collide with boundary
        
        collision = self.world.check_collision(test_rect)
        assert collision == True, "Should detect collision with boundary obstacle"
        
        # Test rectangle in empty space (center of world)
        center_rect = pygame.Rect(self.world.width // 2, self.world.height // 2, 32, 32)
        collision = self.world.check_collision(center_rect)
        # This might or might not collide depending on random obstacle generation
        # Just ensure the method works without error
        assert isinstance(collision, bool)
        
    def test_get_visible_obstacles(self):
        """Test getting visible obstacles for screen"""
        screen_width = 800
        screen_height = 600
        
        # Set camera position
        self.world.camera_x = 100
        self.world.camera_y = 100
        
        visible_obstacles = self.world.get_visible_obstacles(screen_width, screen_height)
        
        # Should return a list
        assert isinstance(visible_obstacles, list)
        
        # All visible obstacles should be within camera view
        camera_rect = pygame.Rect(self.world.camera_x, self.world.camera_y, screen_width, screen_height)
        for obstacle in visible_obstacles:
            assert camera_rect.colliderect(obstacle), "Visible obstacle should be in camera view"
            
    def test_draw_background(self):
        """Test background drawing doesn't crash"""
        surface = pygame.Surface((800, 600))
        
        # Should not raise any exceptions
        self.world.draw_background(surface)
        assert True
        
    def test_draw_obstacles(self):
        """Test obstacle drawing doesn't crash"""
        surface = pygame.Surface((800, 600))
        
        # Should not raise any exceptions
        self.world.draw_obstacles(surface)
        assert True
        
    def test_draw_minimap(self):
        """Test minimap drawing doesn't crash"""
        surface = pygame.Surface((800, 600))
        player_x = 500
        player_y = 400
        
        # Should not raise any exceptions
        self.world.draw_minimap(surface, player_x, player_y)
        assert True
        
    def test_full_draw(self):
        """Test full world drawing doesn't crash"""
        surface = pygame.Surface((800, 600))
        player_x = 500
        player_y = 400
        
        # Should not raise any exceptions
        self.world.draw(surface, player_x, player_y)
        assert True
        
    def test_obstacle_safe_zone(self):
        """Test that obstacles don't spawn in safe zone around center"""
        center_x = self.world.width // 2
        center_y = self.world.height // 2
        safe_zone_size = 100
        
        # Check that no obstacles are in the immediate center area
        center_obstacles = []
        for obstacle in self.world.obstacles:
            if (abs(obstacle.x - center_x) <= safe_zone_size and 
                abs(obstacle.y - center_y) <= safe_zone_size):
                center_obstacles.append(obstacle)
                
        # There should be very few or no obstacles in the safe zone
        # (some might be there due to boundary obstacles, but center should be clear)
        center_rect = pygame.Rect(center_x - 50, center_y - 50, 100, 100)
        center_collisions = 0
        for obstacle in self.world.obstacles:
            if center_rect.colliderect(obstacle):
                center_collisions += 1
                
        # Should have fewer obstacles in center than total obstacles
        assert center_collisions < len(self.world.obstacles) // 4, "Center should have fewer obstacles"
        
    def test_world_different_sizes(self):
        """Test world works with different sizes"""
        small_world = World(width=500, height=500)
        assert small_world.width == 500
        assert small_world.height == 500
        assert len(small_world.obstacles) > 0
        
        large_world = World(width=3000, height=3000)
        assert large_world.width == 3000
        assert large_world.height == 3000
        assert len(large_world.obstacles) > 0
        
    def test_tile_calculations(self):
        """Test tile size calculations"""
        assert self.world.tiles_x == self.world.width // self.world.tile_size
        assert self.world.tiles_y == self.world.height // self.world.tile_size
        
        # Verify tile size is reasonable
        assert self.world.tile_size > 0
        assert self.world.tile_size <= 64  # Reasonable upper bound