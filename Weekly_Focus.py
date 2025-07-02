import sqlite3
from collections import defaultdict
import statistics
from datetime import datetime

UPPER_BELTS = {"Blue", "Purple", "Brown", "Red"}
JUNIORS = "Junior"

def get_weekly_focus(db_path="dojo_attendance.sqlite"):
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    # Day -> week_key -> total/upper/lower counts
    totals = defaultdict(lambda: defaultdict(int))
    juniors = defaultdict(lambda: defaultdict(int))
    uppers = defaultdict(lambda: defaultdict(int))
    lowers = defaultdict(lambda: defaultdict(int))

    cur.execute("""
        SELECT day_of_week, date, belt FROM attendance
    """)
    rows = cur.fetchall()
    conn.close()

    for day_of_week, date_str, belt in rows:
        dt = datetime.strptime(date_str, "%Y-%m-%d")
        iso_year, iso_week, _ = dt.isocalendar()
        week_key = f"{iso_year}-W{iso_week:02d}"

        totals[day_of_week][week_key] += 1
        if belt == JUNIORS:
            juniors[day_of_week][week_key] += 1
        elif belt in UPPER_BELTS:
            uppers[day_of_week][week_key] += 1
        else:
            lowers[day_of_week][week_key] += 1

    # Build structured result
    result = {
        "allstudent":[],
        "junior":[],
        "lower":[],
        "upper":[],
        }

    for day in ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]:
        _Mapping = {
            "allstudent":list(totals[day].values()), 
            "junior":list(juniors[day].values()),
            "lower":list(lowers[day].values()),
            "upper":list(uppers[day].values())
        }

        def avg(lst): return round(statistics.mean(lst), 2) if lst else None
        for key,val in _Mapping.items():
            result[key].append( {
            "day": day,
            "avg_total": avg(val),
            "std_dev": round(statistics.stdev(val), 2) if len(val) > 1 else None,
            "variance": round(statistics.variance(val), 2) if len(val) > 1 else None,
        } )

    return result
