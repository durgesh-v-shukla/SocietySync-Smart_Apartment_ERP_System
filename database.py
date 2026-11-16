import psycopg2
import psycopg2.extras
import bcrypt
from datetime import datetime, date
import secrets
import string
import logging

from config import (
    DATABASE_URL,
    ALLOWED_BILL_UPDATE_COLUMNS,
    ALLOWED_COMPLAINT_UPDATE_COLUMNS,
)

logger = logging.getLogger(__name__)


class Database:
    def __init__(self):
        self.connection = None
        self.connect()
        self.create_tables()
        self.create_default_admin()

    # ──────────────────────────────────────────────────────────────────────────
    # Connection
    # ──────────────────────────────────────────────────────────────────────────

    def connect(self):
        self.connection = psycopg2.connect(DATABASE_URL)
        self.connection.autocommit = True

    def ensure_connection(self):
        """Re-connect if the connection has been closed."""
        try:
            if self.connection is None or self.connection.closed:
                self.connect()
            else:
                # lightweight ping
                self.connection.cursor().execute("SELECT 1")
        except Exception:
            self.connect()

    def _cursor(self):
        """Return a RealDictCursor, reconnecting first if needed."""
        self.ensure_connection()
        return self.connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

    # ──────────────────────────────────────────────────────────────────────────
    # Schema — matches societysync_schema.sql exactly
    # ──────────────────────────────────────────────────────────────────────────

    def create_tables(self):
        cur = self._cursor()

        cur.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id SERIAL PRIMARY KEY,
                username VARCHAR(50) NOT NULL UNIQUE,
                password_hash VARCHAR(255) NOT NULL,
                role VARCHAR(20) NOT NULL CHECK (role IN ('admin', 'owner', 'tenant')),
                flat_number VARCHAR(10),
                name VARCHAR(100) NOT NULL,
                email VARCHAR(100),
                phone VARCHAR(15),
                profile_picture TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_login TIMESTAMP,
                password_changed BOOLEAN DEFAULT FALSE,
                initial_password VARCHAR(50)
            )
        """)

        cur.execute("""
            CREATE TABLE IF NOT EXISTS owners (
                owner_id SERIAL PRIMARY KEY,
                user_id INTEGER REFERENCES users(user_id) ON DELETE CASCADE,
                flat_number VARCHAR(10) NOT NULL,
                ownership_start_date DATE,
                emergency_contact VARCHAR(15),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        cur.execute("""
            CREATE TABLE IF NOT EXISTS tenants (
                tenant_id SERIAL PRIMARY KEY,
                user_id INTEGER REFERENCES users(user_id) ON DELETE CASCADE,
                owner_id INTEGER REFERENCES owners(owner_id),
                flat_number VARCHAR(10) NOT NULL,
                rent_amount NUMERIC(10,2),
                lease_start_date DATE,
                lease_end_date DATE,
                security_deposit NUMERIC(10,2),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        cur.execute("""
            CREATE TABLE IF NOT EXISTS bills (
                bill_id SERIAL PRIMARY KEY,
                flat_number VARCHAR(10) NOT NULL,
                bill_type VARCHAR(50) NOT NULL,
                amount NUMERIC(10,2) NOT NULL,
                due_date DATE NOT NULL,
                payment_status VARCHAR(20) DEFAULT 'pending'
                    CHECK (payment_status IN ('pending', 'paid', 'overdue')),
                payment_date DATE,
                payment_method VARCHAR(50),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                created_by INTEGER REFERENCES users(user_id)
            )
        """)

        cur.execute("""
            CREATE TABLE IF NOT EXISTS complaints (
                complaint_id SERIAL PRIMARY KEY,
                user_id INTEGER REFERENCES users(user_id),
                flat_number VARCHAR(10) NOT NULL,
                title VARCHAR(200) NOT NULL,
                description TEXT NOT NULL,
                category VARCHAR(50) NOT NULL,
                priority VARCHAR(20) DEFAULT 'medium'
                    CHECK (priority IN ('low', 'medium', 'high', 'urgent')),
                status VARCHAR(20) DEFAULT 'open'
                    CHECK (status IN ('open', 'in_progress', 'resolved', 'closed')),
                admin_response TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                resolved_at TIMESTAMP
            )
        """)

        cur.execute("""
            CREATE TABLE IF NOT EXISTS notifications (
                notification_id SERIAL PRIMARY KEY,
                title VARCHAR(200) NOT NULL,
                message TEXT NOT NULL,
                created_by INTEGER REFERENCES users(user_id),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                priority VARCHAR(20) DEFAULT 'normal'
                    CHECK (priority IN ('low', 'normal', 'high'))
            )
        """)

        cur.execute("""
            CREATE TABLE IF NOT EXISTS notification_reads (
                read_id SERIAL PRIMARY KEY,
                notification_id INTEGER REFERENCES notifications(notification_id) ON DELETE CASCADE,
                user_id INTEGER REFERENCES users(user_id) ON DELETE CASCADE,
                read_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(notification_id, user_id)
            )
        """)

        cur.execute("""
            CREATE TABLE IF NOT EXISTS polls (
                poll_id SERIAL PRIMARY KEY,
                title VARCHAR(200) NOT NULL,
                description TEXT,
                created_by INTEGER REFERENCES users(user_id),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                end_date DATE,
                status VARCHAR(20) DEFAULT 'active'
                    CHECK (status IN ('active', 'closed'))
            )
        """)

        cur.execute("""
            CREATE TABLE IF NOT EXISTS poll_options (
                option_id SERIAL PRIMARY KEY,
                poll_id INTEGER REFERENCES polls(poll_id) ON DELETE CASCADE,
                option_text VARCHAR(200) NOT NULL,
                vote_count INTEGER DEFAULT 0
            )
        """)

        cur.execute("""
            CREATE TABLE IF NOT EXISTS votes (
                vote_id SERIAL PRIMARY KEY,
                poll_id INTEGER REFERENCES polls(poll_id) ON DELETE CASCADE,
                option_id INTEGER REFERENCES poll_options(option_id) ON DELETE CASCADE,
                user_id INTEGER REFERENCES users(user_id) ON DELETE CASCADE,
                voted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(poll_id, user_id)
            )
        """)

        cur.execute("""
            CREATE TABLE IF NOT EXISTS visitors (
                visitor_id SERIAL PRIMARY KEY,
                flat_number VARCHAR(10) NOT NULL,
                visitor_name VARCHAR(100) NOT NULL,
                visitor_phone VARCHAR(15),
                purpose VARCHAR(200),
                entry_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                exit_time TIMESTAMP,
                vehicle_number VARCHAR(20),
                logged_by INTEGER REFERENCES users(user_id),
                status VARCHAR(20) DEFAULT 'in'
                    CHECK (status IN ('in', 'out')),
                visitor_photo TEXT
            )
        """)

        cur.close()

    # ──────────────────────────────────────────────────────────────────────────
    # Admin bootstrap
    # ──────────────────────────────────────────────────────────────────────────

    def create_default_admin(self):
        cur = self._cursor()
        cur.execute("SELECT user_id FROM users WHERE role = 'admin' LIMIT 1")
        if cur.fetchone():
            cur.close()
            return
        pw_hash = bcrypt.hashpw(b'admin123', bcrypt.gensalt()).decode()
        cur.execute(
            """INSERT INTO users (username, password_hash, role, flat_number, name, email, password_changed)
               VALUES (%s, %s, 'admin', 'ADMIN', 'System Administrator', 'admin@societysync.com', TRUE)""",
            ('admin', pw_hash)
        )
        cur.close()

    # ──────────────────────────────────────────────────────────────────────────
    # Username / password helpers
    # ──────────────────────────────────────────────────────────────────────────

    def generate_username(self, role, name):
        base = f"{role}_{name.lower().replace(' ', '_')}"
        cur = self._cursor()
        cur.execute("SELECT username FROM users WHERE username LIKE %s", (base + '%',))
        existing = {r['username'] for r in cur.fetchall()}
        cur.close()
        if base not in existing:
            return base
        i = 1
        while f"{base}_{i}" in existing:
            i += 1
        return f"{base}_{i}"

    def generate_password(self, length=8):
        chars = string.ascii_letters + string.digits
        return ''.join(secrets.choice(chars) for _ in range(length))

    # ──────────────────────────────────────────────────────────────────────────
    # Authentication
    # ──────────────────────────────────────────────────────────────────────────

    def authenticate_user(self, username, password):
        cur = self._cursor()
        cur.execute("SELECT * FROM users WHERE username = %s", (username,))
        user = cur.fetchone()
        cur.close()
        if not user:
            return None
        stored_hash = user['password_hash']
        if not bcrypt.checkpw(password.encode('utf-8'), stored_hash.encode('utf-8')):
            return None
        self.update_last_login(user['user_id'])
        return {
            'user_id': user['user_id'],
            'username': user['username'],
            'password_hash': user['password_hash'],
            'role': user['role'],
            'flat_number': user['flat_number'],
            'name': user['name'],
            'email': user['email'],
            'phone': user['phone'],
            'password_changed': bool(user['password_changed']),
            'initial_password': user.get('initial_password'),
        }

    def update_last_login(self, user_id):
        cur = self._cursor()
        cur.execute("UPDATE users SET last_login = CURRENT_TIMESTAMP WHERE user_id = %s", (user_id,))
        cur.close()

    def change_password(self, user_id, new_password):
        pw_hash = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        cur = self._cursor()
        cur.execute(
            "UPDATE users SET password_hash = %s, password_changed = TRUE WHERE user_id = %s",
            (pw_hash, user_id)
        )
        cur.close()
        return True

    # ──────────────────────────────────────────────────────────────────────────
    # User management
    # ──────────────────────────────────────────────────────────────────────────

    def create_user(self, role, name, email, phone, flat_number, **kwargs):
        cur = self._cursor()
        username = self.generate_username(role, name)
        initial_password = self.generate_password()
        pw_hash = bcrypt.hashpw(initial_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

        cur.execute(
            """INSERT INTO users
               (username, password_hash, role, flat_number, name, email, phone, initial_password)
               VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
               RETURNING user_id""",
            (username, pw_hash, role, flat_number, name, email, phone, initial_password)
        )
        user_id = cur.fetchone()['user_id']

        if role == 'owner':
            cur.execute(
                """INSERT INTO owners (user_id, flat_number, ownership_start_date, emergency_contact)
                   VALUES (%s, %s, %s, %s)""",
                (user_id, flat_number, kwargs.get('ownership_start_date'), kwargs.get('emergency_contact'))
            )
        elif role == 'tenant':
            cur.execute(
                """INSERT INTO tenants
                   (user_id, owner_id, flat_number, rent_amount, lease_start_date, lease_end_date, security_deposit)
                   VALUES (%s, %s, %s, %s, %s, %s, %s)""",
                (user_id, kwargs.get('owner_id'), flat_number,
                 kwargs.get('rent_amount'), kwargs.get('lease_start_date'),
                 kwargs.get('lease_end_date'), kwargs.get('security_deposit'))
            )
        cur.close()
        return {'username': username, 'initial_password': initial_password, 'user_id': user_id}

    def delete_user(self, user_id):
        cur = self._cursor()
        cur.execute("SELECT role, flat_number FROM users WHERE user_id = %s", (user_id,))
        user = cur.fetchone()
        if not user:
            cur.close()
            return False
        if user['role'] == 'admin':
            cur.close()
            raise ValueError("Cannot delete admin user")

        # Clean up dependents
        cur.execute("DELETE FROM votes WHERE user_id = %s", (user_id,))
        cur.execute("DELETE FROM notification_reads WHERE user_id = %s", (user_id,))
        cur.execute("DELETE FROM complaints WHERE user_id = %s", (user_id,))
        cur.execute("DELETE FROM tenants WHERE user_id = %s", (user_id,))

        cur.execute("SELECT owner_id FROM owners WHERE user_id = %s", (user_id,))
        owner = cur.fetchone()
        if owner:
            cur.execute("UPDATE tenants SET owner_id = NULL WHERE owner_id = %s", (owner['owner_id'],))
            cur.execute("DELETE FROM owners WHERE owner_id = %s", (owner['owner_id'],))

        # Nullify visitor logs_by reference instead of deleting
        cur.execute("UPDATE visitors SET logged_by = NULL WHERE logged_by = %s", (user_id,))

        cur.execute("DELETE FROM users WHERE user_id = %s", (user_id,))
        cur.close()
        return True

    def get_society_stats(self):
        cur = self._cursor()
        stats = {}
        cur.execute("SELECT COUNT(*) AS c FROM users WHERE role = 'owner'")
        stats['total_owners'] = cur.fetchone()['c']
        cur.execute("SELECT COUNT(*) AS c FROM users WHERE role = 'tenant'")
        stats['total_tenants'] = cur.fetchone()['c']
        cur.execute("SELECT COUNT(*) AS c FROM bills WHERE payment_status = 'pending'")
        stats['pending_bills'] = cur.fetchone()['c']
        cur.execute("SELECT COUNT(*) AS c FROM complaints WHERE status IN ('open','in_progress')")
        stats['open_complaints'] = cur.fetchone()['c']
        cur.execute("SELECT COUNT(*) AS c FROM visitors WHERE status = 'in'")
        stats['current_visitors'] = cur.fetchone()['c']
        cur.execute("SELECT payment_status, COUNT(*) AS count FROM bills GROUP BY payment_status")
        stats['bill_stats'] = [dict(r) for r in cur.fetchall()]
        cur.execute("SELECT status, COUNT(*) AS count FROM complaints GROUP BY status")
        stats['complaint_stats'] = [dict(r) for r in cur.fetchall()]
        cur.close()
        return stats

    # ──────────────────────────────────────────────────────────────────────────
    # Bills
    # ──────────────────────────────────────────────────────────────────────────

    def get_user_bills(self, flat_number):
        cur = self._cursor()
        cur.execute(
            """SELECT bill_id, flat_number, bill_type, amount, due_date,
                      payment_status, payment_date, payment_method, created_at, created_by
               FROM bills WHERE flat_number = %s ORDER BY created_at DESC""",
            (flat_number,)
        )
        bills = [dict(r) for r in cur.fetchall()]
        cur.close()
        return bills

    def pay_bill(self, bill_id, payment_method):
        cur = self._cursor()
        cur.execute(
            """UPDATE bills
               SET payment_status = 'paid', payment_date = CURRENT_DATE, payment_method = %s
               WHERE bill_id = %s""",
            (payment_method, bill_id)
        )
        cur.close()
        return True

    def delete_bill(self, bill_id):
        cur = self._cursor()
        cur.execute("DELETE FROM bills WHERE bill_id = %s", (bill_id,))
        affected = cur.rowcount
        cur.close()
        return affected > 0

    def update_bill(self, bill_id, **fields):
        if not fields:
            return False
        for key in fields:
            if key not in ALLOWED_BILL_UPDATE_COLUMNS:
                raise ValueError(f"Invalid column for bills update: {key}")
        cur = self._cursor()
        set_clause = ', '.join([f"{k} = %s" for k in fields])
        params = list(fields.values()) + [bill_id]
        cur.execute(f"UPDATE bills SET {set_clause} WHERE bill_id = %s", params)
        cur.close()
        return True

    # ──────────────────────────────────────────────────────────────────────────
    # Complaints
    # ──────────────────────────────────────────────────────────────────────────

    def get_user_complaints(self, user_id):
        cur = self._cursor()
        cur.execute(
            """SELECT complaint_id, user_id, flat_number, title, description,
                      category, priority, status, admin_response,
                      created_at, updated_at, resolved_at
               FROM complaints WHERE user_id = %s ORDER BY created_at DESC""",
            (user_id,)
        )
        complaints = [dict(r) for r in cur.fetchall()]
        cur.close()
        return complaints

    def create_complaint(self, user_id, flat_number, title, description, category, priority):
        cur = self._cursor()
        cur.execute(
            """INSERT INTO complaints (user_id, flat_number, title, description, category, priority)
               VALUES (%s, %s, %s, %s, %s, %s) RETURNING complaint_id""",
            (user_id, flat_number, title, description, category, priority)
        )
        complaint_id = cur.fetchone()['complaint_id']
        cur.close()
        return complaint_id

    def update_complaint(self, complaint_id, **fields):
        if not fields:
            return False
        for key in fields:
            if key not in ALLOWED_COMPLAINT_UPDATE_COLUMNS:
                raise ValueError(f"Invalid column for complaints update: {key}")
        cur = self._cursor()
        set_clause = ', '.join([f"{k} = %s" for k in fields])
        params = list(fields.values()) + [complaint_id]
        cur.execute(f"UPDATE complaints SET {set_clause} WHERE complaint_id = %s", params)
        cur.close()
        return True

    def delete_complaint(self, complaint_id):
        cur = self._cursor()
        cur.execute("DELETE FROM complaints WHERE complaint_id = %s", (complaint_id,))
        affected = cur.rowcount
        cur.close()
        return affected > 0

    # ──────────────────────────────────────────────────────────────────────────
    # Notifications
    # ──────────────────────────────────────────────────────────────────────────

    def get_unread_notifications(self, user_id):
        cur = self._cursor()
        cur.execute(
            """SELECT n.notification_id, n.title, n.message, n.created_by,
                      n.created_at, n.priority
               FROM notifications n
               WHERE n.notification_id NOT IN (
                   SELECT notification_id FROM notification_reads WHERE user_id = %s
               )
               ORDER BY n.created_at DESC""",
            (user_id,)
        )
        result = [dict(r) for r in cur.fetchall()]
        cur.close()
        return result

    def mark_notification_read(self, notification_id, user_id):
        cur = self._cursor()
        cur.execute(
            """INSERT INTO notification_reads (notification_id, user_id)
               VALUES (%s, %s) ON CONFLICT (notification_id, user_id) DO NOTHING""",
            (notification_id, user_id)
        )
        cur.close()
        return True

    def create_notification_for_flat(self, flat_number, title, message, created_by, priority='normal'):
        cur = self._cursor()
        cur.execute(
            """INSERT INTO notifications (title, message, created_by, priority)
               VALUES (%s, %s, %s, %s) RETURNING notification_id""",
            (title, message, created_by, priority)
        )
        notification_id = cur.fetchone()['notification_id']
        cur.close()
        return notification_id, 1

    def delete_notification(self, notification_id):
        """ON DELETE CASCADE handles notification_reads automatically."""
        cur = self._cursor()
        cur.execute("DELETE FROM notifications WHERE notification_id = %s", (notification_id,))
        affected = cur.rowcount
        cur.close()
        return affected > 0

    def update_notification(self, notification_id, title=None, message=None, priority=None):
        cur = self._cursor()
        cur.execute(
            "UPDATE notifications SET title = %s, message = %s, priority = %s WHERE notification_id = %s",
            (title, message, priority, notification_id)
        )
        cur.close()
        return True

    # ──────────────────────────────────────────────────────────────────────────
    # Visitors
    # ──────────────────────────────────────────────────────────────────────────

    def log_visitor_with_photo(self, flat_number, visitor_name, visitor_phone=None,
                               purpose=None, vehicle_number=None, logged_by=None, visitor_photo=None):
        cur = self._cursor()
        cur.execute(
            """INSERT INTO visitors
               (flat_number, visitor_name, visitor_phone, purpose, vehicle_number, logged_by, visitor_photo)
               VALUES (%s, %s, %s, %s, %s, %s, %s) RETURNING visitor_id""",
            (flat_number, visitor_name, visitor_phone, purpose, vehicle_number, logged_by, visitor_photo)
        )
        visitor_id = cur.fetchone()['visitor_id']
        cur.close()
        message = f"Visitor {visitor_name} arrived at Flat {flat_number}"
        self.create_notification_for_flat(flat_number, "New Visitor", message, logged_by or 1)
        return visitor_id

    def get_visitors_for_flat(self, flat_number, limit=10):
        cur = self._cursor()
        cur.execute(
            """SELECT visitor_id, flat_number, visitor_name, visitor_phone, purpose,
                      entry_time, exit_time, vehicle_number, logged_by, status, visitor_photo
               FROM visitors WHERE flat_number = %s ORDER BY entry_time DESC LIMIT %s""",
            (flat_number, limit)
        )
        visitors = []
        for r in cur.fetchall():
            d = dict(r)
            d['logged_by_name'] = None
            d['flat_owner_name'] = None
            visitors.append(d)
        cur.close()
        return visitors

    def get_all_visitors(self, status_filter=None, limit=50):
        cur = self._cursor()
        if status_filter and status_filter != 'all':
            cur.execute(
                """SELECT visitor_id, flat_number, visitor_name, visitor_phone, purpose,
                          entry_time, exit_time, vehicle_number, logged_by, status, visitor_photo
                   FROM visitors WHERE status = %s ORDER BY entry_time DESC LIMIT %s""",
                (status_filter, limit)
            )
        else:
            cur.execute(
                """SELECT visitor_id, flat_number, visitor_name, visitor_phone, purpose,
                          entry_time, exit_time, vehicle_number, logged_by, status, visitor_photo
                   FROM visitors ORDER BY entry_time DESC LIMIT %s""",
                (limit,)
            )
        visitors = []
        for r in cur.fetchall():
            d = dict(r)
            d['logged_by_name'] = None
            d['flat_owner_name'] = None
            visitors.append(d)
        cur.close()
        return visitors

    def delete_visitor(self, visitor_id):
        cur = self._cursor()
        cur.execute("DELETE FROM visitors WHERE visitor_id = %s", (visitor_id,))
        affected = cur.rowcount
        cur.close()
        return affected > 0

    # ──────────────────────────────────────────────────────────────────────────
    # Polls
    # ──────────────────────────────────────────────────────────────────────────

    def delete_poll(self, poll_id):
        cur = self._cursor()
        # CASCADE handles votes and poll_options
        cur.execute("DELETE FROM polls WHERE poll_id = %s", (poll_id,))
        affected = cur.rowcount
        cur.close()
        return affected > 0

    # ──────────────────────────────────────────────────────────────────────────
    # Misc
    # ──────────────────────────────────────────────────────────────────────────

    def close_connection(self):
        if self.connection and not self.connection.closed:
            self.connection.close()
