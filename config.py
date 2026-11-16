import os
from dotenv import load_dotenv

load_dotenv()

# ─── Database ──────────────────────────────────────────────────────────────────
DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://postgres:root@localhost:5432/societysync')

# ─── Application ───────────────────────────────────────────────────────────────
APP_NAME = "Vishwakarma Apartment"
APP_SUBTITLE = "SocietySync ERP"
APP_LOCATION = "Pune"

# ─── Flat structure: 4 blocks × 5 floors × 5 units = 100 flats ────────────────
FLAT_BLOCKS = ['A', 'B', 'C', 'D']
FLAT_FLOORS = range(1, 6)
FLAT_UNITS_PER_FLOOR = range(1, 6)

# ─── Domain lists ──────────────────────────────────────────────────────────────
BILL_TYPES = ["Maintenance", "Electricity", "Water", "Parking", "Security", "Other"]

COMPLAINT_CATEGORIES = [
    "Maintenance", "Plumbing", "Electrical", "Security",
    "Noise", "Parking", "Cleanliness", "Elevator", "Water Supply", "Other"
]

PAYMENT_METHODS = ["Online Banking", "UPI", "Credit Card", "Debit Card", "Cash"]

PRIORITY_LEVELS = ["low", "medium", "high", "urgent"]
NOTIFICATION_PRIORITIES = ["low", "normal", "high"]
NOTIFICATION_TYPES = ["general", "maintenance", "emergency", "billing"]

# ─── Security: whitelisted columns for dynamic UPDATE queries ──────────────────
ALLOWED_BILL_UPDATE_COLUMNS = {
    'flat_number', 'bill_type', 'amount', 'due_date',
    'payment_status', 'payment_date', 'payment_method'
}
ALLOWED_COMPLAINT_UPDATE_COLUMNS = {
    'status', 'priority', 'admin_response', 'resolved_at', 'updated_at'
}

# ─── Auth ──────────────────────────────────────────────────────────────────────
MIN_PASSWORD_LENGTH = 6
