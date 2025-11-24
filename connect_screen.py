from kivy.uix.screenmanager import Screen
from kivy.properties import ObjectProperty
from kivy.event import EventDispatcher
from kivy.utils import platform
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.metrics import dp
from kivy.uix.anchorlayout import AnchorLayout
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.spinner import Spinner
from kivy.uix.popup import Popup

# Для Android
if platform == 'android':
    from usb4a import usb
    from usbserial4a import serial4a
# Для ПК
else:
    import serial.tools.list_ports
    import serial
    
from utils.logging_utils import log_message

class ConnectScreen(Screen, EventDispatcher):
    # Событие, которое будет вызываться при успешном подключении
    __events__ = ('on_connected',)
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.serial_port = None
        self.baudrate = 115200
        #self.bytesize = 8
        #self.parity = 'N'
        #self.stopbits = 1
        self.timeout = 1000

        self.name = "connect_screen"
        self.serial_port = None
                
        # Главный layout с центрированием
        main_layout = AnchorLayout(anchor_x='center', anchor_y='center')
        
        # Центральный контейнер
        center_container = BoxLayout(
            orientation="vertical",
            padding=dp(20),
            spacing=dp(15),
            size_hint=(None, None)
        )
        center_container.bind(minimum_width=center_container.setter('width'))
        center_container.width = dp(400)  # Базовая ширина
        center_container.height = dp(250)  # Увеличенная высота для лучшего распределения
        
        # Заголовок
        title_label = Label(
            text="Подключение к устройству",
            font_size=dp(24),
            size_hint_y=None,
            height=dp(50),
            text_size=(dp(380), None),
            halign='center',
            valign='middle'
        )
        title_label.bind(texture_size=title_label.setter('size'))
        center_container.add_widget(title_label)

        # Надпись "Выберите COM-порт"
        com_port_label = Label(
            text="Выберите COM-порт:",
            size_hint_y=None,
            height=dp(30),
            halign='center',
            valign='middle'
        )
        center_container.add_widget(com_port_label)

        # Контейнер для спиннера
        spinner_container = BoxLayout(
            orientation='vertical',
            size_hint_y=None,
            height=dp(50),
            padding=[dp(10), dp(5)],
        )
        
        # Спиннер для выбора порта
        self.com_port_spinner = Spinner(
            text="Выберите порт",
            values=self.get_available_ports(),
            size_hint=(1, 1),
            text_size=(None, None),
        )
        
        spinner_container.add_widget(self.com_port_spinner)
        center_container.add_widget(spinner_container)

        # Кнопка обновления списка портов
        self.refresh_button = Button(
            text="Обновить список",
            size_hint=(None, None),
            size=(dp(200), dp(40)),
            pos_hint={'center_x': 0.5}
        )
        self.refresh_button.bind(on_press=self.refresh_ports)
        center_container.add_widget(self.refresh_button)
        
        # Кнопка подключения
        self.connect_button = Button(
            text="Подключиться",
            size_hint=(None, None),
            size=(dp(200), dp(50)),
            pos_hint={'center_x': 0.5}
        )
        self.connect_button.bind(on_press=self.on_connect_button)
        center_container.add_widget(self.connect_button)

        # Добавляем центрированный контейнер в главный layout
        main_layout.add_widget(center_container)
        self.add_widget(main_layout)

        # Привязываем обновление размеров к изменению размера окна
        Window.bind(on_resize=self.on_window_resize)


    def on_window_resize(self, instance, width, height):
        # Обновляем размеры контейнера при изменении размера окна
        container = self.children[0].children[0]  # Получаем center_container
        container.width = min(dp(400), width * 0.9)  # Не более 90% ширины окна

    def show_popup(self, title, message):
        popup = Popup(
            title=title,
            content=Label(
                text=message,
                text_size=(dp(300), None),
                halign='center',
                valign='middle'
            ),
            size_hint=(None, None),
            size=(dp(350), dp(200))
        )
        popup.open()


    def get_available_ports(self):
        """Получает список доступных портов в зависимости от платформы"""
        if platform == 'android':
            return self.get_android_ports()
        else:
            return self.get_pc_ports()


    def get_pc_ports(self):
        """Получает список COM-портов для ПК"""
        try:
            return [port.device for port in serial.tools.list_ports.comports()]
        except Exception as e:
            log_message(f'Ошибка получения PC портов: {str(e)}')
            return []


    def get_android_ports(self):
        """Получает список USB-устройств для Android"""
        try:
            usb_device_list = usb.get_usb_device_list()
            if usb_device_list:
                return [device.getDeviceName() for device in usb_device_list]
            return []
        except Exception as e:
            log_message(f'Ошибка получения Android портов: {str(e)}')
            return []
        
    def refresh_ports(self, instance):
        """Обновляет список доступных портов"""
        self.com_port_spinner.values = self.get_available_ports()
        if not self.com_port_spinner.values:
            self.com_port_spinner.text = "Устройства не найдены"
        else:
            self.com_port_spinner.text = "Выберите порт"

    def on_connect_button(self, instance):
        """Обработчик кнопки подключения"""
        try:
            selected_port = self.com_port_spinner.text
            if selected_port in ("Выберите порт", "Устройства не найдены"):
                self.show_popup("Ошибка", "Выберите порт")
                return

            if platform == 'android':
                self.connect_android_device(selected_port)
            else:
                self.connect_pc_device(selected_port)
                
        except Exception as e:
            self.show_popup("Ошибка", f"Ошибка подключения: {str(e)}")

    def connect_android_device(self, device_name):
        """Подключение на Android"""
        device = usb.get_usb_device(device_name)
        if not device:
            self.show_popup("Ошибка", "Устройство не найдено")
            return

        if not usb.has_usb_permission(device):
            usb.request_usb_permission(device)
            self.show_popup("Информация", "Запрошено разрешение. Попробуйте снова.")
            return

        self.serial_port = serial4a.get_serial_port(
            device_name,
            self.baudrate,
            #self.bytesize,
            #self.parity,
            #self.stopbits,
            #timeout=self.timeout
        )

        if self.serial_port and self.serial_port.is_open:
            self.show_popup("Успех", "Подключено!")
            self.dispatch('on_connected')  # Уведомляем главный файл
        else:
            self.show_popup("Ошибка", "Не удалось открыть порт")

    def connect_pc_device(self, port):
        """Подключение на ПК"""
        try:
            self.serial_port = serial.Serial(
                port,
                baudrate=self.baudrate,
                #bytesize=self.bytesize,
                #parity=self.parity,
                #stopbits=self.stopbits,
                timeout=self.timeout
            )
            self.show_popup("Успех", "Подключено!")
            self.dispatch('on_connected')  # Уведомляем главный файл
        except Exception as e:
            self.show_popup("Ошибка", f"Не удалось подключиться: {str(e)}")

    def on_connected(self, *args):
        """Метод-заглушка для события"""
        pass

