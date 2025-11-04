from .exceptions import ConfigurationConflictError, InvalidLengthError, InvalidOrEmptyNameError
import random
import string

def generate(length=8, only_int=False, without_int=False, only_letters=False,
            upper_letters=False, lower_letters=False, special_symbols=False):
    """
    Генерирует случайную строку заданной длины.

    Args:
        length (int): длина строки (по умолчанию 8)
        only_int (bool): если True — только цифры (0–9)
        without_int (bool): если True — без цифр (только буквы a–z, A–Z)
        only_letters (bool): если True — только буквы (a–z, A–Z)
        upper_letters (bool): если True — только заглавные буквы (A–Z)
        lower_letters (bool): если True — только строчные буквы (a–z)
        special_symbols (bool): если True — включает специальные символы (!@#$%^&*()_+-=[]{}|;:,.<>?)

    Returns:
        str: сгенерированная случайная строка

    Raises:
        ConfigurationConflictError: конфликт параметров
        InvalidLengthError: длина не является положительным целым числом
    """
    # Проверка длины
    if not isinstance(length, int):
        raise InvalidLengthError(length, "Длина должна быть целым числом.")
    if length <= 0:
        raise InvalidLengthError(length)

    # Список параметров, задающих «тип символов»
    char_type_params = [
        ('only_int', only_int),
        ('without_int', without_int),
        ('only_letters', only_letters),
        ('upper_letters', upper_letters),
        ('lower_letters', lower_letters),
        ('special_symbols', special_symbols)
    ]

    # Считаем активные параметры
    active = [name for name, value in char_type_params if value]
    if len(active) > 1:
        raise ConfigurationConflictError(
            f"Нельзя одновременно использовать: {', '.join(active)}. "
            "Выберите только один параметр для определения набора символов."
        )

    # Определяем набор символов
    if only_int:
        charset = string.digits
    elif without_int:
        charset = string.ascii_letters
    elif only_letters:
        charset = string.ascii_letters
    elif upper_letters:
        charset = string.ascii_uppercase  # A–Z
    elif lower_letters:
        charset = string.ascii_lowercase  # a–z
    elif special_symbols:
        # Определяем набор специальных символов
        special_chars = "!@#$%^&*()_+-=[]{}|;:,.<>?"
        charset = string.ascii_letters + string.digits + special_chars
    else:
        charset = string.ascii_letters + string.digits  # буквы + цифры

    return ''.join(random.choice(charset) for _ in range(length))

def generate_with_name(name, length=8, only_int=False, without_int=False,
                      only_letters=False, upper_letters=False,
                      lower_letters=False, special_symbols=False):
    """
    Генерирует случайную строку с заданным стартовым именем.

    Args:
        name (str): стартовое имя пароля
        length (int): общая длина итоговой строки (по умолчанию 8)
        only_int (bool): если True — только цифры (0–9)
        without_int (bool): если True — без цифр (только буквы a–z, A–Z)
        only_letters (bool): если True — только буквы (a–z, A–Z)
        upper_letters (bool): если True — только заглавные буквы (A–Z)
        lower_letters (bool): если True — только строчные буквы (a–z)
        special_symbols (bool): если True — включает специальные символы

    Returns:
        str: сгенерированная строка, начинающаяся с name

    Raises:
        InvalidOrEmptyNameError: имя пустое или некорректного типа
        ConfigurationConflictError: конфликт параметров
        InvalidLengthError: длина некорректна
    """
    # Проверка имени
    if not isinstance(name, str):
        raise InvalidOrEmptyNameError(name, "Имя должно быть строкой.")
    if len(name) == 0:
        raise InvalidOrEmptyNameError(name, "Имя не может быть пустым.")

    # Проверяем, что общая длина не меньше длины имени
    if length < len(name):
        raise InvalidLengthError(
            length,
            f"Общая длина ({length}) не может быть меньше длины имени ({len(name)})."
        )

    # Генерируем оставшуюся часть строки
    remaining_length = length - len(name)
    if remaining_length == 0:
        return name

    # Используем основную функцию generate для генерации оставшейся части
    remaining_part = generate(
        length=remaining_length,
        only_int=only_int,
        without_int=without_int,
        only_letters=only_letters,
        upper_letters=upper_letters,
        lower_letters=lower_letters,
        special_symbols=special_symbols
    )
    return name + remaining_part