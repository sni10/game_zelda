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
            self._validate_enemies_settings(parser)
            self._validate_combat_settings(parser)
            self._validate_pickups_settings(parser)
            self._validate_drops_settings(parser)
            self._validate_progression_settings(parser)
            self._validate_autosave_settings(parser)

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
                'PLAYER_MAX_HEALTH': parser.getint('player', 'player_max_health')
                    if parser.has_option('player', 'player_max_health') else 1000,
                # Sprint - опциональный (default = 1.8 если не задан в config)
                'PLAYER_SPRINT_MULTIPLIER': (
                    parser.getfloat('player', 'player_sprint_multiplier')
                    if parser.has_option('player', 'player_sprint_multiplier')
                    else 1.8
                ),
                
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

                # Autosave (v0.3.3) — секция опциональна, дефолты сохраняют
                # обратную совместимость.
                'AUTOSAVE_ENABLED': (
                    parser.getboolean('autosave', 'autosave_enabled')
                    if parser.has_option('autosave', 'autosave_enabled') else True
                ),
                'AUTOSAVE_INTERVAL_MINUTES': (
                    parser.getfloat('autosave', 'autosave_interval_minutes')
                    if parser.has_option('autosave', 'autosave_interval_minutes')
                    else 5.0
                ),
                'AUTOSAVE_LIMIT': (
                    parser.getint('autosave', 'autosave_limit')
                    if parser.has_option('autosave', 'autosave_limit') else 3
                ),
                'AUTOSAVE_ON_LEVEL_UP': (
                    parser.getboolean('autosave', 'autosave_on_level_up')
                    if parser.has_option('autosave', 'autosave_on_level_up')
                    else True
                ),
            }

            # Загружаем все ключи из секции [enemies] - они опциональные,
            # подхватятся через get_config() как ENEMIES_<UPPERCASE_KEY>.
            for section_name, prefix in [('enemies', 'ENEMIES'),
                                          ('combat', 'COMBAT'),
                                          ('pickups', 'PICKUPS'),
                                          ('drops', 'DROPS'),
                                          ('progression', 'PROGRESSION')]:
                if not parser.has_section(section_name):
                    continue
                for key, value in parser.items(section_name):
                    upper_key = f"{prefix}_{key.upper()}"
                    # Цвета (содержат запятую) парсим как tuple
                    if ',' in value:
                        try:
                            self._config[upper_key] = tuple(
                                int(v.strip()) for v in value.split(',')
                            )
                            continue
                        except ValueError:
                            pass
                    # Boolean
                    if value.lower() in ('true', 'false'):
                        self._config[upper_key] = value.lower() == 'true'
                        continue
                    # Числа - int или float
                    try:
                        self._config[upper_key] = int(value)
                    except ValueError:
                        try:
                            self._config[upper_key] = float(value)
                        except ValueError:
                            self._config[upper_key] = value

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

        # Множитель спринта - опциональный (для обратной совместимости).
        # Если задан - должен быть >= 1.0 (иначе спринт замедлял бы).
        if parser.has_option('player', 'player_sprint_multiplier'):
            sprint = parser.getfloat('player', 'player_sprint_multiplier')
            if sprint < 1.0:
                raise ConfigValidationError(
                    "player_sprint_multiplier must be >= 1.0"
                )

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

    def _validate_enemies_settings(self, parser):
        """Валидация секции [enemies]: статы 3 типов + параметры спавна."""
        if not parser.has_section('enemies'):
            raise ConfigValidationError("Missing [enemies] section in config")

        # Положительные числа
        positive_int_keys = [
            'light_max_health', 'light_speed', 'light_size', 'light_damage',
            'heavy_max_health', 'heavy_speed', 'heavy_size', 'heavy_damage',
            'fast_max_health', 'fast_speed', 'fast_size', 'fast_damage',
            'patrol_radius_tiles', 'spawn_min_distance', 'spawn_max_attempts',
        ]
        for key in positive_int_keys:
            if not parser.has_option('enemies', key):
                raise ConfigValidationError(f"Missing enemies.{key}")
            value = parser.getint('enemies', key)
            if value <= 0:
                raise ConfigValidationError(f"enemies.{key} must be positive")

        # respawn_interval - опциональный float (если не задан = 5.0)
        if parser.has_option('enemies', 'respawn_interval'):
            interval = parser.getfloat('enemies', 'respawn_interval')
            if interval <= 0:
                raise ConfigValidationError(
                    "enemies.respawn_interval must be positive"
                )

        # Неотрицательные счётчики (могут быть 0 если этот тип не нужен)
        for key in ('initial_count_light', 'initial_count_heavy', 'initial_count_fast'):
            if not parser.has_option('enemies', key):
                raise ConfigValidationError(f"Missing enemies.{key}")
            if parser.getint('enemies', key) < 0:
                raise ConfigValidationError(f"enemies.{key} must be >= 0")

        # Цвета RGB
        for key in ('light_color', 'heavy_color', 'fast_color'):
            if not parser.has_option('enemies', key):
                raise ConfigValidationError(f"Missing enemies.{key}")
            color_str = parser.get('enemies', key)
            try:
                parts = [int(x.strip()) for x in color_str.split(',')]
                if len(parts) != 3 or not all(0 <= c <= 255 for c in parts):
                    raise ValueError
            except ValueError:
                raise ConfigValidationError(
                    f"enemies.{key} must be 'R,G,B' with values 0..255"
                )

    def _validate_combat_settings(self, parser):
        """Валидация секции [combat]."""
        if not parser.has_section('combat'):
            raise ConfigValidationError("Missing [combat] section in config")
        positive_float_keys = [
            'player_iframe_duration', 'player_knockback_speed',
            'player_knockback_duration', 'enemy_knockback_speed',
            'enemy_knockback_duration', 'enemy_attack_cooldown',
            'enemy_retreat_speed', 'enemy_retreat_duration',
        ]
        for key in positive_float_keys:
            if not parser.has_option('combat', key):
                raise ConfigValidationError(f"Missing combat.{key}")
            val = parser.getfloat('combat', key)
            if val <= 0:
                raise ConfigValidationError(f"combat.{key} must be positive")

    def _validate_pickups_settings(self, parser):
        """Валидация секции [pickups]."""
        if not parser.has_section('pickups'):
            raise ConfigValidationError("Missing [pickups] section in config")
        positive_float_keys = ['magnet_radius', 'magnet_speed', 'lifetime']
        positive_int_keys = ['heart_heal_amount', 'coin_value', 'xp_orb_value']
        for key in positive_float_keys:
            if not parser.has_option('pickups', key):
                raise ConfigValidationError(f"Missing pickups.{key}")
            if parser.getfloat('pickups', key) <= 0:
                raise ConfigValidationError(f"pickups.{key} must be positive")
        for key in positive_int_keys:
            if not parser.has_option('pickups', key):
                raise ConfigValidationError(f"Missing pickups.{key}")
            if parser.getint('pickups', key) <= 0:
                raise ConfigValidationError(f"pickups.{key} must be positive")

    def _validate_drops_settings(self, parser):
        """Валидация секции [drops]."""
        if not parser.has_section('drops'):
            raise ConfigValidationError("Missing [drops] section in config")
        for prefix in ('light', 'heavy', 'fast'):
            # Шансы [0..1]
            for suffix in ('heart_chance', 'coin_chance'):
                key = f'{prefix}_{suffix}'
                if not parser.has_option('drops', key):
                    raise ConfigValidationError(f"Missing drops.{key}")
                val = parser.getfloat('drops', key)
                if not (0.0 <= val <= 1.0):
                    raise ConfigValidationError(
                        f"drops.{key} must be between 0 and 1"
                    )
            # Количество монет min/max
            for suffix in ('coin_min', 'coin_max'):
                key = f'{prefix}_{suffix}'
                if not parser.has_option('drops', key):
                    raise ConfigValidationError(f"Missing drops.{key}")
                if parser.getint('drops', key) < 0:
                    raise ConfigValidationError(f"drops.{key} must be >= 0")
            # XP amount
            xp_key = f'{prefix}_xp_amount'
            if not parser.has_option('drops', xp_key):
                raise ConfigValidationError(f"Missing drops.{xp_key}")
            if parser.getint('drops', xp_key) < 0:
                raise ConfigValidationError(f"drops.{xp_key} must be >= 0")

    def _validate_progression_settings(self, parser):
        """Валидация секции [progression]."""
        if not parser.has_section('progression'):
            raise ConfigValidationError("Missing [progression] section in config")
        for key in ('xp_base', 'max_level'):
            if not parser.has_option('progression', key):
                raise ConfigValidationError(f"Missing progression.{key}")
            if parser.getint('progression', key) < 1:
                raise ConfigValidationError(
                    f"progression.{key} must be >= 1"
                )
        for key in ('xp_growth',):
            if not parser.has_option('progression', key):
                raise ConfigValidationError(f"Missing progression.{key}")
            if parser.getfloat('progression', key) <= 0:
                raise ConfigValidationError(
                    f"progression.{key} must be positive"
                )
        for key in ('hp_per_level', 'damage_per_level'):
            if not parser.has_option('progression', key):
                raise ConfigValidationError(f"Missing progression.{key}")
            if parser.getint('progression', key) < 0:
                raise ConfigValidationError(
                    f"progression.{key} must be >= 0"
                )
        # heal_on_level_up - boolean
        if parser.has_option('progression', 'heal_on_level_up'):
            parser.getboolean('progression', 'heal_on_level_up')

    def _validate_autosave_settings(self, parser):
        """Валидация секции [autosave] (опциональна — даём дефолты)."""
        if not parser.has_section('autosave'):
            return
        if parser.has_option('autosave', 'autosave_enabled'):
            parser.getboolean('autosave', 'autosave_enabled')
        if parser.has_option('autosave', 'autosave_on_level_up'):
            parser.getboolean('autosave', 'autosave_on_level_up')
        if parser.has_option('autosave', 'autosave_interval_minutes'):
            interval = parser.getfloat('autosave', 'autosave_interval_minutes')
            if interval <= 0:
                raise ConfigValidationError(
                    "autosave.autosave_interval_minutes must be positive"
                )
        if parser.has_option('autosave', 'autosave_limit'):
            limit = parser.getint('autosave', 'autosave_limit')
            if limit < 1:
                raise ConfigValidationError(
                    "autosave.autosave_limit must be >= 1"
                )

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