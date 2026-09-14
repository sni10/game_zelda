"""
Экраны кампании миссий (см. CAMPAIGN_PLAN.md, issue #68):

- MissionCompleteScreen  - конец промежуточной миссии (босс убит, есть
  следующая миссия). Снимок статистики ЭТОЙ миссии + кнопка "Следующая миссия".
- CampaignCompleteScreen - конец последней миссии кампании. Суммарная
  статистика по всем пройденным миссиям + кнопка "Выйти в меню".

Оба класса следуют уже принятому в проекте паттерну экрана (см. GameOverScreen/
SaveLoadMenu): handle_input(event) обрабатывает и клавиатуру, и мышь,
draw(screen) рисует поверх последнего кадра игры полупрозрачным фоном.
"""

import pygame

from src.core.config_loader import get_color


def _format_stat_lines(snapshot: dict) -> list:
    """Отформатировать снимок статистики (GameStats.to_dict()-подобный
    numeric-дельта/сумма dict, см. src/systems/mission.py) в строки для
    отображения. Показываем не все 11 полей - только то, что игроку
    действительно интересно видеть после миссии."""
    minutes = int(snapshot.get("play_time", 0) // 60)
    seconds = int(snapshot.get("play_time", 0) % 60)
    return [
        f"Время: {minutes:02d}:{seconds:02d}",
        f"Убито врагов: {int(snapshot.get('enemies_killed', 0))}",
        f"Урон нанесён: {int(snapshot.get('damage_dealt', 0))}",
        f"Урон получен: {int(snapshot.get('damage_taken', 0))}",
        f"Собрано предметов: {int(snapshot.get('items_collected', 0))}",
        f"Пройдено: {snapshot.get('distance_traveled', 0):.0f} м",
    ]


class _BaseStatsScreen:
    """Общая механика: заголовок + список статов + одна кнопка по центру
    снизу, кликабельная мышью и активируемая Enter/Space."""

    ACTION = None  # переопределяется в наследниках

    def __init__(self, screen_width, screen_height, title, snapshot, button_label):
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.title = title
        self.snapshot = snapshot
        self.button_label = button_label

        self.title_font = pygame.font.Font(None, 64)
        self.text_font = pygame.font.Font(None, 32)
        self.button_font = pygame.font.Font(None, 40)

        self.button_rect = pygame.Rect(0, 0, 340, 60)
        self.button_rect.center = (screen_width // 2, screen_height - 120)
        self.button_hovered = False

    def handle_input(self, event):
        if event.type == pygame.MOUSEMOTION:
            self.button_hovered = self.button_rect.collidepoint(event.pos)
            return None
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.button_rect.collidepoint(event.pos):
                return self.ACTION
            return None
        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_RETURN, pygame.K_SPACE):
                return self.ACTION
        return None

    def draw(self, screen):
        overlay = pygame.Surface((self.screen_width, self.screen_height))
        overlay.set_alpha(220)
        overlay.fill(get_color("BLACK"))
        screen.blit(overlay, (0, 0))

        cx = self.screen_width // 2
        title_surf = self.title_font.render(self.title, True, get_color("YELLOW"))
        screen.blit(title_surf, title_surf.get_rect(center=(cx, 110)))

        y = 190
        for line in _format_stat_lines(self.snapshot):
            surf = self.text_font.render(line, True, get_color("WHITE"))
            screen.blit(surf, surf.get_rect(center=(cx, y)))
            y += 40

        color = get_color("YELLOW") if self.button_hovered else get_color("GRAY")
        pygame.draw.rect(screen, color, self.button_rect, border_radius=6)
        pygame.draw.rect(
            screen, get_color("WHITE"), self.button_rect, 2, border_radius=6
        )
        btn_surf = self.button_font.render(self.button_label, True, get_color("BLACK"))
        screen.blit(btn_surf, btn_surf.get_rect(center=self.button_rect.center))


class MissionCompleteScreen(_BaseStatsScreen):
    """Показывается сразу после смерти босса, если это НЕ последняя миссия
    кампании. Enter/Space/клик по кнопке -> Game запускает MapTransition
    на следующую карту (см. Game._start_mission_transition)."""

    ACTION = "NEXT"

    def __init__(self, screen_width, screen_height, mission_title, snapshot):
        super().__init__(
            screen_width,
            screen_height,
            title=f"✅ {mission_title} пройдена",
            snapshot=snapshot,
            button_label="Следующая миссия",
        )


class CampaignCompleteScreen(_BaseStatsScreen):
    """Показывается после смерти босса ПОСЛЕДНЕЙ миссии кампании - итоговая
    статистика (сумма снимков всех пройденных миссий, см. Campaign.total_snapshot)."""

    ACTION = "MENU"

    def __init__(self, screen_width, screen_height, snapshot):
        super().__init__(
            screen_width,
            screen_height,
            title="🏆 Кампания пройдена!",
            snapshot=snapshot,
            button_label="Выйти в меню",
        )
