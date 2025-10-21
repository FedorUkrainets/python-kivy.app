# family.py
from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.scrollview import ScrollView
from kivy.metrics import dp
from kivy.app import App
from kivy.uix.widget import Widget

class FamilyScreen(Screen):
    def __init__(self, db=None, **kwargs):
        super().__init__(**kwargs)
        self.db = db
        root = BoxLayout(orientation="vertical", padding=dp(16), spacing=dp(12))

        root.add_widget(Label(text="[b]Семейные профили[/b]", markup=True, font_size=20, size_hint_y=None, height=dp(40)))

        self.scroll = ScrollView(size_hint=(1, 0.55))
        self.grid = GridLayout(cols=1, spacing=dp(8), size_hint_y=None)
        self.grid.bind(minimum_height=self.grid.setter('height'))
        self.scroll.add_widget(self.grid)
        root.add_widget(self.scroll)

        form = BoxLayout(orientation="vertical", size_hint_y=None, height=dp(140), spacing=dp(8))
        self.input_name = TextInput(hint_text="Имя (например: Мама)", multiline=False, size_hint_y=None, height=dp(44))
        self.input_role = TextInput(hint_text="Роль (опционально)", multiline=False, size_hint_y=None, height=dp(44))
        self.input_color = TextInput(hint_text="HEX цвет (например: #6C5CE7)", multiline=False, size_hint_y=None, height=dp(44))
        form.add_widget(self.input_name)
        form.add_widget(self.input_role)
        form.add_widget(self.input_color)
        root.add_widget(form)

        btns = BoxLayout(size_hint_y=None, height=dp(50), spacing=dp(8))
        btn_add = Button(text="Добавить участника", background_normal="", background_color=(0.2,0.6,0.9,1))
        btn_add.bind(on_press=self.add_member)
        btn_refresh = Button(text="Обновить")
        btn_refresh.bind(on_press=lambda *a: self.refresh())
        btn_back = Button(text="Назад", background_normal="", background_color=(0.25,0.25,0.25,1))
        btn_back.bind(on_press=lambda *a: setattr(self.manager, "current", "main"))
        btns.add_widget(btn_add)
        btns.add_widget(btn_refresh)
        btns.add_widget(btn_back)
        root.add_widget(btns)

        root.add_widget(Widget(size_hint_y=0.1))
        self.add_widget(root)
        self.refresh()

    def refresh(self):
        self.grid.clear_widgets()
        db_loc = self.db or App.get_running_app().db
        members = db_loc.get_family_members()
        if not members:
            self.grid.add_widget(Label(text="Нет членов семьи. Добавьте участника.", size_hint_y=None, height=dp(40)))
            return
        for m in members:
            row = BoxLayout(size_hint_y=None, height=dp(48))
            name_lbl = Label(text=f"[b]{m['name']}[/b] — {m.get('role','')}", markup=True, halign="left", valign="middle")
            name_lbl.bind(size=name_lbl.setter("text_size"))
            btn_del = Button(text="Удалить", size_hint_x=None, width=dp(100), background_normal="", background_color=(0.9,0.3,0.3,1))
            btn_del.bind(on_press=lambda inst, mid=m["id"]: self.delete_member(mid))
            row.add_widget(name_lbl)
            row.add_widget(btn_del)
            self.grid.add_widget(row)

    def add_member(self, *args):
        db_loc = self.db or App.get_running_app().db
        name = self.input_name.text.strip()
        role = self.input_role.text.strip()
        color = self.input_color.text.strip() or "#6C5CE7"
        if not name:
            return
        new_id = db_loc.add_family_member(name, role, color, "")
        # очистка полей
        self.input_name.text = ""
        self.input_role.text = ""
        self.input_color.text = ""
        self.refresh()

    def delete_member(self, member_id):
        db_loc = self.db or App.get_running_app().db
        db_loc.remove_family_member(member_id)
        self.refresh()