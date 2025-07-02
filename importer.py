import csv
import sqlite3
from datetime import datetime, timedelta
from glob import glob
from pathlib import Path
import os

# Connect to SQLite and prepare schema
conn = sqlite3.connect("dojo_attendance.sqlite")
cur = conn.cursor()

print("Rebuilding DB...")

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
# Load membership list into a set of names
membership_file = next(Path("data").glob("*Membership*.csv"), None)

if not membership_file:
    print("No junior detection can happen without a file for Juniors. Expects a csv with col1=F_name and col2=L_name.")
    print()
else:
    print("Junior membership file detected.")

jr_belts = set()
with open(membership_file, "r", encoding="utf-8") as f:
    reader = csv.reader(f)
    next(reader)  # skip header
    for row in reader:
        f_name, l_name = row[0].strip(), row[1].strip()
        name = f"{f_name} {l_name}"
        if name:
            print(name)
            jr_belts.add(name.lower())

# Loop through all CSV files in data/ folder
for file_path in glob("data/*.csv"):
    with open(file_path, "r", newline='', encoding="utf-8") as fi:
        if "studentaccessreport" in file_path.lower():
            reader = csv.reader(fi)
            next(reader)  # Skip header

            for row in reader:
                student = row[1].strip()

                if student.lower() in jr_belts:
                    belt = "Junior"
                else:
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
        else:
            print("No StudentAccessReport files found, failing now.")
            raise(FileNotFoundError("No StudentAccessReport files found, expecting filename'*StudentAccessReport*.csv'"))

conn.commit()
conn.close()

print("DB build complete!")
print("__*__"*4)