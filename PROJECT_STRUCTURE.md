# 📂 SocietySync ERP — Project Structure

> Every file in this repository explained — what it does, why it exists, and how it connects to the rest of the system.

---

## Directory Layout

```
SocietySync-Smart_Apartment_ERP_System/
│
├── 📱 Core Application
│   ├── app.py                      # Entry point — Streamlit app + routing
│   ├── auth.py                     # Login, session, password hashing
│   ├── database.py                 # DB connection pool + all query functions
│   ├── config.py                   # App settings, constants, column whitelist
│   ├── utils.py                    # Shared helper functions
│   └── base_dashboard.py           # Shared dashboard components
│
├── 🖥️ Role Dashboards
│   ├── admin_dashboard.py          # Admin panel — full system control
│   ├── owner_dashboard.py          # Owner panel — flat & billing management
│   └── tenant_dashboard.py         # Tenant panel — bills, complaints, polls
│
├── 🗄️ Database
│   ├── societysync_schema.sql      # DDL — CREATE TABLE, constraints, indices
│   └── societysync_data.sql        # DML — seed data + sequence resets
│
├── 🎨 Assets
│   ├── assets/banner.svg           # Animated SVG banner (used in README)
│   └── assets/architecture.svg    # Animated system architecture diagram
│
├── 📊 ER Diagrams
│   ├── er_diagram_conceptual.png   # Chen's Notation ER diagram
│   ├── er_diagram_relational.png   # Crow's Foot / Relational schema diagram
│   └── er_diagram_architecture.png # System-level architecture diagram
│
├── ⚙️ Configuration
│   ├── .env.example                # Template for environment variables
│   ├── .gitignore                  # Files excluded from version control
│   ├── requirements.txt            # Python package dependencies
│   └── LICENSE                     # MIT License
│
├── 🚀 Run Scripts
│   ├── run_app.ps1                 # PowerShell launcher (Windows)
│   └── run_app.bat                 # Batch file launcher (Windows CMD)
│
└── 📄 Documentation & Academic Deliverables
    ├── README.md                   # Project overview, features, quickstart
    ├── SETUP.md                    # Full installation & setup guide
    ├── PROJECT_STRUCTURE.md        # This file
    ├── SocietySyncERP_Presentation.pptx # 10-slide academic project presentation
    ├── SocietySyncERP_Report.docx  # Comprehensive academic project report (IEEE-style)
    └── SocietySyncERP_Walkthrough.mp4 # Full HD video walkthrough with neural voiceover
```

---

## File-by-File Reference

### 📱 Core Application

---

#### `app.py` — Application Entry Point
**What it does:** The main Streamlit application file. Handles:
- Page configuration (`st.set_page_config`)
- Session state initialization (logged-in user, role)
- Login form rendering
- Role-based routing: after login, renders the correct dashboard based on `user['role']`
- Default admin auto-creation on first startup (calls `database.py`)

**Connects to:** `auth.py`, `database.py`, `admin_dashboard.py`, `owner_dashboard.py`, `tenant_dashboard.py`

---

#### `auth.py` — Authentication Module
**What it does:**
- `login_user(username, password)` — queries users table, verifies bcrypt hash
- `hash_password(plain)` — wraps bcrypt for new user creation
- `verify_password(plain, hashed)` — secure comparison
- Session token management via `st.session_state`

**Security model:** Passwords are hashed with `bcrypt` (cost factor 12). The plaintext password is never stored or logged — only the hash in the `users.password_hash` column.

**Connects to:** `database.py`, called from `app.py`

---

#### `database.py` — Database Layer
**What it does:** The single source of truth for all database interactions. Contains:
- `get_connection()` decorated with `@st.cache_resource` — creates one persistent connection per Streamlit session (singleton pattern)
- `execute_query(sql, params)` — parameterized query runner (prevents SQL injection)
- All CRUD functions organized by domain:
  - `get_user()`, `create_user()`, `update_user()` — user management
  - `get_bills()`, `create_bill()`, `mark_bill_paid()` — billing
  - `get_complaints()`, `create_complaint()`, `resolve_complaint()` — complaints
  - `get_visitors()`, `log_visitor()` — visitor management
  - `get_notifications()`, `create_notification()`, `mark_read()` — notifications
  - `get_polls()`, `create_poll()`, `cast_vote()` — polls & voting
  - Dashboard analytics queries (counts, totals, charts data)

**Connects to:** Every other module that needs data

---

#### `config.py` — Application Configuration
**What it does:**
- `DATABASE_URL` — reads from `.env` via `python-dotenv`
- `ALLOWED_SORT_COLUMNS` — a whitelist of column names allowed in dynamic `ORDER BY` clauses, preventing SQL injection through user-controlled sort parameters
- UI constants: page title, items per page, date formats
- Role constants: `ROLE_ADMIN`, `ROLE_OWNER`, `ROLE_TENANT`

**Why the column whitelist:** Dynamic `ORDER BY` cannot use parameterized queries in SQL, so without a whitelist an attacker could inject via sort column names. The whitelist in `config.py` is the security boundary.

---

#### `utils.py` — Shared Helpers
**What it does:** Small utility functions used across multiple modules:
- Date formatting and parsing helpers
- Currency formatting (₹ with locale-aware separators)
- Status badge color mapping (pending → orange, resolved → green, etc.)
- Pagination helpers for Streamlit tables
- Flash message / success-error notification display helpers

**Connects to:** Imported by all dashboard modules

---

#### `base_dashboard.py` — Shared Dashboard Components
**What it does:** Common UI components reused across all three dashboards:
- Sidebar navigation with role-aware menu items
- Header bar with username, role badge, and logout button
- Notification bell with unread count badge
- Standard page layout wrapper (`render_page_header`)

**Why separate:** Avoids duplicating sidebar/header code across all three dashboard files. Each dashboard calls `base_dashboard.render_sidebar()` at the top.

**Connects to:** Imported by `admin_dashboard.py`, `owner_dashboard.py`, `tenant_dashboard.py`

---

### 🖥️ Role Dashboards

---

#### `admin_dashboard.py` — Admin Panel
**What it does:** The most feature-rich dashboard. Sections:
- **Overview:** Society-wide KPIs (total residents, pending bills, open complaints, upcoming visitors)
- **User Management:** Create owners and tenants; view/edit/delete users
- **Billing:** Generate bills for any flat; view all payment statuses; analytics charts
- **Complaints:** View all complaints; respond with admin notes; mark resolved
- **Visitors:** Full visitor log with search/filter
- **Notifications:** Create broadcast announcements with priority levels
- **Polls:** Create polls with options; view live results with bar charts

**Access control:** Only rendered when `session_state.role == 'admin'`

---

#### `owner_dashboard.py` — Owner Panel
**What it does:**
- **Overview:** Personal flat summary, outstanding bills, recent complaints
- **My Bills:** View own bills; mark as paid
- **Complaints:** File new complaints; track existing ones
- **Visitors:** Log expected visitors; view visitor history for own flat
- **Polls:** View active polls; cast votes (one per poll, enforced by DB UNIQUE constraint)
- **Notifications:** View announcements; mark as read

**Access control:** Only rendered when `session_state.role == 'owner'`

---

#### `tenant_dashboard.py` — Tenant Panel
**What it does:** Subset of owner features appropriate for tenants:
- **Overview:** Current rent, bill status, complaint summary
- **My Bills:** View rent + utility bills
- **Complaints:** File complaints about maintenance issues
- **Visitors:** Log expected guests
- **Polls:** Participate in community polls
- **Notifications:** View announcements

**Access control:** Only rendered when `session_state.role == 'tenant'`

---

### 🗄️ Database Files

---

#### `societysync_schema.sql` — Database Schema (DDL)
**What it does:** Creates the entire database structure:
- 11 `CREATE TABLE` statements with all column definitions
- `PRIMARY KEY`, `FOREIGN KEY`, `UNIQUE`, `CHECK` constraints
- `ON DELETE CASCADE` and `ON DELETE SET NULL` rules
- `CREATE INDEX` statements for performance-critical columns (`user_id`, `flat_number`, `poll_id`)
- `SERIAL` sequences for auto-incrementing PKs

**Run this first** (before data). Safe to re-run only on a fresh database.

---

#### `societysync_data.sql` — Seed Data (DML)
**What it does:**
- `INSERT` statements for sample data: 1 admin, 5 owners, 8 tenants, bills, complaints, visitors, notifications, polls
- `SELECT setval(...)` calls to reset all sequences after bulk inserts (so new records get correct IDs)
- Sample passwords are bcrypt-hashed directly in SQL

**Run this after schema.** The admin user (`admin` / `admin123`) is defined here.

---

### 🎨 Assets

---

#### `assets/banner.svg` — Project Banner
**What it does:** An animated SVG used at the top of `README.md`. Features:
- Gradient background (indigo → purple → blue)
- Animated floating dots
- Text shimmer animation on the project name
- Role icons (🏢 Admin · 👤 Owner · 🏠 Tenant)
- Research paper published badge

---

#### `assets/architecture.svg` — Architecture Diagram
**What it does:** Animated SVG showing the 3-layer system architecture:
- **Layer 1:** Users (Admin, Owner, Tenant browsers)
- **Layer 2:** Streamlit Application (auth, dashboards, business logic)
- **Layer 3:** PostgreSQL Database (11 tables)
- Animated flow arrows showing data direction between layers

---

### 📊 ER Diagrams

---

#### `er_diagram_conceptual.png` — Chen's Notation ER Diagram
Academic-style Entity-Relationship diagram using Chen's notation:
- Rectangles = Entities (`USERS`, `OWNERS`, `TENANTS`, `BILLS`, etc.)
- Diamonds = Relationships (`Has Owner`, `Rents To`, `Creates Poll`, etc.)
- Ovals = Attributes (with double-oval for primary keys)
- Lines with 1/N cardinality labels

---

#### `er_diagram_relational.png` — Relational Schema (Crow's Foot)
Physical database schema diagram in Crow's Foot / IE notation:
- Tables with column lists showing PK/FK indicators
- Relationship lines with Crow's Foot cardinality symbols
- Shows all foreign key relationships between the 11 tables
- Format matches tools like pgAdmin, MySQL Workbench, dbdiagram.io

---

#### `er_diagram_architecture.png` — System Architecture Diagram
High-level architectural overview showing component interactions between the presentation layer, application layer, and data layer.

---

### ⚙️ Configuration

---

#### `.env.example` — Environment Template
Template file showing which environment variables are required. Copy to `.env` and fill in your values. The actual `.env` file is git-ignored.

#### `.gitignore` — Git Exclusions
Excludes: `__pycache__/`, `*.pyc`, `.env`, virtual environment folders (`venv/`, `societysync_env/`), `.streamlit/`, IDE folders, OS files. Does **not** exclude PNG or SVG files.

#### `requirements.txt` — Python Dependencies
Pinned minimum versions for all Python packages. Install with `pip install -r requirements.txt`.

#### `LICENSE` — MIT License
Open source MIT license. Free to use, modify, and distribute with attribution.

---

### 🚀 Run Scripts

---

#### `run_app.ps1` — PowerShell Launcher (Windows)
Activates the virtual environment (if present) and runs `streamlit run app.py`. Recommended for Windows users.

#### `run_app.bat` — Batch Launcher (Windows CMD)
Same as above but for Windows Command Prompt users who prefer `.bat` files.

---

## Module Dependency Map

```
app.py
├── auth.py
│   └── database.py ──→ PostgreSQL
├── admin_dashboard.py
│   ├── base_dashboard.py
│   ├── database.py
│   └── utils.py
├── owner_dashboard.py
│   ├── base_dashboard.py
│   ├── database.py
│   └── utils.py
└── tenant_dashboard.py
    ├── base_dashboard.py
    ├── database.py
    └── utils.py

config.py ──→ (imported by database.py, all dashboards)
```

All database access flows through `database.py`. No module queries PostgreSQL directly — this enforces a clean separation of concerns and makes it easy to swap the database layer if needed.

---

*For setup instructions, see [SETUP.md](SETUP.md). For the full project overview, see [README.md](README.md).*
