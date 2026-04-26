"""
SaveSystem — сохранение и загрузка прогресса игры в JSON.

v0.3.1 — фикс F9: теперь сериализуем
- позицию/HP/направление/прогрессию игрока,
- текущий индекс оружия и i-frame таймер,
- живых врагов (тип, HP, позиция, attack_cooldown),
- лежащие на земле пикапы,
- GameStats (kills/distance/playtime/...),
- метаданные (версия, timestamp).

Загрузка валидирует схему: повреждённые файлы возвращают None и
не крашат игру (см. _validate_save_data).
"""
import json
import os
from datetime import datetime


class SaveValidationError(ValueError):
    """Сохранение не прошло валидацию схемы."""


class SaveSystem:
    """Система сохранения и загрузки игрового прогресса."""

    SAVE_VERSION = "1.1"

    # Версии, с которыми мы умеем работать на загрузке.
    # 1.0 — старый формат без enemies/pickups/game_stats/weapon_index.
    # 1.1 — текущий полноценный формат.
    SUPPORTED_VERSIONS = {"1.0", "1.1"}

    # Обязательные верхнеуровневые ключи в save_data
    _REQUIRED_TOP_KEYS = ("version", "player")
    # Обязательные ключи внутри player
    _REQUIRED_PLAYER_KEYS = ("x", "y", "health", "max_health")

    def __init__(self):
        self.save_version = self.SAVE_VERSION
        self.saves_dir = "saves"
        self.quicksave_file = "quicksave.json"

        # Создаём папку сохранений если её нет
        if not os.path.exists(self.saves_dir):
            os.makedirs(self.saves_dir)

    # --- Сохранение --------------------------------------------------------

    def save_game(self, player, world, game_stats=None, pickup_manager=None,
                  enemy_manager=None, filename=None):
        """Сохранение игрового состояния в JSON файл.

        Args:
            player: объект игрока
            world: объект мира (содержит enemy_manager, если enemy_manager
                   не передан явно)
            game_stats: GameStats (опционально, .to_dict() будет вызван)
            pickup_manager: PickupManager (опционально)
            enemy_manager: EnemyManager (опционально, по умолчанию берётся
                           из world.enemy_manager)
            filename: имя файла (по умолчанию quicksave.json)

        Returns:
            bool: True если сохранение успешно, False если ошибка.
        """
        try:
            if filename is None:
                filename = self.quicksave_file

            filepath = os.path.join(self.saves_dir, filename)

            # Авто-определение enemy_manager из world
            if enemy_manager is None and world is not None:
                enemy_manager = getattr(world, "enemy_manager", None)

            save_data = {
                "version": self.save_version,
                "timestamp": datetime.now().isoformat() + "Z",
                "player": self._serialize_player(player),
                "world": self._serialize_world(world),
                "enemies": (
                    enemy_manager.serialize()
                    if enemy_manager is not None and hasattr(enemy_manager, "serialize")
                    else None
                ),
                "pickups": (
                    pickup_manager.serialize()
                    if pickup_manager is not None and hasattr(pickup_manager, "serialize")
                    else []
                ),
                "game_stats": (
                    game_stats.to_dict()
                    if game_stats is not None and hasattr(game_stats, "to_dict")
                    else (game_stats if isinstance(game_stats, dict) else {})
                ),
                "inventory": {
                    "items": [],  # зарезервировано под будущий инвентарь
                    "gold": getattr(player, "coins", 0) if player else 0,
                },
            }

            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(save_data, f, indent=2, ensure_ascii=False)

            print(f"Игра сохранена: {filename}")
            return True

        except Exception as e:
            print(f"Ошибка сохранения: {e}")
            return False

    # --- Загрузка ----------------------------------------------------------

    def load_game(self, filename=None):
        """Загрузка игрового состояния из JSON файла.

        Возвращает dict или None при ошибке/повреждённом файле.
        """
        try:
            if filename is None:
                filename = self.quicksave_file

            filepath = os.path.join(self.saves_dir, filename)

            if not os.path.exists(filepath):
                print(f"Файл сохранения не найден: {filename}")
                return None

            with open(filepath, "r", encoding="utf-8") as f:
                save_data = json.load(f)

            # Валидация схемы — порченный файл не должен крашнуть игру
            try:
                self._validate_save_data(save_data)
            except SaveValidationError as ve:
                print(f"Сохранение повреждено: {ve}")
                return None

            version = save_data.get("version")
            if version not in self.SUPPORTED_VERSIONS:
                print(
                    f"Предупреждение: версия сохранения {version} "
                    f"не поддерживается ({sorted(self.SUPPORTED_VERSIONS)}). "
                    f"Попытка загрузить как best-effort."
                )

            print(f"Игра загружена: {filename}")
            return save_data

        except (json.JSONDecodeError, OSError) as e:
            print(f"Ошибка загрузки (повреждённый файл): {e}")
            return None
        except Exception as e:
            print(f"Ошибка загрузки: {e}")
            return None

    # --- Валидация ---------------------------------------------------------

    def _validate_save_data(self, data) -> None:
        """Минимальная валидация схемы сохранения.

        Кидает SaveValidationError при несоответствии. Не пытается быть
        строгой: проверяет только то, без чего apply_* гарантированно
        упадёт (тип игрока, обязательные числовые поля).
        """
        if not isinstance(data, dict):
            raise SaveValidationError("save_data должен быть объектом (dict)")
        for key in self._REQUIRED_TOP_KEYS:
            if key not in data:
                raise SaveValidationError(f"отсутствует ключ '{key}'")

        player = data.get("player")
        if not isinstance(player, dict):
            raise SaveValidationError("'player' должен быть объектом")
        for key in self._REQUIRED_PLAYER_KEYS:
            if key not in player:
                raise SaveValidationError(f"player: отсутствует '{key}'")
            try:
                float(player[key])
            except (TypeError, ValueError):
                raise SaveValidationError(
                    f"player['{key}'] должно быть числом, "
                    f"получено {type(player[key]).__name__}"
                )

        # Опциональные коллекции должны быть нужного типа, если присутствуют
        if "pickups" in data and data["pickups"] is not None:
            if not isinstance(data["pickups"], list):
                raise SaveValidationError("'pickups' должно быть списком")
        if "enemies" in data and data["enemies"] is not None:
            if not isinstance(data["enemies"], dict):
                raise SaveValidationError("'enemies' должно быть объектом")
        if "game_stats" in data and data["game_stats"] is not None:
            if not isinstance(data["game_stats"], dict):
                raise SaveValidationError("'game_stats' должно быть объектом")

    # --- Сериализация ------------------------------------------------------

    def _serialize_player(self, player):
        """Сериализация данных игрока."""
        return {
            "x": int(player.x),
            "y": int(player.y),
            "health": int(player.health),
            "max_health": int(player.max_health),
            "facing_direction": player.facing_direction,
            "level": int(player.level),
            "xp": int(player.xp),
            "coins": int(player.coins),
            "damage_bonus": int(player.damage_bonus),
            "current_weapon_index": int(getattr(player, "current_weapon_index", 0)),
            "iframe_timer": float(getattr(player.stats, "iframe_timer", 0.0)),
        }

    def _serialize_world(self, world):
        """Сериализация данных мира.

        В текущей single-world реализации мир статичен — сериализуем только
        идентификатор карты.
        """
        return {
            "current_map": "main_world",
            "discovered_areas": ["spawn"],
        }

    # --- Применение к объектам --------------------------------------------

    def apply_save_data_to_player(self, player, save_data):
        """Применение загруженных данных к объекту игрока."""
        try:
            player_data = save_data["player"]
            player.x = float(player_data["x"])
            player.y = float(player_data["y"])
            player.health = int(player_data["health"])
            player.max_health = int(player_data["max_health"])
            player.facing_direction = player_data.get("facing_direction", "down")

            # Прогрессия (backward compat — defaults для старых сейвов)
            stats = player.stats
            stats.level = int(player_data.get("level", 1))
            stats.xp = int(player_data.get("xp", 0))
            stats.coins = int(player_data.get("coins", 0))
            stats.damage_bonus = int(player_data.get("damage_bonus", 0))
            stats.iframe_timer = float(player_data.get("iframe_timer", 0.0))

            # Активное оружие — выставляем напрямую, без switch_weapon
            # (тот блокирует переключение во время attacking и при том же
            # индексе — не подходит для загрузки).
            weapon_index = int(player_data.get("current_weapon_index", 0))
            if hasattr(player, "current_weapon_index"):
                weapons = getattr(player, "weapons", [])
                if 0 <= weapon_index < len(weapons):
                    player.current_weapon_index = weapon_index

            # Обновляем rect игрока
            player.rect.x = int(player.x)
            player.rect.y = int(player.y)

            print(f"Позиция игрока восстановлена: ({player.x}, {player.y})")
            print(f"Здоровье игрока: {player.health}/{player.max_health}")

        except Exception as e:
            print(f"Ошибка применения данных игрока: {e}")

    def apply_save_data_to_world(self, world, save_data):
        """Применение загруженных данных к объекту мира.

        Сейчас мир статичен — фактически не делаем ничего, но оставляем
        точку расширения для будущих карт/областей.
        """
        try:
            world_data = save_data.get("world") or {}
            print(f"Мир восстановлен: {world_data.get('current_map', 'main_world')}")
        except Exception as e:
            print(f"Ошибка применения данных мира: {e}")

    def apply_save_data_to_enemies(self, enemy_manager, save_data):
        """Восстановить EnemyManager (живых врагов + target_counts)."""
        if enemy_manager is None:
            return
        enemies_data = save_data.get("enemies")
        if not enemies_data:
            return  # старый сейв без врагов — оставляем как есть
        try:
            enemy_manager.deserialize(enemies_data)
            print(f"Враги восстановлены: {len(enemy_manager.enemies)}")
        except Exception as e:
            print(f"Ошибка восстановления врагов: {e}")

    def apply_save_data_to_pickups(self, pickup_manager, save_data):
        """Восстановить лежащие на земле пикапы."""
        if pickup_manager is None:
            return
        pickups_data = save_data.get("pickups")
        if pickups_data is None:
            return
        try:
            pickup_manager.deserialize(pickups_data)
            print(f"Пикапы восстановлены: {pickup_manager.count()}")
        except Exception as e:
            print(f"Ошибка восстановления пикапов: {e}")

    def apply_save_data_to_game_stats(self, game_stats, save_data):
        """Восстановить GameStats."""
        if game_stats is None:
            return
        stats_data = save_data.get("game_stats")
        if not stats_data or not hasattr(game_stats, "apply_dict"):
            return
        try:
            game_stats.apply_dict(stats_data)
            print(
                f"Статистика восстановлена: kills={game_stats.enemies_killed}, "
                f"distance={game_stats.distance_traveled:.0f}, "
                f"play_time={game_stats.play_time:.1f}s"
            )
        except Exception as e:
            print(f"Ошибка восстановления статистики: {e}")

    # --- Утилиты -----------------------------------------------------------

    def quicksave_exists(self):
        """Проверка существования файла быстрого сохранения."""
        filepath = os.path.join(self.saves_dir, self.quicksave_file)
        return os.path.exists(filepath)
