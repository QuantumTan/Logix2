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
├─ src/
│  ├─ __init__.py
│  ├─ config.py
│  ├─ database/             # Database layer (modularized)
│  │  ├─ __init__.py
│  │  ├─ attendance.py      # Attendance actions + reports aggregations
│  │  ├─ auth.py            # Staff/Admin auth + management
│  │  ├─ db_config.py       # MySQL connection config
│  │  ├─ db_queries.py      # Thin facade re-exporting domain modules
│  │  ├─ db_setup.py        # One-time DB/table bootstrap + migrations
│  │  ├─ employees.py       # Employee CRUD + search
│  │  └─ utils.py           # Small helpers (e.g., hash_password)
│  ├─ screens/              # UI screens
│  │  ├─ __init__.py
│  │  ├─ add_employee_modal.py
│  │  ├─ add_staff_modal.py
│  │  ├─ admin_dashboard.py
│  │  ├─ base_dashboard.py  # Shared dashboard scaffolding (tabs, reports, tables)
│  │  ├─ change_password_modal.py
│  │  ├─ emp_details.py
│  │  ├─ employee_dashboard.py
│  │  ├─ reports.py
│  │  ├─ staff_dashboard.py
│  │  ├─ components/
│  │  │  ├─ __init__.py
│  │  │  ├─ attendance_view.py
│  │  │  ├─ employee_management_view.py
│  │  │  └─ reports_view.py
│  │  └─ login_screens/
│  │     ├─ __init__.py
│  │     ├─ admin_login.py
│  │     └─ staff_login.py
│  ├─ utils/
│  │  ├─ __init__.py
│  │  └─ export_helpers.py
│  └─ widgets/
│     ├─ __init__.py
│     └─ reports_chart.py
└─ tests/                   # Test suite (place your tests here)
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
