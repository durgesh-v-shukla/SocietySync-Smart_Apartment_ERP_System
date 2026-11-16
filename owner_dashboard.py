import streamlit as st
import psycopg2.extras
from datetime import date

from base_dashboard import BaseDashboard
from utils import format_currency, format_date, format_datetime, get_status_color


class OwnerDashboard(BaseDashboard):
    def __init__(self, db):
        super().__init__(db)

    def show(self):
        user = st.session_state.user
        st.title("🏠 Vishwakarma Apartment")
        st.caption(f"📍 Pune | Owner Dashboard | Welcome, {user['name']} | Flat: {user['flat_number']}")

        stats = self._get_owner_stats(user['flat_number'], user['user_id'])

        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Pending Bills", stats['pending_bills'])
        col2.metric("Open Complaints", stats['open_complaints'])
        col3.metric("Unread Notifications", stats['unread_notifications'])
        col4.metric("Active Polls", stats['active_polls'])

        st.divider()
        col1, col2 = st.columns(2)

        with col1:
            st.subheader("💰 Recent Bills")
            recent_bills = self.get_recent_bills(user['flat_number'])
            if recent_bills:
                for bill in recent_bills:
                    st.write(
                        f"{get_status_color(bill['payment_status'])} "
                        f"{bill['bill_type']} — {format_currency(bill['amount'])} "
                        f"(Due: {format_date(bill['due_date'])})"
                    )
            else:
                st.info("No recent bills")

        with col2:
            st.subheader("📝 Recent Complaints")
            recent_complaints = self.get_recent_complaints(user['user_id'])
            if recent_complaints:
                for c in recent_complaints:
                    st.write(f"{get_status_color(c['status'])} {c['title']} — {c['status'].title()}")
            else:
                st.info("No recent complaints")

        st.divider()
        st.subheader("⚡ Quick Actions")
        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("💰 Pay Bills", use_container_width=True):
                st.session_state.selected_tab = "💰 My Bills"
                st.rerun()
        with col2:
            if st.button("📝 Raise Complaint", use_container_width=True):
                st.session_state.selected_tab = "📝 My Complaints"
                st.rerun()
        with col3:
            if st.button("🗳️ Vote in Polls", use_container_width=True):
                st.session_state.selected_tab = "🗳️ Polls"
                st.rerun()

    def _get_owner_stats(self, flat_number, user_id):
        cur = self._cursor()
        cur.execute("SELECT COUNT(*) AS c FROM bills WHERE flat_number = %s AND payment_status = 'pending'",
                    (flat_number,))
        pending_bills = cur.fetchone()['c']

        cur.execute("""SELECT COUNT(*) AS c FROM complaints
                       WHERE flat_number = %s AND status IN ('open','in_progress')""", (flat_number,))
        open_complaints = cur.fetchone()['c']

        cur.execute("SELECT COUNT(*) AS c FROM polls WHERE status = 'active'")
        active_polls = cur.fetchone()['c']
        cur.close()

        unread_notifs = self.db.get_unread_notifications(user_id)
        return {
            'pending_bills': pending_bills,
            'open_complaints': open_complaints,
            'unread_notifications': len(unread_notifs),
            'active_polls': active_polls,
        }
