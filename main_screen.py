# main_screen.py
from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.label import Label
from kivy.uix.widget import Widget
from kivy.uix.behaviors import ButtonBehavior
from kivy.uix.spinner import Spinner
from kivy.graphics import Color, RoundedRectangle, Rectangle
from kivy.animation import Animation
from kivy.metrics import dp
from kivy.properties import ListProperty, StringProperty, NumericProperty
from kivy.app import App


class CardButton(ButtonBehavior, BoxLayout):
    bg_color = ListProperty([0.2, 0.6, 0.9, 1])
    title = StringProperty("")

    def __init__(self, title="", bg_color=None, **kwargs):
        super().__init__(orientation="vertical", padding=dp(14), spacing=dp(6), **kwargs)
        if bg_color:
            self.bg_color = bg_color
        self.title = title

        with self.canvas.before:
            self._color_inst = Color(*self.bg_color)
            self._rect = RoundedRectangle(pos=self.pos, size=self.size, radius=[dp(16)])
        self.bind(pos=self._update_rect, size=self._update_rect, bg_color=self._update_color)

        lbl_title = Label(
            text=self.title,
            font_size=18,
            size_hint=(1, None),
            height=dp(36),
            halign="center",
            valign="middle",
            color=(1, 1, 1, 1)
        )
        lbl_title.bind(size=lbl_title.setter("text_size"))
        self.add_widget(Widget(size_hint_y=1))
        self.add_widget(lbl_title)
        self.add_widget(Widget(size_hint_y=0.2))

    def _update_rect(self, *args):
        self._rect.pos = self.pos
        self._rect.size = self.size

    def _update_color(self, *args):
        r, g, b, a = self.bg_color
        self._color_inst.r, self._color_inst.g, self._color_inst.b, self._color_inst.a = r, g, b, a

    def on_press(self):
        r, g, b, a = self.bg_color
        dark = (max(0, r * 0.8), max(0, g * 0.8), max(0, b * 0.8), a)
        Animation(r=dark[0], g=dark[1], b=dark[2], a=dark[3], duration=0.07).start(self._color_inst)

    def on_release(self):
        r, g, b, a = self.bg_color
        Animation(r=r, g=g, b=b, a=a, duration=0.1).start(self._color_inst)
        return super().on_release()


class GoalProgressBar(BoxLayout):
    progress = NumericProperty(0.0)

    def __init__(self, **kwargs):
        super().__init__(orientation="vertical", size_hint=(1, None), height=dp(20), **kwargs)
        with self.canvas.before:
            Color(0.18, 0.18, 0.25, 1)
            self.bg_rect = RoundedRectangle(pos=self.pos, size=self.size, radius=[dp(10)])
            Color(0.6, 0.2, 1.0, 1)
            self.fill_rect = RoundedRectangle(pos=self.pos, size=(0, self.height), radius=[dp(10)])
        self.bind(pos=self._update_rects, size=self._update_rects, progress=self._update_progress)

    def _update_rects(self, *args):
        self.bg_rect.pos = self.pos
        self.bg_rect.size = self.size
        self._update_progress()

    def _update_progress(self, *args):
        total_width = self.width
        fill_width = max(0, min(self.progress, 1)) * total_width
        self.fill_rect.pos = self.pos
        self.fill_rect.size = (fill_width, self.height)

    def animate_to(self, value):
        Animation(progress=value, duration=0.6, t="out_quad").start(self)


class MainScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        with self.canvas.before:
            Color(0.08, 0.08, 0.12, 1)
            self._bg_rect = Rectangle(pos=self.pos, size=self.size)
        self.bind(pos=self._update_bg, size=self._update_bg)

        root = BoxLayout(orientation="vertical", padding=dp(18), spacing=dp(14))

        # ---------- Блок баланса ----------
        self.balance_card = BoxLayout(orientation="vertical", size_hint=(1, None), height=dp(180), padding=dp(12), spacing=dp(6))
        with self.balance_card.canvas.before:
            Color(0.13, 0.12, 0.16, 1)
            self._bal_rect = RoundedRectangle(pos=self.balance_card.pos, size=self.balance_card.size, radius=[dp(18)])
        self.balance_card.bind(pos=lambda *a: setattr(self._bal_rect, "pos", self.balance_card.pos),
                               size=lambda *a: setattr(self._bal_rect, "size", self.balance_card.size))

        self.lbl_balance_title = Label(text="[b]Баланс[/b]", markup=True, font_size=14,
                                       size_hint=(1, None), height=dp(26),
                                       halign="left", valign="middle", color=(0.85, 0.85, 0.9, 1))
        self.lbl_balance_title.bind(size=self.lbl_balance_title.setter("text_size"))

        self.lbl_balance_amount = Label(text="₽ 0.00", font_size=26,
                                        size_hint=(1, None), height=dp(44),
                                        halign="left", valign="middle", color=(1, 1, 1, 1))
        self.lbl_balance_amount.bind(size=self.lbl_balance_amount.setter("text_size"))

        self.goal_bar = GoalProgressBar()
        self.lbl_goal_status = Label(text="", font_size=12, color=(0.7, 0.7, 0.9, 1),
                                     size_hint=(1, None), height=dp(20), halign="right", valign="middle")
        self.lbl_goal_status.bind(size=self.lbl_goal_status.setter("text_size"))

        # ---------- Spinner выбора ----------
        app = App.get_running_app()
        self.members = app.db.get_all_members_with_summary()
        names = ["Все"] + [m["name"] for m in self.members]
        self.spinner_member = Spinner(
            text="Я" if "Я" in names else names[0],
            values=names,
            size_hint=(None, None),
            size=(dp(150), dp(36)),
            pos_hint={"right": 1},
        )
        self.spinner_member.bind(text=self.on_member_select)

        # ---------- Layout с балансом + переключателем ----------
        bal_layout = BoxLayout(orientation="horizontal", size_hint=(1, None), height=dp(44))
        bal_layout.add_widget(self.lbl_balance_amount)
        bal_layout.add_widget(self.spinner_member)

        self.balance_card.add_widget(self.lbl_balance_title)
        self.balance_card.add_widget(bal_layout)
        self.balance_card.add_widget(self.goal_bar)
        self.balance_card.add_widget(self.lbl_goal_status)
        root.add_widget(self.balance_card)

        # ---------- Кнопки ----------
        scroll = ScrollView(size_hint=(1, 1))
        grid = GridLayout(cols=2, spacing=dp(12), padding=(0, dp(6)), size_hint_y=None)
        grid.bind(minimum_height=grid.setter('height'))

        buttons = [
            ("Доходы", "income", (0.15, 0.7, 0.4, 1)),
            ("Расходы", "expense", (0.9, 0.3, 0.3, 1)),
            ("История", "history", (0.2, 0.6, 0.9, 1)),
            ("Цели", "goal", (0.8, 0.6, 0.2, 1)),
            ("Аналитика", "analytics", (0.5, 0.4, 0.9, 1)),
            ("Семья", "family", (0.3, 0.7, 0.5, 1)),
            ("Выход", "login", (0.45, 0.45, 0.45, 1))
        ]

        for title, screen_name, color in buttons:
            card = CardButton(title=title, bg_color=color, size_hint_y=None, height=dp(120))
            card.bind(on_release=lambda inst, s=screen_name: self.switch_screen(s))
            grid.add_widget(card)

        scroll.add_widget(grid)
        root.add_widget(scroll)
        self.add_widget(root)

    # ---------- Логика обновления ----------
    def _update_bg(self, *args):
        self._bg_rect.pos = self.pos
        self._bg_rect.size = self.size

    def on_pre_enter(self, *args):
        self.update_members()
        self.update_balance_display()

    def update_members(self):
        app = App.get_running_app()
        self.members = app.db.get_all_members_with_summary()
        names = ["Все"] + [m["name"] for m in self.members]
        self.spinner_member.values = names
        if "Я" in names:
            self.spinner_member.text = "Я"

    def on_member_select(self, spinner, name):
        self.update_balance_display()

    def update_balance_display(self):
        app = App.get_running_app()
        db = app.db
        selected = self.spinner_member.text

        # Если выбран "Все" — общий баланс семьи
        if selected == "Все":
            total_balance = 0
            for m in self.members:
                if m["name"] == "Я":
                    total_balance += db.get_balance()
                else:
                    total_balance += m["balance"]
            self.lbl_balance_amount.text = f"₽ {total_balance:,.2f}"
            self.lbl_goal_status.text = "Общий баланс семьи"
            self.goal_bar.animate_to(0)
            return

        # Баланс выбранного участника
        member = next((m for m in self.members if m["name"] == selected), None)
        if member:
            if selected == "Я":
                bal = db.get_balance()
                target = db.get_goal()
                progress = min(1, bal / target) if target > 0 else 0
                self.goal_bar.animate_to(progress)
                self.lbl_goal_status.text = f"Цель: {bal:,.0f} / {target:,.0f} ₽" if target > 0 else f"Баланс: {bal:,.0f} ₽"
            else:
                bal = member["balance"]
                self.goal_bar.animate_to(0)
                self.lbl_goal_status.text = f"Баланс участника: {bal:,.0f} ₽"
            self.lbl_balance_amount.text = f"₽ {bal:,.2f}"

    def switch_screen(self, screen_name):
        app = App.get_running_app()
        if screen_name == "login":
            try:
                app.db.logout()
            except Exception:
                pass
        self.manager.current = screen_name
