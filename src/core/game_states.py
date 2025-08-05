from enum import Enum


class GameState(Enum):
    """Перечисление состояний игры"""
    MENU = "menu"
    PLAYING = "playing"
    GAME_OVER = "game_over"