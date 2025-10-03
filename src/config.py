# Global configuration constants for refresh intervals and thresholds
# Times are in milliseconds for Qt timers

ATTENDANCE_REFRESH_MS = 3000
REPORTS_REFRESH_MS = 10000
INDIV_SEARCH_DEBOUNCE_MS = 300
TIME_TICK_MS = 1000

# Time/date formats
TIME_DISPLAY_FORMAT = "hh:mm:ss AP"
DATE_DISPLAY_FORMAT = "MMMM d, yyyy"

# CSV/PDF defaults
DEFAULT_CSV_ENCODING = "utf-8"
PDF_PAGE_SIZE = "A4"  # For documentation; actual implementation uses QPageSize.A4
