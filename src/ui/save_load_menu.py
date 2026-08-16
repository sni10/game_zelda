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
    Мышь    — наведение подсвечивает строку/кнопку, клик по строке выделяет её,
              клик по кнопке ("Загрузить"/"Сохранить", "Удалить", "Назад")
              выполняет то же действие, что и соответствующая клавиша

Меню само управляет модальными подтверждениями (перезапись/удаление):
    Y / кнопка "Да" — да, N/Esc / кнопка "Нет" — нет.

Класс **stateful**: вызывайте :meth:`refresh` после изменений на диске
(вход в меню, после сохранения/удаления).

API ↔ Game:
    handle_input(event) → action dict | None
        {"type": "load_quicksave"}                   — загрузить quicksave
        {"type": "load_slot", "slot_id": N}          — загрузить manual-слот N
        {"type": "save_slot", "slot_id": N}          — (под)твердили сохранение в N
        {"type": "delete_slot", "slot_id": N}        — подтверждили удаление N
        {"type": "load_autosave", "slot_id": N}      — загрузить автосейв N (v0.3.3)
        {"type": "delete_autosave", "slot_id": N}    — подтверждили удаление автосейва (v0.3.3)
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
        self.font_button = pygame.font.Font(None, 28)
        self.font_modal = pygame.font.Font(None, 36)

        # Состояние списка
        self.selected_index = 0
        # Активная модалка: None | "overwrite" | "delete"
        self.modal = None
        self.modal_slot_id = None
        # Какого вида запись подтверждаем (manual / autosave) —
        # нужно для маршрутизации delete-action.
        self.modal_kind = None

        # Наведение мыши (только визуальная подсветка) — что сейчас под курсором.
        # _hover_kind: None | "entry" | "button" | "modal_button"
        self._hover_kind = None
        self._hover_index = None   # индекс строки списка (kind == "entry")
        self._hover_name = None    # имя кнопки (kind == "button"/"modal_button")

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
        self.modal_kind = None
        self._clear_hover()
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
            # Автосейвы (v0.3.3) — после quicksave, до manual-слотов.
            list_autosaves = getattr(
                self.save_system, "list_autosaves", None
            )
            if callable(list_autosaves):
                for meta in list_autosaves():
                    reason = meta.get("reason") or ""
                    label = f"🕐 Автосохранение #{meta['slot_id']:02d}"
                    if reason:
                        label = f"{label}  ({reason})"
                    entries.append({
                        "kind": "autosave",
                        "slot_id": meta["slot_id"],
                        "label": label,
                        "meta": meta,
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

    def _clear_hover(self) -> None:
        self._hover_kind = None
        self._hover_index = None
        self._hover_name = None

    # --- Ввод --------------------------------------------------------------

    def handle_input(self, event):
        """Обработать KEYDOWN/MOUSEMOTION/MOUSEBUTTONDOWN, вернуть action dict или None."""
        if event.type == pygame.KEYDOWN:
            return self._handle_keydown(event)
        if event.type == pygame.MOUSEMOTION:
            self._handle_mouse_motion(event.pos)
            return None
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            return self._handle_mouse_click(event.pos)
        return None

    def _handle_keydown(self, event):
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

    def _handle_mouse_motion(self, pos):
        self._clear_hover()
        width = get_config('WIDTH')
        height = get_config('HEIGHT')

        if self.modal is not None:
            for name, rect in self._modal_button_rects(width, height).items():
                if rect.collidepoint(pos):
                    self._hover_kind = "modal_button"
                    self._hover_name = name
                    return
            return

        for i, rect in self._entry_rects():
            if rect.collidepoint(pos):
                self._hover_kind = "entry"
                self._hover_index = i
                return

        for name, _label, rect in self._action_buttons():
            if rect.collidepoint(pos):
                self._hover_kind = "button"
                self._hover_name = name
                return

    def _handle_mouse_click(self, pos):
        width = get_config('WIDTH')
        height = get_config('HEIGHT')

        if self.modal is not None:
            for name, rect in self._modal_button_rects(width, height).items():
                if rect.collidepoint(pos):
                    return self._resolve_modal(confirm=(name == "yes"))
            return None

        # Клик по строке — только выделяет её (действие выполняется кнопкой).
        for i, rect in self._entry_rects():
            if rect.collidepoint(pos):
                self.selected_index = i
                return None

        for name, _label, rect in self._action_buttons():
            if rect.collidepoint(pos):
                return self._trigger_button(name)
        return None

    def _trigger_button(self, name):
        if name == "back":
            return {"type": "back"}
        if not self.entries:
            return None
        entry = self.entries[self.selected_index]
        if name == "primary":
            return self._handle_enter(entry)
        if name == "delete":
            return self._handle_delete(entry)
        return None

    def _handle_enter(self, entry):
        if self.mode == self.MODE_LOAD:
            if entry["kind"] == "quicksave":
                return {"type": "load_quicksave"}
            if entry["kind"] == "autosave":
                return {"type": "load_autosave", "slot_id": entry["slot_id"]}
            return {"type": "load_slot", "slot_id": entry["slot_id"]}
        # save mode
        if entry["meta"] is None:
            # пустой слот — сохраняем без подтверждения
            return {"type": "save_slot", "slot_id": entry["slot_id"]}
        # занятый слот — модалка перезаписи
        self.modal = "overwrite"
        self.modal_slot_id = entry["slot_id"]
        self.modal_kind = entry["kind"]
        return None

    def _handle_delete(self, entry):
        # Quicksave удалять нельзя (см. BACKLOG.md v0.3.2 п.8)
        if entry["kind"] not in ("manual", "autosave"):
            return None
        if entry["meta"] is None:
            # пустой слот — нечего удалять
            return None
        self.modal = "delete"
        self.modal_slot_id = entry["slot_id"]
        self.modal_kind = entry["kind"]
        return None

    def _handle_modal_input(self, event):
        if event.key == pygame.K_y:
            return self._resolve_modal(confirm=True)
        if event.key in (pygame.K_n, pygame.K_ESCAPE):
            return self._resolve_modal(confirm=False)
        return None

    def _resolve_modal(self, confirm: bool):
        modal, slot_id, kind = self.modal, self.modal_slot_id, self.modal_kind
        self.modal = None
        self.modal_slot_id = None
        self.modal_kind = None
        self._clear_hover()
        if not confirm:
            return None
        if modal == "overwrite":
            return {"type": "save_slot", "slot_id": slot_id}
        if modal == "delete":
            if kind == "autosave":
                return {"type": "delete_autosave", "slot_id": slot_id}
            return {"type": "delete_slot", "slot_id": slot_id}
        return None

    # --- Хит-тестинг мыши (геометрия должна совпадать с draw()) ------------

    def _visible_entries_window(self):
        """(list_top, row_h, start, end) — видимое окно строк списка."""
        list_top = 130
        row_h = 60
        height = get_config('HEIGHT')
        max_rows = max(1, (height - list_top - 80) // row_h)
        start = 0
        if len(self.entries) > max_rows:
            start = max(
                0,
                min(self.selected_index - max_rows // 2,
                    len(self.entries) - max_rows),
            )
        end = min(len(self.entries), start + max_rows)
        return list_top, row_h, start, end

    def _entry_rects(self):
        """[(entry_index, rect), ...] для видимых строк списка."""
        if not self.entries:
            return []
        width = get_config('WIDTH')
        list_top, row_h, start, end = self._visible_entries_window()
        rects = []
        for visible_i, i in enumerate(range(start, end)):
            y = list_top + visible_i * row_h
            rect = pygame.Rect(width // 2 - 320, y - 5, 640, row_h - 10)
            rects.append((i, rect))
        return rects

    def _action_buttons(self):
        """[(name, label, rect), ...] — кнопки действий внизу экрана."""
        width = get_config('WIDTH')
        height = get_config('HEIGHT')
        btn_w, btn_h, gap = 170, 44, 24
        total_w = btn_w * 3 + gap * 2
        x0 = width // 2 - total_w // 2
        y = height - 90

        primary_label = "Загрузить" if self.mode == self.MODE_LOAD else "Сохранить"
        return [
            ("primary", primary_label, pygame.Rect(x0, y, btn_w, btn_h)),
            ("delete", "Удалить", pygame.Rect(x0 + btn_w + gap, y, btn_w, btn_h)),
            ("back", "Назад", pygame.Rect(x0 + 2 * (btn_w + gap), y, btn_w, btn_h)),
        ]

    def _button_enabled(self, name):
        if name == "back":
            return True
        if not self.entries:
            return False
        entry = self.entries[self.selected_index]
        if name == "primary":
            return True
        if name == "delete":
            return entry["kind"] in ("manual", "autosave") and entry["meta"] is not None
        return True

    def _modal_button_rects(self, width, height):
        """{"yes": rect, "no": rect} — кнопки модалки подтверждения."""
        box_w, box_h = 600, 200
        box = pygame.Rect((width - box_w) // 2, (height - box_h) // 2,
                          box_w, box_h)
        btn_w, btn_h, gap = 120, 40, 30
        y = box.y + 130
        return {
            "yes": pygame.Rect(width // 2 - gap // 2 - btn_w, y, btn_w, btn_h),
            "no": pygame.Rect(width // 2 + gap // 2, y, btn_w, btn_h),
        }

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

        # Кнопки действий + подсказка по клавиатуре
        self._draw_action_buttons(screen, width, height)

        # Модалка
        if self.modal == "overwrite":
            self._draw_modal(
                screen, width, height,
                title="Перезаписать сохранение?",
                detail=self._slot_detail(self.modal_slot_id),
            )
        elif self.modal == "delete":
            self._draw_modal(
                screen, width, height,
                title="Удалить сохранение?",
                detail=self._slot_detail(self.modal_slot_id, self.modal_kind),
            )

    def _draw_entries(self, screen, width, height):
        for i, rect in self._entry_rects():
            entry = self.entries[i]
            y = rect.y + 5

            selected = i == self.selected_index
            hovered = self._hover_kind == "entry" and self._hover_index == i
            color = get_color('YELLOW') if selected else get_color('WHITE')
            if selected:
                pygame.draw.rect(screen, get_color('DARK_GRAY'), rect, 2)
            elif hovered:
                pygame.draw.rect(screen, get_color('DARK_GRAY'), rect, 1)

            label_surf = self.font_item.render(entry["label"], True, color)
            screen.blit(label_surf, (width // 2 - 300, y))

            # Метаданные / "пустой"
            meta = entry["meta"]
            if meta is None:
                meta_text = "-- Пустой слот --"
                meta_color = get_color('GRAY')
            elif not meta.get("valid", True):
                meta_text = "[повреждён]"
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

    def _draw_action_buttons(self, screen, width, height):
        for name, label, rect in self._action_buttons():
            enabled = self._button_enabled(name)
            hovered = self._hover_kind == "button" and self._hover_name == name

            if not enabled:
                color = get_color('GRAY')
            elif hovered:
                color = get_color('YELLOW')
            else:
                color = get_color('WHITE')

            pygame.draw.rect(screen, color, rect, 2)
            text = self.font_button.render(label, True, color)
            screen.blit(text, text.get_rect(center=rect.center))

        hint = self.font_help.render(
            "↑↓ — навигация    клик по строке — выделить", True, get_color('GRAY')
        )
        screen.blit(hint, hint.get_rect(center=(width // 2, height - 20)))

    def _draw_modal(self, screen, width, height, title, detail):
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

        for name, rect in self._modal_button_rects(width, height).items():
            hovered = self._hover_kind == "modal_button" and self._hover_name == name
            color = get_color('YELLOW') if hovered else get_color('WHITE')
            pygame.draw.rect(screen, color, rect, 2)
            label = "Да" if name == "yes" else "Нет"
            text = self.font_button.render(label, True, color)
            screen.blit(text, text.get_rect(center=rect.center))

    def _slot_detail(self, slot_id, kind=None) -> str:
        if slot_id is None:
            return ""
        for e in self.entries:
            if e.get("slot_id") != slot_id or e["meta"] is None:
                continue
            if kind is not None and e.get("kind") != kind:
                continue
            m = e["meta"]
            prefix = ("Автосейв" if e.get("kind") == "autosave"
                      else "Слот")
            return (
                f"{prefix} {slot_id:02d} — "
                f"{_format_timestamp(m.get('timestamp', ''))}, "
                f"Lv.{m.get('level', 0)}, "
                f"⏱ {_format_playtime(m.get('play_time', 0.0))}"
            )
        return f"Слот {slot_id:02d}"
