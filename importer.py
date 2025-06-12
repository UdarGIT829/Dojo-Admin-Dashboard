import csv
import sqlite3
from datetime import datetime, timedelta
from glob import glob
import os

# Connect to SQLite and prepare schema
conn = sqlite3.connect("dojo_attendance.sqlite")
cur = conn.cursor()

# Drop for testing only — remove in production
cur.execute("DROP TABLE IF EXISTS attendance")

cur.execute("""
CREATE TABLE IF NOT EXISTS attendance (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_name TEXT,
    belt TEXT,
    datetime TEXT,
    date TEXT,
    day_of_week TEXT,
    start_unix INTEGER,
    end_unix INTEGER,
    duration_hours REAL,
    is_upper_belt BOOLEAN,
    UNIQUE(student_name, belt, datetime)  -- prevent duplicates
)
""")

upper_belts = {"Blue", "Purple", "Brown", "Red"}

# Loop through all CSV files in data/ folder
for file_path in glob("data/*.csv"):
    with open(file_path, "r", newline='', encoding="utf-8") as fi:
        reader = csv.reader(fi)
        next(reader)  # Skip header

        for row in reader:
            student = row[1].strip()
            belt = row[2].strip()
            timestamp_str = row[3].strip()
            duration = float(row[4])

            dt_start = datetime.strptime(timestamp_str.split(" (")[0], "%a %b %d %Y %H:%M:%S GMT%z")
            dt_end = dt_start + timedelta(hours=duration)

            date_only = dt_start.strftime("%Y-%m-%d")
            day_of_week = dt_start.strftime("%a")

            cur.execute("""
                INSERT OR IGNORE INTO attendance
                (student_name, belt, datetime, date, day_of_week,
                 start_unix, end_unix, duration_hours, is_upper_belt)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                student, belt, timestamp_str, date_only, day_of_week,
                int(dt_start.timestamp()), int(dt_end.timestamp()), duration,
                belt in upper_belts
            ))

conn.commit()
conn.close()
