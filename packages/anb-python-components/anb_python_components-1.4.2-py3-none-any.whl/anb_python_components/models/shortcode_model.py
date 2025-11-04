from typing import Callable

class ShortCodeModel:
    """
    Модель добавления шорткода.
    """
    
    def __init__ (
            self, short_code: str | None = None, on_set: Callable | None = None,
            on_unset: Callable | None = None, on_validate: Callable | None = None
            ):
        """
        Конструктор модели.

        :param short_code: Буква, символ или последовательность символов, которая будет использоваться для шорткода.
                           Если не указана, то будет использована пустая строка.
        :type short_code: str | None
        :param on_set: Обработчик действия шорткода при обработке текста, когда шорткод включен.
                      Функция должна принимать два аргумента: content (str) и params (dict).
        :type on_set: Callable | None
        :param on_unset: Обработчик действия шорткода при обработке текста, когда шорткод отключен.
                        Аналогично OnSet.
        :type on_unset: Callable | None
        :param on_validate: Обработчик действия шорткода при валидации самого шорткода.
                           Функционал тот же, что и у OnSet и OnUnSet.
        :type on_validate: Callable | None
        """
        self.shortcode: str = short_code or ''
        self.on_set: Callable | None = on_set
        self.on_unset: Callable | None = on_unset
        self.on_validate: Callable | None = on_validate