"""
EnemyFactory - реестр типов врагов + создание по type_id.

Расширяемость: чтобы добавить новый тип врага, нужно только:
  1. Создать класс в enemy.py с classmethod create(x, y, patrol_zone)
  2. Зарегистрировать его в этом модуле через EnemyFactory.register()

Существующий код менять не нужно (Open/Closed Principle).

Если нужны "параметрические" типы (например, "boss_level_5"), фабрика
поддерживает регистрацию любого callable, не только классов.
"""
from typing import Callable, Dict
import pygame

from src.entities.enemy import Enemy, LightEnemy, HeavyEnemy, FastEnemy


# Тип фабричной функции: (x, y, patrol_zone) -> Enemy
EnemyFactoryFunc = Callable[[float, float, pygame.Rect], Enemy]


class UnknownEnemyTypeError(KeyError):
    """Запрошен незарегистрированный type_id врага."""


class EnemyFactory:
    """Глобальный реестр фабричных функций по type_id строке."""

    _registry: Dict[str, EnemyFactoryFunc] = {}

    @classmethod
    def register(cls, type_id: str, factory_func: EnemyFactoryFunc) -> None:
        """Зарегистрировать фабрику для типа. Перезапись разрешена
        (например для тестов / модов)."""
        cls._registry[type_id] = factory_func

    @classmethod
    def create(cls, type_id: str, x: float, y: float,
               patrol_zone: pygame.Rect) -> Enemy:
        """Создать врага указанного type_id."""
        if type_id not in cls._registry:
            raise UnknownEnemyTypeError(
                f"Unknown enemy type '{type_id}'. "
                f"Registered: {sorted(cls._registry)}"
            )
        return cls._registry[type_id](x, y, patrol_zone)

    @classmethod
    def registered_types(cls) -> list:
        """Список всех зарегистрированных type_id."""
        return sorted(cls._registry.keys())

    @classmethod
    def clear(cls) -> None:
        """Очистить реестр (для тестов)."""
        cls._registry.clear()


# === Регистрация дефолтных типов ============================================
# Выполняется при первом импорте модуля.

EnemyFactory.register(LightEnemy.TYPE_ID, LightEnemy.create)
EnemyFactory.register(HeavyEnemy.TYPE_ID, HeavyEnemy.create)
EnemyFactory.register(FastEnemy.TYPE_ID, FastEnemy.create)

