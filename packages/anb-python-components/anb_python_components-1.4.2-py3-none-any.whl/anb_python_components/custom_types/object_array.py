# anb_python_components/custom_types/object_array.py
from __future__ import annotations

import copy
from functools import cmp_to_key, reduce
from typing import Any, Callable, get_args, get_type_hints

from anb_python_components.enums.type_copy_strategy import TypeCopyStrategy
from anb_python_components.extensions.type_extension import TypeExtension

class ObjectArray[T]:
    """
    Класс для хранения массива объектов.
    """
    
    # Добавление слотов для хранения массива
    __slots__ = ['__container']
    
    def __init__ (self, array: list[T] | None = None, copy_strategy: TypeCopyStrategy = TypeCopyStrategy.AUTO):
        """
        Инициализация массива объектов.
        
        :param array: Список объектов или None.
        :type array: list[T] | None
        """
        # Если массив не задан
        if array is None:
            # - то создаем пустой массив
            self.__container: list[T] = []
        
        # Если массив задан, то присваиваем его согласно стратегии копирования
        match copy_strategy:
            # - если копировать не нужно
            case TypeCopyStrategy.IGNORE:
                # -- то просто присваиваем его
                self.__container: list[T] = array
            
            # - если это примитивный тип
            case TypeCopyStrategy.COPY:
                # -- то копируем его
                self.__container: list[T] = array.copy()
            # - если это сложный тип
            case TypeCopyStrategy.DEEP_COPY:
                # -- то глубоко копируем его
                self.__container: list[T] = copy.deepcopy(array)
            # - если стратегия - автоматический выбор
            case TypeCopyStrategy.AUTO:
                # -- получаем тип аргумента T
                t_type = get_args(get_type_hints(self.__class__).get('T'))
                
                # -- анализируем его
                if TypeExtension.is_immutable_type(t_type):
                    # --- если тип T - примитивный, то просто копируем его
                    self.__container: list[T] = array.copy()
                else:
                    # --- иначе глубоко копируем его
                    self.__container: list[T] = copy.deepcopy(array)
    
    def __iter__ (self):
        """
        Итератор.
        :return: Итератор.
        :rtype: Iterator[T]
        """
        return iter(self.__container)
    
    def __getitem__ (self, key: int) -> T | None:
        """
        Доступ к атрибутам по ключу.
       :param key: Ключ атрибута.
        :type key: int
        :return: Значение атрибута или None, если атрибут не найден.
        :rtype: T | None
        """
        # Если ключ отрицательный или больше или равен длине массива
        if key < 0 or key >= len(self.__container):
            # - то возвращаем None
            return None
        
        # Возвращаем значение
        return self.__container[key]
    
    def __setitem__ (self, key: int, value: T) -> None:
        """
        Установить значение атрибута.
        :param key: Ключ атрибута.
        :type key: int
        :param value: Значение атрибута.
        :type value: T
        :return: None
        """
        self.__container[key] = value
    
    def __contains__ (self, item: T) -> bool:
        """
        Проверка наличия элемента в массиве.
        :param item: Проверяемый элемент.
        :type item: T
        :return: True, если элемент найден, False, если элемент не найден.
        """
        return self.is_exists(lambda elem: elem == item)
    
    def __len__ (self) -> int:
        """
        Количество атрибутов.
        :return: Количество атрибутов.
        :rtype: int
       """
        return self.count()
    
    @staticmethod
    def default_compare () -> Callable[[T, T], bool]:
        """
        Статический метод для получения функции сравнения по умолчанию.
        :return: Функция сравнения по умолчанию.
        :rtype: Callable[[T, T], bool]
        """
        return lambda x, y: x == y
    
    ### Специальные методы ###
    def clear (self) -> None:
        """
        Очистка массива.
        """
        self.__container.clear()
    
    def add (self, value: T) -> None:
        """
        Добавление значения в массив.
        :param value: Значение.
        :type value: T
        """
        # Если значения нет в массиве
        if value not in self.__container:
            # - то добавляем
            self.__container.append(value)
    
    def add_range (self, values: list[T] | ObjectArray[T]) -> None:
        """
        Добавление диапазона значений в массив.
        :param values: Значения, которые нужно добавить. Можно передавать массив или объект класса ObjectArray.
        :type values: list[T] | ObjectArray[T]
        """
        # Если передан массив, то не изменяем его, а если передан объект класса ObjectArray, то конвертируем его в массив объектов
        object_array = values.to_array() if isinstance(values, ObjectArray) else values
        
        # Если значения есть
        if len(object_array) > 0:
            # - то добавляем их
            self.__container += object_array
    
    def to_array (self) -> list[T]:
        """
        Получение массива.
        :return: Массив.
        :rtype: list[T]
        """
        # Если массив не пустой
        if len(self.__container) > 0:
            # - то возвращаем его
            return self.__container
        else:
            # - иначе возвращаем пустой массив
            return []
    
    ### Поиск и сортировка ###
    def find (self, value: Any, compare: Callable[[T, Any], bool] = default_compare()) -> T | None:
        """
        Поиск значения в массиве.
        :param value: Значение, которое нужно найти.
        :type value: Any
        :param compare: Функция сравнения.
        :type value: Callable[[T, Any], bool]
        :return: Найденное значение или None.
        :rtype: T | None
        """
        
        # Для каждого элемента массива
        for item in self.__container:
            # - выполняем сравнение по функции сравнения
            if compare(item, value):
                # -- и возвращаем элемент, если он найден
                return item
        
        # Если мы сюда дошли, значить объект не найден - возвращаем None
        return None
    
    def sort (self, object_property: str, descending: bool = False) -> None:
        """
        Сортирует контейнер объектов по указанному атрибуту.
    
        :param object_property: Имя атрибута объекта для сортировки
        :type object_property: str
        :param descending: если True — сортировка по убыванию
        :type descending: bool
        """
        # Копируем список (чтобы не сортировать исходный напрямую)
        result: list[T] = self.__container[:]
        
        # Сортируем по указанному атрибуту
        result.sort(
                key = lambda obj: getattr(obj, object_property),
                reverse = descending
                )
        
        # Присваиваем результат обратно в контейнер
        self.__container = result
    
    def sort_callback (
            self,
            predicate: Callable[[T], Any],
            descending: bool = False
            ) -> None:
        """
        Сортирует контейнер, используя пользовательскую функцию-предикат.
    
        :param predicate: Функция, принимающая объект и возвращающая значение свойства для сравнения.
        :type predicate: Callable[[T], Any]
        :param descending: если True — сортировка по убыванию.
        :type descending: bool
        """
        # Копируем список (чтобы не сортировать исходный напрямую)
        result: list[T] = self.__container[:]
        
        # Определяем компаратор
        def comparator (a: Any, b: Any) -> int:
            """
            Функция сравнения двух значений.
            :param a: Значение 1.
            :type a: Any
            :param b: Значение 2.
            :type b: Any
            :return: -1, если значение 1 меньше значения 2, 1, если значение 1 больше значения 2 и 0, если значения равны.
            :rtype: int
            """
            # - получаем значения для сравнения по переданной функции
            # -- значение 1
            val_a = predicate(a)
            # -- значение 2
            val_b = predicate(b)
            
            # - если значение 1 меньше значения 2
            if val_a < val_b:
                # -- то возвращаем -1
                return -1
            # - если значение 1 больше значения 2
            elif val_a > val_b:
                # -- то возвращаем 1
                return 1
            # - если значения равны
            else:
                # -- то возвращаем 0
                return 0
        
        # Если нужен обратный порядок
        if descending:
            # - то создаем компаратор, который меняет порядок
            def reversed_comparator (a: Any, b: Any) -> int:
                """
                Функция для создания компаратора, который меняет порядок.
                :param a: Значение 1.
                :type a: Any
                :param b: Значение 2.
                :type b: Any
                :return: -1, если значение 1 больше значения 2, 1, если значение 1 меньше значения 2 и 0, если значения равны.
                :rtype: int
                """
                return -comparator(a, b)
            
            # - сортируем по компаратору, который меняет порядок
            result.sort(key = cmp_to_key(reversed_comparator))
        else:
            # - иначе сортируем по компаратору по умолчанию
            result.sort(key = cmp_to_key(comparator))
        
        # Присваиваем результат обратно в контейнер
        self.__container = result
    
    ### Операторы LINQ ###
    ### 1. Операторы проверки существования и количества ###
    def count (self, where: Callable[[T], bool] = None) -> int:
        """
        Количество элементов в массиве.
        :param where: Функция выборки элементов. Вместо неё можно передать None, тогда будут возвращено общее
            количество объектов в массиве. По умолчанию, None.
        :type where: Callable[[T], bool] | None
        :return: Количество элементов.
        :rtype: int
        """
        # Если массив пустой
        if not self.__container:
            # - то возвращаем 0
            return 0
        
        # Если функция выборки не задана
        if where is None:
            # - то возвращаем длину массива
            return len(self.__container)
        
        # Задаём счетчик
        result = 0
        
        # Для каждого элемента массива
        for item in self.__container:
            # - выполняем выборку
            if where(item):
                # -- и если элемент удовлетворяет условию, то увеличиваем счетчик на 1
                result += 1
            else:
                # -- иначе переходим к следующему элементу
                continue
        
        # Возвращаем результат
        return result
    
    def is_exists (self, where: Callable[[T], bool]) -> bool:
        """
        Проверка наличия элементов в массиве.
        :param where: Функция выборки элементов.
        :type where: Callable[[T], bool]
        :return: True, если есть хотя бы один элемент, удовлетворяющий условию, иначе False.
        :rtype: bool
        """
        return self.count(where) > 0
    
    ### 2. Операторы выбора минимума и максимума ###
    def min (self, by_value: Callable[[T], Any]) -> T | None:
        """
        Минимальное значение.
        :param by_value: Функция, возвращающая значение для сравнения.
        :type by_value: Callable[[T], Any]
        :return: Минимальное значение или None.
        :rtype: T | None
        """
        # Если массив пустой
        if not self.__container:
            # - то возвращаем None
            return None
        
        # Возвращаем минимальное значение
        return reduce(
                lambda current, value: value if current is None or by_value(value) < by_value(current) else current,
                self.__container,
                None
                )
    
    def max (self, by_value: Callable[[T], Any]) -> T | None:
        """
        Максимальное значение.
        :param by_value: Функция, возвращающая значение для сравнения.
        :type by_value: Callable[[T], Any]
        :return: Максимальное значение или None.
        :rtype: T | None
        """
        # Если массив пустой
        if not self.__container:
            # - то возвращаем None
            return None
        
        # Возвращаем максимальное значение
        return reduce(
                lambda current, value: value if current is None or by_value(value) > by_value(current) else current,
                self.__container,
                None
                )
    
    ### 3. Операторы выбора элементов ###
    def get_rows (self, where: Callable[[T], bool] = None) -> ObjectArray[T]:
        """
        Выделяет из массива объектов объекты, удовлетворяющие условию.
        :param where: Функция выборки объектов. Вместо неё можно передать None, тогда будут возвращены все объекты.
            По умолчанию, None.
        :type where: Callable[[T], bool] | None
        :return: Массив объектов, удовлетворяющих условию.
        :rtype: ObjectArray[T]
        """
        # Если функция выборки не задана или массив пустой
        if where is None or not self.__container:
            # - то просто копируем массив
            return ObjectArray(self.__container)
        
        # Выбираем элементы, удовлетворяющие условию
        items = [item for item in self.__container if where(item)]
        
        # И создаём новый массив
        return ObjectArray(items)
    
    def get_row (self, where: Callable[[T], bool] = None) -> T | None:
        """
        Выбирает из массива объектов объект, удовлетворяющий условию.
        :param where: Функция выборки объектов. Вместо неё можно передать None, тогда будет возвращён первый объект.
            По умолчанию, None.
        :type where: Callable[[T], bool] | None
        :return: Объект, удовлетворяющий условию или None, если объект не найден.
        :rtype: T | None
        """
        # Если массив пустой
        if not self.__container:
            # - то возвращаем None
            return None
        
        # Если функция выборки не задана
        if where is None:
            # - то возвращаем первый элемент
            return self.__container[0]
        
        # Выбираем элементы, удовлетворяющие условию
        rows: ObjectArray[T] = self.get_rows(where)
        
        # Если элементов не найдено
        if len(rows) == 0:
            # - то возвращаем None
            return None
        
        # Возвращаем первый найденный элемент
        return rows[0]
    
    def where (self, where: Callable[[T], bool]) -> T | ObjectArray[T] | None:
        """
        Выбирает из массива объектов объекты, удовлетворяющие условию.
        :param where: Функция выборки объектов.
        :type where: Callable[[T], bool]
        :return: Массив объектов, удовлетворяющих условию, если объектов несколько, или объект, удовлетворяющий условию,
            если объект единственный, или None, если объект не найден.
        :rtype: T | ObjectArray[T] | None
        """
        # Получаем массив объектов, удовлетворяющих условию
        rows: ObjectArray[T] = self.get_rows(where)
        
        # Если массив пустой
        if len(rows) == 0:
            # - то возвращаем None
            return None
        # - если массив содержит только один элемент
        elif len(rows) == 1:
            # -- то возвращаем его
            return rows[0]
        # - если массив содержит более одного элемента
        else:
            # -- то возвращаем массив
            return rows
    
    def get_column (self, column_name: str, where: Callable[[T], bool] = None) -> ObjectArray[Any]:
        """
        Выбирает из массива объектов значения свойства.
        :param column_name: Имя свойства.
        :type column_name: str
        :param where: Функция выборки объектов. По умолчанию, None. Если None, то возвращаются свойства всех объектов.
        :type where: Callable[[T], bool] | None
        :return: Массив значений свойства.
        :rtype: ObjectArray[Any]
        """
        return self.get_column_callback(
                lambda item: getattr(item, column_name, None) if hasattr(item, column_name) else None,
                where
                )
    
    def get_column_callback (self, column: Callable[[T], Any], where: Callable[[T], bool] = None) -> ObjectArray[Any]:
        """
        Выбирает из массива объектов значения свойства.
        :param column: Функция получения значения свойства.
        :type column: Callable[[T], Any]
        :param where: Функция выборки объектов. По умолчанию, None. Если None, то возвращаются все объекты.
        :type where: Callable[[T], bool] | None
        :return: Массив значений свойства.
        :rtype: ObjectArray[Any]
        """
        # Получаем массив объектов, удовлетворяющих условию
        items = [column(item) for item in self.__container if where is None or where(item)]
        
        # Возвращаем массив
        return ObjectArray(items)
    
    def get_value (self, column: str, where: Callable[[T], bool] = None) -> Any | None:
        """
        Получение значение единичного поля. Если полей по выборке будет больше одного, то вернёт первое из них.
        :param column: Требуемый столбец.
        :type column: str
        :param where:Условие выборки., которое проверяет, подходит элемент или нет. Можно передать None, тогда будет
            пробран весь массив. По умолчанию, None.
        :type where: Callable[[T], bool] | None
        :return: Значение поля или None, если поля нет.
        :rtype: Any | None
        """
        # Получаю колонку
        result = self.get_column(column, where)
        
        # Если колонка пустая
        if len(result) == 0:
            # -- возвращаю None
            return None
        
        # Возвращаю первый элемент колонки
        return result[0]
    
    ### 4. Операторы удаления ###
    def delete (self, where: Callable[[T], bool] = None) -> bool:
        """
        Удаление элементов из массива.
        :param where: Функция выборки элементов. По умолчанию, None. Если None, то будут удалены все элементы.
        :type where: Callable[[T], bool] | None
        :return: True, если удаление успешно, False, если удаление не удалось.
        :rtype: bool
        """
        # Если функция выборки не задана
        if where is None:
            # - то очищаем массив
            self.clear()
            # - и прерываем функцию
            return True
        
        # Получаем индексы элементов для удаления
        remove_indices: list[int] = [i for i, item in enumerate(self.__container) if where(item)]
        
        # Если индексы элементов для удаления не найдены
        if not remove_indices:
            # - то прерываем функцию
            return False
        
        # Проходим по индексам элементов для удаления в обратном порядке
        for i in reversed(remove_indices):
            # - удаляем элемент
            del self.__container[i]
        
        # Возвращаем True
        return True
    
    ### 5. Операторы получения ###
    def first (self, default: T | None = None) -> T | None:
        """
        Безопасное получение первого элемента массива.
        :param default: Значение по умолчанию или None. По умолчанию, None.
        :return: Первый элемент массива, значение по умолчанию или None.
        :rtype: T | None
        """
        return self.__container[0] if self.__container else default
    
    def last (self, default: T | None = None) -> T | None:
        """
        Безопасное получение последнего элемента массива.
        :param default: Значение по умолчанию или None. По умолчанию, None.
        :return: Последний элемент массива, значение по умолчанию или None.
        :rtype: T | None
        """
        return self.__container[-1] if self.__container else default
    
    def skip (self, count: int) -> ObjectArray[T]:
        """
        Пропускает первые count элементов в массиве.
        :param count: Количество пропускаемых элементов.
        :type count: int
        :return: Массив без первых count элементов.
        :rtype: ObjectArray[T]
        """
        # Если требуется пропустить отрицательное количество элементов или нуль
        if count <= 0:
            # - то просто копируем массив
            return ObjectArray(self.__container)
        
        # Если требуется пропустить больше элементов, чем есть в массиве
        if count >= len(self.__container):
            # - то возвращаем пустой массив
            return ObjectArray()
        
        # Возвращаем массив без первых count элементов
        return ObjectArray(self.__container[count:], TypeCopyStrategy.IGNORE)
    
    def take (self, count: int) -> ObjectArray[T]:
        """
        Возвращает первые count элементов в массиве.
        :param count: Количество возвращаемых элементов.
        :type count: int
        :return: Массив с первыми count элементами.
        :rtype: ObjectArray[T]
        """
        # Если требуется взять отрицательное количество элементов или нуль
        if count <= 0:
            # - то возвращаем пустой массив
            return ObjectArray()
        
        # Если требуется взять больше элементов, чем есть в массиве
        if count >= len(self.__container):
            # - то просто копируем массив
            return ObjectArray(self.__container)
        
        # Возвращаем массив с первыми count элементами
        return ObjectArray(self.__container[:count], TypeCopyStrategy.IGNORE)
    
    def skip_and_take (self, skip_count: int, take_count: int) -> ObjectArray[T]:
        """
        Пропускает skip_count элементов и возвращает take_count элементов.
        :param skip_count: Количество пропускаемых элементов.
        :type skip_count: int
        :param take_count: Количество возвращаемых элементов.
        :type skip_count: int
        :return: Массив с пропущенными skip_count элементами и take_count элементами.
        :rtype: ObjectArray[T]
        """
        # Если требуется пропустить отрицательное количество элементов
        if skip_count < 0:
            # - то приравниваем skip_count к нулю
            skip_count = 0
        
        # Если требуется взять отрицательное количество элементов
        if take_count <= 0:
            # - то возвращаем пустой массив
            return ObjectArray([])
        
        # Задаём начало
        start = skip_count
        # Задаём конец - начало + количество элементов, которые нужно взять
        end = start + take_count
        
        # Если начало больше длины массива
        if start >= len(self.__container):
            # - то возвращаем пустой массив
            return ObjectArray([])
        
        # Если конец больше длины массива
        if end >= len(self.__container):
            # - то обрезаем массив до конца
            end = len(self.__container)
        
        # Делаем обрезку массива по началу и концу и возвращаем результат
        return ObjectArray(self.__container[start:end], TypeCopyStrategy.IGNORE)