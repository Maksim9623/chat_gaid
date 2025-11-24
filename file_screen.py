from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.scrollview import ScrollView
from kivy.uix.popup import Popup
from kivy.uix.gridlayout import GridLayout
from kivy.properties import StringProperty, ObjectProperty
from kivy.clock import Clock
from kivy.graphics import Color, RoundedRectangle, Rectangle
from kivy.core.window import Window
from kivy.animation import Animation
from kivy.metrics import dp, sp
from kivy.core.text import Label as CoreLabel
from plyer import filechooser
from kivy.uix.progressbar import ProgressBar
from kivy.uix.widget import Widget
from kivy.app import App



class FileScreen(App):
    
    #def __init__(self, **kwargs):
    #    super().__init__(**kwargs)
        
        
        
    def build(self):    
        layout = GridLayout(cols=1)

        

        # Добавляем кнопки-файлы

        
        btn = Button(background_normal=r"C:\Программы\Эрика для передачи данных\kivy_new\icons\default_icon.png", size_hint=(None, None), size=(90, 90), on_press=self.open_file_content)
        layout.add_widget(btn)
            

        return layout
        
        
    def open_file_content(self, instance):
        """Открывает окно просмотра содержимого файла"""
        content = f"Содержимое файла {instance.text}"
        popup_layout = GridLayout(rows=2)
        label = Label(text=content, size_hint_y=None, height=Window.height * 0.7)
        close_btn = Button(text="Закрыть")
        popup_layout.add_widget(label)
        popup_layout.add_widget(close_btn)
   
        popup = Popup(title='Просмотр файла', content=popup_layout,
                     size_hint=(None, None), size=(600, 600))
        close_btn.bind(on_release=popup.dismiss)
        popup.open()
        
if __name__ == '__main__':
    FileScreen().run()