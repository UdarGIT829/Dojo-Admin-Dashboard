import sqlite3
from datetime import datetime
from collections import defaultdict, Counter
import statistics


def get_admin_focus(db_path="dojo_attendance.sqlite"):
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    now = datetime.now()
    today_str = now.strftime("%a")  # Mon, Tue, etc.
    current_hour_float = now.hour + now.minute / 60

    # Fetch ALL attendance records
    cur.execute("SELECT student_name, date, day_of_week, start_unix FROM attendance")
    all_rows = cur.fetchall()

    # Fetch most recent attendance date
    cur.execute("SELECT MAX(date) FROM attendance")
    last_db_date_str = cur.fetchone()[0]
    last_db_date = datetime.strptime(last_db_date_str, "%Y-%m-%d").date()
    conn.close()

    total_attendance = defaultdict(int)
    weekday_attendance = defaultdict(lambda: defaultdict(int))  # student -> day -> count
    last_seen = {}
    visits_per_week = defaultdict(set)
    late_visits_per_week = defaultdict(set)

    for name, date_str, day, start_unix in all_rows:
        total_attendance[name] += 1
        weekday_attendance[name][day] += 1

        dt = datetime.strptime(date_str, "%Y-%m-%d")
        if name not in last_seen or dt > last_seen[name]:
            last_seen[name] = dt

        # Only use rows matching today's weekday for weekly aggregates
        if day == today_str:
            iso_year, iso_week, _ = dt.isocalendar()
            week_key = f"{iso_year}-W{iso_week:02d}"
            visits_per_week[week_key].add(name)

            arrival_hour = datetime.fromtimestamp(start_unix).hour + datetime.fromtimestamp(start_unix).minute / 60
            if arrival_hour > current_hour_float:
                late_visits_per_week[week_key].add(name)

    all_counts = [len(s) for s in visits_per_week.values()]
    late_counts = [len(s) for s in late_visits_per_week.values()]

    expected_students = []
    for name in total_attendance:
        total = total_attendance[name]
        on_this_day = weekday_attendance[name].get(today_str, 0)
        if total == 0:
            continue

        likelihood = round(on_this_day / total, 4)
        days_ago = (last_db_date - last_seen[name].date()).days
        on_break = days_ago > 14

        expected_students.append({
            "name": name,
            "visits": on_this_day,
            "likelihood": likelihood,
            "last_seen_days_ago": days_ago,
            "on_break": on_break
        })

    # Sort by descending likelihood, then by recency
    expected_students.sort(key=lambda s: (-s["likelihood"], s["last_seen_days_ago"]))

    return {
        "day": today_str,
        "now": now.strftime("%Y-%m-%d %H:%M"),
        "avg_students_today": round(statistics.mean(all_counts), 2) if all_counts else None,
        "avg_late_students": round(statistics.mean(late_counts), 2) if late_counts else None,
        "expected_students": expected_students
    }


# Example usage:
if __name__ == "__main__":
    import pprint
    pprint.pprint(get_admin_focus())
