import sys
from datetime import datetime, timedelta, time
from PyQt5.QtCore import Qt, QTimer, QThread

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QLabel, QVBoxLayout,
    QHBoxLayout, QLineEdit, QPushButton, QTabWidget, QTableWidget,
    QTableWidgetItem, QCompleter, QComboBox, QTextEdit, QFrame, QMenu,
    QCheckBox, QDoubleSpinBox
)
from PyQt5.QtGui import QColor

import qdarkstyle

# Autoruns importer.py
import importer

from Admin_Focus import get_admin_focus
from Weekly_Focus import get_weekly_focus
from Student_Focus import get_student_focus, get_all_students

# --- Discord thread loader --------------------------------------------------
import discord_client
discord_client.start_background_client()
# ---------------------------------------------------------------------------




def format_week_range_label(week_key):
    year, week = map(int, week_key.split("-W"))
    monday = datetime.strptime(f'{year}-W{week}-1', "%G-W%V-%u")
    sunday = monday + timedelta(days=6)
    return f"{monday.strftime('%b')} {monday.day}–{sunday.strftime('%b')} {sunday.day} ({week_key})"


def float_to_ampm(hour_float):
    if hour_float is None:
        return "—"
    hour = int(hour_float)
    minute = int(round((hour_float - hour) * 60))
    return time(hour, minute).strftime("%I:%M %p")



class WeeklyFocusTab(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout()
        label = QLabel("📊 Weekly Focus")
        label.setStyleSheet("font-size: 24px; font-weight: bold;")

        data = get_weekly_focus()
        for table_name, table_content in data.items():
            print(table_name)
            label = QLabel(f"{table_name}")
            label.setStyleSheet("font-size: 18px; font-weight: bold;")

            table = QTableWidget()
            table.setColumnCount(4)
            table.setHorizontalHeaderLabels(["Day", "Avg Students", "Std Dev", "Variance"])


            table.setRowCount(len(table_content))
            print(table_content)
            for row_idx, row in enumerate(table_content):
                print(row_idx)
                print(row)
                print(row["day"])
                table.setItem(row_idx, 0, QTableWidgetItem(row["day"]))
                table.setItem(row_idx, 1, QTableWidgetItem(str(row["avg_total"] or "—")))
                table.setItem(row_idx, 2, QTableWidgetItem(str(row["std_dev"] or "—")))
                table.setItem(row_idx, 3, QTableWidgetItem(str(row["variance"] or "—")))

            layout.addWidget(label)
            layout.addWidget(table)
            self.setLayout(layout)
            table.resizeColumnsToContents()


class StudentFocusTab(QWidget):
    def __init__(self):
        super().__init__()
        self.students = get_all_students()
        self.init_ui()

    class _DiscordRefreshThread(QThread):
        def run(self):
            import asyncio
            asyncio.run(discord_client.pull_threads_once())

    def run_thread_refresh(self):
        self.status_label.setText("Status: Pulling threads…")
        discord_client.trigger_refresh()          # runs on Discord loop, returns immediately


    def update_status_label(self):
        from discord_client import PULL_IN_PROGRESS

        if PULL_IN_PROGRESS:
            self.status_label.setText("Status: Pulling threads…")
            self.refresh_button.setEnabled(False)
            self.status_timer.setInterval(1000)
        else:
            self.status_label.setText("Status: Idle")
            self.refresh_button.setEnabled(True)
            self.status_timer.setInterval(3000)

    def init_ui(self):
        layout = QVBoxLayout()

        # Title
        title = QLabel("🎓 Student Focus")
        title.setStyleSheet("font-size: 24px; font-weight: bold;")

        # Search bar
        search_layout = QHBoxLayout()
        self.input = QLineEdit()
        self.input.setPlaceholderText("Enter student name...")

        completer = QCompleter(self.students)
        completer.setCaseSensitivity(False)
        self.input.setCompleter(completer)

        self.dropdown = QComboBox()
        self.dropdown.addItem("— Select —")
        self.dropdown.addItems(self.students)
        self.dropdown.currentIndexChanged.connect(self.set_input_from_dropdown)

        self.button = QPushButton("Search")
        self.button.clicked.connect(self.load_student_data)

        search_layout.addWidget(self.input)
        search_layout.addWidget(self.dropdown)
        search_layout.addWidget(self.button)

        # Summary text
        self.summary_label = QLabel("")
        self.summary_label.setStyleSheet("font-size: 18px; padding: 10px 0;")
        self.summary_label.setWordWrap(True)

        # Likelihood table
        self.likelihood_table = QTableWidget()
        self.likelihood_table.setColumnCount(3)
        self.likelihood_table.setHorizontalHeaderLabels(["Day", "Visits", "Likelihood"])

        # Weekly presence matrix (dynamic)
        self.weekly_matrix_table = QTableWidget()

        # Arrival stats table
        self.arrival_table = QTableWidget()
        self.arrival_table.setColumnCount(5)
        self.arrival_table.setHorizontalHeaderLabels(["Avg Arrival", "Q1", "Q3", "Std Dev (Hours)", "Variance"])
        self.arrival_table.setVerticalHeaderLabels(["Weekdays", "Saturday"])

        # Layout
        layout.addWidget(title)
        layout.addLayout(search_layout)
        layout.addWidget(self.summary_label)
        layout.addWidget(QLabel("Likelihood of Arrival"))
        layout.addWidget(self.likelihood_table)
        layout.addWidget(QLabel("Weekly Attendance Matrix"))
        layout.addWidget(self.weekly_matrix_table)
        layout.addWidget(QLabel("Arrival Time Analysis"))
        layout.addWidget(self.arrival_table)

        discord_layout = QVBoxLayout()
        # --- Discord Section ---
        discord_layout.addWidget(QLabel("⚡🤖 Discord Focus"))

        self.discord_thread_box = QTextEdit()
        self.discord_thread_box.setReadOnly(True)
        discord_layout.addWidget(self.discord_thread_box)

        # --- Pull Button ---
        self.refresh_button = QPushButton("🔄 Refresh Threads")
        self.refresh_button.clicked.connect(self.run_thread_refresh)
        discord_layout.addWidget(self.refresh_button)

        # --- Pull Status ---
        self.status_label = QLabel("Status: Idle")
        discord_layout.addWidget(self.status_label)


        # Combine both into main horizontal layout
        main_layout = QHBoxLayout()
        main_layout.addLayout(layout)
        main_layout.addLayout(discord_layout)

        self.setLayout(main_layout)

        self.status_timer = QTimer(self)
        self.status_timer.timeout.connect(self.update_status_label)
        self.status_timer.start(1000)  # start fast


    def set_input_from_dropdown(self, index):
        if index > 0:  # ignore the placeholder
            name = self.dropdown.itemText(index)
            self.input.setText(name)

    def load_student_data(self):
        name = self.input.text().strip()
        if not name:
            self.summary_label.setText("Please enter a student name.")
            self.clear_tables()
            return

        data = get_student_focus(name)
        if not data:
            self.summary_label.setText(f"No data found for <b>{name}</b>.")
            self.clear_tables()
            return

        # Summary with break flag
        summary = (
            f"<b>Belt: {data['student_belt'].upper()}<br>"
            f"<b>{data['student']}</b> has attended <b>{data['total_visits']}</b> times "
            f"across <b>{data['weeks_attended']}</b> weeks.<br>"
            f"Average visits/week: <b>{data['avg_visits_per_week']}</b><br>"
            f"Last seen: <i>{data['last_seen']}</i><br>"
        )
        if data["on_break"]:
            summary += (
                f"<span style='color:red; font-weight:bold;'>⚠️ On break "
                f"({data['days_since_last_seen']} days)</span>"
            )
        self.summary_label.setText(summary)

        # Likelihood table
        self.likelihood_table.setRowCount(6)
        for i, day in enumerate(["Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]):
            stats = data["weekday_likelihood"].get(day, {"count": 0, "likelihood": 0.0})
            self.likelihood_table.setItem(i, 0, QTableWidgetItem(day))
            self.likelihood_table.setItem(i, 1, QTableWidgetItem(str(stats["count"])))
            self.likelihood_table.setItem(i, 2, QTableWidgetItem(f"{stats['likelihood']:.2%}"))

        # Weekly matrix table (dynamic)
        week_columns = data["week_columns"]
        matrix = data["weekly_presence_matrix"]

        self.weekly_matrix_table.setRowCount(6)
        self.weekly_matrix_table.setColumnCount(len(week_columns) + 1)


        headers = ["Day"] + [format_week_range_label(w) for w in week_columns]
        self.weekly_matrix_table.setHorizontalHeaderLabels(headers)

        for i, day in enumerate(["Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]):
            self.weekly_matrix_table.setItem(i, 0, QTableWidgetItem(day))
            for j, week in enumerate(week_columns):
                present = matrix.get(day, {}).get(week, False)
                if present:
                    item = QTableWidgetItem(f"✅ {present}")
                    item.setBackground(QColor("darkgreen"))  # or QColor(144, 238, 144)
                else:
                    item = QTableWidgetItem("❌")
                self.weekly_matrix_table.setItem(i, j + 1, item)

        self.weekly_matrix_table.resizeColumnsToContents()


        # Arrival stats
        at = data["arrival_time"]
        self.arrival_table.setRowCount(2)
        labels = ["Weekdays", "Saturday"]
        for i, key in enumerate(["weekday", "saturday"]):
            stats = at.get(key, {})
            self.arrival_table.setItem(i, 0, QTableWidgetItem(float_to_ampm(stats.get("average"))))
            self.arrival_table.setItem(i, 1, QTableWidgetItem(float_to_ampm(stats.get("q1"))))
            self.arrival_table.setItem(i, 2, QTableWidgetItem(float_to_ampm(stats.get("q3"))))
            self.arrival_table.setItem(i, 3, QTableWidgetItem(str(stats.get("std_dev") or "—")))
            self.arrival_table.setItem(i, 4, QTableWidgetItem(str(stats.get("variance") or "—")))
        
        self.arrival_table.setVerticalHeaderLabels(["Weekdays", "Saturday"])

        thread = discord_client.STUDENT_THREADS.get(name.lower())
        if thread:
            self.discord_thread_box.setPlainText("\n\n".join(thread[-20:]))  # show last 20 messages
        else:
            self.discord_thread_box.setPlainText("No thread found.")


    def clear_tables(self):
        self.likelihood_table.setRowCount(0)
        self.weekly_matrix_table.setRowCount(0)
        self.weekly_matrix_table.setColumnCount(0)
        self.arrival_table.setRowCount(0)







class AdminFocusTab(QWidget):
    def __init__(self, parent=None):
        super().__init__()
        self.main_window = parent

        self.BELT_RANKS = [
            "Junior", "White", "Yellow", "Orange", "Green", "Blue", "Purple", "Brown", "Red", "Black"
        ]
        self.BELT_RANK_MAP = {belt: i for i, belt in enumerate(self.BELT_RANKS)}


        self.init_ui()


        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_focus_data)
        self.timer.start(30_000)  # 30 seconds in milliseconds


    def belt_passes(self,student, belt_filter):
        mode = belt_filter.get("mode")
        if mode == "any":
            return True
        elif mode == "juniors":
            return student.get("belt", "") == "Junior"
        elif mode == "lower":
            return not student.get("is_upper_belt", False)
        elif mode == "upper":
            return student.get("is_upper_belt", False)
        elif mode == "min_rank":
            student_rank = self.BELT_RANK_MAP.get(student.get("belt", ""), -1)
            return student_rank >= belt_filter["rank"]
        return True  # fallback

    def show_context_menu(self, pos):
        index = self.student_table.indexAt(pos)
        if not index.isValid():
            return

        row = index.row()
        name_item = self.student_table.item(row, 0)
        if not name_item:
            return

        name = name_item.text()

        menu = QMenu(self)
        action = menu.addAction("Check Student Focus")
        action.triggered.connect(lambda: self.goto_student_focus(name))
        menu.exec_(self.student_table.viewport().mapToGlobal(pos))

    def goto_student_focus(self, student_name):
        if not self.main_window:
            return
        self.main_window.tabs.setCurrentIndex(1)  # Switch to Student tab
        self.main_window.student_tab.input.setText(student_name)
        self.main_window.student_tab.load_student_data()

    def update_summary_box(self):
        avg_today = f"{self.data['avg_students_today']:.2f}" if self.data["avg_students_today"] is not None else "—"
        avg_late = f"{self.data['avg_late_students']:.2f}" if self.data["avg_late_students"] is not None else "—"

        self.summary_box.setHtml(
            f"<b>Today:</b> {self.data['day']} ({self.data['now']})<br>"
            f"<b>Avg students on {self.data['day']}s:</b> {avg_today}<br>"
            f"<b>Avg students arriving after now:</b> {avg_late}"
        )

    def populate_student_table(self):
        students = self.data["expected_students"]
        self.student_table.setRowCount(len(students))

        for i, s in enumerate(students):
            self.student_table.setItem(i, 0, QTableWidgetItem(s["name"]))
            self.student_table.setItem(i, 1, QTableWidgetItem(str(s["visits"])))
            self.student_table.setItem(i, 2, QTableWidgetItem(str(s["last_seen_days_ago"])))
            self.student_table.setItem(i, 3, QTableWidgetItem(f"{s['likelihood']:.2%}"))
            self.student_table.setItem(i, 4, QTableWidgetItem(str(s.get("belt", "—"))))

            _breakChar = {0: "—", 1: "💤", 2: "🚫"}
            break_item = QTableWidgetItem(_breakChar.get(s["on_break"]))
            if s["on_break"] > 1:
                break_item.setForeground(Qt.red)
            elif s["on_break"] > 0:
                break_item.setForeground(Qt.blue)
            self.student_table.setItem(i, 5, break_item)
        self.student_table.resizeColumnsToContents()

    def update_focus_data(self):
        raw_data = get_admin_focus()

        show_break1 = self.break1_checkbox.isChecked()
        show_break2 = self.break2_checkbox.isChecked()
        min_likelihood = self.min_likelihood_box.value()
        belt_filter = self.min_belt_dropdown.currentData()

        filtered_students = [
            s for s in raw_data["expected_students"]
            if s["likelihood"] >= min_likelihood and
            (s["on_break"] == 0 or
                (s["on_break"] == 1 and show_break1) or
                (s["on_break"] == 2 and show_break2)) and
            self.belt_passes(s, belt_filter)
        ]

        self.data = raw_data.copy()
        self.data["expected_students"] = filtered_students

        self.update_summary_box()
        self.populate_student_table()

    def init_ui(self):
        self.data = get_admin_focus()

        # --- Top: Admin Overview Panel ---
        self.top_panel = QFrame()
        self.top_panel.setFrameStyle(QFrame.StyledPanel)
        top_layout = QVBoxLayout()
        top_title = QLabel("🧭 Admin Overview")
        top_title.setStyleSheet("font-size: 20px; font-weight: bold;")

        self.summary_box = QTextEdit()
        self.summary_box.setReadOnly(True)
        self.summary_box.setHtml(
            f"<b>Today:</b> {self.data['day']} ({self.data['now']})<br>"
            f"<b>Avg students on {self.data['day']}s:</b> {self.data['avg_students_today']:.2f}<br>"
            f"<b>Avg students arriving after now:</b> {self.data['avg_late_students']}"
        )
        top_layout.addWidget(top_title)
        top_layout.addWidget(self.summary_box)
        self.top_panel.setLayout(top_layout)

        # --- Bottom Left: Weekly Embedded View ---
        self.bottom_left = QFrame()
        self.bottom_left.setFrameStyle(QFrame.StyledPanel)
        left_layout = QVBoxLayout()
        left_title = QLabel("📅 Weekly Embedded View")
        left_title.setStyleSheet("font-weight: bold;")

        # Mini version of the Weekly Focus table
        weekly_table = QTableWidget()
        weekly_data = get_weekly_focus()["allstudent"]
        weekly_table.setColumnCount(3)
        weekly_table.setHorizontalHeaderLabels(["Day", "Avg", "Std Dev"])
        weekly_table.setRowCount(len(weekly_data))
        for i, row in enumerate(weekly_data):
            weekly_table.setItem(i, 0, QTableWidgetItem(row["day"]))
            weekly_table.setItem(i, 1, QTableWidgetItem(str(row["avg_total"] or "—")))
            weekly_table.setItem(i, 2, QTableWidgetItem(str(row["std_dev"] or "—")))

        left_layout.addWidget(left_title)
        left_layout.addWidget(weekly_table)
        self.bottom_left.setLayout(left_layout)

        # --- Bottom Right: Student Embedded View ---
        self.bottom_right = QFrame()
        self.bottom_right.setFrameStyle(QFrame.StyledPanel)
        right_layout = QVBoxLayout()
        right_title = QLabel("👥 Expected Students Today")
        right_title.setStyleSheet("font-weight: bold;")

        self.break1_checkbox = QCheckBox("Show 💤 (Short Break)")
        self.break1_checkbox.setChecked(True)
        self.break1_checkbox.stateChanged.connect(self.update_focus_data)

        self.break2_checkbox = QCheckBox("Show 🚫 (Long Break)")
        self.break2_checkbox.setChecked(True)
        self.break2_checkbox.stateChanged.connect(self.update_focus_data)

        self.min_likelihood_box = QDoubleSpinBox()
        self.min_likelihood_box.setRange(0.0, 1.0)
        self.min_likelihood_box.setSingleStep(0.05)
        self.min_likelihood_box.setValue(0.0)
        self.min_likelihood_box.setPrefix("Min Likelihood: ")
        self.min_likelihood_box.setDecimals(2)
        self.min_likelihood_box.valueChanged.connect(self.update_focus_data)

        self.min_belt_dropdown = QComboBox()
        self.min_belt_dropdown.addItem("Any Belt", {"mode": "any"})  # Special value for no filter
        self.min_belt_dropdown.addItem("Only Juniors", {"mode": "juniors"})
        self.min_belt_dropdown.addItem("Only Lower Belts", {"mode": "lower"})
        self.min_belt_dropdown.addItem("Only Upper Belts", {"mode": "upper"})
        
        # Add specific minimum belt ranks
        for belt, rank in self.BELT_RANK_MAP.items():
            self.min_belt_dropdown.addItem(f"Min Belt: {belt}", {"mode": "min_rank", "rank": rank})

        self.min_belt_dropdown.currentIndexChanged.connect(self.update_focus_data)


        checkbox_row = QHBoxLayout()
        checkbox_row.addWidget(self.break1_checkbox)
        checkbox_row.addWidget(self.break2_checkbox)
        checkbox_row.addWidget(self.min_likelihood_box)
        checkbox_row.addWidget(self.min_belt_dropdown)


        right_layout.addLayout(checkbox_row)

        self.student_table = QTableWidget()
        students = self.data["expected_students"]
        self.student_table.setColumnCount(6)
        self.student_table.setHorizontalHeaderLabels(["Name", "Visits", "Days Ago", "Likelihood", "Belt", "Break?"])
        self.student_table.setRowCount(len(students))
        self.populate_student_table()

        self.student_table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.student_table.customContextMenuRequested.connect(self.show_context_menu)

        right_layout.addWidget(right_title)
        right_layout.addWidget(self.student_table)
        self.bottom_right.setLayout(right_layout)

        # Combine Layouts
        bottom_panel = QFrame()
        bottom_layout = QHBoxLayout()
        bottom_layout.addWidget(self.bottom_left)
        bottom_layout.addWidget(self.bottom_right)
        bottom_panel.setLayout(bottom_layout)

        main_layout = QVBoxLayout()
        main_layout.addWidget(self.top_panel)
        main_layout.addWidget(bottom_panel)
        self.setLayout(main_layout)

        self.populate_student_table()

class AdminConsole(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Dojo Admin Console")
        self.setGeometry(100, 100, 800, 600)

        self.tabs = QTabWidget()
        self.student_tab = StudentFocusTab()
        self.tabs.addTab(WeeklyFocusTab(), "📊 Weekly")
        self.tabs.addTab(self.student_tab, "🎓 Student")
        self.tabs.addTab(AdminFocusTab(parent=self), "🧠 Admin")
        self.setCentralWidget(self.tabs)

        self.setCentralWidget(self.tabs)


if __name__ == "__main__":
    from PyQt5.QtCore import QCoreApplication, QLibraryInfo
    from PyQt5.QtGui import QFont
    import ctypes

    # Enable High DPI scaling (must be set before QApplication is created)
    QCoreApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    QCoreApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)

    # Optional: Enable DPI awareness on Windows (especially useful for 4K)
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(1)  # SYSTEM_AWARE
    except Exception:
        pass

    app = QApplication(sys.argv)

    # Apply a global font scale factor based on DPI
    screen = app.primaryScreen()
    dpi = screen.logicalDotsPerInch()
    scale_factor = dpi / 96  # 96 DPI is baseline
    default_font = app.font()
    default_font.setPointSizeF(default_font.pointSizeF() * scale_factor)
    app.setFont(default_font)

    app.setStyleSheet(qdarkstyle.load_stylesheet_pyqt5())

    window = AdminConsole()
    window.show()
    sys.exit(app.exec_())

