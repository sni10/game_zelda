"""
Tests to improve SaveSystem coverage
"""
import pytest
import pygame
import os
import json
import tempfile
import shutil
from src.systems.save_system import SaveSystem
from src.entities.player import Player


class TestSaveSystemCoverage:
    """Additional tests for SaveSystem coverage"""
    
    @classmethod
    def setup_class(cls):
        """Set up pygame for testing"""
        os.environ['SDL_VIDEODRIVER'] = 'dummy'
        pygame.init()
    
    def setup_method(self):
        """Set up test fixtures"""
        self.temp_dir = tempfile.mkdtemp()
        self.save_system = SaveSystem()
        # Override saves directory for testing
        self.save_system.saves_dir = self.temp_dir
    
    def teardown_method(self):
        """Clean up after test"""
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    def test_save_game_exception_handling(self):
        """Test save_game exception handling"""
        # Create invalid save system to trigger exception
        invalid_save_system = SaveSystem()
        invalid_save_system.saves_dir = "/invalid/path/that/does/not/exist"
        
        player = Player(100, 200)
        world = type('MockWorld', (), {'width': 1000, 'height': 1000, 'camera_x': 0, 'camera_y': 0})()
        
        result = invalid_save_system.save_game(player, world)
        assert result is False
    
    def test_load_game_file_not_exists(self):
        """Test load_game when file doesn't exist"""
        result = self.save_system.load_game("nonexistent.json")
        assert result is None
    
    def test_load_game_json_error(self):
        """Test load_game with invalid JSON"""
        # Create invalid JSON file
        bad_file = os.path.join(self.temp_dir, "bad.json")
        with open(bad_file, 'w') as f:
            f.write("invalid json {")
        
        result = self.save_system.load_game("bad.json")
        assert result is None
    
    def test_load_game_version_warning(self):
        """Test version warning in load_game"""
        # Create save with different version
        save_data = {
            "version": "999.0",  # Different version
            "player": {"x": 100, "y": 200},
            "world": {"width": 1000, "height": 1000}
        }
        
        version_file = os.path.join(self.temp_dir, "version.json")
        with open(version_file, 'w') as f:
            json.dump(save_data, f)
        
        # Should still load but print warning
        result = self.save_system.load_game("version.json")
        assert result is not None
        assert result["version"] == "999.0"
    
    def test_apply_save_data_to_player_exception(self):
        """Test player data application exception handling"""
        player = Player(0, 0)
        bad_data = {"no_player_key": True}  # Missing "player" key
        
        # Should not crash, just handle gracefully
        self.save_system.apply_save_data_to_player(player, bad_data)
        # Player should remain unchanged
        assert player.x == 0
        assert player.y == 0
    
    def test_apply_save_data_to_world_exception(self):
        """Test world data application exception handling"""
        world = type('MockWorld', (), {})()  # Simple mock
        bad_data = {"no_world_key": True}  # Missing "world" key
        
        # Should not crash, just handle gracefully
        self.save_system.apply_save_data_to_world(world, bad_data)