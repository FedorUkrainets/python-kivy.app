# app.py
from kivy.app import App
from kivy.uix.screenmanager import ScreenManager
from welcome import WelcomeScreen
from main_screen import MainScreen
from login import LoginScreen
from analytics import AnalyticsScreen
from income import IncomeScreen
from expense import ExpenseScreen
from history import HistoryScreen
from goal import GoalScreen
from family import FamilyScreen
from database import Database

class FUApp(App):
    def build(self):
        self.title = "Финансовый ассистент"
        self.db = Database()

        self.manager = ScreenManager()
        self.manager.add_widget(WelcomeScreen(name="welcome"))
        self.manager.add_widget(LoginScreen(name="login"))
        self.manager.add_widget(MainScreen(name="main"))
        self.manager.add_widget(AnalyticsScreen(name="analytics", db=self.db))
        self.manager.add_widget(IncomeScreen(name="income", db=self.db))
        self.manager.add_widget(ExpenseScreen(name="expense", db=self.db))
        self.manager.add_widget(HistoryScreen(name="history", db=self.db))
        self.manager.add_widget(GoalScreen(name="goal", db=self.db))
        self.manager.add_widget(FamilyScreen(name="family", db=self.db))

        return self.manager

    def on_stop(self):
        try:
            self.db.close()
        except Exception:
            pass

if __name__ == "__main__":
    FUApp().run()
