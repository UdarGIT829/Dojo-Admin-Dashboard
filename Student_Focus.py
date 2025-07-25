import sqlite3
import statistics
from datetime import datetime
from collections import defaultdict

def get_all_students(db_path="dojo_attendance.sqlite"):
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute("SELECT DISTINCT student_name FROM attendance ORDER BY student_name ASC")
    names = [row[0] for row in cur.fetchall()]
    conn.close()
    return names


def get_student_focus(student_name, db_path="dojo_attendance.sqlite"):
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    # Fetch all attendance entries for the student
    cur.execute("""
        SELECT belt, date, day_of_week, start_unix
        FROM attendance
        WHERE student_name = ?
        ORDER BY date ASC
    """, (student_name,))
    rows = cur.fetchall()
    student_belt = ""

    if not rows:
        conn.close()
        return None  # No data for student

    # Determine latest attendance date in the database
    cur.execute("SELECT MAX(date) FROM attendance")
    latest_date_str = cur.fetchone()[0]
    latest_db_date = datetime.strptime(latest_date_str, "%Y-%m-%d").date()
    conn.close()

    # Track data
    by_day = {day: [] for day in ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]}
    arrival_times = []
    weekly_visit_totals = defaultdict(int)
    weekday_weekly_counts = {}

    for belt, date, day, start_unix in rows:
        student_belt = belt
        by_day[day].append(date)
        arrival_times.append(datetime.fromtimestamp(start_unix).time())

        dt = datetime.strptime(date, "%Y-%m-%d")
        iso_year, iso_week, _ = dt.isocalendar()
        week_key = f"{iso_year}-W{iso_week:02d}"
        weekly_visit_totals[week_key] += 1

    total_visits = len(rows)
    weeks_attended = len(weekly_visit_totals)
    avg_visits_per_week = round(total_visits / weeks_attended, 2) if weeks_attended else None

    weekday_likelihood = {
        day: {
            "count": len(by_day[day]),
            "likelihood": round(len(by_day[day]) / total_visits, 4) if total_visits else 0
        }
        for day in by_day
    }

    weekday_week_keys = {}
    for day in by_day:
        week_keys = set()
        for date in by_day[day]:
            iso_year, iso_week, _ = datetime.strptime(date, "%Y-%m-%d").isocalendar()
            key = f"{iso_year}-W{iso_week:02d}"
            week_keys.add(key)
        weekday_week_keys[day] = sorted(week_keys)

    weekday_hours = []
    saturday_hours = []

    for belt, date, day, start_unix in rows:
        hour_val = datetime.fromtimestamp(start_unix).hour + datetime.fromtimestamp(start_unix).minute / 60
        if day == "Sat":
            saturday_hours.append(hour_val)
        else:
            weekday_hours.append(hour_val)

    def compute_arrival_stats(hour_list):
        if len(hour_list) >= 2:
            q1, q3 = statistics.quantiles(hour_list, n=4)[0], statistics.quantiles(hour_list, n=4)[2]
            std_dev = statistics.stdev(hour_list)
            var = statistics.variance(hour_list)
        else:
            q1 = q3 = std_dev = var = None
        avg = round(statistics.mean(hour_list), 2) if hour_list else None
        return {
            "average": avg,
            "q1": round(q1, 2) if q1 is not None else None,
            "q3": round(q3, 2) if q3 is not None else None,
            "std_dev": round(std_dev, 2) if std_dev is not None else None,
            "variance": round(var, 2) if var is not None else None
        }

    arrival_time = {
        "weekday": compute_arrival_stats(weekday_hours),
        "saturday": compute_arrival_stats(saturday_hours)
    }

    last_visit_date = max(datetime.strptime(date, "%Y-%m-%d") for _,date, _, _ in rows).date()
    days_since_last_seen = (latest_db_date - last_visit_date).days
    on_break = days_since_last_seen > 14

    # Generate weekly presence matrix (day x week -> True/False)
    weekday_presence_matrix = defaultdict(dict)
    all_week_keys = set()

    for _, date, day, start_unix in rows:
        dt = datetime.strptime(date, "%Y-%m-%d")
        iso_year, iso_week, _ = dt.isocalendar()
        week_key = f"{iso_year}-W{iso_week:02d}"
        all_week_keys.add(week_key)
    
        arrival_time_str = datetime.fromtimestamp(start_unix).strftime("%I:%M %p").lstrip("0")
        weekday_presence_matrix[day][week_key] = arrival_time_str

    sorted_week_columns = sorted(all_week_keys)


    return {
        "student": student_name,
        "student_belt": student_belt,
        "total_visits": total_visits,
        "weeks_attended": weeks_attended,
        "avg_visits_per_week": avg_visits_per_week,
        "last_seen": str(last_visit_date),
        "on_break": on_break,
        "days_since_last_seen": days_since_last_seen,
        "weekday_likelihood": weekday_likelihood,
        "weekly_counts_by_day": weekday_weekly_counts,
        "weekly_total_counts": dict(weekly_visit_totals),
        "weekly_visits_by_day": weekday_week_keys,
        "weekly_presence_matrix": dict(weekday_presence_matrix),
        "week_columns": sorted_week_columns,

        "arrival_time": arrival_time
    }
