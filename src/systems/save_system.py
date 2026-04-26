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

    # Лимит ручных слотов (см. v0.3.2 в BACKLOG.md)
    MANUAL_SLOT_LIMIT = 10
    # Подпапка для ручных слотов, чтобы они не смешивались с quicksave/autosave
    MANUAL_SUBDIR = "manual"
    # Имя файла слота: slot_01.json ... slot_10.json
    _SLOT_FILENAME_FMT = "slot_{:02d}.json"

    # Автосохранения (v0.3.3) — отдельная подпапка, ротация по mtime.
    AUTOSAVE_SUBDIR = "autosave"
    AUTOSAVE_DEFAULT_LIMIT = 3
    _AUTOSAVE_FILENAME_FMT = "autosave_{:02d}.json"

    def __init__(self):
        self.save_version = self.SAVE_VERSION
        self.saves_dir = "saves"
        self.quicksave_file = "quicksave.json"
        self.manual_dir = os.path.join(self.saves_dir, self.MANUAL_SUBDIR)
        self.autosave_dir = os.path.join(self.saves_dir, self.AUTOSAVE_SUBDIR)

        # Создаём папки сохранений если их нет
        if not os.path.exists(self.saves_dir):
            os.makedirs(self.saves_dir)
        if not os.path.exists(self.manual_dir):
            os.makedirs(self.manual_dir)
        if not os.path.exists(self.autosave_dir):
            os.makedirs(self.autosave_dir)

    # --- Сохранение --------------------------------------------------------

    def save_game(self, player, world, game_stats=None, pickup_manager=None,
                  enemy_manager=None, filename=None):
        """Сохранение игрового состояния в quicksave-файл (или filename).

        Manual-слоты сохраняются через :meth:`save_to_slot` — это сделано
        специально, чтобы quicksave (`saves/quicksave.json`) и слоты
        (`saves/manual/slot_NN.json`) физически не пересекались.
        """
        try:
            if filename is None:
                filename = self.quicksave_file
            filepath = os.path.join(self.saves_dir, filename)
            return self._write_save(
                filepath, player, world, game_stats, pickup_manager, enemy_manager
            )
        except Exception as e:
            print(f"Ошибка сохранения: {e}")
            return False

    def _write_save(self, filepath, player, world, game_stats=None,
                    pickup_manager=None, enemy_manager=None,
                    extra_data=None):
        """Низкоуровневая запись save_data в указанный путь.

        ``extra_data`` — опциональный dict, который добавляется в save_data
        верхним уровнем (используется автосейвом для поля ``autosave_reason``).
        """
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

        if extra_data:
            for k, v in extra_data.items():
                save_data[k] = v

        # Папка должна существовать (для произвольных filepath)
        parent = os.path.dirname(filepath)
        if parent and not os.path.exists(parent):
            os.makedirs(parent)

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(save_data, f, indent=2, ensure_ascii=False)

        print(f"Игра сохранена: {os.path.basename(filepath)}")
        return True

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

    # --- Manual-слоты (v0.3.2) --------------------------------------------

    def _slot_filepath(self, slot_id: int) -> str:
        """Полный путь к файлу slot_id (1..MANUAL_SLOT_LIMIT)."""
        return os.path.join(
            self.manual_dir, self._SLOT_FILENAME_FMT.format(int(slot_id))
        )

    def slot_exists(self, slot_id: int) -> bool:
        return os.path.exists(self._slot_filepath(slot_id))

    def save_to_slot(self, slot_id: int, player, world, game_stats=None,
                     pickup_manager=None, enemy_manager=None) -> bool:
        """Сохранить игру в ручной слот ``slot_id`` (1..10).

        Перезаписывает слот без подтверждения — подтверждение должно
        делаться на уровне UI.
        """
        if not (1 <= int(slot_id) <= self.MANUAL_SLOT_LIMIT):
            print(
                f"Ошибка: slot_id {slot_id} вне диапазона "
                f"1..{self.MANUAL_SLOT_LIMIT}"
            )
            return False
        try:
            return self._write_save(
                self._slot_filepath(slot_id),
                player, world, game_stats, pickup_manager, enemy_manager,
            )
        except Exception as e:
            print(f"Ошибка сохранения в слот {slot_id}: {e}")
            return False

    def load_from_slot(self, slot_id: int):
        """Загрузить save_data из manual-слота. None при ошибке."""
        filepath = self._slot_filepath(slot_id)
        if not os.path.exists(filepath):
            print(f"Слот {slot_id} пуст")
            return None
        return self._load_from_path(filepath)

    def delete_slot(self, slot_id: int) -> bool:
        """Удалить файл manual-слота."""
        filepath = self._slot_filepath(slot_id)
        if not os.path.exists(filepath):
            return False
        try:
            os.remove(filepath)
            print(f"Слот {slot_id} удалён")
            return True
        except OSError as e:
            print(f"Ошибка удаления слота {slot_id}: {e}")
            return False

    def list_manual_saves(self):
        """Список метаданных всех заполненных manual-слотов.

        Возвращает list[dict] вида::

            {"slot_id": 1, "timestamp": "...", "level": 3,
             "play_time": 124.5, "hp": 80, "max_hp": 100, "filename": "slot_01.json"}

        Пустые слоты в список не попадают. Сортировка по slot_id ASC.
        """
        result = []
        for slot_id in range(1, self.MANUAL_SLOT_LIMIT + 1):
            filepath = self._slot_filepath(slot_id)
            if not os.path.exists(filepath):
                continue
            meta = self._read_metadata(filepath)
            meta["slot_id"] = slot_id
            meta["filename"] = os.path.basename(filepath)
            result.append(meta)
        return result

    def get_quicksave_metadata(self):
        """Метаданные quicksave (или None если quicksave нет)."""
        filepath = os.path.join(self.saves_dir, self.quicksave_file)
        if not os.path.exists(filepath):
            return None
        meta = self._read_metadata(filepath)
        meta["filename"] = self.quicksave_file
        return meta

    def get_free_slot(self):
        """Первый свободный slot_id (1..10) или None если все заняты."""
        for slot_id in range(1, self.MANUAL_SLOT_LIMIT + 1):
            if not self.slot_exists(slot_id):
                return slot_id
        return None

    def _load_from_path(self, filepath: str):
        """Прочитать и провалидировать save_data из произвольного пути."""
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                save_data = json.load(f)
            try:
                self._validate_save_data(save_data)
            except SaveValidationError as ve:
                print(f"Сохранение повреждено: {ve}")
                return None
            version = save_data.get("version")
            if version not in self.SUPPORTED_VERSIONS:
                print(
                    f"Предупреждение: версия сохранения {version} "
                    f"не поддерживается ({sorted(self.SUPPORTED_VERSIONS)})."
                )
            print(f"Игра загружена: {os.path.basename(filepath)}")
            return save_data
        except (json.JSONDecodeError, OSError) as e:
            print(f"Ошибка загрузки (повреждённый файл): {e}")
            return None
        except Exception as e:
            print(f"Ошибка загрузки: {e}")
            return None

    def _read_metadata(self, filepath: str) -> dict:
        """Прочитать только метаданные сейва (без полного применения).

        Возвращает dict с ключами: timestamp, level, play_time, hp, max_hp,
        valid (bool). Не кидает исключения — повреждённые файлы получают
        valid=False и плейсхолдеры.
        """
        meta = {
            "timestamp": "",
            "level": 0,
            "play_time": 0.0,
            "hp": 0,
            "max_hp": 0,
            "valid": False,
        }
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
            meta["timestamp"] = data.get("timestamp", "") or ""
            player = data.get("player") or {}
            meta["level"] = int(player.get("level", 0) or 0)
            meta["hp"] = int(player.get("health", 0) or 0)
            meta["max_hp"] = int(player.get("max_health", 0) or 0)
            stats = data.get("game_stats") or {}
            meta["play_time"] = float(stats.get("play_time", 0.0) or 0.0)
            # Дополнительные поля для автосейвов
            meta["reason"] = data.get("autosave_reason", "") or ""
            meta["valid"] = True
        except (OSError, json.JSONDecodeError, ValueError, TypeError):
            # Повреждённый файл — отдаём плейсхолдер с valid=False
            pass
        return meta

    # --- Автосейвы (v0.3.3) -----------------------------------------------

    def _autosave_filepath(self, slot_id: int) -> str:
        """Полный путь к файлу автосейв-слота."""
        return os.path.join(
            self.autosave_dir, self._AUTOSAVE_FILENAME_FMT.format(int(slot_id))
        )

    def autosave(self, player, world, game_stats=None, pickup_manager=None,
                 enemy_manager=None, reason: str = "periodic",
                 limit: int = None) -> bool:
        """Записать автосейв с ротацией.

        Алгоритм слота:
        1. Если есть свободный slot_id (1..limit) — пишем туда.
        2. Иначе — затираем самый старый по mtime.

        ``reason`` сохраняется в save_data как ``autosave_reason`` и потом
        отображается в UI («periodic», «level_up», ...).
        """
        if limit is None:
            limit = self.AUTOSAVE_DEFAULT_LIMIT
        try:
            limit = max(1, int(limit))
        except (TypeError, ValueError):
            limit = self.AUTOSAVE_DEFAULT_LIMIT

        try:
            slot_id = self._pick_autosave_slot(limit)
            filepath = self._autosave_filepath(slot_id)
            ok = self._write_save(
                filepath, player, world, game_stats,
                pickup_manager, enemy_manager,
                extra_data={"autosave_reason": str(reason)},
            )
            if ok:
                # Ротация: если лимит уменьшили в конфиге — почистим хвост.
                self._enforce_autosave_limit(limit)
            return ok
        except Exception as e:
            print(f"Ошибка автосейва: {e}")
            return False

    def _pick_autosave_slot(self, limit: int) -> int:
        """Найти slot_id 1..limit для записи автосейва.

        Сначала первый свободный, иначе — самый старый по mtime.
        """
        for slot_id in range(1, limit + 1):
            if not os.path.exists(self._autosave_filepath(slot_id)):
                return slot_id
        # Все заняты — берём самый старый
        oldest_slot = 1
        oldest_mtime = None
        for slot_id in range(1, limit + 1):
            mtime = os.path.getmtime(self._autosave_filepath(slot_id))
            if oldest_mtime is None or mtime < oldest_mtime:
                oldest_mtime = mtime
                oldest_slot = slot_id
        return oldest_slot

    def _enforce_autosave_limit(self, limit: int) -> None:
        """Удалить автосейвы со slot_id > limit (если лимит уменьшился)."""
        try:
            for filename in os.listdir(self.autosave_dir):
                if not filename.startswith("autosave_") \
                        or not filename.endswith(".json"):
                    continue
                try:
                    slot_id = int(filename[len("autosave_"):-len(".json")])
                except ValueError:
                    continue
                if slot_id > limit:
                    os.remove(os.path.join(self.autosave_dir, filename))
        except OSError:
            pass

    def list_autosaves(self):
        """Список метаданных автосейвов (новый сверху).

        Возвращает list[dict] вида::

            {"slot_id": 1, "timestamp": "...", "level": 3, "play_time": ...,
             "hp": 80, "max_hp": 100, "reason": "level_up",
             "filename": "autosave_01.json", "mtime": 1234567.0, "valid": True}
        """
        result = []
        if not os.path.isdir(self.autosave_dir):
            return result
        for filename in os.listdir(self.autosave_dir):
            if not filename.startswith("autosave_") \
                    or not filename.endswith(".json"):
                continue
            try:
                slot_id = int(filename[len("autosave_"):-len(".json")])
            except ValueError:
                continue
            filepath = os.path.join(self.autosave_dir, filename)
            meta = self._read_metadata(filepath)
            meta["slot_id"] = slot_id
            meta["filename"] = filename
            try:
                meta["mtime"] = os.path.getmtime(filepath)
            except OSError:
                meta["mtime"] = 0.0
            result.append(meta)
        # Свежие сверху
        result.sort(key=lambda m: m.get("mtime", 0.0), reverse=True)
        return result

    def load_from_autosave(self, slot_id: int):
        """Загрузить save_data из автосейв-слота. None при ошибке."""
        filepath = self._autosave_filepath(slot_id)
        if not os.path.exists(filepath):
            print(f"Автосейв {slot_id} не найден")
            return None
        return self._load_from_path(filepath)

    def delete_autosave(self, slot_id: int) -> bool:
        """Удалить файл автосейв-слота."""
        filepath = self._autosave_filepath(slot_id)
        if not os.path.exists(filepath):
            return False
        try:
            os.remove(filepath)
            print(f"Автосейв {slot_id} удалён")
            return True
        except OSError as e:
            print(f"Ошибка удаления автосейва {slot_id}: {e}")
            return False

    def get_latest_autosave_metadata(self):
        """Метаданные самого свежего автосейва (или None)."""
        items = self.list_autosaves()
        return items[0] if items else None
