# LOGIX Attendance Monitoring System

A PyQt6-based attendance monitoring system with MySQL database integration.

## Project Structure

```
Logix/
├── main.py                 # Main application entry point
├── requirements.txt        # Python dependencies
├── README.md              # This file
├── assets/                # Static assets (images, etc.)
│   ├── logix.png
│   └── employees/         # Employee profile images
├── src/                   # Source code
│   ├── database/          # Database modules
│   │   ├── db_config.py   # Database configuration
│   │   ├── db_queries.py  # Database queries
│   │   └── db_setup.py    # Database setup
│   └── screens/           # UI screens
│       ├── login_screens/ # Authentication screens
│       └── *.py          # Various dashboard screens
├── config/               # Configuration files
├── tests/               # Test files (future)
└── utils/               # Utility functions (future)
```

## Installation

1. Clone or download this repository
2. Install dependencies: `pip install -r requirements.txt`
3. Ensure XAMPP MySQL server is running
4. Run the application: `python main.py`

## Features

- Employee attendance tracking
- Admin dashboard
- Staff management
- Reports generation
- User authentication
