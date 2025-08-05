"""
Tests for the GameStats class
"""
import pytest
import time
from unittest.mock import patch
from src.core.game_stats import GameStats


class TestGameStats:
    """Test cases for GameStats class"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.game_stats = GameStats()
    
    def test_game_stats_initialization(self):
        """Test GameStats initialization"""
        assert self.game_stats.enemies_killed == 0
        assert self.game_stats.damage_dealt == 0
        assert self.game_stats.damage_taken == 0
        assert self.game_stats.attacks_made == 0
        assert self.game_stats.items_collected == 0
        assert self.game_stats.distance_traveled == 0
        assert self.game_stats.areas_discovered == 0
        assert self.game_stats.deaths == 0
        assert self.game_stats.health_lost == 0
        assert self.game_stats.health_recovered == 0
        assert hasattr(self.game_stats, 'start_time')
        assert hasattr(self.game_stats, 'last_x')
        assert hasattr(self.game_stats, 'last_y')
    
    def test_record_enemy_kill(self):
        """Test recording enemy kills"""
        initial_kills = self.game_stats.enemies_killed
        initial_damage = self.game_stats.damage_dealt
        
        self.game_stats.record_enemy_kill(25)
        
        assert self.game_stats.enemies_killed == initial_kills + 1
        assert self.game_stats.damage_dealt == initial_damage + 25
    
    def test_record_enemy_kill_no_damage(self):
        """Test recording enemy kill without damage"""
        initial_kills = self.game_stats.enemies_killed
        initial_damage = self.game_stats.damage_dealt
        
        self.game_stats.record_enemy_kill()
        
        assert self.game_stats.enemies_killed == initial_kills + 1
        assert self.game_stats.damage_dealt == initial_damage  # No change
    
    def test_record_attack(self):
        """Test recording attacks"""
        initial_attacks = self.game_stats.attacks_made
        initial_damage = self.game_stats.damage_dealt
        
        self.game_stats.record_attack(15)
        
        assert self.game_stats.attacks_made == initial_attacks + 1
        assert self.game_stats.damage_dealt == initial_damage + 15
    
    def test_record_damage_taken(self):
        """Test recording damage taken"""
        initial_damage_taken = self.game_stats.damage_taken
        initial_health_lost = self.game_stats.health_lost
        
        self.game_stats.record_damage_taken(10)
        
        assert self.game_stats.damage_taken == initial_damage_taken + 10
        assert self.game_stats.health_lost == initial_health_lost + 10
    
    def test_record_healing(self):
        """Test recording healing"""
        initial_health_recovered = self.game_stats.health_recovered
        
        self.game_stats.record_healing(20)
        
        assert self.game_stats.health_recovered == initial_health_recovered + 20
    
    def test_record_item_collected(self):
        """Test recording item collection"""
        initial_items = self.game_stats.items_collected
        
        self.game_stats.record_item_collected()
        
        assert self.game_stats.items_collected == initial_items + 1
    
    def test_record_death(self):
        """Test recording player death"""
        initial_deaths = self.game_stats.deaths
        
        self.game_stats.record_death()
        
        assert self.game_stats.deaths == initial_deaths + 1
    
    def test_update_position(self):
        """Test updating player position and distance tracking"""
        # First position update (should not add distance since no previous position)
        self.game_stats.update_position(0, 0)
        assert self.game_stats.distance_traveled == 0
        assert self.game_stats.last_x == 0
        assert self.game_stats.last_y == 0
        
        # Second position update (should calculate distance)
        self.game_stats.update_position(3, 4)  # 3-4-5 triangle, distance = 5
        assert abs(self.game_stats.distance_traveled - 5.0) < 0.001
        assert self.game_stats.last_x == 3
        assert self.game_stats.last_y == 4
    
    def test_get_distance_traveled_formatted(self):
        """Test formatted distance display"""
        self.game_stats.distance_traveled = 123.456
        
        formatted = self.game_stats.get_distance_traveled_formatted()
        assert formatted == "123 м"
    
    @patch('time.time')
    def test_play_time_tracking(self, mock_time):
        """Test play time tracking"""
        # Mock start time
        mock_time.return_value = 1000.0
        stats = GameStats()
        
        # Mock current time (10 seconds later)
        mock_time.return_value = 1010.0
        stats.update_play_time()
        
        assert stats.play_time == 10.0
    
    @patch('time.time')
    def test_get_play_time_formatted(self, mock_time):
        """Test formatted play time display"""
        # Mock start time
        mock_time.return_value = 1000.0
        stats = GameStats()
        
        # Mock current time (1 minute 35 seconds later)
        mock_time.return_value = 1095.0
        
        formatted = stats.get_play_time_formatted()
        assert formatted == "01:35"
        
        # Test with hours (130 seconds = 2 minutes 10 seconds)
        mock_time.return_value = 1130.0
        formatted = stats.get_play_time_formatted()
        assert formatted == "02:10"
    
    def test_get_summary(self):
        """Test getting stats summary"""
        # Set some test values
        self.game_stats.enemies_killed = 5
        self.game_stats.damage_dealt = 100
        self.game_stats.items_collected = 3
        self.game_stats.distance_traveled = 250.5
        
        summary = self.game_stats.get_summary()
        
        assert 'play_time' in summary
        assert summary['enemies_killed'] == 5
        assert summary['damage_dealt'] == 100
        assert summary['items_collected'] == 3
        assert summary['distance_traveled'] == "250 м"
        assert 'deaths' in summary
        assert 'health_lost' in summary
        assert 'health_recovered' in summary
    
    def test_reset(self):
        """Test resetting stats"""
        # Set some values
        self.game_stats.enemies_killed = 10
        self.game_stats.damage_dealt = 200
        self.game_stats.distance_traveled = 500
        
        # Reset
        self.game_stats.reset()
        
        # Check values are back to initial state
        assert self.game_stats.enemies_killed == 0
        assert self.game_stats.damage_dealt == 0
        assert self.game_stats.distance_traveled == 0
        assert hasattr(self.game_stats, 'start_time')  # Should have new start time
    
    def test_multiple_operations(self):
        """Test multiple operations together"""
        # Simulate a game session
        self.game_stats.record_attack(10)
        self.game_stats.record_attack(15)
        self.game_stats.record_enemy_kill(20)
        self.game_stats.record_damage_taken(5)
        self.game_stats.record_item_collected()
        self.game_stats.record_item_collected()
        
        assert self.game_stats.attacks_made == 2
        assert self.game_stats.damage_dealt == 45  # 10 + 15 + 20
        assert self.game_stats.enemies_killed == 1
        assert self.game_stats.damage_taken == 5
        assert self.game_stats.items_collected == 2