"""
Броня игрока (issue #63) - 4 фиксированных слота экипировки (helmet/chest/
arms/legs). Каждый надетый предмет даёт очки щита сверх HP (энергощит,
поглощает урон ДО того как он доходит до здоровья) плюс базовые статы
(defense/speed_mod/hp_bonus).

Пока без drag-and-drop смены экипировки - стартовый комплект надет с самого
начала (см. default_equipment(), "заглушка для теста" из issue #63). Когда
понадобится смена брони через инвентарь, ARMOR_CATALOG/create_armor() уже
дают нужный паттерн - см. WEAPON_CATALOG/create_weapon() в weapons.py.

Урон от врагов распределяется РАВНОМЕРНО между надетыми предметами со щитом
> 0 (EquipmentSlots.absorb_damage) - если один предмет пробивается раньше
остальных, остаток урона уходит на оставшиеся со щитом, а не на HP.
"""
from typing import Dict, Optional, Tuple, Type

from src.core.config_loader import get_config


SLOT_NAMES: Tuple[str, ...] = ("helmet", "chest", "arms", "legs")


class Armor:
    """Один предмет брони. slot - фиксированный тип (см. SLOT_NAMES)."""

    name: str = "Armor"
    armor_id: str = ""
    slot: str = ""
    color: Tuple[int, int, int] = (120, 120, 140)

    def __init__(self, max_shield: int, defense: int,
                 speed_mod: float, hp_bonus: int):
        self.max_shield = max_shield
        self.defense = defense
        self.speed_mod = speed_mod
        self.hp_bonus = hp_bonus
        self.current_shield = max_shield

    def reset_shield(self) -> None:
        self.current_shield = self.max_shield


class Helmet(Armor):
    name = "Helmet"
    armor_id = "helmet_standard"
    slot = "helmet"
    color = (150, 150, 170)


class Chestplate(Armor):
    name = "Chestplate"
    armor_id = "chest_standard"
    slot = "chest"
    color = (110, 110, 150)


class Bracers(Armor):
    name = "Bracers"
    armor_id = "arms_standard"
    slot = "arms"
    color = (130, 100, 90)


class Greaves(Armor):
    name = "Greaves"
    armor_id = "legs_standard"
    slot = "legs"
    color = (90, 110, 90)


# Каталог всех доступных предметов брони по стабильному armor_id - единственный
# источник правды для создания брони по id (как WEAPON_CATALOG для оружия).
ARMOR_CATALOG: Dict[str, Type[Armor]] = {
    "helmet_standard": Helmet,
    "chest_standard": Chestplate,
    "arms_standard": Bracers,
    "legs_standard": Greaves,
}

# armor_id -> префикс ключей в config.ini [armor] (helmet_shield, ...).
_CONFIG_PREFIX: Dict[str, str] = {
    "helmet_standard": "HELMET",
    "chest_standard": "CHEST",
    "arms_standard": "ARMS",
    "legs_standard": "LEGS",
}


def create_armor(armor_id: str) -> Armor:
    """Создать экземпляр брони по armor_id - статы читаются из
    config.ini [armor] в момент создания (не на уровне класса), чтобы не
    зависеть от порядка импорта/загрузки конфига."""
    cls = ARMOR_CATALOG[armor_id]
    prefix = _CONFIG_PREFIX[armor_id]
    return cls(
        max_shield=get_config(f'ARMOR_{prefix}_SHIELD', 0),
        defense=get_config(f'ARMOR_{prefix}_DEFENSE', 0),
        speed_mod=get_config(f'ARMOR_{prefix}_SPEED_MOD', 0.0),
        hp_bonus=get_config(f'ARMOR_{prefix}_HP_BONUS', 0),
    )


class EquipmentSlots:
    """4 именованных слота брони игрока (см. SLOT_NAMES)."""

    def __init__(self):
        self.slots: Dict[str, Optional[Armor]] = {
            name: None for name in SLOT_NAMES
        }

    def equip(self, armor: Armor) -> None:
        self.slots[armor.slot] = armor

    def _equipped(self):
        return [a for a in self.slots.values() if a is not None]

    @property
    def total_max_shield(self) -> int:
        return sum(a.max_shield for a in self._equipped())

    @property
    def total_shield(self) -> int:
        return sum(a.current_shield for a in self._equipped())

    @property
    def total_defense(self) -> int:
        return sum(a.defense for a in self._equipped())

    @property
    def total_speed_mod(self) -> float:
        return sum(a.speed_mod for a in self._equipped())

    @property
    def total_hp_bonus(self) -> int:
        return sum(a.hp_bonus for a in self._equipped())

    def absorb_damage(self, amount: int) -> int:
        """Поглотить урон щитом, распределяя его поровну между надетыми
        предметами, у которых ещё есть заряд. Если предмет пробивается
        раньше остальных - непоглощённый остаток уходит на предметы,
        у которых щит ещё жив. Возвращает урон, который щит не поглотил
        (должен пройти в HP)."""
        remaining = amount
        while remaining > 0:
            pieces = [a for a in self._equipped() if a.current_shield > 0]
            if not pieces:
                break
            share, extra = divmod(remaining, len(pieces))
            absorbed = 0
            for i, piece in enumerate(pieces):
                take = share + (1 if i < extra else 0)
                actual = min(take, piece.current_shield)
                piece.current_shield -= actual
                absorbed += actual
            remaining -= absorbed
            if absorbed == 0:
                break
        return remaining

    def reset_all_shields(self) -> None:
        for armor in self._equipped():
            armor.reset_shield()


def default_equipment() -> EquipmentSlots:
    """Стартовый комплект брони - все 4 слота заполнены (заглушка для
    теста, см. модуль docstring)."""
    equipment = EquipmentSlots()
    for armor_id in ARMOR_CATALOG:
        equipment.equip(create_armor(armor_id))
    return equipment
