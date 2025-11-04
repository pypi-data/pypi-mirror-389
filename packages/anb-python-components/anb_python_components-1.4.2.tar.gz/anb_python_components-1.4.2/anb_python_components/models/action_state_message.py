# anb_python_components/models/action_state_message.py
from anb_python_components.enums.message_type import MessageType

class ActionStateMessage:
    """
    Модель сообщения о состояния действия.
    """
    
    def __init__ (
            self, message_type: MessageType = MessageType.INFO, message: str = "", flags: dict[str, bool] | None = None
            ):
        """
        Конструктор.
        :param message_type: Тип сообщения (по умолчанию, INFO).
        :param message: Текст сообщения (по умолчанию, пустая строка).
        :param flags: Флаги сообщения (по умолчанию, пустой словарь).
        """
        self.message_type: MessageType = message_type
        self.message: str = message
        self.flags: dict[str, bool] = flags if flags is not None else []
    
    def __str__ (self):
        """
        Переопределение метода __str__.
        :return: Текстовое представление модели.
        """
        return f"[{str(self.message_type).upper()}] {self.message}"