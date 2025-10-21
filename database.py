# database.py
import sqlite3
from datetime import datetime
import hashlib
from typing import List, Dict, Any, Optional, Tuple

DB_DEFAULT = "finance.db"

class Database:
    def __init__(self, db_name: str = DB_DEFAULT):
        self.conn = sqlite3.connect(db_name, check_same_thread=False)
        self.conn.execute("PRAGMA foreign_keys = ON;")
        self.cursor = self.conn.cursor()
        self.current_user_id: Optional[int] = None
        self.create_tables()
        self._migrate_if_needed()

    # ---------- создание таблиц ----------
    def create_tables(self):
        # users
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL
            )
        """)
        # balance
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS balance (
                user_id INTEGER PRIMARY KEY,
                amount REAL DEFAULT 0,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            )
        """)
        # family_members (таблица членов семьи)
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS family_members (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                owner_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                role TEXT,
                color TEXT,
                avatar TEXT,
                FOREIGN KEY(owner_id) REFERENCES users(id) ON DELETE CASCADE
            )
        """)
        # history (операции) — содержит member_id (миграция добавит, если её не было ранее)
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                member_id INTEGER,
                type TEXT NOT NULL,
                amount REAL NOT NULL,
                category TEXT DEFAULT 'Прочее',
                description TEXT,
                date TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                FOREIGN KEY (member_id) REFERENCES family_members(id) ON DELETE SET NULL
            )
        """)
        # goals
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS goals (
                user_id INTEGER PRIMARY KEY,
                target REAL DEFAULT 0,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            )
        """)
        self.conn.commit()

    # ---------- миграция схемы ----------
    def _migrate_if_needed(self):
        # Добавим колонку member_id в history, если её нет (без потери данных)
        try:
            self.cursor.execute("PRAGMA table_info(history)")
            cols = [r[1] for r in self.cursor.fetchall()]
            if "member_id" not in cols:
                try:
                    self.cursor.execute("ALTER TABLE history ADD COLUMN member_id INTEGER;")
                    self.conn.commit()
                except Exception:
                    # если ALTER по какой-то причине не сработал, просто продолжаем
                    pass
        except Exception:
            pass

    # ---------- пароли ----------
    def _hash_password(self, password: str) -> str:
        return hashlib.sha256(password.encode("utf-8")).hexdigest()

    # ---------- users ----------
    def register_user(self, username: str, password: str) -> bool:
        """
        Регистрирует пользователя. Возвращает True при успехе, False при уже существующем username.
        При регистрации создаются: запись в balance, goals и default член семьи "Я".
        """
        try:
            ph = self._hash_password(password)
            self.cursor.execute("INSERT INTO users (username, password_hash) VALUES (?, ?)", (username, ph))
            user_id = self.cursor.lastrowid
            # инициализация баланса и цели
            self.cursor.execute("INSERT OR REPLACE INTO balance (user_id, amount) VALUES (?, ?)", (user_id, 0.0))
            self.cursor.execute("INSERT OR REPLACE INTO goals (user_id, target) VALUES (?, ?)", (user_id, 0.0))
            # создаём default member "Я"
            self.cursor.execute(
                "INSERT INTO family_members (owner_id, name, role, color, avatar) VALUES (?, ?, ?, ?, ?)",
                (user_id, "Я", "Владелец", "#6C5CE7", "")
            )
            self.conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False
        except Exception:
            return False

    def login_user(self, username: str, password: str) -> bool:
        """
        Логин: устанавливает self.current_user_id при успехе.
        Гарантирует наличие записей balance/goals и хотя бы одного family_member.
        """
        ph = self._hash_password(password)
        self.cursor.execute("SELECT id FROM users WHERE username=? AND password_hash=?", (username, ph))
        row = self.cursor.fetchone()
        if row:
            self.current_user_id = int(row[0])
            # ensure balance and goals
            self.cursor.execute("INSERT OR IGNORE INTO balance (user_id, amount) VALUES (?, ?)", (self.current_user_id, 0.0))
            self.cursor.execute("INSERT OR IGNORE INTO goals (user_id, target) VALUES (?, ?)", (self.current_user_id, 0.0))
            # ensure default family member exists
            self.cursor.execute("SELECT id FROM family_members WHERE owner_id=? LIMIT 1", (self.current_user_id,))
            if self.cursor.fetchone() is None:
                self.cursor.execute(
                    "INSERT INTO family_members (owner_id, name, role, color, avatar) VALUES (?, ?, ?, ?, ?)",
                    (self.current_user_id, "Я", "Владелец", "#6C5CE7", "")
                )
            self.conn.commit()
            return True
        return False

    def logout(self):
        self.current_user_id = None

    # ---------- проверка ----------
    def check_user(self):
        if self.current_user_id is None:
            raise ValueError("Пользователь не авторизован")

    # ---------- баланс ----------
    def get_balance(self) -> float:
        if self.current_user_id is None:
            return 0.0
        self.cursor.execute("SELECT amount FROM balance WHERE user_id=?", (self.current_user_id,))
        r = self.cursor.fetchone()
        return float(r[0]) if r and r[0] is not None else 0.0

    def update_balance(self, new_balance: float):
        if self.current_user_id is None:
            return
        self.cursor.execute("UPDATE balance SET amount=? WHERE user_id=?", (float(new_balance), self.current_user_id))
        self.conn.commit()

    # ---------- история ----------
    def add_history(self, ttype: str, amount: float, category: str = "Прочее",
                    description: str = "", date: Optional[str] = None, member_id: Optional[int] = None):
        """
        Добавляет запись в history.
        Порядок параметров совместим с остальными экранами:
          add_history(type, amount, category, description, date=None, member_id=None)
        """
        if self.current_user_id is None:
            return
        if date is None:
            date = datetime.now().strftime("%d.%m.%Y %H:%M")
        self.cursor.execute(
            "INSERT INTO history (user_id, member_id, type, amount, category, description, date) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (self.current_user_id, member_id, ttype, float(amount), category, description, date)
        )
        self.conn.commit()

    def get_history(self) -> List[Tuple[Any, ...]]:
        """
        Возвращает все записи history для текущего пользователя в формате:
          (type, amount, category, description, date, member_id)
        """
        if self.current_user_id is None:
            return []
        self.cursor.execute(
            "SELECT type, amount, category, description, date, member_id FROM history WHERE user_id=? ORDER BY id DESC",
            (self.current_user_id,)
        )
        return self.cursor.fetchall()

    # ---------- цели ----------
    def get_goal(self) -> float:
        if self.current_user_id is None:
            return 0.0
        self.cursor.execute("SELECT target FROM goals WHERE user_id=?", (self.current_user_id,))
        r = self.cursor.fetchone()
        return float(r[0]) if r and r[0] is not None else 0.0

    def set_goal(self, new_goal: float):
        if self.current_user_id is None:
            return
        self.cursor.execute("UPDATE goals SET target=? WHERE user_id=?", (float(new_goal), self.current_user_id))
        self.conn.commit()

    # ---------- family members ----------
    def get_family_members(self, user_id: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Возвращает членов семьи для owner_id.
        Если user_id не задан, используется self.current_user_id.
        Результат: список словарей {id, name, role, color, avatar}.
        """
        uid = user_id if user_id is not None else self.current_user_id
        if uid is None:
            return []
        self.cursor.execute("SELECT id, name, role, color, avatar FROM family_members WHERE owner_id=? ORDER BY id", (uid,))
        rows = self.cursor.fetchall()
        return [{"id": r[0], "name": r[1], "role": r[2], "color": r[3], "avatar": r[4]} for r in rows]

    def add_family_member(self, name: str, role: str = "", color: str = "#6C5CE7", avatar: str = "") -> Optional[int]:
        """
        Добавляет нового члена семьи для текущего пользователя.
        Ограничение: максимум 5 членов.
        Возвращает id нового члена или None (если не авторизован / достигнут лимит).
        """
        if self.current_user_id is None:
            return None
        self.cursor.execute("SELECT COUNT(*) FROM family_members WHERE owner_id=?", (self.current_user_id,))
        count = self.cursor.fetchone()[0]
        if count >= 5:
            return None
        self.cursor.execute(
            "INSERT INTO family_members (owner_id, name, role, color, avatar) VALUES (?, ?, ?, ?, ?)",
            (self.current_user_id, name, role, color, avatar)
        )
        self.conn.commit()
        return self.cursor.lastrowid

    def remove_family_member(self, member_id: int):
        """
        Удаляет члена семьи (если он принадлежит текущему пользователю).
        Записи history останутся, поле member_id станет NULL (ON DELETE SET NULL).
        """
        if self.current_user_id is None:
            return
        self.cursor.execute("SELECT owner_id FROM family_members WHERE id=?", (member_id,))
        r = self.cursor.fetchone()
        if not r or r[0] != self.current_user_id:
            return
        self.cursor.execute("DELETE FROM family_members WHERE id=?", (member_id,))
        self.conn.commit()

    def get_member_name(self, member_id: Optional[int]) -> str:
        if member_id is None:
            return "Я"
        self.cursor.execute("SELECT name FROM family_members WHERE id=?", (member_id,))
        r = self.cursor.fetchone()
        return r[0] if r else "Неизвестно"

    def get_member_summary(self, member_id: Optional[int]) -> Dict[str, float]:
        """Возвращает суммарные доходы, расходы и баланс для конкретного member_id (или для 'Я' при None)."""
        if self.current_user_id is None:
            return {"income": 0.0, "expense": 0.0, "balance": 0.0}
        if member_id is None:
            # NULL member_id => 'Я'
            self.cursor.execute("SELECT IFNULL(SUM(amount),0) FROM history WHERE user_id=? AND type='income' AND member_id IS NULL", (self.current_user_id,))
            inc = self.cursor.fetchone()[0] or 0.0
            self.cursor.execute("SELECT IFNULL(SUM(amount),0) FROM history WHERE user_id=? AND type='expense' AND member_id IS NULL", (self.current_user_id,))
            exp = self.cursor.fetchone()[0] or 0.0
        else:
            self.cursor.execute("SELECT IFNULL(SUM(amount),0) FROM history WHERE user_id=? AND type='income' AND member_id=?", (self.current_user_id, member_id))
            inc = self.cursor.fetchone()[0] or 0.0
            self.cursor.execute("SELECT IFNULL(SUM(amount),0) FROM history WHERE user_id=? AND type='expense' AND member_id=?", (self.current_user_id, member_id))
            exp = self.cursor.fetchone()[0] or 0.0
        return {"income": float(inc), "expense": float(exp), "balance": float(inc) - float(exp)}

    def get_all_members_with_summary(self) -> List[Dict[str, Any]]:
        members = self.get_family_members()
        res = []
        for m in members:
            s = self.get_member_summary(m["id"])
            row = {"id": m["id"], "name": m["name"], "role": m["role"], "color": m["color"], **s}
            res.append(row)
        # include 'Я' aggregate if missing
        has_me = any(m["name"] == "Я" for m in members)
        if not has_me:
            s = self.get_member_summary(None)
            res.insert(0, {"id": None, "name": "Я", "role": "Владелец", "color": "#6C5CE7", **s})
        return res

    # ---------- категории ----------
    def get_all_categories(self) -> List[str]:
        return [
            "Еда", "Транспорт", "Развлечения", "Покупки", "Коммунальные",
            "Здоровье", "Образование", "Подарки", "Одежда", "Прочее"
        ]

    # ---------- close ----------
    def close(self):
        try:
            self.conn.commit()
        except Exception:
            pass
        try:
            self.conn.close()
        except Exception:
            pass
