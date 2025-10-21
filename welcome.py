# welcome.py
from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.metrics import dp
from kivy.graphics import Color, Rectangle
from kivy.animation import Animation
from kivy.uix.popup import Popup
from kivy.app import App

class WelcomeScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)


        with self.canvas.before:
            Color(0.08,0.08,0.12,1)
            self.rect = Rectangle(size=self.size, pos=self.pos)
        self.bind(size=self.update_rect, pos=self.update_rect)

        layout = BoxLayout(orientation="vertical", spacing=30, padding=[40,80,40,80])

        self.lbl_title = Label(
            text="[b]Добро пожаловать[/b]\nв Финансовый Ассистент",
            markup=True,
            font_size=32,
            halign="center",
            valign="middle",
            size_hint=(1,0.3),
            color=(1,1,1,1)
        )
        self.lbl_title.bind(size=self.lbl_title.setter("text_size"))
        layout.add_widget(self.lbl_title)

        self.lbl_subtitle = Label(
            text="Управляйте доходами и расходами,\nотслеживайте баланс и аналитику.",
            font_size=18,
            halign="center",
            valign="middle",
            size_hint=(1,0.2),
            color=(0.7,0.7,0.75,1)
        )
        self.lbl_subtitle.bind(size=self.lbl_subtitle.setter("text_size"))
        layout.add_widget(self.lbl_subtitle)

        btns = BoxLayout(orientation="vertical", spacing=20, size_hint=(1,0.5))

        self.btn_login = Button(
            text="Авторизация",
            font_size=20,
            background_normal="",
            background_color=(0.4,0.2,0.9,1),
            color=(1,1,1,1),
            size_hint=(1,None),
            height=dp(55)
        )
        self.btn_login.bind(on_press=lambda x: self.animate_button(x, "login"))

        btns.add_widget(self.btn_login)
        layout.add_widget(btns)
        self.add_widget(layout)

    def update_rect(self, *args):
        self.rect.pos = self.pos
        self.rect.size = self.size

    def animate_button(self, instance, screen_name=None):
        anim = Animation(size=(instance.width*1.02, instance.height*1.1), duration=0.1) + \
               Animation(size=(instance.width, instance.height), duration=0.1)
        if screen_name:
            anim.bind(on_complete=lambda *a: setattr(self.manager, "current", screen_name))
        anim.start(instance)