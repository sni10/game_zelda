import pygame
import time


class GameStats:
    """Система отслеживания игровой статистики"""
    
    def __init__(self):
        # Время игры
        self.start_time = time.time()
        self.play_time = 0.0
        
        # Боевая статистика
        self.enemies_killed = 0
        self.damage_dealt = 0
        self.damage_taken = 0
        self.attacks_made = 0
        
        # Исследование
        self.items_collected = 0
        self.distance_traveled = 0
        self.areas_discovered = 0
        
        # Смерти и здоровье
        self.deaths = 0
        self.health_lost = 0
        self.health_recovered = 0
        
        # Последняя позиция для подсчета дистанции
        self.last_x = 0
        self.last_y = 0
    
    def update_play_time(self):
        """Обновить время игры"""
        current_time = time.time()
        self.play_time = current_time - self.start_time
    
    def get_play_time_formatted(self):
        """Получить отформатированное время игры"""
        self.update_play_time()
        minutes = int(self.play_time // 60)
        seconds = int(self.play_time % 60)
        return f"{minutes:02d}:{seconds:02d}"
    
    def record_enemy_kill(self, damage_dealt=0):
        """Записать убийство врага"""
        self.enemies_killed += 1
        self.damage_dealt += damage_dealt
    
    def record_attack(self, damage_dealt=0):
        """Записать атаку"""
        self.attacks_made += 1
        self.damage_dealt += damage_dealt
    
    def record_damage_taken(self, damage):
        """Записать полученный урон"""
        self.damage_taken += damage
        self.health_lost += damage
    
    def record_healing(self, amount):
        """Записать восстановление здоровья"""
        self.health_recovered += amount
    
    def record_item_collected(self):
        """Записать сбор предмета"""
        self.items_collected += 1
    
    def record_death(self):
        """Записать смерть игрока"""
        self.deaths += 1
    
    def update_position(self, x, y):
        """Обновить позицию игрока для подсчета пройденного расстояния"""
        if hasattr(self, 'last_x') and hasattr(self, 'last_y'):
            # Вычисляем расстояние от последней позиции
            dx = x - self.last_x
            dy = y - self.last_y
            distance = (dx * dx + dy * dy) ** 0.5
            self.distance_traveled += distance
        
        self.last_x = x
        self.last_y = y
    
    def get_distance_traveled_formatted(self):
        """Получить отформатированное пройденное расстояние"""
        return f"{self.distance_traveled:.0f} м"
    
    def get_summary(self):
        """Получить сводку статистики"""
        return {
            'play_time': self.get_play_time_formatted(),
            'enemies_killed': self.enemies_killed,
            'damage_dealt': self.damage_dealt,
            'damage_taken': self.damage_taken,
            'attacks_made': self.attacks_made,
            'items_collected': self.items_collected,
            'distance_traveled': self.get_distance_traveled_formatted(),
            'deaths': self.deaths,
            'health_lost': self.health_lost,
            'health_recovered': self.health_recovered
        }
    
    def reset(self):
        """Сбросить статистику для новой игры"""
        self.__init__()