"""
SaveLoadMenu — единое меню слотов сохранений (v0.3.2).

Один класс работает в двух режимах:

* ``mode="load"`` — выбор сейва для загрузки. В списке: quicksave (если есть)
  отдельной строкой сверху + все непустые manual-слоты.
* ``mode="save"`` — выбор manual-слота для сохранения. В списке: все 10 слотов
  (пустые показываются как «-- Пустой слот --»). Quicksave **не** показывается.

Управление:
    ↑/↓     — навигация
    Enter   — выбрать (load/overwrite save)
    Del     — удалить (только manual-слот, в любом режиме); quicksave удалить нельзя
    Esc     — назад в главное меню (или в игру, если открыт по F6)

Меню само управляет модальными подтверждениями (перезапись/удаление):
    Y — да, N/Esc — нет.

Класс **stateful**: вызывайте :meth:`refresh` после изменений на диске
(вход в меню, после сохранения/удаления).

API ↔ Game:
    handle_input(event) → action dict | None
        {"type": "load_quicksave"}                   — загрузить quicksave
        {"type": "load_slot", "slot_id": N}          — загрузить manual-слот N
        {"type": "save_slot", "slot_id": N}          — (под)твердили сохранение в N
        {"type": "delete_slot", "slot_id": N}        — подтверждили удаление N
        {"type": "back"}                             — Esc, выход из меню
"""
import pygame
from datetime import datetime

from src.core.config_loader import get_config, get_color


# Особое значение selected_index для строки quicksave (в load-режиме)
QUICKSAVE_INDEX = -1


def _format_timestamp(iso_ts: str) -> str:
    """ISO-таймстамп → человекочитаемая дата-время."""
    if not iso_ts:
        return "—"
    ts = iso_ts.rstrip("Z")
    try:
        dt = datetime.fromisoformat(ts)
        return dt.strftime("%Y-%m-%d %H:%M:%S")
    except ValueError:
        return iso_ts


def _format_playtime(seconds: float) -> str:
    """N секунд → 'HH:MM:SS' или 'MM:SS'."""
    s = int(max(0.0, seconds))
    h, rem = divmod(s, 3600)
    m, sec = divmod(rem, 60)
    if h > 0:
        return f"{h:02d}:{m:02d}:{sec:02d}"
    return f"{m:02d}:{sec:02d}"


class SaveLoadMenu:
    """Меню слотов: load/save с подтверждениями."""

    MODE_LOAD = "load"
    MODE_SAVE = "save"

    def __init__(self, save_system, mode: str = MODE_LOAD):
        if mode not in (self.MODE_LOAD, self.MODE_SAVE):
            raise ValueError(f"Unknown mode: {mode}")
        self.save_system = save_system
        self.mode = mode

        self.font_title = pygame.font.Font(None, 56)
        self.font_item = pygame.font.Font(None, 32)
        self.font_meta = pygame.font.Font(None, 22)
        self.font_help = pygame.font.Font(None, 22)
        self.font_modal = pygame.font.Font(None, 36)

        # Состояние списка
        self.selected_index = 0
        # Активная модалка: None | "overwrite" | "delete"
        self.modal = None
        self.modal_slot_id = None

        # entries — список словарей, представляющих строки списка.
        # Для load: optional quicksave + только заполненные manual-слоты.
        # Для save: все 10 manual-слотов (включая пустые).
        self.entries: list[dict] = []
        self.refresh()

    # --- Состояние ---------------------------------------------------------

    def set_mode(self, mode: str) -> None:
        """Сменить режим (load↔save). Сбрасывает курсор и обновляет список."""
        if mode != self.mode:
            self.mode = mode
        self.selected_index = 0
        self.modal = None
        self.modal_slot_id = None
        self.refresh()

    def refresh(self) -> None:
        """Перечитать состояние слотов с диска."""
        entries: list[dict] = []
        if self.mode == self.MODE_LOAD:
            qs_meta = self.save_system.get_quicksave_metadata()
            if qs_meta is not None:
                entries.append({
                    "kind": "quicksave",
                    "slot_id": None,
                    "label": "🕒 Быстрое сохранение (F5)",
                    "meta": qs_meta,
                })
            for meta in self.save_system.list_manual_saves():
                entries.append({
                    "kind": "manual",
                    "slot_id": meta["slot_id"],
                    "label": f"Слот {meta['slot_id']:02d}",
                    "meta": meta,
                })
        else:  # MODE_SAVE
            existing = {m["slot_id"]: m
                        for m in self.save_system.list_manual_saves()}
            for slot_id in range(1, self.save_system.MANUAL_SLOT_LIMIT + 1):
                meta = existing.get(slot_id)
                entries.append({
                    "kind": "manual",
                    "slot_id": slot_id,
                    "label": f"Слот {slot_id:02d}",
                    "meta": meta,  # None если пустой
                })

        self.entries = entries
        if self.selected_index >= len(self.entries):
            self.selected_index = max(0, len(self.entries) - 1)

    # --- Ввод --------------------------------------------------------------

    def handle_input(self, event):
        """Обработать KEYDOWN, вернуть action dict или None."""
        if event.type != pygame.KEYDOWN:
            return None

        # Модалка перехватывает ввод
        if self.modal is not None:
            return self._handle_modal_input(event)

        if event.key == pygame.K_ESCAPE:
            return {"type": "back"}

        if not self.entries:
            # Нет элементов — единственное доступное действие это back
            return None

        if event.key == pygame.K_UP:
            self.selected_index = (self.selected_index - 1) % len(self.entries)
            return None
        if event.key == pygame.K_DOWN:
            self.selected_index = (self.selected_index + 1) % len(self.entries)
            return None

        entry = self.entries[self.selected_index]

        if event.key == pygame.K_RETURN:
            return self._handle_enter(entry)
        if event.key == pygame.K_DELETE:
            return self._handle_delete(entry)
        return None

    def _handle_enter(self, entry):
        if self.mode == self.MODE_LOAD:
            if entry["kind"] == "quicksave":
                return {"type": "load_quicksave"}
            return {"type": "load_slot", "slot_id": entry["slot_id"]}
        # save mode
        if entry["meta"] is None:
            # пустой слот — сохраняем без подтверждения
            return {"type": "save_slot", "slot_id": entry["slot_id"]}
        # занятый слот — модалка перезаписи
        self.modal = "overwrite"
        self.modal_slot_id = entry["slot_id"]
        return None

    def _handle_delete(self, entry):
        # Quicksave удалять нельзя (см. BACKLOG.md v0.3.2 п.8)
        if entry["kind"] != "manual":
            return None
        if entry["meta"] is None:
            # пустой слот — нечего удалять
            return None
        self.modal = "delete"
        self.modal_slot_id = entry["slot_id"]
        return None

    def _handle_modal_input(self, event):
        if event.key in (pygame.K_y,):
            modal, slot_id = self.modal, self.modal_slot_id
            self.modal = None
            self.modal_slot_id = None
            if modal == "overwrite":
                return {"type": "save_slot", "slot_id": slot_id}
            if modal == "delete":
                return {"type": "delete_slot", "slot_id": slot_id}
        elif event.key in (pygame.K_n, pygame.K_ESCAPE):
            self.modal = None
            self.modal_slot_id = None
        return None

    # --- Отрисовка ---------------------------------------------------------

    def draw(self, screen):
        screen.fill(get_color('BLACK'))
        width = get_config('WIDTH')
        height = get_config('HEIGHT')

        # Заголовок
        title = ("ЗАГРУЗИТЬ ИГРУ" if self.mode == self.MODE_LOAD
                 else "СОХРАНИТЬ ИГРУ")
        title_surf = self.font_title.render(title, True, get_color('WHITE'))
        screen.blit(title_surf, title_surf.get_rect(center=(width // 2, 60)))

        # Список
        if not self.entries:
            empty = self.font_item.render(
                "Сохранений нет", True, get_color('GRAY')
            )
            screen.blit(empty, empty.get_rect(center=(width // 2, height // 2)))
        else:
            self._draw_entries(screen, width, height)

        # Подсказки
        self._draw_help(screen, width, height)

        # Модалка
        if self.modal == "overwrite":
            self._draw_modal(
                screen, width, height,
                title="Перезаписать сохранение?",
                detail=self._slot_detail(self.modal_slot_id),
                hint="Y — да, N/Esc — нет",
            )
        elif self.modal == "delete":
            self._draw_modal(
                screen, width, height,
                title="Удалить сохранение?",
                detail=self._slot_detail(self.modal_slot_id),
                hint="Y — да, N/Esc — нет",
            )

    def _draw_entries(self, screen, width, height):
        list_top = 130
        row_h = 60
        # Если вдруг список длиннее экрана — простой scroll вокруг курсора
        max_rows = max(1, (height - list_top - 80) // row_h)
        start = 0
        if len(self.entries) > max_rows:
            start = max(
                0,
                min(self.selected_index - max_rows // 2,
                    len(self.entries) - max_rows),
            )
        end = min(len(self.entries), start + max_rows)

        for visible_i, i in enumerate(range(start, end)):
            entry = self.entries[i]
            y = list_top + visible_i * row_h

            selected = i == self.selected_index
            color = (get_color('YELLOW') if selected
                     else get_color('WHITE'))
            if selected:
                rect = pygame.Rect(width // 2 - 320, y - 5, 640, row_h - 10)
                pygame.draw.rect(screen, get_color('DARK_GRAY'), rect, 2)

            label_surf = self.font_item.render(entry["label"], True, color)
            screen.blit(label_surf, (width // 2 - 300, y))

            # Метаданные / "пустой"
            meta = entry["meta"]
            if meta is None:
                meta_text = "-- Пустой слот --"
                meta_color = get_color('GRAY')
            elif not meta.get("valid", True):
                meta_text = "[повреждён]"
                meta_color = get_color('RED') if 'RED' in dir() else (200, 80, 80)
                meta_color = (200, 80, 80)
            else:
                meta_text = (
                    f"{_format_timestamp(meta.get('timestamp', ''))}  "
                    f"|  Lv.{meta.get('level', 0)}  "
                    f"|  HP {meta.get('hp', 0)}/{meta.get('max_hp', 0)}  "
                    f"|  ⏱ {_format_playtime(meta.get('play_time', 0.0))}"
                )
                meta_color = get_color('GRAY')
            meta_surf = self.font_meta.render(meta_text, True, meta_color)
            screen.blit(meta_surf, (width // 2 - 300, y + 28))

    def _draw_help(self, screen, width, height):
        if self.mode == self.MODE_LOAD:
            lines = [
                "↑↓ — Навигация    Enter — Загрузить    Del — Удалить    Esc — Назад",
            ]
        else:
            lines = [
                "↑↓ — Навигация    Enter — Сохранить    Del — Удалить    Esc — Назад",
            ]
        y = height - 40
        for line in lines:
            surf = self.font_help.render(line, True, get_color('GRAY'))
            screen.blit(surf, surf.get_rect(center=(width // 2, y)))
            y += 22

    def _draw_modal(self, screen, width, height, title, detail, hint):
        # Затемняем фон
        overlay = pygame.Surface((width, height), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        screen.blit(overlay, (0, 0))

        box_w, box_h = 600, 200
        box = pygame.Rect((width - box_w) // 2, (height - box_h) // 2,
                          box_w, box_h)
        pygame.draw.rect(screen, get_color('DARK_GRAY'), box)
        pygame.draw.rect(screen, get_color('WHITE'), box, 2)

        title_surf = self.font_modal.render(title, True, get_color('WHITE'))
        screen.blit(title_surf,
                    title_surf.get_rect(center=(width // 2, box.y + 50)))

        detail_surf = self.font_meta.render(detail, True, get_color('GRAY'))
        screen.blit(detail_surf,
                    detail_surf.get_rect(center=(width // 2, box.y + 100)))

        hint_surf = self.font_help.render(hint, True, get_color('YELLOW'))
        screen.blit(hint_surf,
                    hint_surf.get_rect(center=(width // 2, box.y + 150)))

    def _slot_detail(self, slot_id) -> str:
        if slot_id is None:
            return ""
        for e in self.entries:
            if e.get("slot_id") == slot_id and e["meta"] is not None:
                m = e["meta"]
                return (
                    f"Слот {slot_id:02d} — "
                    f"{_format_timestamp(m.get('timestamp', ''))}, "
                    f"Lv.{m.get('level', 0)}, "
                    f"⏱ {_format_playtime(m.get('play_time', 0.0))}"
                )
        return f"Слот {slot_id:02d}"
