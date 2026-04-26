"""
SessionLogger - отдельный класс для записи логов одной игровой сессии.

Single Responsibility: создание лог-файла, запись сообщений с уровнями,
закрытие при завершении. Не знает про pygame и игровой цикл.
"""
import os
import datetime


class SessionLogger:
    """Логгер игровой сессии. Каждый запуск пишет в отдельный файл logs/game_session_*.log."""

    IMPORTANT_LEVELS = ("IMPORTANT", "ERROR", "WARNING")

    def __init__(self, log_dir: str = "logs"):
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)

        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        self.filename = os.path.join(log_dir, f"game_session_{timestamp}.log")
        self._file = open(self.filename, 'w', encoding='utf-8')
        self._file.write(
            f"=== ИГРОВАЯ СЕССИЯ НАЧАЛАСЬ: "
            f"{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ===\n\n"
        )
        self._file.flush()
        print(f"📝 Логи записываются в: {self.filename}")

    def log(self, message: str, level: str = "INFO") -> None:
        """Записать сообщение в лог. Важные уровни также печатаются в консоль."""
        timestamp = datetime.datetime.now().strftime("%H:%M:%S.%f")[:-3]
        log_entry = f"[{timestamp}] [{level}] {message}\n"

        self._file.write(log_entry)
        self._file.flush()

        if level in self.IMPORTANT_LEVELS:
            print(message)

    def close(self) -> None:
        """Закрыть файл логов. Безопасно вызывать повторно."""
        if self._file and not self._file.closed:
            self._file.close()

