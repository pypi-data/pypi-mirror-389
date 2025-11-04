# anb_python_components/custom_types/guid.py
from __future__ import annotations

import re
import secrets

from anb_python_components.exceptions.wrong_type_exception import WrongTypeException

class GUID:
    """
    Тип GUID.
    """
    
    # Константа пустого GUID
    EMPTY: str = "00000000-0000-0000-0000-000000000000"
    
    def __init__ (self, guid: str | GUID = EMPTY):
        """
        Инициализация расширения.
        :param guid: str | GUID - Передаваемый GUID
        """
        # Проверка типа аргумента guid
        if not isinstance(guid, str) or not isinstance(guid, GUID):
            # - если аргумент не является строкой или экземпляром GUID, то генерируем исключение
            raise WrongTypeException("Неверный тип аргумента!", "GUID", str(type(guid)), "guid")
        
        # Проверка GUID на валидность
        if not GUID.validate(guid):
            # и если GUID невалидный, то генерируем исключение
            raise WrongTypeException("Неверный формат GUID!", "GUID", str(type(guid)), "guid")
        
        # Инициализируем приватный атрибут __value (текстовое представление хранящегося GUID)
        self.__value = str(guid)
    
    def __str__ (self):
        """
        Переопределение метода __str__.
        :return: Текстовое представление GUID.
        """
        return self.__value if self.__value else self.EMPTY
    
    def __eq__ (self, other):
        """
        Переопределение метода __eq__.
        :param other: Объект для сравнения.
        :return: True, если GUID равны, иначе False.
        """
        
        # Если аргумент не является экземпляром GUID
        if not isinstance(other, GUID):
            # - генерируем исключение
            raise WrongTypeException("Неверный тип аргумента!", "GUID", type(other), "other")
        
        # Преобразование второго аргумента в строку
        other_str = str(other)
        
        # Сравниваем строки
        return self.__value == other_str
    
    @staticmethod
    def generate () -> GUID:
        """
        Генерирует уникальный идентификатор GUID согласно стандарту RFC 4122.
        """
        # Генерация отдельных компонентов GUID
        time_low = secrets.randbits(32) & 0xffffffff
        time_mid = secrets.randbits(16) & 0xffff
        time_hi_and_version = ((secrets.randbits(12) << 4) | 0x4000) & 0xffff
        clock_seq_hi_and_reserved = ((secrets.randbits(14) << 2) | 0x8000) & 0xffff
        node_id = secrets.randbits(48) & 0xffffffffffff
        
        # Объединение компонентов в единый GUID
        guid_parts = [
                time_low >> 16, time_low & 0xffff,
                time_mid,
                time_hi_and_version,
                clock_seq_hi_and_reserved,
                node_id >> 32, (node_id >> 16) & 0xffff, node_id & 0xffff
                ]
        
        # Форматируем компоненты в виде строки GUID
        guid_str = "-".join(
                [
                        "%08x" % guid_parts[0],
                        "%04x" % guid_parts[1],
                        "%04x" % guid_parts[2],
                        "%04x" % guid_parts[3],
                        ("%04x%04x%04x" % tuple(guid_parts[4:])),
                        ]
                )
        
        # Возвращаем экземпляр GUID
        return GUID(guid_str)
    
    @staticmethod
    def is_equal (guid1: str | GUID, guid2: str | GUID) -> bool:
        
        # Если guid1 не является GUID или строкой
        if not isinstance(guid1, GUID) or not isinstance(guid1, str):
            # - генерируем исключение
            raise WrongTypeException("Неверный тип аргумента!", "GUID|str", var_name = "guid1")
        
        # Если guid2 не является GUID или строкой
        if not isinstance(guid2, GUID) or not isinstance(guid2, str):
            # - генерируем исключение
            raise WrongTypeException("Неверный тип аргумента!", "GUID|str", var_name = "guid2")
        
        # Если guid1 является строкой
        if not isinstance(guid1, GUID):
            # - преобразуем её в GUID
            guid1 = GUID(guid1)
        
        # Если guid2 является строкой
        if not isinstance(guid2, GUID):
            # - преобразуем её в GUID
            guid2 = GUID(guid2)
        
        # Сравниваем GUID
        return guid1 == guid2
    
    @staticmethod
    def validate (guid: str | GUID) -> bool:
        """
        Проверка GUID на валидность.
        :param guid: GUID для проверки.
        :return: True, если GUID валидный, иначе False.
        """
        # Если guid не является строкой, то преобразуем его в неё
        guid = guid if isinstance(guid, str) else str(guid)
        
        # Регулярное выражение для проверки формата GUID
        pattern = r'^[0-9A-Fa-f]{8}-([0-9A-Fa-f]{4}-){3}[0-9A-Fa-f]{12}$'
        
        # Проверка на соответствие формату
        return bool(re.fullmatch(pattern, guid))
    
    @staticmethod
    def is_invalid_or_empty (guid: str | GUID) -> bool:
        """
        Проверка GUID на валидность и не пустоту.
        :param guid: Класс или строка GUID для проверки.
        :return: True, если GUID не валидный или пустой, иначе False.
        """
        # Если guid не является строкой, то преобразуем его в неё
        guid = guid if isinstance(guid, str) else str(guid)
        
        # Проверяем GUID
        return not GUID.validate(guid) or guid.lower() == GUID.EMPTY.lower()
    
    @classmethod
    def parse (cls, guid_string: str, empty_if_not_valid: bool = True) -> GUID:
        """
        Парсинг GUID из строки.
        :param guid_string: Строка GUID.
        :param empty_if_not_valid: Если True, то возвращается пустой GUID, если GUID недействителен.
        """
        
        # Проверяем строку на соответствие формату GUID
        if cls.validate(guid_string):
            # - если GUID действителен, возвращаем экземпляр GUID
            return GUID(guid_string)
        
        # Если же GUID недействителен и запрещено выбрасывать исключение
        if empty_if_not_valid:
            # -- то возвращаем пустой GUID
            return GUID(GUID.EMPTY)
        else:
            # -- иначе выбрасываем исключение
            raise WrongTypeException('Предан неверный GUID / Wrong GUID.')