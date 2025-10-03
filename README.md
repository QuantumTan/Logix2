# LOGIX Attendance Monitoring System

A PyQt6-based attendance monitoring system with MySQL database integration.

## Project Structure

```
Logix/
├─ main.py                  # App entrypoint
├─ requirements.txt         # Python dependencies
├─ README.md                # This file
├─ assets/                  # Static assets (images, etc.)
│  ├─ logix.png
│  └─ employees/            # Employee profile images
└─ src/
   ├─ database/             # Database layer (modularized)
   │  ├─ db_config.py       # MySQL connection config
   │  ├─ db_setup.py        # One-time DB/table bootstrap + migrations
   │  ├─ utils.py           # Small helpers (e.g., hash_password)
   │  ├─ employees.py       # Employee CRUD + search
   │  ├─ auth.py            # Staff/Admin auth + management
   │  ├─ attendance.py      # Attendance actions + reports aggregations
   │  └─ db_queries.py      # Thin facade re-exporting the above modules
   ├─ widgets/              # Reusable UI widgets
   │  └─ reports_chart.py   # Charts widget (matplotlib-backed, lazy-loaded)
   └─ screens/              # UI screens
      ├─ login_screens/
      │  ├─ admin_login.py
      │  └─ staff_login.py
      ├─ base_dashboard.py  # Shared dashboard scaffolding (tabs, reports, tables)
      ├─ admin_dashboard.py # Admin dashboard (extends base)
      ├─ staff_dashboard.py # Staff dashboard (extends base)
      └─ employee_dashboard.py
```

## Architecture at a glance
- Database layer is split by responsibility (employees, auth, attendance) to avoid a monolithic file. `db_queries.py` is now a compatibility facade so existing imports continue working.
- Reports chart is extracted into `src/widgets/reports_chart.py` and lazy-loaded from dashboards.
- Shared UI logic (attendance table, reports, export, employee details modal launcher) lives in `base_dashboard.py`, while Admin/Staff dashboards extend and specialize.

## Installation
1) Install deps

```
pip install -r requirements.txt
```

2) Ensure MySQL (XAMPP) is running. Defaults used: host 127.0.0.1, port 3306, user root, empty password, db `logix`.

3) Run the app

```
python main.py
```

## Notes
- Charts require matplotlib. To install:

```
pip install matplotlib
```

- You can disable charts at runtime by setting environment variable `LOGIX_DISABLE_CHARTS=1` before launching the app.

## Features
- Employee attendance (check-in/out)
- Admin/Staff dashboards
- Employee management (soft delete, leave credits)
- Department attendance reports (daily/weekly/monthly/yearly)
- Individual hours summaries (monthly/yearly)
- CSV/PDF exports
- Simple username/password authentication for Admin/Staff
