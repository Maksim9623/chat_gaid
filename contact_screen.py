from kivy.uix.image import Image
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.scrollview import ScrollView
from kivy.uix.gridlayout import GridLayout
from kivy.uix.screenmanager import Screen
from kivy.uix.popup import Popup
from kivy.core.window import Window
from kivy.metrics import dp

import os

class ContactsScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = "contacts_screen"
        self.contacts = {}
        self.load_contacts()
        
        # Основной макет
        layout = BoxLayout(orientation="vertical", padding=dp(10), spacing=dp(10))
        
        # Заголовок
        title = Label(
            text="Контакты", 
            size_hint_y=None, 
            height=dp(50),
            font_size=dp(24),
            halign='center'
        )
        layout.add_widget(title)
        
        # Поля для добавления нового контакта
        new_contact_layout = GridLayout(
            cols=3, 
            size_hint_y=None, 
            height=dp(60),
            spacing=dp(5)
        )
        self.new_contact_id = TextInput(
            hint_text="ID (только цифры)", 
            size_hint_y=None, 
            height=dp(50),
            font_size=dp(16),
            multiline=True
        )
        
        self.new_contact_name = TextInput(
            hint_text="Имя", 
            size_hint_y=None, 
            height=dp(50),
            font_size=dp(16),
            multiline=True
        )
        
        add_button = Button(
            text="Добавить", 
            size_hint_y=None, 
            height=dp(50),
            font_size=dp(16)
        )
        add_button.bind(on_press=self.add_contact)
        new_contact_layout.add_widget(self.new_contact_id)
        new_contact_layout.add_widget(self.new_contact_name)
        new_contact_layout.add_widget(add_button)
        layout.add_widget(new_contact_layout)
        
        # Список контактов с прокруткой
        self.contacts_scroll = ScrollView(
            size_hint=(1, 1),
            bar_width=dp(10),
            scroll_type=['bars', 'content']
        )
        
        self.contacts_grid = GridLayout(
            cols=1, 
            spacing=dp(10), 
            size_hint_y=None,
            padding=[dp(5), 0, dp(5), 0]
        )
        self.contacts_grid.bind(minimum_height=self.contacts_grid.setter('height'))
        self.update_contacts_list()
        self.contacts_scroll.add_widget(self.contacts_grid)
        layout.add_widget(self.contacts_scroll)
        
        self.add_widget(layout)
        
        # Обработчик изменения размера окна
        Window.bind(on_resize=self.on_window_resize)

    def on_window_resize(self, window, width, height):
        # Обновляем размеры элементов при изменении размера окна
        self.update_contacts_list()

    def load_contacts(self):
        if os.path.exists("contacts.txt"):
            with open("contacts.txt", "r", encoding='utf-8') as f:
                for line in f:
                    contact_id, contact_name = line.strip().split(":")
                    self.contacts[contact_id] = contact_name

    def save_contacts(self):
        with open("contacts.txt", "w", encoding='utf-8') as f:
            for contact_id, contact_name in self.contacts.items():
                f.write(f"{contact_id}:{contact_name}\n")

    def add_contact(self, instance):
        contact_id = self.new_contact_id.text.strip()
        contact_name = self.new_contact_name.text.strip()

        if not contact_id.isdigit():
            self.show_popup("Ошибка", "ID должен состоять только из цифр.")
            return

        if contact_id in self.contacts:
            self.show_popup("Ошибка", f"Контакт с ID {contact_id} уже существует.")
            return

        if contact_id and contact_name:
            self.contacts[contact_id] = contact_name
            self.save_contacts()
            self.update_contacts_list()
            self.new_contact_id.text = ""
            self.new_contact_name.text = ""
            self.show_popup("Успешно", f"Контакт {contact_name} добавлен.")
        else:
            self.show_popup("Ошибка", "Поля ID и Имя не могут быть пустыми.")

    def update_contacts_list(self):
        self.contacts_grid.clear_widgets()
        for contact_id, contact_name in self.contacts.items():
            contact_layout = BoxLayout(
                orientation="horizontal", 
                size_hint_y=None, 
                height=dp(60), 
                spacing=dp(10),
                padding=[0, dp(1), 0, dp(1)]
            )
            
            # Кнопка для открытия чата
            chat_button = Button(
                text=f"{contact_name}",# (ID: {contact_id})", 
                size_hint_x=0.7,
                font_size=dp(18),
                halign='left',
                valign='middle'
            )
            chat_button.bind(on_press=lambda x, cid=contact_id: self.open_chat(cid))
            
            # Кнопка для удаления контакта с иконкой
            delete_button = Button(
                size_hint_x=0.3, 
                background_normal="", 
                background_color=(1, 1, 1, 0)
            )
            delete_icon = Image(
                source="icons/delete_icon.png", 
                size_hint=(None, None), 
                size=(dp(40), dp(40))
            )
            delete_button.add_widget(delete_icon)
            delete_button.bind(on_press=lambda x, cid=contact_id: self.delete_contact(cid))
            delete_button.bind(size=self.center_icon)
            delete_button.bind(pos=self.center_icon)
            
            contact_layout.add_widget(chat_button)
            contact_layout.add_widget(delete_button)
            self.contacts_grid.add_widget(contact_layout)

    def center_icon(self, instance, value):
        if instance.children:
            icon = instance.children[0]
            icon.pos = instance.center_x - icon.width / 2, instance.center_y - icon.height / 2

    def delete_contact(self, contact_id):
        if contact_id in self.contacts:
            contact_name = self.contacts.pop(contact_id)
            self.save_contacts()
            self.update_contacts_list()
            self.show_popup("Успешно", f"Контакт {contact_name} удален.")
        else:
            self.show_popup("Ошибка", "Контакт не найден.")

    def open_chat(self, contact_id):
        chat_screen = self.manager.get_screen('chat_screen')
        chat_screen.contact_id = contact_id
        chat_screen.contact_name = self.contacts[contact_id]
        chat_screen.update_title()
        chat_screen.load_chat_history()
        self.manager.current = 'chat_screen'

    def show_popup(self, title, message):
        popup_layout = BoxLayout(orientation="vertical", padding=dp(10), spacing=dp(10))
        popup_label = Label(
            text=message, 
            size_hint_y=0.8,
            font_size=dp(18),
            halign='center',
            valign='middle'
        )
        popup_button = Button(
            text="OK", 
            size_hint_y=0.3,
            size_hint_x=0.5,
            pos_hint={'center_x': 0.5},
            font_size=dp(18)
        )
        popup = Popup(
            title=title, 
            content=popup_layout, 
            size_hint=(0.8, 0.4),
            title_size=dp(20)
        )
        popup_button.bind(on_press=popup.dismiss)
        popup_layout.add_widget(popup_label)
        popup_layout.add_widget(popup_button)
        popup.open()