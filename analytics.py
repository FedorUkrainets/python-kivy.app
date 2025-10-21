from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.spinner import Spinner
from kivy.uix.button import Button
from kivy.uix.togglebutton import ToggleButton
from kivy.uix.scrollview import ScrollView
from kivy.uix.gridlayout import GridLayout
from kivy.uix.widget import Widget
from kivy.metrics import dp
from kivy.app import App
from kivy.graphics import Color, Ellipse, Line, Rectangle
from kivy.clock import Clock
from collections import defaultdict, OrderedDict
from datetime import datetime

class PieWidget(Widget):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.data = {}
        self.colors = [(0.9,0.4,0.4,1),(0.4,0.9,0.6,1),(0.4,0.6,0.9,1),(0.9,0.8,0.4,1),(0.7,0.4,0.9,1),(0.4,0.9,0.8,1)]
        self.bind(pos=self.draw, size=self.draw)

    def set_data(self, data: dict):
        self.data = data or {}
        self.draw()

    def draw(self, *a):
        self.canvas.clear()
        total = sum(self.data.values())
        if total <= 0:
            return
        cx, cy = self.center
        radius = min(self.size) * 0.4
        start = 0
        i = 0
        with self.canvas:
            for k, v in self.data.items():
                angle = 360 * v / total
                Color(*self.colors[i % len(self.colors)])
                Ellipse(pos=(cx-radius, cy-radius), size=(radius*2, radius*2), angle_start=start, angle_end=start+angle)
                start += angle
                i += 1
            # inner circle to make donut
            Color(0.08,0.08,0.10,1)
            Ellipse(pos=(cx-radius*0.5, cy-radius*0.5), size=(radius, radius))

class LineWidget(Widget):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.points = []
        self.bind(pos=self.draw, size=self.draw)

    def set_points(self, points):
        # points: list of (date_obj, value)
        self.points = points or []
        self.draw()

    def draw(self, *a):
        self.canvas.clear()
        if not self.points:
            return
        xs = [p[0].timestamp() for p in self.points]
        ys = [p[1] for p in self.points]
        minx, maxx = min(xs), max(xs)
        miny, maxy = min(ys), max(ys)
        if miny == maxy:
            miny = 0
        w, h = self.size
        px, py = self.pos
        with self.canvas:
            Color(0.1,0.6,1,1)
            pts = []
            for x_val, y_val in zip(xs, ys):
                nx = px + ((x_val - minx) / (maxx - minx if maxx!=minx else 1)) * w
                ny = py + ((y_val - miny) / (maxy - miny if maxy!=miny else 1)) * h
                pts.extend([nx, ny])
            if pts:
                Line(points=pts, width=2)

class AnalyticsScreen(Screen):
    def __init__(self, db=None, **kwargs):
        super().__init__(**kwargs)
        self.db = db
        self.mode = "expense"
        with self.canvas.before:
            Color(0.08,0.08,0.10,1)
            self.bg = Rectangle(size=self.size, pos=self.pos)
        self.bind(size=self._upd, pos=self._upd)

        root = BoxLayout(orientation="vertical", padding=dp(12), spacing=dp(8))

        header = BoxLayout(size_hint_y=None, height=dp(44), spacing=dp(8))
        self.member_spinner = Spinner(text="Все участники", values=["Все участники"], size_hint_x=0.5)
        header.add_widget(self.member_spinner)
        self.btn_exp = ToggleButton(text="Расходы", group="mode", state="down")
        self.btn_inc = ToggleButton(text="Доходы", group="mode")
        self.btn_exp.bind(on_press=lambda *a: self.set_mode("expense"))
        self.btn_inc.bind(on_press=lambda *a: self.set_mode("income"))
        header.add_widget(self.btn_exp)
        header.add_widget(self.btn_inc)
        btn_refresh = Button(text="Обновить", size_hint_x=0.2)
        btn_refresh.bind(on_press=lambda *a: self.refresh())
        header.add_widget(btn_refresh)
        root.add_widget(header)

        main = BoxLayout(spacing=dp(8))
        left = BoxLayout(orientation="vertical", size_hint_x=0.6)
        self.pie = PieWidget(size_hint_y=0.6)
        left.add_widget(self.pie)
        self.line = LineWidget(size_hint_y=0.4)
        left.add_widget(self.line)
        main.add_widget(left)

        right = BoxLayout(orientation="vertical", size_hint_x=0.4)
        self.details = BoxLayout(orientation="vertical")
        self.details_scroll = ScrollView()
        self.details_grid = GridLayout(cols=1, size_hint_y=None, spacing=dp(6))
        self.details_grid.bind(minimum_height=self.details_grid.setter('height'))
        self.details_scroll.add_widget(self.details_grid)
        right.add_widget(self.details_scroll)
        main.add_widget(right)

        root.add_widget(main)

        bottom = BoxLayout(size_hint_y=None, height=dp(48))
        btn_back = Button(text="Назад", background_normal="", background_color=(0.25,0.25,0.25,1))
        btn_back.bind(on_press=lambda *a: setattr(self.manager, "current", "main"))
        bottom.add_widget(btn_back)
        root.add_widget(bottom)

        self.add_widget(root)
        Clock.schedule_once(lambda dt: self.refresh(), 0.1)

    def _upd(self, *a):
        self.bg.size = self.size
        self.bg.pos = self.pos

    def set_mode(self, mode):
        self.mode = mode
        self.refresh()

    def _load_history(self):
        db_loc = self.db or App.get_running_app().db
        return db_loc.get_history()

    def refresh(self):
        db_loc = self.db or App.get_running_app().db
        members = ["Все участники"] + [m["name"] for m in db_loc.get_family_members()]
        self.member_spinner.values = members
        if self.member_spinner.text not in members:
            self.member_spinner.text = "Все участники"

        raw = self._load_history()
        # filter by mode and member
        selected_member = self.member_spinner.text
        data_by_cat = defaultdict(float)
        daily = defaultdict(float)
        for typ, amount, category, desc, date_str, member_id in raw:
            if self.mode == "income" and typ != "income":
                continue
            if self.mode == "expense" and typ != "expense":
                continue
            # member filter
            member_name = db_loc.get_member_name(member_id)
            if selected_member != "Все участники" and member_name != selected_member:
                continue
            data_by_cat[category or "Прочее"] += amount
            # parse date
            dt = None
            try:
                dt = datetime.strptime(date_str, "%d.%m.%Y %H:%M")
            except:
                try:
                    dt = datetime.strptime(date_str.split()[0], "%d.%m.%Y")
                except:
                    dt = None
            if dt:
                daily[dt.date()] += amount

        # pie
        self.pie.set_data(dict(data_by_cat))
        # trend: convert daily to sorted list
        if daily:
            ordered = OrderedDict(sorted(daily.items()))
            points = [(datetime.combine(d, datetime.min.time()), v) for d, v in ordered.items()]
            self.line.set_points(points)
        else:
            self.line.set_points([])

        # details
        self.details_grid.clear_widgets()
        if not data_by_cat:
            self.details_grid.add_widget(Label(text="Нет данных для отображения", size_hint_y=None, height=dp(40)))
        else:
            for cat, val in sorted(data_by_cat.items(), key=lambda x: -x[1]):
                lbl = Label(text=f"{cat}: {val:.2f} ₽", size_hint_y=None, height=dp(30), halign="left", valign="middle")
                lbl.bind(size=lbl.setter("text_size"))
                self.details_grid.add_widget(lbl)

    def on_pre_enter(self, *args):
        Clock.schedule_once(lambda dt: self.refresh(), 0.05)