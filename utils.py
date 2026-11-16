import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from datetime import datetime, date
import hashlib
import logging
import psycopg2.extras

from config import FLAT_BLOCKS, FLAT_FLOORS, FLAT_UNITS_PER_FLOOR

logger = logging.getLogger(__name__)


# ── Sidebar navigation ────────────────────────────────────────────────────────

def create_sidebar_navigation(user_role, auth_manager):
    st.sidebar.title("🏢 Vishwakarma Apartment")
    st.sidebar.caption("📍 Pune | Powered by SocietySync")

    user = auth_manager.get_current_user()
    st.sidebar.markdown(f"""
    <div style='
        background: white;
        border-radius: 10px;
        padding: 1rem;
        margin: 1rem 0;
        border: 1px solid #e5e7eb;
        box-shadow: 0 1px 4px rgba(0, 0, 0, 0.1);
    '>
        <p style='margin: 0.3rem 0; color: #111827; font-weight: 600;'>👤 {user['name']}</p>
        <p style='margin: 0.3rem 0; color: #4b5563;'>Role: <strong>{user_role.title()}</strong></p>
        <p style='margin: 0.3rem 0; color: #4b5563;'>Flat: <strong>{user['flat_number']}</strong></p>
    </div>
    """, unsafe_allow_html=True)

    st.sidebar.divider()

    if user_role == 'admin':
        options = [
            "🏠 Dashboard", "👥 Manage Users", "💰 Billing",
            "📝 Complaints", "🚶 Visitors", "📢 Notifications",
            "🗳️ Polls", "👤 Profile"
        ]
    else:
        options = [
            "🏠 Dashboard", "💰 My Bills", "📝 My Complaints",
            "👥 My Visitors", "🔔 Notifications", "🗳️ Polls", "👤 Profile"
        ]

    selected = st.sidebar.radio("Navigation", options)
    st.sidebar.divider()

    if st.sidebar.button("🚪 Logout"):
        auth_manager.logout()

    return selected


# ── Charts ────────────────────────────────────────────────────────────────────

def create_pie_chart(data, names, values, title):
    if not data:
        return None
    try:
        df = pd.DataFrame(data) if not isinstance(data, pd.DataFrame) else data
        if df.empty:
            return None
        fig = px.pie(df, names=names, values=values, title=title)
        fig.update_traces(textposition='inside', textinfo='percent+label')
        return fig
    except Exception as e:
        logger.error(f"create_pie_chart error: {e}")
        return None


def create_bar_chart(data, x, y, title):
    if not data:
        return None
    try:
        df = pd.DataFrame(data) if not isinstance(data, pd.DataFrame) else data
        if df.empty:
            return None
        fig = px.bar(df, x=x, y=y, title=title)
        fig.update_layout(showlegend=False)
        return fig
    except Exception as e:
        logger.error(f"create_bar_chart error: {e}")
        return None


# ── Notification badge ────────────────────────────────────────────────────────

def display_notification_badge(unread_count):
    if unread_count > 0:
        st.sidebar.error(f"🔴 {unread_count} unread notifications")
    else:
        st.sidebar.success("✅ No unread notifications")


# ── Formatting helpers ────────────────────────────────────────────────────────

def format_currency(amount):
    if amount is None:
        return "₹0.00"
    try:
        return f"₹{float(amount):,.2f}"
    except (ValueError, TypeError):
        return "₹0.00"


def format_date(date_obj):
    if not date_obj:
        return "N/A"
    if isinstance(date_obj, str):
        return date_obj
    try:
        return date_obj.strftime("%d-%m-%Y")
    except Exception:
        return "N/A"


def format_datetime(datetime_obj):
    if not datetime_obj:
        return "N/A"
    if isinstance(datetime_obj, str):
        return datetime_obj
    try:
        return datetime_obj.strftime("%d-%m-%Y %H:%M")
    except Exception:
        return "N/A"


def get_status_color(status):
    colors = {
        'pending': '🟡', 'paid': '🟢', 'overdue': '🔴',
        'open': '🟡', 'in_progress': '🟠', 'resolved': '🟢',
        'closed': '⚫', 'active': '🟢', 'inactive': '🔴'
    }
    return colors.get(str(status).lower(), '⚪')


def get_status_badge(status):
    status_colors = {
        'pending': ('#fef3c7', '#92400e', '⏳'),
        'paid': ('#d1fae5', '#065f46', '✅'),
        'overdue': ('#fee2e2', '#991b1b', '❌'),
        'open': ('#fef3c7', '#92400e', '🔓'),
        'in_progress': ('#dbeafe', '#1e40af', '⚙️'),
        'resolved': ('#d1fae5', '#065f46', '✅'),
        'closed': ('#e5e7eb', '#374151', '🔒'),
        'active': ('#d1fae5', '#065f46', '✅'),
        'expired': ('#fee2e2', '#991b1b', '⏰'),
    }
    bg, fg, icon = status_colors.get(str(status).lower(), ('#e5e7eb', '#374151', '•'))
    return f"""
        <span style='background-color:{bg};color:{fg};padding:0.3rem 0.8rem;
                     border-radius:20px;font-weight:600;font-size:0.85rem;
                     display:inline-block;margin:0.2rem;'>
            {icon} {status.upper()}
        </span>"""


def get_priority_badge(priority):
    priority_colors = {
        'low': ('#d1fae5', '#065f46', '🟢'),
        'medium': ('#fef3c7', '#92400e', '🟡'),
        'high': ('#fed7aa', '#9a3412', '🟠'),
        'urgent': ('#fee2e2', '#991b1b', '🔴'),
    }
    bg, fg, icon = priority_colors.get(str(priority).lower(), ('#e5e7eb', '#374151', '⚪'))
    return f"""
        <span style='background-color:{bg};color:{fg};padding:0.3rem 0.8rem;
                     border-radius:20px;font-weight:600;font-size:0.85rem;
                     display:inline-block;margin:0.2rem;'>
            {icon} {priority.upper()}
        </span>"""


# ── Data table ────────────────────────────────────────────────────────────────

def create_data_table(data, columns=None):
    if not data:
        st.info("No data available")
        return
    try:
        df = pd.DataFrame(data)
        if df.empty:
            st.info("No data available")
            return
        if 'amount' in df.columns:
            df['amount'] = df['amount'].apply(lambda x: format_currency(x) if x is not None else 'N/A')
        if 'created_at' in df.columns:
            df['created_at'] = df['created_at'].apply(lambda x: format_datetime(x) if x is not None else 'N/A')
        if 'due_date' in df.columns:
            df['due_date'] = df['due_date'].apply(lambda x: format_date(x) if x is not None else 'N/A')
        if 'payment_date' in df.columns:
            df['payment_date'] = df['payment_date'].apply(lambda x: format_date(x) if x is not None else 'N/A')
        if columns:
            st.dataframe(df[columns], use_container_width=True)
        else:
            st.dataframe(df, use_container_width=True)
    except Exception as e:
        st.error(f"Error creating data table: {e}")


# ── Validation ────────────────────────────────────────────────────────────────

def validate_email(email):
    import re
    if not email:
        return False
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None


def validate_phone(phone):
    import re
    if not phone:
        return False
    clean_phone = re.sub(r'[^0-9]', '', phone)
    return re.match(r'^[0-9]{10}$', clean_phone) is not None


# ── Flat helpers ──────────────────────────────────────────────────────────────

def get_flat_numbers():
    flats = []
    for block in FLAT_BLOCKS:
        for floor in FLAT_FLOORS:
            for unit in FLAT_UNITS_PER_FLOOR:
                flats.append(f"{block}{floor}{unit:02d}")
    return flats


def get_available_flat_numbers(db=None):
    try:
        if db is None:
            from database import Database
            db = Database()
        cur = db.connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        all_flats = get_flat_numbers()
        cur.execute("SELECT DISTINCT flat_number FROM users WHERE flat_number IS NOT NULL AND role != 'admin'")
        assigned = {r['flat_number'] for r in cur.fetchall()}
        cur.close()
        available = [f for f in all_flats if f not in assigned]
        return available if available else ["No flats available"]
    except Exception as e:
        logger.error(f"get_available_flat_numbers error: {e}")
        return get_flat_numbers()


def get_allotted_flat_numbers(db=None):
    try:
        if db is None:
            from database import Database
            db = Database()
        cur = db.connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute("SELECT DISTINCT flat_number FROM users WHERE flat_number IS NOT NULL ORDER BY flat_number")
        flats = [r['flat_number'] for r in cur.fetchall()]
        cur.close()
        return flats
    except Exception as e:
        logger.error(f"get_allotted_flat_numbers error: {e}")
        return get_flat_numbers()


def get_flats_with_occupants(db=None):
    try:
        if db is None:
            from database import Database
            db = Database()
        cur = db.connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute("""
            SELECT DISTINCT u.flat_number, u.name, u.role, u.user_id
            FROM users u
            WHERE u.flat_number IS NOT NULL AND u.role != 'admin'
            ORDER BY u.flat_number, u.role DESC
        """)
        rows = cur.fetchall()
        flats_info = {}
        for row in rows:
            flat_number = row['flat_number']
            role = row['role']
            user_id = row['user_id']
            occupancy_type = 'Owner-Occupied' if role == 'owner' else 'Tenant-Occupied'
            owner_name = None
            if role == 'tenant':
                cur.execute("""
                    SELECT u.name FROM tenants t
                    JOIN owners o ON t.owner_id = o.owner_id
                    JOIN users u ON o.user_id = u.user_id
                    WHERE t.user_id = %s
                """, (user_id,))
                owner_row = cur.fetchone()
                if owner_row:
                    owner_name = owner_row['name']
            if flat_number not in flats_info:
                flats_info[flat_number] = {
                    'flat_number': flat_number,
                    'residents': [],
                    'primary_occupancy': occupancy_type,
                    'owner_name': owner_name
                }
            flats_info[flat_number]['residents'].append({'name': row['name'], 'role': role})
        cur.close()
        return flats_info
    except Exception as e:
        logger.error(f"get_flats_with_occupants error: {e}")
        return {}


def get_flat_display_options(db=None):
    try:
        flats_info = get_flats_with_occupants(db)
        options = {}
        for flat_num, info in flats_info.items():
            if flat_num == 'ADMIN':
                continue
            residents_str = ", ".join([f"{r['name']} ({r['role'].title()})" for r in info['residents']])
            if info['primary_occupancy'] == 'Owner-Occupied':
                display_text = f"{flat_num} - 🏠 Owner: {residents_str}"
            elif info['primary_occupancy'] == 'Tenant-Occupied':
                if info['owner_name']:
                    display_text = f"{flat_num} - 🏘️ Tenant: {residents_str} (Owner: {info['owner_name']})"
                else:
                    display_text = f"{flat_num} - 🏘️ Tenant: {residents_str}"
            else:
                display_text = f"{flat_num} - ❓ {residents_str}"
            options[display_text] = flat_num
        return options
    except Exception as e:
        logger.error(f"get_flat_display_options error: {e}")
        return {}


# ── Bill overdue check (once per session) ────────────────────────────────────

def check_overdue_bills(db):
    if st.session_state.get('_overdue_checked', False):
        return
    try:
        cur = db.connection.cursor()
        cur.execute("""
            UPDATE bills
            SET payment_status = 'overdue'
            WHERE payment_status = 'pending' AND due_date < CURRENT_DATE
        """)
        cur.close()
        st.session_state._overdue_checked = True
    except Exception as e:
        logger.error(f"check_overdue_bills error: {e}")


# ── Notification display ──────────────────────────────────────────────────────

def create_notification_display(notifications, db, user_id):
    if not notifications:
        st.info("No new notifications")
        return
    for notification in notifications:
        with st.expander(f"📢 {notification['title']} — {format_datetime(notification['created_at'])}"):
            st.write(notification['message'])
            col1, col2 = st.columns([3, 1])
            with col2:
                if st.button("Mark as Read", key=f"read_{notification['notification_id']}"):
                    db.mark_notification_read(notification['notification_id'], user_id)
                    st.success("Marked as read!")
                    st.rerun()


# ── Poll display ──────────────────────────────────────────────────────────────

def create_poll_display(polls, db, user_id):
    if not polls:
        st.info("No active polls")
        return

    for poll in polls:
        st.subheader(f"🗳️ {poll['title']}")
        if poll.get('description'):
            st.write(poll['description'])

        cur = db.connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute("SELECT vote_id FROM votes WHERE poll_id = %s AND user_id = %s",
                    (poll['poll_id'], user_id))
        has_voted = cur.fetchone() is not None

        if has_voted:
            st.info("✅ You have already voted in this poll")
            cur.execute("""
                SELECT option_text, vote_count FROM poll_options
                WHERE poll_id = %s ORDER BY vote_count DESC
            """, (poll['poll_id'],))
            results = cur.fetchall()
            if results:
                results_df = pd.DataFrame(results)
                fig = create_bar_chart(results_df, 'option_text', 'vote_count', "Poll Results")
                if fig:
                    st.plotly_chart(fig, use_container_width=True, theme="streamlit")
        else:
            cur.execute("SELECT option_id, option_text FROM poll_options WHERE poll_id = %s",
                        (poll['poll_id'],))
            options = cur.fetchall()
            if options:
                option_texts = [opt['option_text'] for opt in options]
                selected_option = st.radio("Select your choice:", option_texts,
                                           key=f"poll_{poll['poll_id']}")
                if st.button("Vote", key=f"vote_{poll['poll_id']}"):
                    selected_id = next(o['option_id'] for o in options if o['option_text'] == selected_option)
                    cur.execute("INSERT INTO votes (poll_id, option_id, user_id) VALUES (%s, %s, %s)",
                                (poll['poll_id'], selected_id, user_id))
                    cur.execute("UPDATE poll_options SET vote_count = vote_count + 1 WHERE option_id = %s",
                                (selected_id,))
                    st.success("✅ Vote recorded successfully!")
                    st.rerun()

        cur.close()
        st.divider()


# ── Unique key generator ──────────────────────────────────────────────────────

def generate_unique_key(prefix, obj, index=None):
    key_parts = [prefix]
    for field in ['bill_id', 'complaint_id', 'visitor_id', 'notification_id', 'poll_id']:
        if field in obj:
            key_parts.append(str(obj[field]))
            break
    for field in ['flat_number', 'bill_type', 'created_at']:
        if field in obj and obj[field]:
            key_parts.append(str(obj[field]).replace(' ', '_'))
    if index is not None:
        key_parts.append(str(index))
    obj_hash = hashlib.md5(str(sorted(obj.items())).encode()).hexdigest()[:8]
    key_parts.append(obj_hash)
    return "_".join(key_parts)


# ── Misc UI helpers ───────────────────────────────────────────────────────────

def show_success_animation(message):
    st.success(f"✅ {message}")


def show_error_animation(message):
    st.error(f"❌ {message}")


def create_info_card(title, content, icon="ℹ️"):
    st.markdown(f"""
        <div class='card'>
            <h3>{icon} {title}</h3>
            <p style='color: #64748b; font-size: 1.1rem;'>{content}</p>
        </div>
    """, unsafe_allow_html=True)
