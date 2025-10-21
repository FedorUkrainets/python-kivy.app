from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.spinner import Spinner
from kivy.uix.scrollview import ScrollView
from kivy.uix.widget import Widget
from kivy.app import App
from kivy.graphics import Color, Rectangle, RoundedRectangle
from kivy.animation import Animation
from kivy.metrics import dp

class ExpenseScreen(Screen):
    def __init__(self, db=None, **kwargs):
        super().__init__(**kwargs)
        self.db = db
        with self.canvas.before:
            Color(0.08,0.08,0.10,1)
            self.rect = Rectangle(size=self.size, pos=self.pos)
        self.bind(size=self.update_rect, pos=self.update_rect)

        root = BoxLayout(orientation="vertical", padding=dp(16), spacing=dp(12))

        # Баланс
        self.card = BoxLayout(size_hint_y=None, height=dp(100))
        with self.card.canvas.before:
            Color(0.13,0.12,0.16,1)
            self._card_bg = RoundedRectangle(pos=self.card.pos, size=self.card.size, radius=[16])
        self.card.bind(pos=lambda *a: setattr(self._card_bg, "pos", self.card.pos),
                       size=lambda *a: setattr(self._card_bg, "size", self.card.size))
        self.lbl_balance = Label(text="", font_size=26, halign="center", valign="middle", color=(1,1,1,1))
        self.lbl_balance.bind(size=self.lbl_balance.setter("text_size"))
        self.card.add_widget(self.lbl_balance)
        root.add_widget(self.card)

        root.add_widget(Label(text="[b]Добавить расход[/b]", markup=True, size_hint_y=None, height=dp(30)))

        # Сумма
        self.input_amount = TextInput(hint_text="Сумма", multiline=False, input_filter="int", size_hint_y=None, height=dp(46))
        root.add_widget(self.input_amount)

        # Категории расходов
        categories = []
        try:
            db_loc = self.db or App.get_running_app().db
            categories = db_loc.get_all_categories()
        except Exception:
            categories = ["Еда","Транспорт","Прочее"]
        self.input_category = Spinner(text=categories[0], values=categories, size_hint_y=None, height=dp(46))
        root.add_widget(self.input_category)

        # Выбор члена семьи
        self.member_spinner = Spinner(text="Я", size_hint_y=None, height=dp(46))
        self.member_spinner.bind(text=self.on_member_select)
        root.add_widget(self.member_spinner)

        self.input_description = TextInput(hint_text="Описание (опционально)", multiline=False, size_hint_y=None, height=dp(46))
        root.add_widget(self.input_description)

        # Кнопки
        btns = BoxLayout(size_hint_y=None, height=dp(50), spacing=dp(8))
        self.btn_add = Button(text="Добавить расход", background_normal="", background_color=(0.9,0.3,0.3,1))
        self.btn_add.bind(on_press=self.add_expense)
        btn_back = Button(text="Назад", background_normal="", background_color=(0.25,0.25,0.25,1))
        btn_back.bind(on_press=lambda inst: self.animate_and_switch(inst, "main"))
        btns.add_widget(self.btn_add)
        btns.add_widget(btn_back)
        root.add_widget(btns)

        # История расходов
        root.add_widget(Label(text="[b]История расходов[/b]", markup=True, size_hint_y=None, height=dp(26)))
        self.scroll = ScrollView()
        self.box_list = BoxLayout(orientation="vertical", size_hint_y=None, spacing=dp(6))
        self.box_list.bind(minimum_height=self.box_list.setter("height"))
        self.scroll.add_widget(self.box_list)
        root.add_widget(self.scroll)

        root.add_widget(Widget(size_hint_y=0.1))
        self.add_widget(root)

    # ----------------- вспомогательные -----------------
    def update_rect(self, *args):
        self.rect.pos = self.pos
        self.rect.size = self.size

    def animate_button(self, instance):
        anim = Animation(size=(instance.width*1.03, instance.height*1.03), duration=0.08) + Animation(size=(instance.width,instance.height), duration=0.08)
        anim.start(instance)

    def animate_and_switch(self, instance, screen_name):
        self.animate_button(instance)
        self.manager.current = screen_name

    def _member_values(self):
        try:
            db_loc = self.db or App.get_running_app().db
            members = db_loc.get_family_members()
            vals = ["Я"]
            for m in members:
                if m["name"] == "Я":
                    continue
                vals.append(m["name"])
            return vals
        except Exception:
            return ["Я"]

    def on_member_select(self, spinner, text):
        db_loc = self.db or App.get_running_app().db
        member_id = None if text == "Я" else next((m["id"] for m in db_loc.get_family_members() if m["name"] == text), None)
        summary = db_loc.get_member_summary(member_id)
        self.lbl_balance.text = f"₽ {summary['balance']:,.2f}"

    # ----------------- логика добавления расхода -----------------
    def add_expense(self, instance):
        self.animate_button(instance)
        try:
            amount = int(self.input_amount.text)
        except Exception:
            return
        category = self.input_category.text
        description = self.input_description.text.strip()
        member_name = self.member_spinner.text
        db_loc = self.db or App.get_running_app().db
        member_id = None if member_name == "Я" else next((m["id"] for m in db_loc.get_family_members() if m["name"] == member_name), None)
        db_loc.add_history("expense", amount, category, description, None, member_id)
        self.on_member_select(self.member_spinner, member_name)
        self.input_amount.text = ""
        self.input_description.text = ""
        self.member_spinner.values = self._member_values()
        self.update_list()

    def update_list(self):
        self.box_list.clear_widgets()
        db_loc = self.db or App.get_running_app().db
        history = db_loc.get_history()
        expenses = [h for h in history if h[0] == "expense"]
        for typ, amount, category, desc, date, member_id in expenses:
            member_name = db_loc.get_member_name(member_id)
            lbl = Label(text=f"{date} [{member_name}] [{category}] -{amount} ₽ ({desc})",
                        size_hint_y=None, height=dp(28), halign="left", valign="middle", color=(1,0.3,0.3,1))
            lbl.bind(size=lbl.setter("text_size"))
            self.box_list.add_widget(lbl)

    def on_pre_enter(self, *args):
        self.member_spinner.values = self._member_values()
        self.member_spinner.text = "Я"
        self.on_member_select(self.member_spinner, "Я")
        self.update_list()
