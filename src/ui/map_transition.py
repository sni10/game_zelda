"""
MapTransition - затухание экрана в чёрный при смене карты между миссиями.

Три фазы: OUT (чёрный прямоугольник alpha 0->255 поверх текущей сцены) ->
в момент полной черноты одноразовый callback подменяет Game.world/player на
следующую миссию -> IN (alpha 255->0). Сам класс ничего не знает про World/
Mission - только таймер и alpha, подмена происходит в переданном callback.
"""

import pygame

from src.core.config_loader import get_color


class MapTransition:
    """Самостоятельный маленький таймер-оверлей. Использование:

    map_transition.start(on_swap=callback)
    # каждый кадр, пока map_transition.active:
    map_transition.update(dt)
    map_transition.draw(screen)  # поверх обычной отрисовки сцены
    """

    FADE_MS = 500  # длительность одной фазы (полное затухание/появление)

    def __init__(self):
        self._phase: str = None  # None | 'out' | 'in'
        self._elapsed_ms = 0.0
        self._on_swap = None
        self._swapped = False

    @property
    def active(self) -> bool:
        return self._phase is not None

    def start(self, on_swap) -> None:
        """Запустить переход. on_swap() вызывается один раз в момент полной
        черноты - там и нужно подменить Game.world/player на новую миссию."""
        self._phase = "out"
        self._elapsed_ms = 0.0
        self._on_swap = on_swap
        self._swapped = False

    def update(self, dt: float) -> None:
        if self._phase is None:
            return
        self._elapsed_ms += dt * 1000.0
        if self._phase == "out" and self._elapsed_ms >= self.FADE_MS:
            if not self._swapped and self._on_swap is not None:
                self._on_swap()
                self._swapped = True
            self._phase = "in"
            self._elapsed_ms = 0.0
        elif self._phase == "in" and self._elapsed_ms >= self.FADE_MS:
            self._phase = None
            self._on_swap = None

    def draw(self, screen) -> None:
        if self._phase is None:
            return
        t = min(1.0, self._elapsed_ms / self.FADE_MS)
        alpha = int(255 * t) if self._phase == "out" else int(255 * (1 - t))
        if alpha <= 0:
            return
        overlay = pygame.Surface(screen.get_size())
        overlay.set_alpha(alpha)
        overlay.fill(get_color("BLACK"))
        screen.blit(overlay, (0, 0))
