import streamlit as st
import psycopg2.extras
from datetime import date

from base_dashboard import BaseDashboard
from utils import format_currency, format_date, format_datetime, get_status_color


class TenantDashboard(BaseDashboard):
    def __init__(self, db):
        super().__init__(db)

    def show(self):
        user = st.session_state.user
        st.title("🔑 Vishwakarma Apartment")
        st.caption(f"📍 Pune | Tenant Dashboard | Welcome, {user['name']} | Flat: {user['flat_number']}")

        tenant_info = self._get_tenant_info(user['user_id'])
        if tenant_info:
            col1, col2 = st.columns(2)
            with col1:
                st.subheader("🏠 Rental Information")
                st.write(f"**Owner:** {tenant_info.get('owner_name') or 'N/A'}")
                st.write(f"**Monthly Rent:** {format_currency(tenant_info['rent_amount'])}")
                st.write(f"**Security Deposit:** {format_currency(tenant_info['security_deposit'])}")
            with col2:
                st.subheader("📅 Lease Details")
                st.write(f"**Lease Start:** {format_date(tenant_info['lease_start_date'])}")
                st.write(f"**Lease End:** {format_date(tenant_info['lease_end_date'])}")
                if tenant_info['lease_end_date']:
                    remaining = (tenant_info['lease_end_date'] - date.today()).days
                    if remaining > 0:
                        st.write(f"**Days Remaining:** {remaining}")
                    else:
                        st.error(f"**Lease Expired:** {abs(remaining)} days ago")
            st.divider()

        stats = self._get_tenant_stats(user['flat_number'], user['user_id'])
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

    def _get_tenant_info(self, user_id):
        cur = self._cursor()
        cur.execute("SELECT * FROM tenants WHERE user_id = %s", (user_id,))
        tenant = cur.fetchone()
        if not tenant:
            cur.close()
            return None
        owner_name = None
        if tenant['owner_id']:
            cur.execute("""
                SELECT u.name FROM owners o
                JOIN users u ON o.user_id = u.user_id
                WHERE o.owner_id = %s
            """, (tenant['owner_id'],))
            row = cur.fetchone()
            if row:
                owner_name = row['name']
        cur.close()
        return {
            'tenant_id': tenant['tenant_id'],
            'user_id': tenant['user_id'],
            'flat_number': tenant['flat_number'],
            'rent_amount': tenant['rent_amount'],
            'lease_start_date': tenant['lease_start_date'],
            'lease_end_date': tenant['lease_end_date'],
            'security_deposit': tenant['security_deposit'],
            'owner_id': tenant['owner_id'],
            'created_at': tenant['created_at'],
            'owner_name': owner_name,
        }

    def _get_tenant_stats(self, flat_number, user_id):
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
        unread = self.db.get_unread_notifications(user_id)
        return {
            'pending_bills': pending_bills,
            'open_complaints': open_complaints,
            'unread_notifications': len(unread),
            'active_polls': active_polls,
        }

    def show_rental_agreement(self):
        """Detailed rental agreement view for tenants."""
        user = st.session_state.user
        st.title("📄 Rental Agreement")
        tenant_info = self._get_tenant_info(user['user_id'])
        if not tenant_info:
            st.error("No rental agreement information found")
            return

        # Calculate remaining days here so it's in scope everywhere below
        remaining_days = None
        if tenant_info['lease_end_date']:
            remaining_days = (tenant_info['lease_end_date'] - date.today()).days

        col1, col2 = st.columns(2)
        with col1:
            st.subheader("🏠 Property Details")
            st.write(f"**Flat Number:** {user['flat_number']}")
            st.write(f"**Owner:** {tenant_info.get('owner_name') or 'N/A'}")
            st.write("**Property Type:** Apartment")

            st.subheader("💰 Financial Details")
            st.write(f"**Monthly Rent:** {format_currency(tenant_info['rent_amount'])}")
            st.write(f"**Security Deposit:** {format_currency(tenant_info['security_deposit'])}")

            lease_start = tenant_info['lease_start_date']
            if lease_start and lease_start <= date.today():
                months_elapsed = ((date.today().year - lease_start.year) * 12
                                  + date.today().month - lease_start.month)
                total_rent_due = months_elapsed * float(tenant_info['rent_amount'] or 0)
                cur = self._cursor()
                cur.execute("""
                    SELECT COALESCE(SUM(amount), 0) AS total
                    FROM bills
                    WHERE flat_number = %s AND payment_status = 'paid' AND bill_type = 'Maintenance'
                """, (user['flat_number'],))
                total_rent_paid = float(cur.fetchone()['total'])
                cur.close()
                st.write(f"**Total Maintenance Due:** {format_currency(total_rent_due)}")
                st.write(f"**Total Maintenance Paid:** {format_currency(total_rent_paid)}")
                if total_rent_paid < total_rent_due:
                    st.error(f"**Outstanding:** {format_currency(total_rent_due - total_rent_paid)}")
                else:
                    st.success("✅ Payments up to date")

        with col2:
            st.subheader("📅 Lease Terms")
            st.write(f"**Start Date:** {format_date(tenant_info['lease_start_date'])}")
            st.write(f"**End Date:** {format_date(tenant_info['lease_end_date'])}")

            if tenant_info['lease_start_date'] and tenant_info['lease_end_date']:
                duration = (tenant_info['lease_end_date'] - tenant_info['lease_start_date']).days
                st.write(f"**Duration:** {duration} days ({duration // 30} months)")

            if remaining_days is not None:
                if remaining_days > 0:
                    st.success(f"**Days Remaining:** {remaining_days}")
                    if remaining_days <= 60:
                        st.warning(f"⏰ Lease expires in {remaining_days} days. Consider renewal!")
                else:
                    st.error(f"**Lease Expired:** {abs(remaining_days)} days ago")

            st.subheader("📋 Agreement Status")
            if remaining_days is not None and remaining_days > 0:
                st.write("**Status:** Active")
            else:
                st.write("**Status:** Expired")
            st.write(f"**Created:** {format_date(tenant_info['created_at'])}")

        st.divider()
        st.subheader("📝 Lease Terms & Conditions")
        for i, term in enumerate([
            "Rent must be paid by the 5th of each month",
            "No subletting without owner's written consent",
            "Tenant is responsible for utility bills",
            "Security deposit will be refunded after deducting any damages",
            "30 days notice required for lease termination",
            "No pets allowed without prior approval",
            "Maintenance requests must be submitted through the system",
        ], 1):
            st.write(f"{i}. {term}")
