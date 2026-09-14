"""
Mission / Campaign - кампания из последовательных миссий-карт.

См. CAMPAIGN_PLAN.md (корень репозитория) и issue #68 - полное обоснование
архитектуры. Кратко:
- MissionObjective (Strategy, как уже Weapon/AIBehavior) - когда миссия
  считается пройденной.
- Mission - данные одной миссии (карта + цель), не поведение.
- Campaign - последовательность миссий + агрегация статистики по ним.

Мир остаётся "один за раз" (ADR 2026-04-26 в DESIGN.md, multi-world не
возвращаем) - смена миссии это замена Game.world, не второй активный мир.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Dict, List, Optional


# --- Цели миссии -------------------------------------------------------


class MissionObjective(ABC):
    """Стратегия условия завершения миссии."""

    @abstractmethod
    def is_complete(self, world) -> bool:
        """True когда цель миссии достигнута."""
        raise NotImplementedError

    @abstractmethod
    def progress(self, world) -> str:
        """Короткая строка для HUD/отладки, например 'Босс: жив'."""
        raise NotImplementedError


class DefeatBossObjective(MissionObjective):
    """Цель миссии - убить босса. Готово, когда на карте не осталось живых
    врагов с флагом is_boss (см. EnemyManager.boss_alive()).

    Можно теоретически проскочить мимо всех рядовых врагов и убить только
    босса - это осознанно разрешено (см. CAMPAIGN_PLAN.md), не проверяем
    что рядовые враги тоже зачищены."""

    def is_complete(self, world) -> bool:
        return not world.enemy_manager.boss_alive()

    def progress(self, world) -> str:
        return "Босс повержен" if self.is_complete(world) else "Цель: уничтожить босса"


# --- Данные миссии/кампании ---------------------------------------------


@dataclass
class Mission:
    """Одна миссия кампании - данные, не поведение."""

    map_file: str  # имя файла в data/ без .txt (main_world/big_world/...)
    world_width: int  # реальный пиксельный размер ИМЕННО этой карты
    world_height: int
    title: str
    objective: MissionObjective
    boss_type_id: str = "boss"  # какой type_id заспавнить как босса на старте


# Числовые поля GameStats.to_dict(), которые имеет смысл считать за миссию
# (снимок/дельта/сумма). last_x/last_y - позиция, не метрика прогресса -
# осознанно исключены.
_STAT_FIELDS = (
    "play_time",
    "enemies_killed",
    "damage_dealt",
    "damage_taken",
    "attacks_made",
    "items_collected",
    "distance_traveled",
    "areas_discovered",
    "deaths",
    "health_lost",
    "health_recovered",
)


def _diff_stats(current: dict, baseline: dict) -> Dict[str, float]:
    """current - baseline по числовым полям статистики (дельта за миссию)."""
    return {k: current.get(k, 0) - baseline.get(k, 0) for k in _STAT_FIELDS}


def _sum_stats(snapshots: List[dict]) -> Dict[str, float]:
    """Просуммировать несколько снимков статистики (итог кампании)."""
    total = {k: 0 for k in _STAT_FIELDS}
    for snap in snapshots:
        for k in _STAT_FIELDS:
            total[k] += snap.get(k, 0)
    return total


@dataclass
class Campaign:
    """Последовательность миссий + агрегация статистики по пройденным."""

    missions: List[Mission]
    index: int = 0
    mission_snapshots: List[dict] = field(default_factory=list)
    _baseline: Optional[dict] = field(default=None, repr=False)

    @property
    def current(self) -> Mission:
        return self.missions[self.index]

    @property
    def is_last(self) -> bool:
        return self.index >= len(self.missions) - 1

    def begin_mission(self, game_stats) -> None:
        """Снимок кумулятивной GameStats на старте текущей миссии - опорная
        точка для дельты этой миссии в complete_mission()."""
        self._baseline = game_stats.to_dict()

    def complete_mission(self, game_stats) -> Dict[str, float]:
        """Посчитать дельту статистики текущей миссии, сохранить и вернуть."""
        current = game_stats.to_dict()
        baseline = self._baseline or {}
        snapshot = _diff_stats(current, baseline)
        self.mission_snapshots.append(snapshot)
        return snapshot

    def advance(self) -> Optional[Mission]:
        """Перейти к следующей миссии. None если кампания уже пройдена
        (advance() вызван на последней миссии)."""
        if self.is_last:
            return None
        self.index += 1
        return self.current

    def total_snapshot(self) -> Dict[str, float]:
        """Суммарная статистика по всем завершённым миссиям (итог кампании,
        для финального экрана победы)."""
        return _sum_stats(self.mission_snapshots)


def build_dev_campaign() -> Campaign:
    """Кампания для разработки/обкатки механизма - 2 уже существующие карты
    (main_world -> big_world), обе с целью 'убить босса'. Полная кампания
    по плану - 10 карт (см. CAMPAIGN_PLAN.md); список здесь просто станет
    длиннее, сам механизм не меняется."""
    return Campaign(
        missions=[
            Mission(
                map_file="main_world",
                world_width=2000,
                world_height=2000,
                title="Миссия 1: Зачистка окраины",
                objective=DefeatBossObjective(),
            ),
            Mission(
                map_file="big_world",
                world_width=6400,
                world_height=6400,
                title="Миссия 2: Руины города",
                objective=DefeatBossObjective(),
            ),
        ]
    )
