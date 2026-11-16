"""
base_dashboard.py — shared methods for OwnerDashboard and TenantDashboard.
Both classes inherit from BaseDashboard.
"""
import streamlit as st
import pandas as pd
from datetime import datetime, date
import psycopg2.extras

from config import (
    BILL_TYPES, COMPLAINT_CATEGORIES, PAYMENT_METHODS, PRIORITY_LEVELS,
    NOTIFICATION_PRIORITIES
)
from utils import (
    format_currency, format_date, format_datetime,
    get_status_color, create_notification_display, create_poll_display,
    check_overdue_bills, create_bar_chart
)

_CARD_STYLE = """
    <div style='
        background: white; border-radius: 15px; padding: 2rem;
        margin-bottom: 2rem; box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        border: 1px solid #e5e7eb; text-align: center;
    '>
        <h1 style='font-size: 2.2rem; color: #111827; font-weight: 700; margin: 0;'>
            {icon} {title}
        </h1>
    </div>"""


def _page_header(icon, title):
    st.markdown(_CARD_STYLE.format(icon=icon, title=title), unsafe_allow_html=True)


class BaseDashboard:
    def __init__(self, db):
        self.db = db

    def _cursor(self):
        return self.db.connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

    # ── Bills ─────────────────────────────────────────────────────────────────

    def get_recent_bills(self, flat_number, limit=5):
        return self.db.get_user_bills(flat_number)[:limit]

    def show_bills(self):
        user = st.session_state.user
        _page_header("💰", "My Bills")
        check_overdue_bills(self.db)

        bills = self.db.get_user_bills(user['flat_number'])

        if not bills:
            st.info("No bills found for your flat")
            return

        total_pending = sum(float(b['amount']) for b in bills if b['payment_status'] == 'pending')
        total_overdue = sum(float(b['amount']) for b in bills if b['payment_status'] == 'overdue')
        total_paid = sum(float(b['amount']) for b in bills if b['payment_status'] == 'paid')

        col1, col2, col3 = st.columns(3)
        col1.metric("Pending Amount", format_currency(total_pending))
        col2.metric("Overdue Amount", format_currency(total_overdue))
        col3.metric("Paid Amount", format_currency(total_paid))
        st.divider()

        col1, col2 = st.columns(2)
        with col1:
            status_filter = st.selectbox("Filter by Status", ["all", "pending", "paid", "overdue"],
                                         key="bill_status_filter_user")
        with col2:
            type_filter = st.selectbox("Filter by Type", ["all"] + BILL_TYPES,
                                       key="bill_type_filter_user")

        filtered = [b for b in bills
                    if (status_filter == "all" or b['payment_status'] == status_filter)
                    and (type_filter == "all" or b['bill_type'] == type_filter)]

        if not filtered:
            st.info("No bills found with the selected filters")
            return

        for bill in filtered:
            label = (f"{get_status_color(bill['payment_status'])} "
                     f"{bill['bill_type']} — {format_currency(bill['amount'])} "
                     f"(Due: {format_date(bill['due_date'])})")
            with st.expander(label):
                col1, col2 = st.columns([2, 1])
                with col1:
                    st.write(f"**Bill ID:** {bill['bill_id']}")
                    st.write(f"**Type:** {bill['bill_type']}")
                    st.write(f"**Amount:** {format_currency(bill['amount'])}")
                    st.write(f"**Due Date:** {format_date(bill['due_date'])}")
                    st.write(f"**Status:** {bill['payment_status'].title()}")
                    if bill.get('payment_date'):
                        st.write(f"**Payment Date:** {format_date(bill['payment_date'])}")
                        st.write(f"**Payment Method:** {bill.get('payment_method', 'N/A')}")
                with col2:
                    if bill['payment_status'] in ('pending', 'overdue'):
                        st.subheader("💳 Pay Now")
                        payment_method = st.selectbox(
                            "Payment Method", PAYMENT_METHODS,
                            key=f"pm_{bill['bill_id']}"
                        )
                        if st.button("Pay Bill", key=f"pay_{bill['bill_id']}"):
                            try:
                                self.db.pay_bill(bill['bill_id'], payment_method)
                                st.success("✅ Payment successful!")
                                st.rerun()
                            except Exception as e:
                                st.error(f"Payment failed: {e}")

    # ── Complaints ────────────────────────────────────────────────────────────

    def get_recent_complaints(self, user_id, limit=5):
        return self.db.get_user_complaints(user_id)[:limit]

    def show_complaints(self):
        _page_header("📝", "My Complaints")
        tab1, tab2 = st.tabs(["Raise New Complaint", "My Complaints"])
        with tab1:
            self._raise_complaint_form()
        with tab2:
            self._view_my_complaints()

    def _raise_complaint_form(self):
        user = st.session_state.user
        st.subheader("➕ Raise New Complaint")
        with st.form("raise_complaint_form"):
            col1, col2 = st.columns(2)
            with col1:
                title = st.text_input("Complaint Title")
                category = st.selectbox("Category", COMPLAINT_CATEGORIES)
            with col2:
                priority = st.selectbox("Priority", PRIORITY_LEVELS)
            description = st.text_area("Description", height=150)
            submit = st.form_submit_button("Submit Complaint")
            if submit:
                if title and description and category:
                    try:
                        complaint_id = self.db.create_complaint(
                            user['user_id'], user['flat_number'],
                            title, description, category, priority
                        )
                        st.success(f"✅ Complaint submitted! ID: {complaint_id}")
                    except Exception as e:
                        st.error(f"Error: {e}")
                else:
                    st.error("Please fill all required fields")

    def _view_my_complaints(self):
        user = st.session_state.user
        complaints = self.db.get_user_complaints(user['user_id'])
        if not complaints:
            st.info("You haven't raised any complaints yet")
            return
        status_filter = st.selectbox("Filter by Status",
                                     ["all", "open", "in_progress", "resolved", "closed"],
                                     key="complaint_status_filter_user")
        filtered = [c for c in complaints if status_filter == "all" or c['status'] == status_filter]
        if not filtered:
            st.info("No complaints found with the selected filter")
            return
        for c in filtered:
            label = (f"{get_status_color(c['status'])} #{c['complaint_id']} — "
                     f"{c['title']} ({c['priority'].upper()})")
            with st.expander(label):
                col1, col2 = st.columns([2, 1])
                with col1:
                    st.write(f"**Category:** {c['category']}")
                    st.write(f"**Description:** {c['description']}")
                    if c.get('admin_response'):
                        st.write(f"**Admin Response:** {c['admin_response']}")
                with col2:
                    st.write(f"**Status:** {c['status'].title()}")
                    st.write(f"**Priority:** {c['priority'].title()}")
                    st.write(f"**Created:** {format_datetime(c['created_at'])}")
                    st.write(f"**Updated:** {format_datetime(c.get('updated_at'))}")
                    if c.get('resolved_at'):
                        st.write(f"**Resolved:** {format_datetime(c['resolved_at'])}")

    # ── Notifications ─────────────────────────────────────────────────────────

    def show_notifications(self):
        user = st.session_state.user
        _page_header("📢", "Notifications")

        unread = self.db.get_unread_notifications(user['user_id'])
        if unread:
            st.subheader("🔴 Unread Notifications")
            create_notification_display(unread, self.db, user['user_id'])
            st.divider()

        # Single efficient query with LEFT JOIN for read status
        cur = self._cursor()
        cur.execute("""
            SELECT n.notification_id, n.title, n.message, n.created_at, n.priority,
                   nr.read_at
            FROM notifications n
            LEFT JOIN notification_reads nr
                ON n.notification_id = nr.notification_id AND nr.user_id = %s
            ORDER BY n.created_at DESC
            LIMIT 20
        """, (user['user_id'],))
        all_notifs = cur.fetchall()
        cur.close()

        if all_notifs:
            st.subheader("📜 All Notifications")
            for n in all_notifs:
                read_status = "✅ Read" if n['read_at'] else "🔴 Unread"
                with st.expander(f"{n['title']} — {read_status} — {format_datetime(n['created_at'])}"):
                    st.write(n['message'])
                    if n['read_at']:
                        st.write(f"*Read on: {format_datetime(n['read_at'])}*")
                    else:
                        if st.button("Mark as Read", key=f"read_all_{n['notification_id']}"):
                            self.db.mark_notification_read(n['notification_id'], user['user_id'])
                            st.success("Marked as read!")
                            st.rerun()
        elif not unread:
            st.info("No notifications")

    # ── Polls ─────────────────────────────────────────────────────────────────

    def show_polls(self):
        user = st.session_state.user
        _page_header("🗳️", "Polls &amp; Voting")

        cur = self._cursor()
        cur.execute("SELECT * FROM polls WHERE status = 'active' ORDER BY created_at DESC")
        active_polls = [dict(r) for r in cur.fetchall()]

        if active_polls:
            st.subheader("🗳️ Active Polls")
            create_poll_display(active_polls, self.db, user['user_id'])

        cur.execute("SELECT * FROM polls WHERE status = 'closed' ORDER BY created_at DESC LIMIT 10")
        closed_polls = [dict(r) for r in cur.fetchall()]

        if closed_polls:
            st.subheader("📊 Recent Poll Results")
            for poll in closed_polls:
                with st.expander(f"📊 {poll['title']} (Closed)"):
                    if poll.get('description'):
                        st.write(poll['description'])
                    st.write(f"**End Date:** {format_date(poll.get('end_date'))}")
                    cur.execute("""
                        SELECT option_text, vote_count FROM poll_options
                        WHERE poll_id = %s ORDER BY vote_count DESC
                    """, (poll['poll_id'],))
                    results = cur.fetchall()
                    if results:
                        total_votes = sum(r['vote_count'] for r in results)
                        st.write("**Results:**")
                        for i, r in enumerate(results):
                            pct = (r['vote_count'] / total_votes * 100) if total_votes > 0 else 0
                            emoji = ["🥇", "🥈", "🥉"][i] if i < 3 else "•"
                            st.write(f"{emoji} {r['option_text']}: {r['vote_count']} votes ({pct:.1f}%)")
                        st.write(f"**Total Votes:** {total_votes}")

                        # Did the current user vote?
                        cur.execute("""
                            SELECT po.option_text FROM votes v
                            JOIN poll_options po ON v.option_id = po.option_id
                            WHERE v.poll_id = %s AND v.user_id = %s
                        """, (poll['poll_id'], user['user_id']))
                        user_vote = cur.fetchone()
                        if user_vote:
                            st.info(f"✅ You voted for: {user_vote['option_text']}")

        if not active_polls and not closed_polls:
            st.info("No polls available")

        cur.close()

    # ── Visitors ──────────────────────────────────────────────────────────────

    def show_visitors(self):
        user = st.session_state.user
        _page_header("🚶", "My Visitors")

        visitors = self.db.get_visitors_for_flat(user['flat_number'], limit=20)
        if not visitors:
            st.info(f"No visitor records found for Flat {user['flat_number']}")
            return

        st.subheader(f"Recent Visitors to Flat {user['flat_number']}")
        for v in visitors:
            # 🟢 = inside, 🔴 = exited
            status_icon = "🟢" if v['status'] == 'in' else "🔴"
            with st.expander(f"{status_icon} {v['visitor_name']} — {format_datetime(v['entry_time'])}"):
                col1, col2, col3 = st.columns([2, 1, 1])
                with col1:
                    st.write(f"**Name:** {v['visitor_name']}")
                    st.write(f"**Phone:** {v.get('visitor_phone') or 'N/A'}")
                    st.write(f"**Purpose:** {v.get('purpose') or 'N/A'}")
                    st.write(f"**Vehicle:** {v.get('vehicle_number') or 'N/A'}")
                    st.write(f"**Entry Time:** {format_datetime(v['entry_time'])}")
                    if v.get('exit_time'):
                        st.write(f"**Exit Time:** {format_datetime(v['exit_time'])}")
                    st.write(f"**Status:** {v['status'].title()}")
                with col2:
                    if v.get('visitor_photo'):
                        try:
                            import base64, io
                            from PIL import Image
                            photo_bytes = base64.b64decode(v['visitor_photo'])
                            st.image(Image.open(io.BytesIO(photo_bytes)),
                                     caption="Visitor Photo", width=150)
                        except Exception:
                            st.write("📷 Photo available (error displaying)")
                    else:
                        st.write("📷 No photo")
                with col3:
                    if v['status'] == 'in':
                        st.success("Currently Inside")
                    else:
                        st.info("Exited")
