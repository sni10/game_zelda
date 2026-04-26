"""
AI-стратегии для врагов (Strategy pattern).

Каждый враг агрегирует одну стратегию через композицию. Это позволяет:
- Переключать поведение врага в runtime (например, патруль -> погоня)
- Переиспользовать стратегии для разных типов (один PatrolBehavior для всех)
- Добавлять новые стратегии без правки класса Enemy (OCP)

MVP-стратегии:
- IdleBehavior     - стоит на месте (для тестов и неподвижных врагов)
- PatrolBehavior   - случайное блуждание в пределах patrol_zone

Будущие стратегии (после MVP):
- ChaseBehavior    - преследование игрока в радиусе агро
- FleeBehavior     - убегает при низком HP
- RangedBehavior   - стреляет с дистанции
"""
from abc import ABC, abstractmethod
import random
import math


class AIBehavior(ABC):
    """Базовая стратегия поведения врага."""

    @abstractmethod
    def update(self, enemy, dt: float, world) -> None:
        """Обновить состояние врага за один кадр.

        Стратегия читает/изменяет enemy.x, enemy.y, enemy.rect.
        World передаётся для проверки коллизий с террейном.
        """
        raise NotImplementedError


class IdleBehavior(AIBehavior):
    """Враг неподвижен. Используется для тестов и декоративных врагов."""

    def update(self, enemy, dt, world):
        return


class PatrolBehavior(AIBehavior):
    """Случайное axial-блуждание внутри patrol_zone врага.

    Враг выбирает случайную точку, СОВПАДАЮЩУЮ по одной координате
    с текущей. То есть за один отрезок движется ТОЛЬКО горизонтально
    или ТОЛЬКО вертикально - никаких диагоналей "как муха".
    Результат - спокойный патруль типа "влево-вниз-влево-вверх".

    Достигнув цели (или истечения таймера) - выбирает новую.
    Если упёрся в препятствие - сразу выбирает новую цель.
    """

    # Время до выбора новой цели если враг застрял или цель достигнута
    DEFAULT_REPATH_INTERVAL = 2.0  # секунды
    REACH_THRESHOLD = 4.0          # px до цели = "достиг"

    def __init__(self, repath_interval: float = DEFAULT_REPATH_INTERVAL):
        self.repath_interval = repath_interval

    def _pick_target(self, enemy):
        """Случайная axial-цель в patrol_zone.

        Выбираем одну из осей (x или y) и движемся ТОЛЬКО по ней.
        Координата другой оси совпадает с текущей - никаких диагоналей.
        """
        zone = enemy.patrol_zone
        max_x = max(zone.left, zone.right - enemy.rect.width)
        max_y = max(zone.top, zone.bottom - enemy.rect.height)

        # Случайно: горизонтальное или вертикальное движение
        if random.random() < 0.5:
            # Горизонталь: меняем X, Y оставляем (округлённый до int чтобы
            # не было микро-дрожаний)
            target_x = random.randint(zone.left, max_x) if max_x > zone.left else zone.left
            target_y = enemy.y
        else:
            # Вертикаль: меняем Y, X оставляем
            target_x = enemy.x
            target_y = random.randint(zone.top, max_y) if max_y > zone.top else zone.top

        timeout = random.uniform(0.6, self.repath_interval)
        return target_x, target_y, timeout

    def _ensure_target(self, enemy):
        """Лениво создаём цель если её ещё нет (после spawn)."""
        if not hasattr(enemy, '_patrol_target'):
            tx, ty, t = self._pick_target(enemy)
            enemy._patrol_target = (tx, ty)
            enemy._patrol_timer = t

    def update(self, enemy, dt, world):
        self._ensure_target(enemy)
        enemy._patrol_timer -= dt

        target_x, target_y = enemy._patrol_target
        dx = target_x - enemy.x
        dy = target_y - enemy.y
        distance = math.hypot(dx, dy)

        # Достигли цели или истёк таймер - выбираем новую
        if distance < self.REACH_THRESHOLD or enemy._patrol_timer <= 0:
            tx, ty, t = self._pick_target(enemy)
            enemy._patrol_target = (tx, ty)
            enemy._patrol_timer = t
            return

        # Двигаемся к цели с скоростью enemy.stats.speed.
        # Поскольку target axial - один из dx/dy будет почти 0,
        # движение получится строго вдоль одной оси.
        speed = enemy.stats.speed
        nx = dx / distance
        ny = dy / distance

        new_x = enemy.x + nx * speed * dt
        new_y = enemy.y + ny * speed * dt

        # Не выходим за патрульную зону
        zone = enemy.patrol_zone
        new_x = max(zone.left, min(new_x, zone.right - enemy.rect.width))
        new_y = max(zone.top, min(new_y, zone.bottom - enemy.rect.height))

        # Проверка коллизии с террейном - если упёрлись, перевыбираем цель
        import pygame
        candidate = pygame.Rect(int(new_x), int(new_y),
                                enemy.rect.width, enemy.rect.height)
        if world is not None and world.check_collision(candidate):
            tx, ty, t = self._pick_target(enemy)
            enemy._patrol_target = (tx, ty)
            enemy._patrol_timer = t
            return

        enemy.x = new_x
        enemy.y = new_y
        enemy.rect.x = int(new_x)
        enemy.rect.y = int(new_y)

