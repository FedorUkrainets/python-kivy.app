# goal.py
from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.widget import Widget
from kivy.app import App
from kivy.graphics import Color, Rectangle
from kivy.animation import Animation
from kivy.metrics import dp

class GoalScreen(Screen):
    def __init__(self, db=None, **kwargs):  # <-- добавлено db
        super().__init__(**kwargs)
        self.db = db  # <-- сохраняем базу

        with self.canvas.before:
            Color(0.08,0.08,0.10,1)
            self.rect = Rectangle(size=self.size, pos=self.pos)
        self.bind(size=self.update_rect, pos=self.update_rect)

        root = BoxLayout(orientation="vertical", padding=dp(20), spacing=dp(15))

        lbl_title = Label(
            text="[b]Установите финансовую цель[/b]",
            markup=True,
            font_size=20,
            size_hint_y=None,
            height=dp(30),
            halign="center",
            valign="middle",
            color=(0.9,0.5,0.5,1)
        )
        lbl_title.bind(size=lbl_title.setter("text_size"))
        root.add_widget(lbl_title)

        self.input_goal = TextInput(
            hint_text="Введите сумму",
            multiline=False,
            input_filter="int",
            size_hint_y=None,
            height=dp(46),
            foreground_color=(1,1,1,1),
            background_color=(0.15,0.15,0.2,1),
            cursor_color=(0.9,0.5,0.5,1),
            padding=(dp(12),dp(12))
        )
        root.add_widget(self.input_goal)

        # используем self.db вместо App.get_running_app()
        try:
            current_goal = self.db.get_goal() if self.db else 0.0
        except Exception:
            current_goal = 0.0

        self.lbl_current_goal = Label(
            text=f"Текущая цель: {current_goal:.0f} ₽",
            font_size=16,
            size_hint_y=None,
            height=dp(30),
            halign="center",
            valign="middle",
            color=(1,1,1,1)
        )
        self.lbl_current_goal.bind(size=self.lbl_current_goal.setter("text_size"))
        root.add_widget(self.lbl_current_goal)

        btns = BoxLayout(spacing=dp(10), size_hint_y=None, height=dp(50))
        self.btn_set = Button(text="Поставить цель", background_normal="", background_color=(0.2,0.6,0.9,1), color=(1,1,1,1))
        self.btn_set.bind(on_press=self.set_goal)
        self.btn_back = Button(text="Назад", background_normal="", background_color=(0.25,0.25,0.25,1), color=(1,1,1,1))
        self.btn_back.bind(on_press=lambda inst: self.animate_and_switch(inst, "main"))
        btns.add_widget(self.btn_set)
        btns.add_widget(self.btn_back)
        root.add_widget(btns)
        root.add_widget(Widget(size_hint_y=1))
        self.add_widget(root)

    def update_rect(self, *args):
        self.rect.pos = self.pos
        self.rect.size = self.size

    def animate_button(self, instance):
        anim = Animation(size=(instance.width*1.03, instance.height*1.03), duration=0.08) + Animation(size=(instance.width, instance.height), duration=0.08)
        anim.start(instance)

    def animate_and_switch(self, instance, screen_name):
        self.animate_button(instance)
        self.manager.current = screen_name

    def set_goal(self, instance):
        self.animate_button(instance)
        try:
            new_goal = int(self.input_goal.text)
        except Exception:
            new_goal = 0
        try:
            if self.db:
                self.db.set_goal(new_goal)
            self.lbl_current_goal.text = f"Текущая цель: {new_goal} ₽"
        except Exception:
            pass
        self.input_goal.text = ""
