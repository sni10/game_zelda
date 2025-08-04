#!/usr/bin/env python3
"""
Zelda-like Game - Main Entry Point

Запуск игры в стиле классической 2D Zelda с использованием Python и Pygame.
"""

import sys
import os

# Добавляем src в путь для импортов
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.core.game import Game


def main():
    """Главная функция запуска игры"""
    print("Запуск Zelda-подобной игры...")
    print("Управление: WASD/Стрелки - движение, Пробел - атака, F1 - отладка, ESC - выход")
    
    try:
        game = Game()
        game.run()
    except KeyboardInterrupt:
        print("\nИгра прервана пользователем")
    except Exception as e:
        print(f"Ошибка при запуске игры: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()