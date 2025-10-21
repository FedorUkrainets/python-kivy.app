# history.py
from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.scrollview import ScrollView
from kivy.uix.widget import Widget
from kivy.app import App
from kivy.graphics import Color, Rectangle
from kivy.metrics import dp
from kivy.animation import Animation

class HistoryScreen(Screen):
    def __init__(self, db=None, **kwargs):
        super().__init__(**kwargs)
        self.db = db
        with self.canvas.before:
            Color(0.08,0.08,0.10,1)
            self.rect = Rectangle(size=self.size, pos=self.pos)
        self.bind(size=self.update_rect, pos=self.update_rect)

        root = BoxLayout(orientation="vertical", padding=dp(16), spacing=dp(10))
        root.add_widget(Label(text="[b]Вся история[/b]", markup=True, font_size=20, size_hint_y=None, height=dp(36)))

        self.scroll = ScrollView()
        self.box_list = BoxLayout(orientation="vertical", size_hint_y=None, spacing=dp(6))
        self.box_list.bind(minimum_height=self.box_list.setter("height"))
        self.scroll.add_widget(self.box_list)
        root.add_widget(self.scroll)

        btn_back = Button(text="Назад", background_normal="", background_color=(0.25,0.25,0.25,1), size_hint_y=None, height=dp(48))
        btn_back.bind(on_press=lambda inst: self.animate_and_switch(inst, "main"))
        root.add_widget(btn_back)
        root.add_widget(Widget(size_hint_y=0.05))
        self.add_widget(root)

    def update_rect(self, *args):
        self.rect.pos = self.pos
        self.rect.size = self.size

    def animate_button(self, instance):
        anim = Animation(size=(instance.width*1.03,instance.height*1.03),duration=0.08)+Animation(size=(instance.width,instance.height),duration=0.08)
        anim.start(instance)

    def animate_and_switch(self, instance, screen_name):
        self.animate_button(instance)
        self.manager.current = screen_name

    def update_list(self):
        self.box_list.clear_widgets()
        db_loc = self.db or App.get_running_app().db
        history = db_loc.get_history()
        for typ, amount, category, desc, date, member_id in history:
            member_name = db_loc.get_member_name(member_id)
            color = (0.2,1,0.6,1) if typ == "income" else (1,0.3,0.3,1)
            lbl = Label(text=f"{date} [{member_name}] [{category}] {'+' if typ=='income' else '-'}{amount} ₽ ({desc})",
                        size_hint_y=None, height=dp(28), halign="left", valign="middle", color=color, markup=False)
            lbl.bind(size=lbl.setter("text_size"))
            self.box_list.add_widget(lbl)

    def on_pre_enter(self, *args):
        self.update_list()