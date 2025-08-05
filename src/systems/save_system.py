import json
import os
from datetime import datetime
import pygame


class SaveSystem:
    """Система сохранения и загрузки игрового прогресса"""
    
    def __init__(self):
        self.save_version = "1.0"
        self.saves_dir = "saves"
        self.quicksave_file = "quicksave.json"
        
        # Создаем папку сохранений если её нет
        if not os.path.exists(self.saves_dir):
            os.makedirs(self.saves_dir)
    
    def save_game(self, player, world, game_stats=None, filename=None):
        """
        Сохранение игрового состояния в JSON файл
        
        Args:
            player: объект игрока
            world: объект мира
            game_stats: статистика игры (опционально)
            filename: имя файла (по умолчанию quicksave.json)
        
        Returns:
            bool: True если сохранение успешно, False если ошибка
        """
        try:
            if filename is None:
                filename = self.quicksave_file
            
            filepath = os.path.join(self.saves_dir, filename)
            
            # Создаем структуру сохранения согласно требованиям
            save_data = {
                "version": self.save_version,
                "timestamp": datetime.now().isoformat() + "Z",
                "player": self._serialize_player(player),
                "world": self._serialize_world(world),
                "inventory": {
                    "items": [],  # Пока пустой, будет расширен позже
                    "gold": 0
                },
                "game_stats": game_stats or {
                    "play_time": 0,  # Будет добавлено позже
                    "enemies_killed": 0,
                    "items_collected": 0
                }
            }
            
            # Записываем в файл с красивым форматированием
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(save_data, f, indent=2, ensure_ascii=False)
            
            print(f"Игра сохранена: {filename}")
            return True
            
        except Exception as e:
            print(f"Ошибка сохранения: {e}")
            return False
    
    def load_game(self, filename=None):
        """
        Загрузка игрового состояния из JSON файла
        
        Args:
            filename: имя файла (по умолчанию quicksave.json)
        
        Returns:
            dict: данные сохранения или None если ошибка
        """
        try:
            if filename is None:
                filename = self.quicksave_file
            
            filepath = os.path.join(self.saves_dir, filename)
            
            if not os.path.exists(filepath):
                print(f"Файл сохранения не найден: {filename}")
                return None
            
            with open(filepath, 'r', encoding='utf-8') as f:
                save_data = json.load(f)
            
            # Проверяем версию сохранения
            if save_data.get("version") != self.save_version:
                print(f"Предупреждение: версия сохранения {save_data.get('version')} отличается от текущей {self.save_version}")
            
            print(f"Игра загружена: {filename}")
            return save_data
            
        except Exception as e:
            print(f"Ошибка загрузки: {e}")
            return None
    
    def _serialize_player(self, player):
        """Сериализация данных игрока"""
        return {
            "x": int(player.x),
            "y": int(player.y),
            "health": player.health,
            "max_health": player.max_health,
            "facing_direction": player.facing_direction
        }
    
    def _serialize_world(self, world):
        """Сериализация данных мира"""
        return {
            "current_map": "main_world",  # Пока статично, можно расширить
            "discovered_areas": ["spawn"]  # Пока базовый список, можно расширить
        }
    
    def apply_save_data_to_player(self, player, save_data):
        """
        Применение загруженных данных к объекту игрока
        
        Args:
            player: объект игрока
            save_data: данные сохранения
        """
        try:
            player_data = save_data["player"]
            player.x = float(player_data["x"])
            player.y = float(player_data["y"])
            player.health = player_data["health"]
            player.max_health = player_data["max_health"]
            player.facing_direction = player_data["facing_direction"]
            
            # Обновляем rect игрока
            player.rect.x = int(player.x)
            player.rect.y = int(player.y)
            
            print(f"Позиция игрока восстановлена: ({player.x}, {player.y})")
            print(f"Здоровье игрока: {player.health}/{player.max_health}")
            
        except Exception as e:
            print(f"Ошибка применения данных игрока: {e}")
    
    def apply_save_data_to_world(self, world, save_data):
        """
        Применение загруженных данных к объекту мира
        
        Args:
            world: объект мира
            save_data: данные сохранения
        """
        try:
            world_data = save_data["world"]
            # Пока мир не требует особого восстановления
            # В будущем здесь можно добавить восстановление открытых областей
            print(f"Мир восстановлен: {world_data.get('current_map', 'main_world')}")
            
        except Exception as e:
            print(f"Ошибка применения данных мира: {e}")
    
    def quicksave_exists(self):
        """Проверка существования файла быстрого сохранения"""
        filepath = os.path.join(self.saves_dir, self.quicksave_file)
        return os.path.exists(filepath)