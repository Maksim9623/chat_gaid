from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.scrollview import ScrollView
from kivy.uix.popup import Popup
from kivy.uix.gridlayout import GridLayout
from kivy.properties import  ObjectProperty # StringProperty,
from kivy.clock import Clock
from kivy.graphics import Color, Rectangle #, RoundedRectangle
from kivy.core.window import Window
from kivy.animation import Animation
from kivy.metrics import dp, sp
from kivy.core.text import Label as CoreLabel
from plyer import filechooser
from kivy.uix.widget import Widget
from kivy.config import Config

import os
from pathlib import Path
import threading
import time
import json
import zlib


from screens.widgets import MessageLabel
from screens.popups import TextSendProgress, FileSendProgress, MessageReceivedPopup, FileReceivedPopup, MessageFailedPopup, MessageDeliveredPopup 
# Импорты для работы с файлами
from utils.file_utils import compress_file, decompress_file, remove_compressed
from utils.logging_utils import log_message
from kivy.utils import platform

# Константы
BLOCK_SIZE = 510  # Размер блока при передаче файлов
PAUSE_DURATION = 5  # Пауза между блоками
DEVICE_UUID = '2' #"c37c2a79-074b-437e-b36b-2fc151c19574"  # Уникальный ID устройства
USER_ID = '' # Уникальный ID Пользователя цифра, для сокращения байт 


class ChatScreen(Screen):
    """Экран чата"""
    serial_port = ObjectProperty(None) # Последовательный порт (передается из ConnectScreen)
    def __init__(self, save_dir, **kwargs):
        super().__init__(**kwargs)
        self.name = "chat_screen"
        self.contact_id = ""
        self.contact_name = ""
        self.chat_history = {}
        self.selected_file_path = None
        self.chat_history_file = "chat_history.json"
        self.SAVE_DIRECTORY = save_dir
        
        Config.set('kivy', 'keyboard_mode', 'systemanddock')
        
        Window.softinput_mode = "below_target"
        
        # Блокировка для работы с портом
        self.port_thread_lock = threading.Lock()
        self.read_thread = None
        self.file_thread = None
        
        # Настройка UI
        self.setup_ui()
        
        # Запуск приема сообщений при инициализации
        self.start_receiving()
        
        #self.start_rec_file()
                
    def setup_ui(self):
        """Настройка пользовательского интерфейса"""       
        # Изменяем фон основного меню
        self.background_color = (0.95, 0.95, 0.95, 1)
        with self.canvas.before:
            Color(*self.background_color)
            self.rect = Rectangle(size=Window.size, pos=self.pos)
        self.bind(size=self._update_rect, pos=self._update_rect)
        
        main_layout = BoxLayout(orientation="vertical", padding=10, spacing=10)
        
        # Заголовок
        title_layout = BoxLayout(size_hint_y=None, height=50)
        back_button = Button(text="Назад", size_hint_x=0.3)
        back_button.bind(on_press=lambda x: setattr(self.manager, 'current', 'contacts_screen'))
        self.title_label = Label(text="", size_hint_x=0.9, color=(0, 0, 0, 1))
        title_layout.add_widget(back_button)
        title_layout.add_widget(self.title_label)
        main_layout.add_widget(title_layout)
        
        # История чата
        #content_layout = BoxLayout(orientation="vertical", spacing=10)
        
        self.chat_scroll = ScrollView(size_hint=(1, 1), do_scroll_x=False)
        self.chat_grid = GridLayout(
            cols=1,
            spacing=dp(3),
            size_hint_y=None,
            #size_hint_x=1,
            padding=[dp(6), dp(8)],
            #-npos_hint={'top': 1}
        )
        self.chat_grid.bind(minimum_height=self.chat_grid.setter('height'))
        self.chat_scroll.add_widget(self.chat_grid)
        main_layout.add_widget(self.chat_scroll)
        
        bottom_panel = BoxLayout(orientation="vertical", size_hint_y=None)
        
        # Поле ввода сообщения
        message_layout = BoxLayout(size_hint_y=None, height=50)
        self.message_input = TextInput(
            hint_text="Сообщение",
            multiline=True,
            size_hint_y=None,
            size_hint_x=0.7,
            write_tab=False,
            do_wrap=True,
            #nscroll_y=1.0,
            allow_copy=True,
            font_size=sp(16),  # Указываем размер шрифта в sp для масштабирования
            line_height=1.5     # Межстрочный интервал
        )
        self.message_input.bind(
            height=lambda instance, value: setattr(message_layout, 'height', max(dp(50), value + dp(10))),
            text=lambda instance, value: self._text_height(instance)
        )
        send_button = Button(text="Отправить", size_hint=(0.2, None), height=60)
        send_button.bind(on_press=self.send_message)
        message_layout.add_widget(self.message_input)
        message_layout.add_widget(send_button)
        bottom_panel.add_widget(message_layout)
               
        # Отправка файлов
        file_layout = BoxLayout(size_hint_y=None, height=60)
        self.file_label = Label(text="Нет файла", size_hint_x=0.25, color=(0, 0, 0, 1))
        browse_button = Button(text="Обзор", size_hint_x=0.15)
        browse_button.bind(on_press=self.browse_files)
        send_file_button = Button(text="Отправить файл", size_hint_x=0.3)
        send_file_button.bind(on_press=self.send_file)
        file_layout.add_widget(self.file_label)
        file_layout.add_widget(browse_button)
        file_layout.add_widget(send_file_button)
        
        bottom_panel.add_widget(file_layout)
        main_layout.add_widget(bottom_panel)
        
        self.add_widget(main_layout)
        
    
    def _update_rect(self, instance, value):
        """Обновление фона сообщения"""
        self.rect.pos = instance.pos
        self.rect.size = instance.size
            
    def on_enter(self):
        """Вызывается при входе на экран"""
        self.update_title()
        if not os.path.exists(self.chat_history_file):
            with open(self.chat_history_file, "w", encoding="utf-8") as f:
                json.dump({}, f)
                
        self.load_chat_history()

    def update_title(self):
        """Обновляет заголовок экрана"""
        self.title_label.text = f"Чат с {self.contact_name}"

    def add_message(self, message, sender, file_path=None):
        """Добавляет сообщение в чат"""
        msg_layout = MessageLabel(message, sender, file_path)
        self.chat_grid.add_widget(msg_layout)
        
        # Если есть файл, добавляем информацию о файле
        # if file_path:
            # self._add_file_to_message(file_path, sender)
        
        Clock.schedule_once(lambda dt: self._scroll_to_bottom())

    def _text_height(self, instance):
        line_count = len(instance.text.split('\n'))
        new_height = max(dp(50), (line_count + 1) * dp(20))
        
        instance.height = new_height
        Clock.schedule_once(lambda dt: self._scroll_to_bottom())
        
                 
    def _scroll_to_bottom(self):
        if self.chat_grid.height > self.chat_scroll.height:
            self.chat_scroll.scroll_y = 0
        else:
            self.chat_scroll.scroll_y = 1
            
            
    def _add_file_to_message(self, file_path, sender):
        """Добавляет информацию о файле к сообщению"""
        try:
            file_name = os.path.basename(file_path)
            file_size = os.path.getsize(file_path) if os.path.exists(file_path) else 0
            file_size_str = f"{file_size / 1024:.1f} KB" if file_size < 1024 * 1024 else f"{file_size / (1024 * 1024):.1f} MB"  
                 
            file_info = f"Файл: {file_name}\nРазмер: {file_size_str}\nПуть хранения: {file_path}"
            file_layout = MessageLabel(file_info, sender)
            self.chat_grid.add_widget(file_layout)
        except Exception as e:
            log_message(f"Ошибка при добавлении файла: {str(e)}")

   
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


    def save_chat_history(self):
        """Сохраняет историю чата в файл"""       
        try:
            with open(self.chat_history_file, 'w', encoding='utf-8') as f:
                json.dump(self.chat_history, f, ensure_ascii=False, indent=2)
        except Exception as e:
            log_message(f"Ошибка сохранения истории: {str(e)}")

    def load_chat_history(self):
        """Загружает историю чата из файла"""
        try:
            if os.path.exists(self.chat_history_file):
                with open(self.chat_history_file, 'r', encoding='utf-8') as f:
                    self.chat_history = json.load(f)
            
            self.chat_grid.clear_widgets()
            
            if self.contact_id in self.chat_history:
                for msg_data in self.chat_history[self.contact_id]:
                    Clock.schedule_once(
                        lambda dt, m=msg_data['message'], s=msg_data['sender'], f=msg_data.get('file_path'): 
                        self.add_message(m, s, f)
                    )
        except Exception as e:
            log_message(f"Ошибка загрузки истории: {str(e)}")
            self.chat_history = {}
            self.chat_history = {self.contact_id: []} if self.contact_id else {}
            
            
    def send_message(self, instance):
        """Отправляет текстовое сообщение"""
        message = self.message_input.text.strip()
        if not message or not self.serial_port:
            return
        
        # Создаем и показываем popup отправки
        self.send_progress = TextSendProgress()
        self.send_progress.open()
        
        # Сохраняем оригинальное сообщение на случай повторных попыток
        original_message = message
        message_id = str(int(time.time())) # ID сообщения
        max_retries = 3
        retry_delay = 2 # сек между попыткаами
           
        # Запускаем отправку в отдельном потоке, чтобы не блокировать UI
        def send_thread():
            for attempt in range(max_retries):
                try:
                    with self.port_thread_lock:
                        if self.serial_port.is_open:
                            data = f"FROM:{self.contact_id}:TO:{DEVICE_UUID}:MSG:{message_id}:{message}\n".encode('utf-8')
                            #print(message)
                            bytes_sent = self.serial_port.write(data)
                            # print(f'Отправлено байт: {bytes_sent}')

                            ack_received = self._wait_for_ack(message_id, timeout=5)
                            if ack_received:
                                Clock.schedule_once(lambda dt: self._message_success(original_message))
                                return

                    if attempt < max_retries - 1:
                        time.sleep(retry_delay)
                        log_message(f"Повторная отправка (попытка {attempt + 2})")

                except Exception as e:
                    log_message(f"Ошибка отправки: {str(e)}")
                    # Clock.schedule_once(
                    #     lambda dt, a=attempt+1, m=max_retries, e=str(e): 
                    #     self._update_progress(a, m, e)
                    # )

            Clock.schedule_once(lambda dt: self._message_failed(original_message))

        threading.Thread(target=send_thread, daemon=True).start()
        
    # def _update_progress(self, current_attempt, max_attempts, error=None):
    #     """Обновляет прогресс-бар"""
    #     if hasattr(self, 'send_progress'):
    #         progress = current_attempt / max_attempts * 100
    #         self.send_progress.progress.value = progress
    #         status_text = f"Попытка {current_attempt} из {max_attempts}"
    #         if error:
    #             status_text = f"Ошибка: {error}"
    #         self.send_progress.status_label.text = status_text

    def _message_success(self, message):
        """Обработка успешной отправки"""
        if hasattr(self, 'send_progress'):
            self.send_progress.dismiss()
        self.message_input.text = ""
        self._update_chat(message, status='delivered')
        self.safe_show_popup(MessageDeliveredPopup, message='Доставлено')

    def _message_failed(self, message):
        """Обработка неудачной отправки"""
        if hasattr(self, 'send_progress'):
            self.send_progress.dismiss()
        self.safe_show_popup(MessageFailedPopup, message="Не удалось доставить")   
        
        
    def _update_chat(self, message, status):
        """Обновляет историю чата после отправки"""
        if self.contact_id not in self.chat_history:
            self.chat_history[self.contact_id] = []
            
        self.chat_history[self.contact_id].append({
            'message': message,
            'sender': 'self',
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
            'status': status
        })
        self.save_chat_history()
        self.add_message(message, 'self')


    def _wait_for_ack(self, message_id, timeout=15):
        """Проверяет статус доставки сообщения"""
        start_time = time.time()
        while time.time() - start_time < timeout:
            if self.serial_port.is_open:
                raw_data = self.serial_port.read(self.serial_port.in_waiting).decode('utf-8')
                print(raw_data)
                if f"ACK:MSG:{message_id}" in raw_data:
                    return True
            time.sleep(0.1)
        return False
        
 
    def send_file(self, instance):
        """Отправляет файл"""
        if not self.selected_file_path or not self.serial_port:
            return

        file_name = os.path.basename(self.selected_file_path)

        # Добавляем в историю
        if self.contact_id not in self.chat_history:
            self.chat_history[self.contact_id] = []

        self.chat_history[self.contact_id].append({
            'message': f"Отправлен файл: {file_name}",
            'sender': 'self',
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
            'file_path': self.selected_file_path
        })
        self.save_chat_history()

        # Показываем в чате
        self._add_file_to_message(self.selected_file_path, 'self')

        # Создаем прогресс-попап в основном потоке
        progress = FileSendProgress()
        progress.open()

        # Запускаем отправку в отдельном потоке
        threading.Thread(
            target=self._send_file,
            args=(self.selected_file_path, progress),
            daemon=True
        ).start()


    def _send_file(self, full_path, progress_popup):
        """Поток для отправки файла"""
        try:
            is_compressed = full_path.endswith('.txt')
            
            compressed_file = compress_file(full_path)
            file_name = os.path.basename(compressed_file)
            file_size = os.path.getsize(compressed_file)
            total_blocks = (file_size // BLOCK_SIZE) + 1


            with self.port_thread_lock:
                if self.serial_port.is_open:
                    with open(compressed_file, 'rb') as file:
                        crc32 = zlib.crc32(file.read()) & 0xffffffff  # Вычисляем CRC32
                        # Отправка заголовка с ID контакта и именем файла
                        header = f"FILE:FROM:{self.contact_id}:TO:{DEVICE_UUID}:{file_name}:{'compressed' if is_compressed else 'rar'}:{crc32}\n".encode('utf-8')

                    self.serial_port.write(header)
                    time.sleep(3)  # Даем время на обработку

                    # Отправляем данные блоками
                    with open(compressed_file, 'rb') as file:
                        for block_num in range(total_blocks):
                            block_data = file.read(BLOCK_SIZE)
                            self.serial_port.write(block_data)
                            time.sleep(PAUSE_DURATION)

                            # Обновляем прогресс через Clock
                            Clock.schedule_once(
                                lambda dt, bn=block_num, tb=total_blocks: 
                                self._update_progress(progress_popup, bn, tb)
                            )
                        # Маркер конца файла
                self.serial_port.write(b'#EOF\n')
            if ".compressed" in compressed_file:
                print(compress_file)
                os.remove(compressed_file)
            #Clock.schedule_once(lambda dt: self._update_log(f"Файл {file_name} отправлен"))
        except Exception as e:
            print(f"Ошибка отправки файла: {str(e)}")
            #Clock.schedule_once(lambda dt: log_message(f"Ошибка отправки файла: {str(e)}"))
        finally:
            Clock.schedule_once(lambda dt: progress_popup.dismiss())

    def _update_progress(self, progress_popup, block_num, total_blocks):
        """Обновляет прогресс-бар"""
        progress_popup.progress.value = (block_num + 1) / total_blocks * 100


    def start_receiving(self):
        """Запускает потоки для приема сообщений"""
        if not self.read_thread:
            self.read_thread = threading.Thread(
                target=self._receive_messages,
                daemon=True
            )
            self.read_thread.start()
    
    
    def _receive_messages(self):
        """Поток для приема текстовых сообщений"""
        current_file = None
        
        while True:
            if self.serial_port and self.serial_port.in_waiting:
                try:
                    with self.port_thread_lock:
                        if not self.serial_port.is_open:
                            break

                        if self.serial_port.is_open:                           
                            raw_data = self.serial_port.read_until(b'\n')  # Читаем данные до символа новой строки
                            # print("Сырые данные", raw_data)
                            line = raw_data.decode('utf-8', errors='ignore').strip()  # Преобразуем в строку

                            if not line:
                                continue

                            parts = line.split(':')                                                     
                            if parts[0] == "FROM" and "TO" in parts:
                                #parts = message.split(":")
                                sender_id = parts[1]
                                recipient_id = parts[3]
                                message_id = parts[5]
                                msg_content = ":".join(parts[6:])
   
                                with open("contacts.txt", "r", encoding='utf-8') as f:
                                    for line in f:
                                        contact_id, contact_name = line.strip().split(":")
                                        if contact_id == sender_id:
                                            self._process_received_message(sender_id, contact_name, msg_content)
                                #ответ о получении смс
                                ack = f"ACK:MSG:{message_id}".encode('utf-8')
                                receve_ack = self.serial_port.write(ack)
                                print('Ответ', ack) 
                                
                            elif len(parts) == 8 or parts[0] == 'FILE':
                                print("Условие", parts)
                                sender_id = parts[2]
                                radio_name = parts[4]
                                file_name = parts[5]
                                is_compressed = parts[6] == 'compressed'
                                receive_crc = parts[7]
                                full_path = os.path.join(self.SAVE_DIRECTORY, file_name)
                                file_name = remove_compressed(file_name)  

                                with open("contacts.txt", "r", encoding='utf-8') as f:
                                    for line in f:
                                        contact_id, contact_name = line.strip().split(":")
                                        if contact_id == sender_id:
                                            print(f"Принято начало файла: от {contact_name}, Имя файла: {file_name}")                                            
                                    try:
                                        current_file = open(full_path, 'ab')  # Открываем файл в бинарном режиме
                                    except Exception as e:
                                        print(f"Ошибка при открытии файла: {e}")
                                        current_file = None 
                                        
                            elif current_file is not None:
                                if b'#EOF\n' in raw_data:  #.decode('utf-8', errors='ignore'):
                                    current_file.write(raw_data.replace(b'#EOF\n', b'')) 
                                    current_file.flush()  # Немедленно очищаем буфер
                                    current_file.close()
                                    current_file = None
                                    # Распаковка файла после получения
                                    with open(full_path, 'rb') as file:
                                        crc32 = zlib.crc32(file.read()) & 0xffffffff
                                        if crc32 == int(receive_crc):
                                            print(crc32)
                                            if is_compressed:
                                                dec_file = decompress_file(full_path)
                                                print(f"Файл {dec_file} получен.")
                                                with open("contacts.txt", "r", encoding='utf-8') as f:
                                                    for line in f:
                                                        contact_id, contact_name = line.strip().split(":")
                                                        if contact_id == sender_id:
                                                            self._process_received_file(sender_id, contact_name, file_name, dec_file)
                                                #self.serial_port.write(b'ACK\n')

                                            elif full_path.endswith(('.rar', '.7z', '.zip', '.gz')):
                                                print(f"Файл {file_name} получен.")
                                                self._process_received_file(sender_id, contact_name, file_name, full_path)
                                                #self.serial_port.write(b'ACK\n')
                                            else:
                                                print(f'Ошибка при распаковке файла {file_name}')
                                        else:
                                            print(crc32, 'Пришло не правильно:' , receive_crc)
                                            if current_file is not None:
                                                current_file.close()
                                                os.remove(full_path)
                                            print(f'Файл {file_name} с ошибкой', is_incoming=True)
                                    if full_path.endswith('.compressed'):
                                        os.remove(full_path)
                                else:
                                    current_file.write(raw_data)  # Записываем сырые данные в файл
                                    current_file.flush()  # Немедленно очищаем буфер                             
                                
                except Exception as e:
                    log_message(f"Ошибка приема: {str(e)}")
                    time.sleep(1)
            else:
                time.sleep(0.1)
    
    
    def _process_received_message(self, sender_id, contact_name, message):
        """Обрабатывает полученное сообщение"""
        sender_name = contact_name
        if hasattr(self, 'contacts') and sender_id in self.contacts:
            sender_name = self.contacts[sender_id]
        # Сохраняем в историю
        if sender_id not in self.chat_history:
            self.chat_history[sender_id] = []
          
        self.chat_history[sender_id].append({
            'message': message,
            'sender': sender_name,
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
        })

        self.save_chat_history()
       
        # Показываем в UI
        if self.contact_id == sender_id:
            self.safe_add_message(message, sender_name)
            self.safe_show_popup(MessageReceivedPopup, message=f"{sender_name}: {message}") 


    def _process_received_file(self, sender_id, contact_name, file_name, file_path):
        """Обрабатывает полученный файл"""
        #sender_name = contact_name #"Неизвестный отправитель"
        if hasattr(self, 'contacts') and sender_id in self.contacts:
            contact_name = self.contacts[sender_id]

        file_size = os.path.getsize(file_path) if os.path.exists(file_path) else 0
        file_size_str = f"{file_size / 1024:.1f} KB" if file_size < 1024 * 1024 else f"{file_size / (1024 * 1024):.1f} MB"

        # Сохраняем в историю
        if sender_id not in self.chat_history:
            self.chat_history[sender_id] = []
            
        self.chat_history[sender_id].append({
            'message': f"Файл: {file_name}\nРазмер: {file_size_str}",
            'sender': contact_name,
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
            'file_path': file_path
        })
        self.save_chat_history()
        
        # Показываем в UI
        self.safe_add_message(f"Получен файл: {file_name}", contact_name, file_path) #f"Получен файл: {file_name}",
        #self.safe_add_message(f"Файл: {file_name}\nРазмер: {file_size_str}")
        self.safe_show_popup(FileReceivedPopup, file_name=file_name, sender=contact_name)

    def safe_add_message(self, message, sender, file_path=None):
        """Безопасно добавляет сообщение из любого потока"""
        Clock.schedule_once(lambda dt: self.add_message(message, sender, file_path))

    def safe_show_popup(self, popup_class, **kwargs):
        """Безопасно показывает popup из любого потока"""
        Clock.schedule_once(lambda dt: popup_class(**kwargs).open())

    def browse_files(self, instance):
        """Открывает диалог выбора файла"""
        filechooser.open_file(
            title="Выберите файл",
            filters=[("Все файлы", "*.*"), ("Текстовые файлы", "*.txt"), ("Изображения", "*.png *.jpg *.jpeg")],
            on_selection=self.handle_file_selection
        )

    def handle_file_selection(self, selection):
        """Обрабатывает выбранный файл"""
        if selection:
            self.selected_file_path = selection[0]
            self.file_label.text = os.path.basename(self.selected_file_path)
        else:
            self.selected_file_path = None
            self.file_label.text = "Нет файла"

    def on_leave(self):
        """Очистка при выходе с экрана"""
        # self.chat_grid.clear_widgets()
        self.selected_file_path = None
        self.file_label.text = "Нет файла"
        self.save_chat_history() 

    def on_stop(self):
        """Закрытие порта при выходе"""
        if self.serial_port:
            with self.port_thread_lock:
                try:
                    if self.serial_port.is_open:
                        self.serial_port.close()
                except:
                    pass
        
        if self.read_thread:
            self.read_thread.join(timeout=1)
        
        if self.file_thread:
            self.file_thread.join(timeout=1)