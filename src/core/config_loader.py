"""
Config Loader - Core configuration management system
Validates and loads configuration from root config.ini file
"""

import configparser
import os
from typing import Dict, Any, Tuple


class ConfigValidationError(Exception):
    """Raised when configuration validation fails"""
    pass


class ConfigLoader:
    """
    Configuration loader and validator class.
    Loads configuration from root config.ini and validates all required settings.
    """
    
    def __init__(self):
        self._config = {}
        self._loaded = False
        
    def load_config(self) -> Dict[str, Any]:
        """
        Load and validate configuration from root config.ini
        Returns validated configuration dictionary
        """
        if self._loaded:
            return self._config
            
        try:
            # Find project root and config.ini file
            project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
            config_path = os.path.join(project_root, 'config.ini')
            
            if not os.path.exists(config_path):
                raise ConfigValidationError(f"Config file not found: {config_path}")
            
            # Parse INI file
            parser = configparser.ConfigParser()
            parser.read(config_path, encoding='utf-8')
            
            # Validate and load configuration
            self._validate_display_settings(parser)
            self._validate_world_settings(parser)
            self._validate_player_settings(parser)
            self._validate_attack_settings(parser)
            self._validate_colors(parser)
            self._validate_debug_settings(parser)
            self._validate_world_generation_settings(parser)
            
            # Store validated configuration
            self._config = {
                # Display settings
                'WIDTH': parser.getint('display', 'window_width'),
                'HEIGHT': parser.getint('display', 'window_height'),
                'FPS': parser.getint('display', 'fps'),
                
                # World settings
                'WORLD_WIDTH': parser.getint('world', 'world_width'),
                'WORLD_HEIGHT': parser.getint('world', 'world_height'),
                'TILE_SIZE': parser.getint('world', 'tile_size'),
                
                # Player settings
                'PLAYER_SPEED': parser.getint('player', 'player_speed'),
                'PLAYER_SIZE': parser.getint('player', 'player_size'),
                
                # Attack settings
                'ATTACK_DURATION': parser.getint('attack', 'attack_duration'),
                'ATTACK_COOLDOWN': parser.getint('attack', 'attack_cooldown'),
                'ATTACK_RANGE': parser.getint('attack', 'attack_range'),
                
                # Debug settings
                'DEBUG_ENABLED': parser.getboolean('debug', 'debug_enabled'),
                'DEBUG_FONT_SIZE': parser.getint('debug', 'debug_font_size'),
                
                # World generation
                'OBSTACLE_COUNT': parser.getint('world_generation', 'obstacle_count'),
                'SAFE_ZONE_SIZE': parser.getint('world_generation', 'safe_zone_size'),
            }
            
            # Load colors
            colors = self._load_colors(parser)
            self._config.update(colors)
            
            self._loaded = True
            return self._config
            
        except configparser.Error as e:
            raise ConfigValidationError(f"INI file parsing error: {e}")
        except ValueError as e:
            raise ConfigValidationError(f"Invalid configuration value: {e}")
        except Exception as e:
            raise ConfigValidationError(f"Configuration validation failed: {e}")
    
    def _validate_display_settings(self, parser):
        """Validate display-related settings"""
        if not parser.has_section('display'):
            raise ConfigValidationError("Missing [display] section in config")
        
        window_width = parser.getint('display', 'window_width')
        if window_width <= 0:
            raise ConfigValidationError("window_width must be a positive integer")
            
        window_height = parser.getint('display', 'window_height')
        if window_height <= 0:
            raise ConfigValidationError("window_height must be a positive integer")
            
        fps = parser.getint('display', 'fps')
        if fps <= 0:
            raise ConfigValidationError("fps must be a positive integer")
    
    def _validate_world_settings(self, parser):
        """Validate world-related settings"""
        if not parser.has_section('world'):
            raise ConfigValidationError("Missing [world] section in config")
            
        world_width = parser.getint('world', 'world_width')
        if world_width <= 0:
            raise ConfigValidationError("world_width must be a positive integer")
            
        world_height = parser.getint('world', 'world_height')
        if world_height <= 0:
            raise ConfigValidationError("world_height must be a positive integer")
            
        tile_size = parser.getint('world', 'tile_size')
        if tile_size <= 0:
            raise ConfigValidationError("tile_size must be a positive integer")
    
    def _validate_player_settings(self, parser):
        """Validate player-related settings"""
        if not parser.has_section('player'):
            raise ConfigValidationError("Missing [player] section in config")
            
        player_speed = parser.getint('player', 'player_speed')
        if player_speed <= 0:
            raise ConfigValidationError("player_speed must be a positive integer")
            
        player_size = parser.getint('player', 'player_size')
        if player_size <= 0:
            raise ConfigValidationError("player_size must be a positive integer")
    
    def _validate_attack_settings(self, parser):
        """Validate attack-related settings"""
        if not parser.has_section('attack'):
            raise ConfigValidationError("Missing [attack] section in config")
            
        attack_duration = parser.getint('attack', 'attack_duration')
        if attack_duration <= 0:
            raise ConfigValidationError("attack_duration must be a positive integer")
            
        attack_cooldown = parser.getint('attack', 'attack_cooldown')
        if attack_cooldown < 0:
            raise ConfigValidationError("attack_cooldown must be a non-negative integer")
            
        attack_range = parser.getint('attack', 'attack_range')
        if attack_range <= 0:
            raise ConfigValidationError("attack_range must be a positive integer")
    
    def _validate_colors(self, parser):
        """Validate color definitions"""
        if not parser.has_section('colors'):
            raise ConfigValidationError("Missing [colors] section in config")
        
        required_colors = ['white', 'black', 'red', 'green', 'dark_green', 
                          'dark_gray', 'brown', 'gray', 'yellow']
        
        for color_name in required_colors:
            if not parser.has_option('colors', color_name):
                raise ConfigValidationError(f"Missing required color: {color_name}")
            
            color_str = parser.get('colors', color_name)
            try:
                color_parts = [int(x.strip()) for x in color_str.split(',')]
                if len(color_parts) != 3:
                    raise ValueError("Must have exactly 3 values")
                if not all(0 <= c <= 255 for c in color_parts):
                    raise ValueError("Values must be between 0 and 255")
            except ValueError as e:
                raise ConfigValidationError(f"Invalid color format for {color_name}: {e}")
    
    def _validate_debug_settings(self, parser):
        """Validate debug-related settings"""
        if not parser.has_section('debug'):
            raise ConfigValidationError("Missing [debug] section in config")
            
        # Boolean validation is handled by getboolean()
        parser.getboolean('debug', 'debug_enabled')
        
        debug_font_size = parser.getint('debug', 'debug_font_size')
        if debug_font_size <= 0:
            raise ConfigValidationError("debug_font_size must be a positive integer")
    
    def _validate_world_generation_settings(self, parser):
        """Validate world generation settings"""
        if not parser.has_section('world_generation'):
            raise ConfigValidationError("Missing [world_generation] section in config")
            
        obstacle_count = parser.getint('world_generation', 'obstacle_count')
        if obstacle_count < 0:
            raise ConfigValidationError("obstacle_count must be a non-negative integer")
            
        safe_zone_size = parser.getint('world_generation', 'safe_zone_size')
        if safe_zone_size < 0:
            raise ConfigValidationError("safe_zone_size must be a non-negative integer")
    
    def _load_colors(self, parser) -> Dict[str, Tuple[int, int, int]]:
        """Load and parse color values from INI format"""
        colors = {}
        color_mapping = {
            'white': 'WHITE',
            'black': 'BLACK', 
            'red': 'RED',
            'green': 'GREEN',
            'dark_green': 'DARK_GREEN',
            'dark_gray': 'DARK_GRAY',
            'brown': 'BROWN',
            'gray': 'GRAY',
            'yellow': 'YELLOW'
        }
        
        for ini_name, const_name in color_mapping.items():
            color_str = parser.get('colors', ini_name)
            color_parts = [int(x.strip()) for x in color_str.split(',')]
            colors[const_name] = tuple(color_parts)
            
        return colors
    
    def get(self, key: str, default=None):
        """Get configuration value by key"""
        if not self._loaded:
            self.load_config()
        return self._config.get(key, default)
    
    def get_color(self, color_name: str) -> Tuple[int, int, int]:
        """Get color tuple by name"""
        if not self._loaded:
            self.load_config()
        return self._config.get(color_name, (255, 255, 255))  # Default to white


# Global config loader instance
_config_loader = ConfigLoader()


def load_config():
    """Load and return validated configuration"""
    return _config_loader.load_config()


def get_config(key: str, default=None):
    """Get configuration value by key"""
    return _config_loader.get(key, default)


def get_color(color_name: str) -> Tuple[int, int, int]:
    """Get color tuple by name"""
    return _config_loader.get_color(color_name)