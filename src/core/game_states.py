from enum import Enum


class GameState(Enum):
    """Перечисление состояний игры"""

    MENU = "menu"
    PLAYING = "playing"
    GAME_OVER = "game_over"
    LOAD_MENU = "load_menu"
    SAVE_MENU = "save_menu"
    INVENTORY = "inventory"
    # Кампания миссий (см. CAMPAIGN_PLAN.md): босс убит, промежуточная миссия -
    # экран статистики миссии с кнопкой "следующая миссия".
    MISSION_COMPLETE = "mission_complete"
    # Затухание экрана между миссиями - см. src/ui/map_transition.py.
    TRANSITION = "transition"
    # Последняя миссия кампании пройдена - итоговый экран с суммарной
    # статистикой по всем миссиям и кнопкой выхода в меню.
    GAME_COMPLETE = "game_complete"
