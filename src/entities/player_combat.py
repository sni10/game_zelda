"""
PlayerCombat - боевые механики игрока.

Single Responsibility: управлять атакой (старт, таймер, cooldown, attack_id),
переключение оружий, расчёт зон поражения. Не знает про рендер или мир.
"""
import pygame

from src.core.config_loader import get_config
from src.entities.weapons import (
    Weapon,
    WEAPON_CATALOG,
    create_weapon,
    starting_slot_assignment,
    RangedWeapon,
)
from typing import Dict, List

# Максимум слотов оружия, открываемых прокачкой (см. PlayerStats.unlocked_weapon_slots).
MAX_WEAPON_SLOTS = 8


class PlayerCombat:
    """Система атаки и оружия игрока."""

    def __init__(self):
        # Runtime-состояние текущей атаки
        self.attacking = False
        self.attack_timer = 0
        self.last_attack_time = 0
        # Уникальный ID взмаха: EnemyManager сравнивает его с last_hit_attack_id
        # у каждого врага, чтобы 1 атака = 1 урон (атака длится несколько кадров).
        self.attack_id = 0

        # Инвентарь оружий: стартует с 2 слотов (мечи), растёт до
        # MAX_WEAPON_SLOTS по мере разлочки уровнями (см. unlock_slot()).
        self.weapons: List[Weapon] = [
            create_weapon(wid) for wid in starting_slot_assignment()
        ]
        self.current_weapon_index = 0

        # Патроны по ammo_type. Только "bullets" (Rifle) заведены сейчас -
        # у melee/AoE weapon.ammo_type == None, они эту систему не трогают.
        self.magazine: Dict[str, int] = {"bullets": RangedWeapon.magazine_size}
        self.reserve: Dict[str, int] = {
            "bullets": get_config('AMMO_RIFLE_STARTING_RESERVE', 36)
        }

    @property
    def current_weapon(self) -> Weapon:
        """Текущее активное оружие."""
        return self.weapons[self.current_weapon_index]

    def switch_weapon(self, index: int) -> bool:
        """Переключить оружие по индексу. Возвращает True если произошло."""
        if self.attacking:
            return False
        if 0 <= index < len(self.weapons) and index != self.current_weapon_index:
            self.current_weapon_index = index
            return True
        return False

    def cycle_slot_weapon(self, index: int) -> bool:
        """Сменить тип оружия в слоте index на следующий по кругу из каталога.

        Свободное назначение: любой слот может держать любое оружие из
        WEAPON_CATALOG, без привязки к melee/ranged. Возвращает True если
        смена произошла."""
        if self.attacking:
            return False
        if not (0 <= index < len(self.weapons)):
            return False
        catalog_ids = list(WEAPON_CATALOG)
        current_id = self.weapons[index].weapon_id
        next_index = (catalog_ids.index(current_id) + 1) % len(catalog_ids)
        self.weapons[index] = create_weapon(catalog_ids[next_index])
        return True

    def move_weapon(self, from_index: int, to_index: int) -> bool:
        """Поменять местами оружие в двух слотах (своп, не сдвиг). Для
        drag-and-drop в InventoryScreen. current_weapon_index не трогаем -
        активным остаётся то, что физически лежит в этом слоте после свопа
        (тот же принцип, что уже работает для cycle_slot_weapon)."""
        if self.attacking:
            return False
        n = len(self.weapons)
        if not (0 <= from_index < n and 0 <= to_index < n):
            return False
        if from_index == to_index:
            return False
        self.weapons[from_index], self.weapons[to_index] = (
            self.weapons[to_index], self.weapons[from_index]
        )
        return True

    def unlock_slot(self) -> bool:
        """Открыть новый слот оружия (до MAX_WEAPON_SLOTS), заполнив его
        первым оружием из каталога. Возвращает True если слот добавлен."""
        if len(self.weapons) >= MAX_WEAPON_SLOTS:
            return False
        first_id = next(iter(WEAPON_CATALOG))
        self.weapons.append(create_weapon(first_id))
        return True

    def try_attack(self) -> None:
        """Попытка атаки с учётом cooldown текущего оружия и патронов
        (если у оружия задан ammo_type - пустой магазин блокирует атаку,
        "щелчок по пустому", без списания cooldown)."""
        current_time = pygame.time.get_ticks()
        weapon = self.current_weapon
        if self.attacking or current_time - self.last_attack_time <= weapon.cooldown_ms:
            return
        if weapon.ammo_type and self.magazine.get(weapon.ammo_type, 0) <= 0:
            return
        if weapon.ammo_type:
            self.magazine[weapon.ammo_type] -= 1
        self.attacking = True
        self.attack_timer = current_time
        self.last_attack_time = current_time
        self.attack_id += 1

    def reload(self) -> bool:
        """Перезарядить магазин текущего оружия из резерва. Блокируется во
        время атаки. Возвращает True если что-то реально перенесено."""
        weapon = self.current_weapon
        if not weapon.ammo_type or self.attacking:
            return False
        ammo_type = weapon.ammo_type
        need = weapon.magazine_size - self.magazine.get(ammo_type, 0)
        if need <= 0:
            return False
        available = self.reserve.get(ammo_type, 0)
        take = min(need, available)
        if take <= 0:
            return False
        self.magazine[ammo_type] = self.magazine.get(ammo_type, 0) + take
        self.reserve[ammo_type] = available - take
        return True

    def add_ammo(self, ammo_type: str, amount: int, cap: int) -> None:
        """Добавить патроны в резерв (с учётом капа). Вызывается из AmmoPickup."""
        self.reserve[ammo_type] = min(cap, self.reserve.get(ammo_type, 0) + amount)

    def update_attack(self) -> None:
        """Обновить таймер атаки — вызывать каждый кадр."""
        if self.attacking:
            current_time = pygame.time.get_ticks()
            if current_time - self.attack_timer > self.current_weapon.duration_ms:
                self.attacking = False

    def get_attack_rects(self, player_rect: pygame.Rect,
                         aim_dx: float, aim_dy: float) -> list:
        """Получить зоны поражения текущей атаки в направлении прицела
        (непрерывный вектор, 360° - не только 8 фиксированных направлений)."""
        if not self.attacking:
            return []
        return self.current_weapon.get_attack_rects(player_rect, aim_dx, aim_dy)

