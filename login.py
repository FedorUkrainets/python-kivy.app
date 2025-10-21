# login.py
from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.popup import Popup
from kivy.app import App
from kivy.metrics import dp
from kivy.graphics import Color, Rectangle
from kivy.animation import Animation

class LoginScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        with self.canvas.before:
            Color(0.08,0.08,0.12,1)
            self.rect = Rectangle(size=self.size, pos=self.pos)
        self.bind(size=self.update_rect, pos=self.update_rect)

        root = BoxLayout(orientation="vertical", padding=dp(20), spacing=dp(15))

        lbl_title = Label(
            text="[b]Вход / Регистрация[/b]",
            markup=True,
            font_size=26,
            halign="center",
            size_hint_y=None,
            height=dp(40),
            color=(1,1,1,1)
        )
        lbl_title.bind(size=lbl_title.setter("text_size"))
        root.add_widget(lbl_title)

        self.input_username = TextInput(
            hint_text="Имя пользователя",
            multiline=False,
            size_hint_y=None,
            height=dp(46),
            foreground_color=(1,1,1,1),
            background_color=(0.15,0.15,0.2,1),
            padding=(dp(12),dp(12))
        )
        root.add_widget(self.input_username)

        self.input_password = TextInput(
            hint_text="Пароль",
            multiline=False,
            password=True,
            size_hint_y=None,
            height=dp(46),
            foreground_color=(1,1,1,1),
            background_color=(0.15,0.15,0.2,1),
            padding=(dp(12),dp(12))
        )
        root.add_widget(self.input_password)

        btns = BoxLayout(spacing=dp(10), size_hint_y=None, height=dp(50))

        self.btn_login = Button(
            text="Войти",
            background_normal="",
            background_color=(0.2,0.6,0.9,1),
            color=(1,1,1,1)
        )
        self.btn_login.bind(on_press=self.login_user)

        self.btn_register = Button(
            text="Регистрация",
            background_normal="",
            background_color=(0.4,0.2,0.9,1),
            color=(1,1,1,1)
        )
        self.btn_register.bind(on_press=self.register_user)

        btns.add_widget(self.btn_login)
        btns.add_widget(self.btn_register)
        root.add_widget(btns)

        self.add_widget(root)

    def update_rect(self, *args):
        self.rect.pos = self.pos
        self.rect.size = self.size

    def popup_message(self, title: str, message: str):
        popup = Popup(title=title,
                      content=Label(text=message),
                      size_hint=(0.7, 0.4),
                      auto_dismiss=True)
        popup.open()

    def login_user(self, instance):
        app = App.get_running_app()
        username = self.input_username.text.strip()
        password = self.input_password.text.strip()
        if not username or not password:
            self.popup_message("Ошибка", "Заполните все поля")
            return
        try:
            if app.db.login_user(username, password):
                self.popup_message("Успех", "Вы успешно вошли")
                self.input_username.text = ""
                self.input_password.text = ""
                self.manager.current = "main"
            else:
                self.popup_message("Ошибка", "Неверный логин или пароль")
        except Exception as e:
            self.popup_message("Ошибка", f"Ошибка при входе: {e}")

    def register_user(self, instance):
        app = App.get_running_app()
        username = self.input_username.text.strip()
        password = self.input_password.text.strip()
        if not username or not password:
            self.popup_message("Ошибка", "Заполните все поля")
            return
        try:
            if app.db.register_user(username, password):
                self.popup_message("Успех", "Регистрация выполнена. Войдите в систему")
                self.input_username.text = ""
                self.input_password.text = ""
            else:
                self.popup_message("Ошибка", "Пользователь уже существует")
        except Exception as e:
            self.popup_message("Ошибка", f"Ошибка при регистрации: {e}")