from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.properties import StringProperty
from kivy.core.window import Window
from kivy.graphics import Color, RoundedRectangle
from kivy.uix.widget import Widget
from kivy.metrics import dp
from kivy.uix.button import Button
from kivy.uix.gridlayout import GridLayout
from kivy.uix.popup import Popup


class MessageLabel(BoxLayout):
    """Виджет для отображения сообщения в чате"""
    sender = StringProperty('')
    
    def __init__(self, message, sender, file_path=None, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'vertical'
        self.size_hint_y = None
        self.size_hint_x = 1
        self.height = dp(0)
        self.padding = [dp(2), dp(1)]
        self.spacing = dp(1)
        
        # Стилизация сообщения
        content_layout = BoxLayout(orientation='horizontal', size_hint_y=None, height=dp(0))
        max_width = min(Window.width * 0.5, dp(300))
        
        message_container = BoxLayout(
            orientation='vertical',
            size_hint=(None, None),
            width=max_width,
            padding=[dp(6), dp(4)]
        )
        
        # Цвет фона в зависимости от отправителя
        with message_container.canvas.before:
            Color(*(0.0, 0.6, 1.0, 1) if sender == 'self' else (0.8, 0.8, 0.8, 1))
            self.rect = RoundedRectangle(radius=[dp(6)])
        message_container.bind(pos=self._update_rect, size=self._update_rect)
        
        # Текст сообщения
        self.message_label = Label(
            text=message,
            size_hint=(1, None),
            height=dp(0),
            halign='left',
            valign='middle',
            text_size=(max_width - dp(12), None),
            color=(0, 0, 0, 1),
            padding=[dp(3), dp(2)],
            line_height=1.1
        )
        self.message_label.bind(texture_size=self._update_label_size)
        message_container.add_widget(self.message_label)
        
        
        # Создаем кнопку с иконкой файла
        file_btn = Button(background_normal=r'C:\Программы\Эрика для передачи данных\kivy_new\icons\preview_placeholder-64x64.png',
            size_hint=(None, None),
            size=(90, 90),
            on_press=lambda x: self.open_file_content(file_path)
            )

        # Выравнивание сообщения
        if sender == 'self':
            content_layout.add_widget(Widget(size_hint_x=0.3))
            #content_layout.add_widget(file_btn)
            content_layout.add_widget(message_container)
            content_layout.add_widget(Widget(size_hint_x=0.05))
        else:
            content_layout.add_widget(Widget(size_hint_x=0.05))
            content_layout.add_widget(message_container)
            content_layout.add_widget(Widget(size_hint_x=0.3))
        
        self.add_widget(content_layout)
        self.message_container = message_container
        self.content_layout = content_layout

    def _update_label_size(self, instance, size):
        """Обновление размера метки сообщения"""
        self.message_label.height = size[1]
        self.message_container.height = size[1] + dp(8)
        self.content_layout.height = self.message_container.height + dp(2)
        self.height = self.content_layout.height + dp(2)

    def _update_rect(self, instance, value):
        """Обновление фона сообщения"""
        self.rect.pos = instance.pos
        self.rect.size = instance.size
        
        
    def open_file_content(self, file_path):
        """Открывает окно просмотра содержимого файла"""
        with open(file_path, "r") as f:
            content = f.read()
        popup_layout = GridLayout(rows=2)
        label = Label(text=content, size_hint_y=None, height=Window.height * 0.7)
        close_btn = Button(text="Закрыть")
        popup_layout.add_widget(label)
        popup_layout.add_widget(close_btn)
   
        popup = Popup(title='Просмотр файла', content=popup_layout,
                     size_hint=(None, None), size=(600, 600))
        close_btn.bind(on_release=popup.dismiss)
        popup.open()