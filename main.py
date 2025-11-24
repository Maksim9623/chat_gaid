from kivy.app import App
from kivy.uix.screenmanager import ScreenManager
from kivy.utils import platform
from screens.connect_screen import ConnectScreen
from screens.contact_screen import ContactsScreen
from screens.chat_screen_new import ChatScreen

import os
from pathlib import Path

from utils.logging_utils import init_logging, log_message

def get_save_directory():
    # Для Android
    if platform == 'android':
        from plyer import storagepath
        return Path(storagepath.get_external_storage_dir()) / "RadioDocks"
    # Для ПК
    else:
        return Path(__file__).parent.parent / "kivy_new" / "RadioDocks"
        
      
class RadioTerminal(App):
    def build(self):
        self.sm = ScreenManager()
        init_logging()
        log_message("Приложение запущенно")
        save_dir = get_save_directory()
        os.makedirs(save_dir, exist_ok=True)
        
        # Создаем экраны
        self.connect_screen = ConnectScreen(name='connect_screen')
        self.contacts_screen = ContactsScreen(name='contacts_screen')
        self.chat_screen = ChatScreen(name='chat_screen', save_dir=save_dir)
                
        # Добавляем экраны в менеджер
        self.sm.add_widget(self.connect_screen)
        self.sm.add_widget(self.contacts_screen)
        self.sm.add_widget(self.chat_screen)
        
        # Привязываем обработчик успешного подключения
        self.connect_screen.bind(on_connected=self.on_connected)
        
        return self.sm
    
    def on_connected(self, instance):
        """Переключаемся на экран контактов после подключения"""
        selected_port = self.connect_screen.serial_port
        self.chat_screen.serial_port = selected_port
        self.sm.current = 'contacts_screen'
        

if __name__ == "__main__":
    RadioTerminal().run()