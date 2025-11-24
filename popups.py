from kivy.uix.popup import Popup
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.progressbar import ProgressBar
from kivy.uix.label import Label


class TextSendProgress(Popup):
    """Popup для отображения прогресса отправки текста"""
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.title = "Отправка сообщения"
        self.size_hint = (0.55, 0.25)
        self.content = BoxLayout(orientation='vertical')
        self.progress = ProgressBar(max=100)
        self.content.add_widget(self.progress)
        self.content.add_widget(Label(text="Отправка сообщения..."))


class FileSendProgress(Popup):
    """Popup для отображения прогресса отправки файла"""
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.title = "Отправка файла"
        self.size_hint = (0.55, 0.25)
        self.content = BoxLayout(orientation='vertical')
        self.progress = ProgressBar(max=100)
        self.content.add_widget(self.progress)
        self.content.add_widget(Label(text="Отправка файла..."))
 
        
class MessageReceivedPopup(Popup):
    """Уведомление о новом сообщении"""
    def __init__(self, message, **kwargs):
        super().__init__(**kwargs)
        self.title = "Новое сообщение"
        self.size_hint = (0.55, 0.2)
        self.content = Label(text=message,
                             text_size=(self.size[0], None),
                             size_hint_y=None,
                             halign='center',
                             valign='middle',
                             padding=(10,10)
                             ) 
        self.content.bind(size=self.content.setter('text_size'))
        

class FileReceivedPopup(Popup):
    """Уведомление о получении файла"""
    def __init__(self, file_name, sender="Неизвестный отправитель", **kwargs):
        super().__init__(**kwargs)
        self.title = "Новый файл"
        self.size_hint = (0.5, 0.2)
        self.content = Label(text=f"От {sender} получен файл:", text_size=(self.size[0], None), size_hint_y=None, halign='center', valign='middle', padding=(10,10)) # {file_name}
        self.content.bind(size=self.content.setter('text_size'))

class MessageDeliveredPopup(Popup):
    """Уведомление о доставленном сообщение"""
    def __init__(self, message, **kwargs):
        super().__init__(**kwargs)
        self.title = "Успешно"
        self.size_hint = (0.55, 0.25)
        self.content = Label(text=f"Сообщение доставлено: ", text_size=(self.size[0], None), size_hint_y=None, halign='center', valign='middle', padding=(10,10)) #{message}
        self.content.bind(size=self.content.setter('text_size'))
        
        
class MessageFailedPopup(Popup):
    """Уведомление о ошибки отправки"""
    def __init__(self, message, **kwargs):
        super().__init__(**kwargs)
        self.title = "Ошибка"
        self.size_hint = (0.55, 0.25)
        self.content = Label(text=f"Ошибка доставки: ", text_size=(self.size[0], None), size_hint_y=None, halign='center', valign='middle', padding=(10,10)) #{message}
        
        self.content.bind(size=self.content.setter('text_size'))