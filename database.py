import psycopg2
import os
import bcrypt
from datetime import datetime, date
import secrets
import string


class Database:
    def __init__(self):
        self.connection = None
        self.connect()
    
    def connect(self):
        db_url = os.getenv('DATABASE_URL')
        self.connection = psycopg2.connect(db_url)
        self.connection.autocommit = True
        self.create_tables()
    
    def create_tables(self):
        cursor = self.connection.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id SERIAL PRIMARY KEY,
                username VARCHAR(50) UNIQUE NOT NULL,
                password_hash VARCHAR(255) NOT NULL,
                role VARCHAR(20) NOT NULL CHECK (role IN ('admin', 'owner', 'tenant')),
                flat_number VARCHAR(10),
                name VARCHAR(100) NOT NULL,
                email VARCHAR(100) UNIQUE NOT NULL,
                phone VARCHAR(15),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                initial_password VARCHAR(20)
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS owners (
                owner_id SERIAL PRIMARY KEY,
                user_id INTEGER UNIQUE REFERENCES users(user_id) ON DELETE CASCADE,
                flat_number VARCHAR(10) NOT NULL,
                ownership_start_date DATE,
                emergency_contact VARCHAR(15),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS tenants (
                tenant_id SERIAL PRIMARY KEY,
                user_id INTEGER UNIQUE REFERENCES users(user_id) ON DELETE CASCADE,
                flat_number VARCHAR(10) NOT NULL,
                rent_amount DECIMAL(10,2),
                lease_start_date DATE,
                lease_end_date DATE,
                security_deposit DECIMAL(10,2),
                owner_id INTEGER REFERENCES owners(owner_id),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS bills (
                bill_id SERIAL PRIMARY KEY,
                flat_number VARCHAR(10) NOT NULL,
                bill_type VARCHAR(50) NOT NULL,
                amount DECIMAL(10,2) NOT NULL,
                due_date DATE NOT NULL,
                payment_status VARCHAR(20) DEFAULT 'pending' CHECK (payment_status IN ('pending', 'paid', 'overdue')),
                created_by INTEGER REFERENCES users(user_id),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                paid_at TIMESTAMP
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS complaints (
                complaint_id SERIAL PRIMARY KEY,
                user_id INTEGER REFERENCES users(user_id),
                flat_number VARCHAR(10) NOT NULL,
                title VARCHAR(200) NOT NULL,
                description TEXT NOT NULL,
                category VARCHAR(50) NOT NULL,
                priority VARCHAR(20) DEFAULT 'medium' CHECK (priority IN ('low', 'medium', 'high', 'urgent')),
                status VARCHAR(20) DEFAULT 'open' CHECK (status IN ('open', 'in_progress', 'resolved', 'closed')),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                resolved_at TIMESTAMP,
                admin_response TEXT
            )
        """)
        
        cursor.execute("""
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
                status VARCHAR(20) DEFAULT 'in' CHECK (status IN ('in', 'out')),
                visitor_photo TEXT
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS notifications (
                notification_id SERIAL PRIMARY KEY,
                title VARCHAR(200) NOT NULL,
                message TEXT NOT NULL,
                created_by INTEGER REFERENCES users(user_id),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                type VARCHAR(50) DEFAULT 'general' CHECK (type IN ('general', 'maintenance', 'emergency', 'billing'))
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS notification_reads (
                read_id SERIAL PRIMARY KEY,
                notification_id INTEGER REFERENCES notifications(notification_id) ON DELETE CASCADE,
                user_id INTEGER REFERENCES users(user_id) ON DELETE CASCADE,
                read_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(notification_id, user_id)
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS polls (
                poll_id SERIAL PRIMARY KEY,
                title VARCHAR(200) NOT NULL,
                description TEXT,
                created_by INTEGER REFERENCES users(user_id),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                end_date DATE,
                is_active BOOLEAN DEFAULT TRUE
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS poll_options (
                option_id SERIAL PRIMARY KEY,
                poll_id INTEGER REFERENCES polls(poll_id) ON DELETE CASCADE,
                option_text VARCHAR(200) NOT NULL,
                votes INTEGER DEFAULT 0
            )
        """)
        
        # adding visitor photo column
        try:
            cursor.execute("""
                ALTER TABLE visitors 
                ADD COLUMN IF NOT EXISTS visitor_photo TEXT
            """)
        except Exception as e:
            print(f"Note: visitor_photo column might already exist: {e}")
        
        cursor.close()
    
    def create_default_admin(self):
        cursor = self.connection.cursor()
        
        # check if admin already exists
        cursor.execute("SELECT * FROM users WHERE role = 'admin'")
        admin = cursor.fetchone()
        
        if admin:
            cursor.close()
            return
        
        # Create admin user
        password = "admin123"
        password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        
        cursor.execute("INSERT INTO users (username, password_hash, role, name, email, flat_number) VALUES (%s, %s, %s, %s, %s, %s)",
                      ("admin", password_hash, "admin", "System Administrator", "admin@societysync.com", "ADMIN"))
        
        cursor.close()
    
    def generate_username(self, role, name):
        username = f"{role[0]}{name.lower().replace(' ', '')}"
        return username
    
    def generate_password(self, length=8):
        chars = string.ascii_letters + string.digits
        return ''.join(secrets.choice(chars) for _ in range(length))
    
    def authenticate_user(self, username, password):
        cursor = self.connection.cursor()
        
        # fetch user details
        cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
        user_data = cursor.fetchone()
        cursor.close()
        
        if not user_data:
            return None
        
        # verify password
        stored_password = user_data[2]
        if not bcrypt.checkpw(password.encode('utf-8'), stored_password.encode('utf-8')):
            return None
        
        # update last login timestamp
        self.update_last_login(user_data[0])
        
        # get initial password details
        initial_password = user_data[12] if len(user_data) > 12 else None
        password_changed_db = user_data[11] if len(user_data) > 11 else True
        
        # check if user changed password or not
        password_changed = True
        if initial_password and isinstance(initial_password, str) and not password_changed_db:
            password_changed = not bcrypt.checkpw(initial_password.encode('utf-8'), stored_password.encode('utf-8'))
        else:
            password_changed = password_changed_db if password_changed_db is not None else True
        
        # return user data
        user = {
            'user_id': user_data[0],
            'username': user_data[1],
            'password_hash': user_data[2],
            'role': user_data[3],
            'flat_number': user_data[4],
            'name': user_data[5],
            'email': user_data[6],
            'phone': user_data[7],
            'password_changed': password_changed,
            'initial_password': initial_password if isinstance(initial_password, str) else None
        }
        return user
    
    def update_last_login(self, user_id):
        cursor = self.connection.cursor()
        cursor.execute("""
            UPDATE users SET last_login = CURRENT_TIMESTAMP WHERE user_id = %s
        """, (user_id,))
        cursor.close()
    
    def change_password(self, user_id, new_password):
        cursor = self.connection.cursor()
        password_hash = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        cursor.execute("UPDATE users SET password_hash = %s, password_changed = TRUE WHERE user_id = %s", (password_hash, user_id))
        
        cursor.close()
        return True
    
    def create_user(self, role, name, email, phone, flat_number, **kwargs):
        cursor = self.connection.cursor()
        
        username = self.generate_username(role, name)
        initial_password = self.generate_password()
        password_hash = bcrypt.hashpw(initial_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        
        cursor.execute("INSERT INTO users (username, password_hash, role, flat_number, name, email, phone, initial_password) VALUES (%s, %s, %s, %s, %s, %s, %s, %s) RETURNING user_id", (username, password_hash, role, flat_number, name, email, phone, initial_password))
        
        user_id = cursor.fetchone()[0]
        
        if role == 'owner':
            cursor.execute("INSERT INTO owners (user_id, flat_number, ownership_start_date, emergency_contact) VALUES (%s, %s, %s, %s)", (user_id, flat_number, kwargs.get('ownership_start_date'), kwargs.get('emergency_contact')))
        
        elif role == 'tenant':
            cursor.execute("INSERT INTO tenants (user_id, flat_number, rent_amount, lease_start_date, lease_end_date, security_deposit, owner_id) VALUES (%s, %s, %s, %s, %s, %s, %s)", (user_id, flat_number, kwargs.get('rent_amount'), kwargs.get('lease_start_date'), kwargs.get('lease_end_date'), kwargs.get('security_deposit'), kwargs.get('owner_id')))
        
        cursor.close()
        return {'username': username, 'initial_password': initial_password, 'user_id': user_id}
    
    def get_society_stats(self):
        cursor = self.connection.cursor()
        stats = {}
        cursor.execute("SELECT COUNT(*) FROM users WHERE role = 'owner'")
        stats['total_owners'] = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM users WHERE role = 'tenant'")
        stats['total_tenants'] = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM bills WHERE payment_status = 'pending'")
        stats['pending_bills'] = cursor.fetchone()[0]
        
        # get open complaints count
        cursor.execute("SELECT COUNT(*) FROM complaints WHERE status = 'open' OR status = 'in_progress'")
        stats['open_complaints'] = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM visitors WHERE status = 'in'")
        stats['current_visitors'] = cursor.fetchone()[0]
        cursor.execute("SELECT payment_status, COUNT(*) FROM bills GROUP BY payment_status")
        stats['bill_stats'] = [{'payment_status': r[0], 'count': r[1]} for r in cursor.fetchall()]
        cursor.execute("SELECT status, COUNT(*) FROM complaints GROUP BY status")
        stats['complaint_stats'] = [{'status': r[0], 'count': r[1]} for r in cursor.fetchall()]
        cursor.close()
        return stats
    
    def get_user_bills(self, flat_number):
        # get bills for this flat
        cursor = self.connection.cursor()
        
        cursor.execute("SELECT * FROM bills WHERE flat_number = %s ORDER BY created_at DESC", (flat_number,))
        
        bills_data = cursor.fetchall()
        cursor.close()
        
        bills = []
        for bill in bills_data:
            bills.append({
                'bill_id': bill[0],
                'flat_number': bill[1],
                'bill_type': bill[2],
                'amount': bill[3],
                'due_date': bill[4],
                'payment_status': bill[5],
                'created_by': bill[6],
                'created_at': bill[7],
                'paid_at': bill[8] if len(bill) > 8 else None,
                'payment_date': bill[8] if len(bill) > 8 else None,
                'payment_method': bill[9] if len(bill) > 9 else None
            })
        
        return bills
    
    def pay_bill(self, bill_id, payment_method):
        cursor = self.connection.cursor()
        
        cursor.execute("UPDATE bills SET payment_status = 'paid', payment_date = CURRENT_DATE, payment_method = %s WHERE bill_id = %s", (payment_method, bill_id))
        
        cursor.close()
        return True
    
    def get_user_complaints(self, user_id):
        cursor = self.connection.cursor()
        cursor.execute("SELECT * FROM complaints WHERE user_id = %s ORDER BY created_at DESC", (user_id,))
        complaints_data = cursor.fetchall()
        cursor.close()
        
        complaints = []
        for complaint in complaints_data:
            complaints.append({
                'complaint_id': complaint[0],
                'user_id': complaint[1],
                'flat_number': complaint[2],
                'title': complaint[3],
                'description': complaint[4],
                'category': complaint[5],
                'priority': complaint[6],
                'status': complaint[7],
                'created_at': complaint[8],
                'resolved_at': complaint[9] if len(complaint) > 9 else None,
                'admin_response': complaint[10] if len(complaint) > 10 else None,
                'updated_at': complaint[8]
            })
        
        return complaints
    
    def create_complaint(self, user_id, flat_number, title, description, category, priority):
        cursor = self.connection.cursor()
        
        cursor.execute("""
            INSERT INTO complaints (user_id, flat_number, title, description, category, priority)
            VALUES (%s, %s, %s, %s, %s, %s)
            RETURNING complaint_id
        """, (user_id, flat_number, title, description, category, priority))
        
        complaint_id = cursor.fetchone()[0]
        cursor.close()
        return complaint_id
    
    def get_unread_notifications(self, user_id):
        # get notifications user hasn't read yet
        cursor = self.connection.cursor()
        
        # fetch all notifications
        cursor.execute("SELECT * FROM notifications ORDER BY created_at DESC")
        all_notifications = cursor.fetchall()
        
        # get list of already read notifications
        cursor.execute("SELECT notification_id FROM notification_reads WHERE user_id = %s", (user_id,))
        read_notifications = cursor.fetchall()
        read_ids = [row[0] for row in read_notifications]
        
        cursor.close()
        
        # filter out the read ones
        unread = []
        for notif in all_notifications:
            if notif[0] not in read_ids:
                unread.append({
                    'notification_id': notif[0],
                    'title': notif[1],
                    'message': notif[2],
                    'created_by': notif[3],
                    'created_at': notif[4],
                    'type': notif[5] if len(notif) > 5 else 'general'
                })
        
        return unread
    
    def mark_notification_read(self, notification_id, user_id):
        cursor = self.connection.cursor()
        
        cursor.execute("INSERT INTO notification_reads (notification_id, user_id) VALUES (%s, %s) ON CONFLICT (notification_id, user_id) DO NOTHING", (notification_id, user_id))
        
        cursor.close()
        return True
    
    def create_notification_for_flat(self, flat_number, title, message, created_by, priority='normal'):
        cursor = self.connection.cursor()
        cursor.execute("INSERT INTO notifications (title, message, created_by) VALUES (%s, %s, %s) RETURNING notification_id", (title, message, created_by))
        
        notification_id = cursor.fetchone()[0]
        cursor.close()
        
        return notification_id, 1


    def delete_bill(self, bill_id):
        cursor = self.connection.cursor()
        cursor.execute("DELETE FROM bills WHERE bill_id = %s", (bill_id,))
        affected_rows = cursor.rowcount
        cursor.close()
        return affected_rows > 0

    def delete_user(self, user_id):
        cursor = self.connection.cursor()
        cursor.execute("SELECT role FROM users WHERE user_id = %s", (user_id,))
        user = cursor.fetchone()
        
        if user and user[0] == 'admin':
            cursor.close()
            raise ValueError("Cannot delete admin user")
        
        # delete related records first
        cursor.execute("DELETE FROM votes WHERE user_id = %s", (user_id,))
        cursor.execute("DELETE FROM notification_reads WHERE user_id = %s", (user_id,))
        cursor.execute("DELETE FROM complaints WHERE user_id = %s", (user_id,))
        
        # if tenant, delete tenant record
        cursor.execute("DELETE FROM tenants WHERE user_id = %s", (user_id,))
        
        # if owner, check if any tenants linked
        cursor.execute("SELECT owner_id FROM owners WHERE user_id = %s", (user_id,))
        owner_result = cursor.fetchone()
        if owner_result:
            owner_id = owner_result[0]
            # update tenants to remove owner link
            cursor.execute("UPDATE tenants SET owner_id = NULL WHERE owner_id = %s", (owner_id,))
            cursor.execute("DELETE FROM owners WHERE owner_id = %s", (owner_id,))
        
        cursor.execute("DELETE FROM users WHERE user_id = %s", (user_id,))
        
        cursor.close()
        return True

    def delete_visitor(self, visitor_id):
        cursor = self.connection.cursor()
        cursor.execute("DELETE FROM visitors WHERE visitor_id = %s", (visitor_id,))
        affected_rows = cursor.rowcount
        cursor.close()
        return affected_rows > 0

    def log_visitor_with_photo(self, flat_number, visitor_name, visitor_phone=None, 
                              purpose=None, vehicle_number=None, logged_by=None, visitor_photo=None):
        cursor = self.connection.cursor()
        cursor.execute("INSERT INTO visitors (flat_number, visitor_name, visitor_phone, purpose, vehicle_number, logged_by, visitor_photo) VALUES (%s, %s, %s, %s, %s, %s, %s) RETURNING visitor_id", (flat_number, visitor_name, visitor_phone, purpose, vehicle_number, logged_by, visitor_photo))
        
        visitor_id = cursor.fetchone()[0]
        cursor.close()
        
        message = f"Visitor {visitor_name} arrived at Flat {flat_number}"
        self.create_notification_for_flat(flat_number, "New Visitor", message, logged_by if logged_by else 1)
        
        return visitor_id

    def get_visitors_for_flat(self, flat_number, limit=10):
        cursor = self.connection.cursor()
        cursor.execute("SELECT * FROM visitors WHERE flat_number = %s ORDER BY entry_time DESC LIMIT %s", (flat_number, limit))
        visitors_data = cursor.fetchall()
        cursor.close()
        
        visitors = []
        for v in visitors_data:
            visitors.append({
                'visitor_id': v[0],
                'flat_number': v[1],
                'visitor_name': v[2],
                'visitor_phone': v[3] if len(v) > 3 else None,
                'purpose': v[4] if len(v) > 4 else None,
                'entry_time': v[5] if len(v) > 5 else None,
                'exit_time': v[6] if len(v) > 6 else None,
                'vehicle_number': v[7] if len(v) > 7 else None,
                'logged_by': v[8] if len(v) > 8 else None,
                'status': v[9] if len(v) > 9 else 'in',
                'visitor_photo': v[10] if len(v) > 10 else None,
                'logged_by_name': None,
                'flat_owner_name': None
            })
        
        return visitors

    def get_all_visitors(self, status_filter=None, limit=50):
        # get all visitor records
        cursor = self.connection.cursor()
        
        # filter by status if needed
        if status_filter and status_filter != 'all':
            cursor.execute("""
                SELECT * FROM visitors 
                WHERE status = %s 
                ORDER BY entry_time DESC 
                LIMIT %s
            """, (status_filter, limit))
        else:
            cursor.execute("""
                SELECT * FROM visitors 
                ORDER BY entry_time DESC 
                LIMIT %s
            """, (limit,))
        
        visitors_data = cursor.fetchall()
        cursor.close()
        
        visitors = []
        for v in visitors_data:
            visitors.append({
                'visitor_id': v[0],
                'flat_number': v[1],
                'visitor_name': v[2],
                'visitor_phone': v[3] if len(v) > 3 else None,
                'purpose': v[4] if len(v) > 4 else None,
                'entry_time': v[5] if len(v) > 5 else None,
                'exit_time': v[6] if len(v) > 6 else None,
                'vehicle_number': v[7] if len(v) > 7 else None,
                'logged_by': v[8] if len(v) > 8 else None,
                'status': v[9] if len(v) > 9 else 'in',
                'visitor_photo': v[10] if len(v) > 10 else None,
                'logged_by_name': None,
                'flat_owner_name': None
            })
        
        return visitors

    def delete_notification(self, notification_id):
        cursor = self.connection.cursor()
        # delete related reads first
        cursor.execute("DELETE FROM notification_reads WHERE notification_id = %s", (notification_id,))
        cursor.execute("DELETE FROM notifications WHERE notification_id = %s", (notification_id,))
        affected_rows = cursor.rowcount
        cursor.close()
        return affected_rows > 0

    def delete_complaint(self, complaint_id):
        cursor = self.connection.cursor()
        cursor.execute("DELETE FROM complaints WHERE complaint_id = %s", (complaint_id,))
        affected_rows = cursor.rowcount
        cursor.close()
        return affected_rows > 0

    def delete_poll(self, poll_id):
        cursor = self.connection.cursor()
        # delete related votes and options first
        cursor.execute("DELETE FROM votes WHERE poll_id = %s", (poll_id,))
        cursor.execute("DELETE FROM poll_options WHERE poll_id = %s", (poll_id,))
        cursor.execute("DELETE FROM polls WHERE poll_id = %s", (poll_id,))
        affected_rows = cursor.rowcount
        cursor.close()
        return affected_rows > 0

    def update_bill(self, bill_id, **fields):
        if not fields:
            return False
        cursor = self.connection.cursor()
        set_clause = ', '.join([f"{k} = %s" for k in fields.keys()])
        params = list(fields.values()) + [bill_id]
        query = f"UPDATE bills SET {set_clause} WHERE bill_id = %s"
        cursor.execute(query, params)
        cursor.close()
        return True

    def update_notification(self, notification_id, title=None, message=None, priority=None):
        cursor = self.connection.cursor()
        cursor.execute("UPDATE notifications SET title = %s, message = %s, priority = %s WHERE notification_id = %s", (title, message, priority, notification_id))
        cursor.close()
        return True

    def update_complaint(self, complaint_id, **fields):
        if not fields:
            return False
        cursor = self.connection.cursor()
        set_clause = ', '.join([f"{k} = %s" for k in fields.keys()])
        params = list(fields.values()) + [complaint_id]
        query = f"UPDATE complaints SET {set_clause} WHERE complaint_id = %s"
        cursor.execute(query, params)
        cursor.close()
        return True
    
    def close_connection(self):
        if self.connection:
            self.connection.close()
