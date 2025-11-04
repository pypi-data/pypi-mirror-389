class PassgenError(Exception):
    """Базовый класс исключений для passgen3."""
    pass

class ConfigurationConflictError(PassgenError):
    """Возникает при конфликте параметров генерации."""
    def __init__(self, message=None):
        default_msg = (
            "Конфликт параметров генерации: невозможно одновременно "
            "установить взаимоисключающие опции."
        )
        super().__init__(message or default_msg)

class InvalidLengthError(PassgenError):
    """Возникает, если длина строки некорректна (≤ 0 или не целое число)."""
    def __init__(self, length, message=None):
        default_msg = f"Некорректная длина строки: {length}. Длина должна быть целым положительным числом."
        super().__init__(message or default_msg)
        self.length = length