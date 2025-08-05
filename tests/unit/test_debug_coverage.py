"""
Tests to improve debug.py coverage
"""
import pytest
import pygame
import os
from unittest.mock import patch


class TestDebugCoverage:
    """Additional tests for debug.py coverage"""
    
    @classmethod
    def setup_class(cls):
        """Set up pygame for testing"""
        os.environ['SDL_VIDEODRIVER'] = 'dummy'
        pygame.init()
        pygame.display.set_mode((800, 600))
    
    def test_debug_basic_usage(self):
        """Test basic debug functionality"""
        from src.utils.debug import debug
        
        # Should not crash
        debug("Test message")
        debug("Position test", x=50, y=100)
    
    def test_debug_with_different_types(self):
        """Test debug with different data types"""
        from src.utils.debug import debug
        
        debug("String")
        debug(42)
        debug(3.14)
        debug(True)
        debug([1, 2, 3])
    
    def test_debug_edge_positions(self):
        """Test debug with edge case positions"""
        from src.utils.debug import debug
        
        debug("Zero", x=0, y=0)
        debug("Large", x=1000, y=1000)
    
    @patch('pygame.display.get_surface', return_value=None)
    def test_debug_no_surface(self, mock_surface):
        """Test debug when no surface available"""
        from src.utils.debug import debug
        
        # Should handle None surface gracefully or raise expected error
        try:
            debug("No surface")
        except (TypeError, AttributeError):
            # Expected when no surface
            pass
    
    def test_debug_long_text(self):
        """Test debug with very long text"""
        from src.utils.debug import debug
        
        long_text = "A" * 500
        debug(long_text)
    
    def test_debug_special_chars(self):
        """Test debug with special characters"""
        from src.utils.debug import debug
        
        debug("!@#$%^&*()")
        debug("Русский текст")
        debug("🎮🕹️")
    
    def test_debug_module_font(self):
        """Test that debug module has font"""
        import src.utils.debug as debug_module
        
        assert hasattr(debug_module, 'font')
        assert debug_module.font is not None