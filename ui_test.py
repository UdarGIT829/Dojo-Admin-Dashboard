import sys
from datetime import datetime, timedelta, time
from PyQt5.QtCore import Qt, QTimer

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QLabel, QVBoxLayout,
    QHBoxLayout, QLineEdit, QPushButton, QTabWidget, QTableWidget,
    QTableWidgetItem, QCompleter, QComboBox, QTextEdit, QFrame, QMenu
)

import qdarkstyle

# Autoruns importer.py
import importer

from Admin_Focus import get_admin_focus
from Weekly_Focus import get_weekly_focus
from Student_Focus import get_student_focus, get_all_students





def format_week_range_label(week_key):
    year, week = map(int, week_key.split("-W"))
    # Monday of the ISO week
    monday = datetime.strptime(f'{year}-W{week}-1', "%G-W%V-%u")
    sunday = monday + timedelta(days=6)
    return f"{monday.strftime('%b %-d')}–{sunday.strftime('%b %-d')} ({week_key})"

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

        table = QTableWidget()
        table.setColumnCount(6)
        table.setHorizontalHeaderLabels(["Day", "Avg Students", "Std Dev", "Variance", "Avg Lowerbelts", "Avg Upperbelts"])

        data = get_weekly_focus()
        table.setRowCount(len(data))

        for row_idx, row in enumerate(data):
            table.setItem(row_idx, 0, QTableWidgetItem(row["day"]))
            table.setItem(row_idx, 1, QTableWidgetItem(str(row["avg_total"] or "—")))
            table.setItem(row_idx, 2, QTableWidgetItem(str(row["std_dev"] or "—")))
            table.setItem(row_idx, 3, QTableWidgetItem(str(row["variance"] or "—")))
            table.setItem(row_idx, 4, QTableWidgetItem(str(row["avg_lower"] or "—")))
            table.setItem(row_idx, 5, QTableWidgetItem(str(row["avg_upper"] or "—")))

        layout.addWidget(label)
        layout.addWidget(table)
        self.setLayout(layout)



class StudentFocusTab(QWidget):
    def __init__(self):
        super().__init__()
        self.students = get_all_students()
        self.init_ui()

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

        self.setLayout(layout)

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
                item = QTableWidgetItem("✅" if present else "❌")
                self.weekly_matrix_table.setItem(i, j + 1, item)

        # Arrival stats
        at = data["arrival_time"]
        self.arrival_table.setRowCount(1)
        self.arrival_table.setItem(0, 0, QTableWidgetItem(float_to_ampm(at["average"])))
        self.arrival_table.setItem(0, 1, QTableWidgetItem(float_to_ampm(at["q1"])))
        self.arrival_table.setItem(0, 2, QTableWidgetItem(float_to_ampm(at["q3"])))
        self.arrival_table.setItem(0, 3, QTableWidgetItem(str(at["std_dev"] or "—")))
        self.arrival_table.setItem(0, 4, QTableWidgetItem(str(at["variance"] or "—")))

    def clear_tables(self):
        self.likelihood_table.setRowCount(0)
        self.weekly_matrix_table.setRowCount(0)
        self.weekly_matrix_table.setColumnCount(0)
        self.arrival_table.setRowCount(0)






class AdminFocusTab(QWidget):
    def __init__(self, parent=None):
        super().__init__()
        self.main_window = parent
        self.init_ui()

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_focus_data)
        self.timer.start(30_000)  # 30 seconds in milliseconds

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
        self.summary_box.setHtml(
            f"<b>Today:</b> {self.data['day']} ({self.data['now']})<br>"
            f"<b>Avg students on {self.data['day']}s:</b> {self.data['avg_students_today']:.2f}<br>"
            f"<b>Avg students arriving after now:</b> {self.data['avg_late_students']:.2f}"
        )

    def update_focus_data(self):
        self.data = get_admin_focus()
        self.update_summary_box()

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
            f"<b>Avg students arriving after now:</b> {self.data['avg_late_students']:.2f}"
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
        weekly_data = get_weekly_focus()
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

        self.student_table = QTableWidget()
        students = self.data["expected_students"]
        self.student_table.setColumnCount(4)
        self.student_table.setHorizontalHeaderLabels(["Name", "Visits", "Days Ago", "Break?"])
        self.student_table.setRowCount(len(students))
        for i, s in enumerate(students):
            self.student_table.setItem(i, 0, QTableWidgetItem(s["name"]))
            self.student_table.setItem(i, 1, QTableWidgetItem(str(s["visits"])))
            self.student_table.setItem(i, 2, QTableWidgetItem(str(s["last_seen_days_ago"])))
            break_item = QTableWidgetItem("✅" if s["on_break"] else "—")
            if s["on_break"]:
                break_item.setForeground(Qt.red)
            self.student_table.setItem(i, 3, break_item)

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
    app = QApplication(sys.argv)
    app.setStyleSheet(qdarkstyle.load_stylesheet_pyqt5())
    window = AdminConsole()
    window.show()
    sys.exit(app.exec_())

