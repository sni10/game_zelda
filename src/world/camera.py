"""
Camera - система следования камеры за целью.

Single Responsibility: вычислять смещение камеры (camera_x, camera_y)
относительно цели с учётом границ мира. Чистая математика, без pygame.
"""


class Camera:
    """Камера, следующая за целью с ограничением по границам мира."""

    def __init__(self):
        self.x: float = 0
        self.y: float = 0

    def follow(
        self,
        target_x: float,
        target_y: float,
        screen_width: int,
        screen_height: int,
        world_width: int,
        world_height: int,
    ) -> None:
        """Центрировать камеру на цели, ограничив границами мира.

        Args:
            target_x, target_y: центр цели (обычно центр игрока).
            screen_width, screen_height: размер видимой области.
            world_width, world_height: размер мира в пикселях.
        """
        # Центрируем камеру на цели
        self.x = target_x - screen_width // 2
        self.y = target_y - screen_height // 2

        # Ограничиваем камеру границами мира
        self.x = max(0, min(self.x, world_width - screen_width))
        self.y = max(0, min(self.y, world_height - screen_height))

