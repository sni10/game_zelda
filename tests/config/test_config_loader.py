"""
Tests for the configuration loader system
"""
import pytest
import os
import tempfile
import configparser
from unittest.mock import patch, mock_open
from src.core.config_loader import ConfigLoader, ConfigValidationError, load_config, get_config, get_color


class TestConfigLoader:
    """Test cases for ConfigLoader class"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.config_loader = ConfigLoader()
        
    def test_config_loader_initialization(self):
        """Test ConfigLoader initializes correctly"""
        assert self.config_loader._config == {}
        assert self.config_loader._loaded == False
        
    def test_load_valid_config(self):
        """Test loading a valid configuration"""
        # This will use the actual config.ini file
        config = self.config_loader.load_config()
        
        # Check that all required keys are present
        required_keys = [
            'WIDTH', 'HEIGHT', 'FPS',
            'WORLD_WIDTH', 'WORLD_HEIGHT', 'TILE_SIZE',
            'PLAYER_SPEED', 'PLAYER_SIZE',
            'ATTACK_DURATION', 'ATTACK_COOLDOWN', 'ATTACK_RANGE',
            'DEBUG_ENABLED', 'DEBUG_FONT_SIZE',
            'OBSTACLE_COUNT', 'SAFE_ZONE_SIZE'
        ]
        
        for key in required_keys:
            assert key in config, f"Missing required config key: {key}"
            
        # Check color keys
        color_keys = ['WHITE', 'BLACK', 'RED', 'GREEN', 'DARK_GREEN', 
                     'DARK_GRAY', 'BROWN', 'GRAY', 'YELLOW']
        for color_key in color_keys:
            assert color_key in config, f"Missing required color: {color_key}"
            assert isinstance(config[color_key], tuple), f"Color {color_key} should be a tuple"
            assert len(config[color_key]) == 3, f"Color {color_key} should have 3 values"
            
    def test_config_caching(self):
        """Test that config is cached after first load"""
        config1 = self.config_loader.load_config()
        config2 = self.config_loader.load_config()
        
        assert config1 is config2  # Should be the same object (cached)
        assert self.config_loader._loaded == True
        
    def test_get_config_value(self):
        """Test getting configuration values"""
        self.config_loader.load_config()
        
        width = self.config_loader.get('WIDTH')
        assert isinstance(width, int)
        assert width > 0
        
        # Test default value
        non_existent = self.config_loader.get('NON_EXISTENT', 'default')
        assert non_existent == 'default'
        
    def test_get_color_value(self):
        """Test getting color values"""
        self.config_loader.load_config()
        
        white = self.config_loader.get_color('WHITE')
        assert isinstance(white, tuple)
        assert len(white) == 3
        assert all(0 <= c <= 255 for c in white)
        
        # Test default color for non-existent color
        non_existent = self.config_loader.get_color('NON_EXISTENT')
        assert non_existent == (255, 255, 255)  # Default white
        
    def test_missing_config_file(self):
        """Test behavior when config file is missing"""
        with patch('os.path.exists', return_value=False):
            with pytest.raises(ConfigValidationError, match="Config file not found"):
                self.config_loader.load_config()
                
    def test_invalid_ini_format(self):
        """Test behavior with invalid INI format"""
        invalid_ini = "invalid ini content [unclosed section"
        
        with patch('configparser.ConfigParser.read') as mock_read:
            mock_read.side_effect = configparser.Error("Invalid format")
            with pytest.raises(ConfigValidationError, match="INI file parsing error"):
                self.config_loader.load_config()


class TestGlobalFunctions:
    """Test cases for global configuration functions"""
    
    def test_load_config_function(self):
        """Test global load_config function"""
        config = load_config()
        assert isinstance(config, dict)
        assert len(config) > 0
        
    def test_get_config_function(self):
        """Test global get_config function"""
        width = get_config('WIDTH')
        assert isinstance(width, int)
        assert width > 0
        
        # Test default value
        default_val = get_config('NON_EXISTENT', 42)
        assert default_val == 42
        
    def test_get_color_function(self):
        """Test global get_color function"""
        white = get_color('WHITE')
        assert isinstance(white, tuple)
        assert len(white) == 3
        assert white == (255, 255, 255)
        
        red = get_color('RED')
        assert isinstance(red, tuple)
        assert len(red) == 3
        assert red == (255, 0, 0)


class TestConfigValidation:
    """Test cases for configuration validation"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.config_loader = ConfigLoader()
        
    def test_display_settings_validation(self):
        """Test display settings validation"""
        # Test with valid parser
        parser = configparser.ConfigParser()
        parser.add_section('display')
        parser.set('display', 'window_width', '1024')
        parser.set('display', 'window_height', '768')
        parser.set('display', 'fps', '60')
        
        # Should not raise exception
        self.config_loader._validate_display_settings(parser)
        
        # Test with missing section
        empty_parser = configparser.ConfigParser()
        with pytest.raises(ConfigValidationError, match="Missing \\[display\\] section"):
            self.config_loader._validate_display_settings(empty_parser)
            
    def test_color_validation(self):
        """Test color validation"""
        parser = configparser.ConfigParser()
        parser.add_section('colors')
        
        # Add all required colors
        required_colors = ['white', 'black', 'red', 'green', 'dark_green', 
                          'dark_gray', 'brown', 'gray', 'yellow']
        for color in required_colors:
            parser.set('colors', color, '255,255,255')
            
        # Should not raise exception
        self.config_loader._validate_colors(parser)
        
        # Test with invalid color format
        parser.set('colors', 'white', 'invalid')
        with pytest.raises(ConfigValidationError, match="Invalid color format"):
            self.config_loader._validate_colors(parser)
            
    def test_positive_integer_validation(self):
        """Test validation of positive integer values"""
        parser = configparser.ConfigParser()
        parser.add_section('world')
        parser.set('world', 'world_width', '2000')
        parser.set('world', 'world_height', '2000')
        parser.set('world', 'tile_size', '32')
        
        # Should not raise exception
        self.config_loader._validate_world_settings(parser)
        
        # Test with zero value
        parser.set('world', 'world_width', '0')
        with pytest.raises(ConfigValidationError, match="world_width must be a positive integer"):
            self.config_loader._validate_world_settings(parser)