# 🛠️ SocietySync ERP — Setup Guide

> Complete step-by-step installation guide. Follow these instructions to get SocietySync ERP running on your machine.

---

## Prerequisites

Make sure the following are installed before starting:

| Requirement | Minimum Version | Download |
|---|---|---|
| **Python** | 3.9+ | [python.org](https://www.python.org/downloads/) |
| **PostgreSQL** | 14+ | [postgresql.org](https://www.postgresql.org/download/) |
| **pip** | (bundled with Python) | — |
| **Git** | any | [git-scm.com](https://git-scm.com/) |

Verify your installations:
```bash
python --version        # or: py --version  (Windows)
psql --version
pip --version
git --version
```

---

## Step 1 — Clone the Repository

```bash
git clone https://github.com/durgesh-v-shukla/SocietySync-Smart_Apartment_ERP_System.git
cd SocietySync-Smart_Apartment_ERP_System
```

---

## Step 2 — Create a Virtual Environment (Recommended)

**Windows (PowerShell):**
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

**Windows (Command Prompt):**
```cmd
python -m venv venv
venv\Scripts\activate.bat
```

**macOS / Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
```

You should now see `(venv)` at the start of your terminal prompt.

---

## Step 3 — Install Dependencies

```bash
pip install -r requirements.txt
```

This installs: `streamlit`, `psycopg2-binary`, `pandas`, `plotly`, `bcrypt`, `python-dotenv`, `Pillow`.

---

## Step 4 — Configure Environment Variables

Copy the example environment file:

```bash
# Windows
copy .env.example .env

# macOS / Linux
cp .env.example .env
```

Open `.env` in any text editor and set your PostgreSQL connection string:

```env
DATABASE_URL=postgresql://postgres:YOUR_PASSWORD@localhost:5432/societysync
```

Replace `YOUR_PASSWORD` with your PostgreSQL superuser password (set during PostgreSQL installation).

> **Note:** The `.env` file is listed in `.gitignore` and will never be committed to version control.

---

## Step 5 — Set Up PostgreSQL Database

### 5a. Start PostgreSQL

Make sure the PostgreSQL service is running:

- **Windows:** Open **Services** (`Win + R` → `services.msc`) → find **postgresql-x64-14** → Start
- **macOS:** `brew services start postgresql@14`
- **Linux:** `sudo systemctl start postgresql`

### 5b. Create the Database

Open a terminal and run:

```bash
psql -U postgres -c "CREATE DATABASE societysync;"
```

If prompted, enter your PostgreSQL password.

### 5c. Create Tables (Schema)

```bash
psql -U postgres -d societysync -f societysync_schema.sql
```

This creates all 11 tables with constraints, indices, and foreign keys.

### 5d. Load Seed Data

```bash
psql -U postgres -d societysync -f societysync_data.sql
```

This loads sample data including:
- Default **admin** user (`admin` / `admin123`)
- Sample owners, tenants, bills, complaints, visitors, notifications, and polls
- Sequence resets (no manual step needed — sequences are automatically corrected)

---

## Step 6 — Run the Application

### Option A — PowerShell Script (Windows, Recommended)

```powershell
.\run_app.ps1
```

### Option B — Batch Script (Windows)

```cmd
run_app.bat
```

### Option C — Direct Command (All Platforms)

```bash
streamlit run app.py
```

The app will open automatically in your browser at:

```
http://localhost:8501
```

---

## Step 7 — First Login

| Field | Value |
|---|---|
| **Username** | `admin` |
| **Password** | `admin123` |

After logging in as admin you can:
1. Create **owner** accounts (go to User Management → Add Owner)
2. Create **tenant** accounts (go to User Management → Add Tenant)
3. Each new user's initial password is displayed **once** at creation — save it

> ⚠️ Change the default admin password immediately in a production environment.

---

## Troubleshooting

### `psql: command not found`
PostgreSQL `bin/` directory is not in your PATH.
- **Windows fix:** Add `C:\Program Files\PostgreSQL\14\bin` to your System PATH environment variable.

### `connection refused` / `could not connect to server`
PostgreSQL is not running. See Step 5a to start the service.

### `database "societysync" does not exist`
You skipped Step 5b. Run the `CREATE DATABASE` command first.

### `role "postgres" does not exist` (macOS/Linux)
On macOS/Linux the default superuser may be your OS username:
```bash
psql -U $(whoami) -c "CREATE DATABASE societysync;"
```

### `ModuleNotFoundError: No module named 'streamlit'`
Your virtual environment is not activated, or you installed packages outside it. Activate the venv (Step 2) then re-run `pip install -r requirements.txt`.

### Port 8501 already in use
Run on a different port:
```bash
streamlit run app.py --server.port 8502
```

### `Error: relation "users" already exists`
The schema was already applied. Skip Step 5c or drop and recreate the database:
```bash
psql -U postgres -c "DROP DATABASE societysync;"
psql -U postgres -c "CREATE DATABASE societysync;"
psql -U postgres -d societysync -f societysync_schema.sql
psql -U postgres -d societysync -f societysync_data.sql
```

---

## macOS / Linux Notes

- Use `python3` instead of `python` if `python` resolves to Python 2
- Use `pip3` instead of `pip` if needed
- PostgreSQL default user on Homebrew macOS installs is your system username, not `postgres`
- Activate venv with `source venv/bin/activate` (not `.\venv\Scripts\Activate.ps1`)

---

## Environment Variables Reference

| Variable | Description | Example |
|---|---|---|
| `DATABASE_URL` | Full PostgreSQL connection string | `postgresql://postgres:pass@localhost:5432/societysync` |

All other configuration is in `config.py`.

---

*For questions or issues, open a GitHub issue at [github.com/durgesh-v-shukla/SocietySync-Smart_Apartment_ERP_System/issues](https://github.com/durgesh-v-shukla/SocietySync-Smart_Apartment_ERP_System/issues)*
