# Dojo-Admin-Dashboard
# Attendance & Student Focus Manager

## Overview

The **Attendance & Student Focus Manager** is a cross‑platform desktop application that consolidates dojo attendance records, weekly analytics, and Discord‑based student conversations into a single, easy‑to‑navigate interface.
It is aimed at instructors and administrators who need a quick, data‑driven snapshot of student engagement without juggling multiple tools.

---

## Features

### Weekly Focus Tab

* Adjust the **Start** and **End** date pickers to refine the visible range. (Not yet implemented)
* View basic statistics about student attendance on certain days

### Student Focus Tab

1. Type a student’s name in the **search bar** (auto‑complete enabled).
2. Review summary stats, arrival heat‑map, and likelihood‑of‑arrival.
3. On the right‑hand pane, read the **Discord thread** for additional context.
4. Select **Refresh Threads** to fetch the latest messages.
   The status indicator turns to *Pulling threads…* while the operation is active; the button is temporarily disabled to prevent duplicate requests.

### Admin Focus Tab

* Oversee the expected traffic in the dojo for the day
* Filter and highlight selected expected students (Switch to Student Focus in right-click menu)
* View Weekly data at a glance

---


## Quick Start

### 1  Prerequisites

* Python 3.11 or newer
* A Discord bot token with **MESSAGE CONTENT INTENT** enabled
* SQLite (bundled with Python)
  *Optional:* Git for cloning the repository

### 2  Installation

```bash
# Clone the repository
$ git clone https://github.com/your‑org/attendance‑manager.git
$ cd attendance‑manager

# Create & activate a virtual environment (recommended)
$ python -m venv .venv
$ source .venv/bin/activate  # Windows: .venv\Scripts\activate

# Install dependencies
$ pip install -r requirements.txt
```

### 3  Configure the Discord bot

1. Create a file named **`BOT_TOKEN.txt`** in the project root.
2. Paste your bot token on the first line—nothing else.
3. Ensure **MESSAGE CONTENT INTENT** is checked in the Discord Developer Portal.

### 4  Run the application

```bash
$ python ui_test.py
```

The main window opens with the Weekly Focus tab selected by default.

---


## Directory Structure

```
attendance‑manager/
├── Admin_Focus.py          # Admin utilities and bulk tools
├── Student_Focus.py        # Student dashboard widgets
├── Weekly_Focus.py         # Weekly matrix & date‑range widgets
├── discord_client.py       # Reusable Discord client (background thread)
├── discord_utils.py        # Helper coroutines for fetching thread history
├── importer.py             # CSV → SQLite importer
├── ui_test.py              # Application entry‑point (PyQt)
├── requirements.txt        # Python dependencies
└── README.md               # You are here
```

---

## Screenshots *(placeholders)*

> **Replace the image paths once screenshots are captured.**

| View                  | File                                                                   |
| --------------------- | ---------------------------------------------------------------------- |
| Weekly Focus          | `![Weekly Focus Tab](docs/screenshots/Weekly_Focus.png)`               |
| Student Focus         | `![Student Focus Tab](docs/screenshots/Student_Focus.png)`             |
| Admin Focus           | `![Admin Focus Tab](docs/screenshots/Admin_Focus.png)` |

---

## Frequently Asked Questions

<details>
<summary>Discord threads are not appearing. What should I check?</summary>

* Confirm the bot has *Read Message History* permission for the target channels.
* Verify that **MESSAGE CONTENT INTENT** is enabled in the Discord Developer Portal.
* Ensure the channel names match the allow‑list in `discord_utils.py`.

</details>

<details>
<summary>The attendance database is empty after import.</summary>

* Make sure the importer script points to the correct CSV directory.
* Check for schema changes; remove the database file to let the application recreate it.

</details>


## License

This project is licensed under the GNU General Public License.  See the `LICENSE` file for details.
