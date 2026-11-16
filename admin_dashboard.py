import streamlit as st
import pandas as pd
import psycopg2.extras
from datetime import datetime, date, timedelta

from config import (
    BILL_TYPES, COMPLAINT_CATEGORIES, PAYMENT_METHODS,
    PRIORITY_LEVELS, NOTIFICATION_PRIORITIES
)
from utils import (
    create_pie_chart, create_bar_chart, format_currency,
    format_date, format_datetime, validate_email, validate_phone,
    get_flat_numbers, get_allotted_flat_numbers, generate_unique_key,
    get_flat_display_options, get_available_flat_numbers, get_flats_with_occupants,
)


class AdminDashboard:
    def __init__(self, db):
        self.db = db

    def _cursor(self):
        return self.db.connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

    # ── Dashboard ─────────────────────────────────────────────────────────────

    def show_dashboard(self):
        st.title("🏠 Vishwakarma Apartment")
        st.caption("📍 Pune | Admin Dashboard")

        stats = self.db.get_society_stats()
        st.markdown("### 📊 Quick Overview")
        col1, col2, col3, col4, col5 = st.columns(5)
        col1.metric("Total Owners", stats['total_owners'])
        col2.metric("Total Tenants", stats['total_tenants'])
        col3.metric("Pending Bills", stats['pending_bills'])
        col4.metric("Open Complaints", stats['open_complaints'])
        col5.metric("Current Visitors", stats['current_visitors'])

        st.markdown("### 🏢 Flat Occupancy Status")
        flats_info = get_flats_with_occupants(self.db)
        if flats_info:
            owner_occ = sum(1 for i in flats_info.values() if i['primary_occupancy'] == 'Owner-Occupied')
            tenant_occ = sum(1 for i in flats_info.values() if i['primary_occupancy'] == 'Tenant-Occupied')
            col1, col2, col3 = st.columns(3)
            col1.metric("🏠 Owner-Occupied", owner_occ)
            col2.metric("🏘️ Tenant-Occupied", tenant_occ)
            col3.metric("📊 Total Occupied", len(flats_info))
            with st.expander("🔍 View Detailed Flat Information", expanded=False):
                for flat_num, info in sorted(flats_info.items()):
                    icon = "🏠" if info['primary_occupancy'] == 'Owner-Occupied' else "🏘️"
                    color = "#22c55e" if info['primary_occupancy'] == 'Owner-Occupied' else "#3b82f6"
                    residents = ", ".join([f"{r['name']} ({r['role'].title()})" for r in info['residents']])
                    if info['owner_name'] and info['primary_occupancy'] == 'Tenant-Occupied':
                        txt = f"{icon} **{flat_num}** — {residents} | Owner: {info['owner_name']}"
                    else:
                        txt = f"{icon} **{flat_num}** — {residents}"
                    st.markdown(f"<p style='color:{color};margin:0.2rem 0;'>{txt}</p>",
                                unsafe_allow_html=True)
        else:
            st.info("ℹ️ No flat occupancy data available.")

        st.divider()
        col1, col2 = st.columns(2)
        with col1:
            if stats.get('bill_stats'):
                fig = create_pie_chart(stats['bill_stats'], 'payment_status', 'count', "Bill Payment Status")
                if fig:
                    st.plotly_chart(fig, use_container_width=True, theme="streamlit")
            else:
                st.info("No bill statistics available")
        with col2:
            if stats.get('complaint_stats'):
                fig = create_bar_chart(stats['complaint_stats'], 'status', 'count', "Complaint Status")
                if fig:
                    st.plotly_chart(fig, use_container_width=True, theme="streamlit")
            else:
                st.info("No complaint statistics available")

        st.markdown("### 📋 Recent Activities")
        cur = self._cursor()
        cur.execute("SELECT title, flat_number, created_at FROM complaints ORDER BY created_at DESC LIMIT 5")
        complaints = cur.fetchall()
        cur.close()
        if complaints:
            for c in complaints:
                st.write(f"• {c['title']} — Flat {c['flat_number']} — {format_datetime(c['created_at'])}")
        else:
            st.info("No recent complaints")

    # ── User Management ───────────────────────────────────────────────────────

    def manage_users(self):
        st.title("👥 Manage Users")
        tab1, tab2, tab3 = st.tabs(["Add New User", "View Users", "User Details"])
        with tab1:
            self._add_user_form()
        with tab2:
            self._view_users()
        with tab3:
            self._user_details()

    def _add_user_form(self):
        st.subheader("➕ Add New User")
        with st.form("add_user_form"):
            col1, col2 = st.columns(2)
            with col1:
                role = st.selectbox("User Role", ["owner", "tenant"])
                name = st.text_input("Full Name")
                email = st.text_input("Email")
                phone = st.text_input("Phone Number")
                st.markdown("**Flat Assignment:**")
                available_flats = get_available_flat_numbers(self.db)
                if available_flats and available_flats[0] != "No flats available":
                    flat_number = st.selectbox("Flat Number", available_flats,
                                               help="Only showing available (unassigned) flats")
                else:
                    st.warning("⚠️ No available flats")
                    flat_number = None
            with col2:
                ownership_start_date = None
                emergency_contact = None
                owner_id = None
                rent_amount = 0.0
                lease_start_date = date.today()
                lease_end_date = date.today() + timedelta(days=365)
                security_deposit = 0.0

                if role == "owner":
                    ownership_start_date = st.date_input("Ownership Start Date", value=date.today())
                    emergency_contact = st.text_input("Emergency Contact")
                else:
                    cur = self._cursor()
                    cur.execute("""
                        SELECT o.owner_id, u.name, u.flat_number
                        FROM owners o JOIN users u ON o.user_id = u.user_id
                        ORDER BY u.flat_number
                    """)
                    owners = cur.fetchall()
                    cur.close()
                    if owners:
                        owner_opts = {f"{o['name']} (Flat {o['flat_number']})": o['owner_id'] for o in owners}
                        sel = st.selectbox("Owner", list(owner_opts.keys()))
                        owner_id = owner_opts[sel]
                    else:
                        st.error("No owners available. Please add an owner first.")
                    rent_amount = st.number_input("Monthly Rent", min_value=0.0, value=0.0)
                    lease_start_date = st.date_input("Lease Start Date", value=date.today())
                    lease_end_date = st.date_input("Lease End Date",
                                                   value=date.today() + timedelta(days=365))
                    security_deposit = st.number_input("Security Deposit", min_value=0.0, value=0.0)

            submit = st.form_submit_button("Create User")
            if submit:
                if not name or not email or not phone:
                    st.error("Please fill all required fields")
                elif not flat_number:
                    st.error("No available flats")
                elif not validate_email(email):
                    st.error("Please enter a valid email address")
                elif not validate_phone(phone):
                    st.error("Please enter a valid 10-digit phone number")
                else:
                    try:
                        kwargs = {}
                        if role == "owner":
                            kwargs = {'ownership_start_date': ownership_start_date,
                                      'emergency_contact': emergency_contact}
                        else:
                            if not owner_id:
                                st.error("Please select an owner")
                                return
                            kwargs = {'owner_id': owner_id, 'rent_amount': rent_amount,
                                      'lease_start_date': lease_start_date,
                                      'lease_end_date': lease_end_date,
                                      'security_deposit': security_deposit}
                        result = self.db.create_user(role, name, email, phone, flat_number, **kwargs)
                        st.success(f"✅ User created successfully!")
                        st.info(f"**Username:** `{result['username']}`")
                        st.info(f"**Initial Password:** `{result['initial_password']}`")
                        st.warning("Share these credentials with the user. They must change password on first login.")
                    except Exception as e:
                        st.error(f"Error creating user: {e}")

    def _view_users(self):
        st.subheader("👥 All Users")
        col1, col2 = st.columns(2)
        with col1:
            role_filter = st.selectbox("Filter by Role", ["all", "owner", "tenant"])
        with col2:
            search_text = st.text_input("Search by Name or Flat")

        cur = self._cursor()
        cur.execute("SELECT * FROM users WHERE role != 'admin' ORDER BY created_at DESC")
        all_users = cur.fetchall()
        cur.close()

        users = []
        for u in all_users:
            if role_filter != "all" and u['role'] != role_filter:
                continue
            if search_text:
                if not ((u['name'] and search_text.lower() in u['name'].lower()) or
                        (u['flat_number'] and search_text in u['flat_number'])):
                    continue
            users.append(dict(u))

        if users:
            df_data = [{
                'Name': u['name'], 'Role': u['role'].title(),
                'Flat': u['flat_number'], 'Email': u['email'],
                'Phone': u['phone'], 'Username': u['username'],
                'Password Changed': '✅' if u['password_changed'] else '❌',
                'Last Login': format_datetime(u['last_login']),
                'Created': format_datetime(u['created_at']),
            } for u in users]
            st.dataframe(pd.DataFrame(df_data), use_container_width=True)

            unchanged = [u for u in users if not u['password_changed'] and u.get('initial_password')]
            if unchanged:
                st.subheader("🔑 Initial Passwords (Not Yet Changed)")
                for u in unchanged:
                    st.write(f"**{u['name']}** (`{u['username']}`): `{u['initial_password']}`")

            st.markdown("---")
            st.subheader("🗑️ Delete User")
            del_opts = {f"{u['name']} ({u['flat_number']})": u['user_id'] for u in users}
            sel = st.selectbox("Select user to delete", list(del_opts.keys()))
            uid = del_opts[sel]
            st.warning("⚠️ This will permanently delete all user data")
            if st.button("🗑️ Delete User"):
                if st.session_state.user.get('user_id') == uid:
                    st.error("Cannot delete the currently logged-in user")
                else:
                    try:
                        self.db.delete_user(uid)
                        st.success("✅ User deleted!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error: {e}")
        else:
            st.info("No users found")

    def _user_details(self):
        st.subheader("👤 User Details")
        cur = self._cursor()
        cur.execute("SELECT user_id, name, username, flat_number FROM users WHERE role != 'admin' ORDER BY name")
        users = cur.fetchall()
        if not users:
            st.info("No users found")
            cur.close()
            return
        user_opts = {f"{u['name']} ({u['flat_number']})": u['user_id'] for u in users}
        sel = st.selectbox("Select User", list(user_opts.keys()))
        uid = user_opts[sel]

        cur.execute("SELECT * FROM users WHERE user_id = %s", (uid,))
        u = cur.fetchone()
        if u:
            col1, col2 = st.columns(2)
            with col1:
                st.write("**Basic Info**")
                for k, v in [('Name', u['name']), ('Role', u['role'].title()),
                              ('Flat', u['flat_number']), ('Email', u['email']),
                              ('Phone', u['phone']), ('Username', u['username'])]:
                    st.write(f"{k}: {v}")
            with col2:
                st.write("**Account Info**")
                st.write(f"Created: {format_datetime(u['created_at'])}")
                st.write(f"Last Login: {format_datetime(u['last_login'])}")
                st.write(f"Password Changed: {'Yes' if u['password_changed'] else 'No'}")
                if not u['password_changed'] and u.get('initial_password'):
                    st.write(f"Initial Password: `{u['initial_password']}`")

            if u['role'] == 'owner':
                cur.execute("SELECT * FROM owners WHERE user_id = %s", (uid,))
                o = cur.fetchone()
                if o:
                    st.write(f"**Owner Info** — Start: {format_date(o['ownership_start_date'])}, "
                             f"Emergency: {o['emergency_contact']}")
            elif u['role'] == 'tenant':
                cur.execute("SELECT * FROM tenants WHERE user_id = %s", (uid,))
                t = cur.fetchone()
                if t:
                    st.write(f"**Tenant Info** — Rent: {format_currency(t['rent_amount'])}, "
                             f"Lease: {format_date(t['lease_start_date'])} to {format_date(t['lease_end_date'])}, "
                             f"Deposit: {format_currency(t['security_deposit'])}")
        cur.close()

    # ── Billing ───────────────────────────────────────────────────────────────

    def billing_management(self):
        st.title("💰 Billing Management")
        tab1, tab2, tab3 = st.tabs(["Create Bills", "View Bills", "Payment Tracking"])
        with tab1:
            self._create_bill_form()
        with tab2:
            self._view_bills()
        with tab3:
            self._payment_tracking()

    def _create_bill_form(self):
        st.subheader("📄 Create New Bill")
        bill_mode = st.radio("Select Bill Creation Mode", ["Single Flat", "All Flats (Bulk)"],
                             horizontal=True)

        if bill_mode == "Single Flat":
            with st.form("create_bill_form"):
                col1, col2 = st.columns(2)
                with col1:
                    flat_opts = get_flat_display_options(self.db)
                    if flat_opts:
                        sel_flat = st.selectbox("Billing Flat (with resident info)", list(flat_opts.keys()))
                        flat_number = flat_opts[sel_flat]
                        st.info(f"💰 Billing: **{flat_number}**")
                    else:
                        flat_number = st.selectbox("Flat Number", get_allotted_flat_numbers(self.db))
                    bill_type = st.selectbox("Bill Type", BILL_TYPES)
                    amount = st.number_input("Amount (₹)", min_value=0.0, value=0.0)
                with col2:
                    due_date = st.date_input("Due Date", value=date.today() + timedelta(days=30))
                    st.text_area("Description (Optional)")

                if st.form_submit_button("Create Bill"):
                    if amount <= 0:
                        st.error("Amount must be greater than 0")
                    else:
                        try:
                            cur = self._cursor()
                            cur.execute("""
                                INSERT INTO bills (flat_number, bill_type, amount, due_date, created_by)
                                VALUES (%s, %s, %s, %s, %s) RETURNING bill_id
                            """, (flat_number, bill_type, amount, due_date,
                                  st.session_state.user['user_id']))
                            bill_id = cur.fetchone()['bill_id']
                            cur.close()
                            st.success(f"✅ Bill created! Bill ID: {bill_id}")
                        except Exception as e:
                            st.error(f"❌ Error: {e}")
        else:
            bill_target = st.radio("Generate Bills For:",
                                   ["All Owner Flats", "All Resident Flats"],
                                   horizontal=True)
            with st.form("bulk_bill_form"):
                col1, col2 = st.columns(2)
                with col1:
                    bill_type = st.selectbox("Bill Type", BILL_TYPES, key="bulk_bt")
                    amount = st.number_input("Amount (₹, same for all)", min_value=0.0, value=0.0, key="bulk_amt")
                with col2:
                    due_date = st.date_input("Due Date", value=date.today() + timedelta(days=30), key="bulk_dd")

                if st.form_submit_button("🚀 Generate Bills"):
                    if amount <= 0:
                        st.error("Amount must be greater than 0")
                    else:
                        cur = self._cursor()
                        if "Owner" in bill_target:
                            cur.execute("SELECT DISTINCT flat_number FROM owners ORDER BY flat_number")
                        else:
                            cur.execute("""
                                SELECT DISTINCT flat_number FROM users
                                WHERE flat_number IS NOT NULL AND role IN ('owner', 'tenant')
                            """)
                        targets = [r['flat_number'] for r in cur.fetchall()]
                        for flat in targets:
                            cur.execute("""
                                INSERT INTO bills (flat_number, bill_type, amount, due_date, created_by)
                                VALUES (%s, %s, %s, %s, %s)
                            """, (flat, bill_type, amount, due_date,
                                  st.session_state.user['user_id']))
                        cur.close()
                        st.success(f"✅ Generated {len(targets)} bills!")

    def _view_bills(self):
        st.subheader("📋 All Bills")
        col1, col2, col3 = st.columns(3)
        with col1:
            status_filter = st.selectbox("Filter by Status", ["all", "pending", "paid", "overdue"],
                                         key="admin_bill_status")
        with col2:
            type_filter = st.selectbox("Filter by Type", ["all"] + BILL_TYPES, key="admin_bill_type")
        with col3:
            flat_filter = st.text_input("Filter by Flat Number", key="admin_bill_flat")

        cur = self._cursor()
        cur.execute("SELECT * FROM bills ORDER BY created_at DESC")
        all_bills = cur.fetchall()
        cur.close()

        bills = []
        seen = set()
        for b in all_bills:
            if b['bill_id'] in seen:
                continue
            seen.add(b['bill_id'])
            if status_filter != "all" and b['payment_status'] != status_filter:
                continue
            if type_filter != "all" and b['bill_type'] != type_filter:
                continue
            if flat_filter and flat_filter not in b['flat_number']:
                continue
            bills.append(dict(b))

        if not bills:
            st.info("No bills found with the selected filters")
            return

        st.write(f"**Found {len(bills)} bills**")
        for i, bill in enumerate(bills):
            sc = "🟡" if bill['payment_status'] == 'pending' else ("🟢" if bill['payment_status'] == 'paid' else "🔴")
            with st.expander(f"{sc} #{bill['bill_id']} — {bill['bill_type']} — {format_currency(bill['amount'])} — Flat {bill['flat_number']}"):
                col1, col2 = st.columns([2, 1])
                with col1:
                    st.write(f"**Flat:** {bill['flat_number']}")
                    st.write(f"**Bill Type:** {bill['bill_type']}")
                    st.write(f"**Amount:** {format_currency(bill['amount'])}")
                    st.write(f"**Due Date:** {format_date(bill['due_date'])}")
                    st.write(f"**Created:** {format_datetime(bill['created_at'])}")
                    if bill.get('payment_date'):
                        st.write(f"**Payment Date:** {format_date(bill['payment_date'])}")
                        st.write(f"**Payment Method:** {bill.get('payment_method', 'N/A')}")
                with col2:
                    st.write(f"**Status:** {bill['payment_status'].title()}")
                    if bill['payment_status'] == 'pending':
                        st.warning("⏳ Pending")
                    elif bill['payment_status'] == 'overdue':
                        st.error("🚨 Overdue!")
                    else:
                        st.success("✅ Paid")

                    if bill['payment_status'] in ('pending', 'overdue'):
                        ukey = generate_unique_key("mark_paid", bill, i)
                        if st.button("Mark as Paid", key=ukey):
                            try:
                                cur = self._cursor()
                                cur.execute("""
                                    UPDATE bills
                                    SET payment_status = 'paid', payment_date = CURRENT_DATE,
                                        payment_method = 'Admin Override'
                                    WHERE bill_id = %s
                                """, (bill['bill_id'],))
                                cur.close()
                                st.success("✅ Marked as paid!")
                                st.rerun()
                            except Exception as e:
                                st.error(f"Error: {e}")

                    st.markdown("---")
                    if st.button("🗑️ Delete Bill", key=f"del_bill_{bill['bill_id']}", type="secondary"):
                        try:
                            self.db.delete_bill(bill['bill_id'])
                            st.success("✅ Bill deleted")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error: {e}")

    def _payment_tracking(self):
        st.subheader("📊 Payment Analytics")
        cur = self._cursor()
        cur.execute("SELECT COUNT(*) AS c FROM bills")
        total = cur.fetchone()['c']
        cur.execute("SELECT COUNT(*) AS c FROM bills WHERE payment_status = 'paid'")
        paid = cur.fetchone()['c']
        cur.execute("SELECT COUNT(*) AS c FROM bills WHERE payment_status = 'pending'")
        pending = cur.fetchone()['c']
        cur.execute("SELECT COUNT(*) AS c FROM bills WHERE payment_status = 'overdue'")
        overdue = cur.fetchone()['c']
        cur.execute("SELECT COALESCE(SUM(amount), 0) AS s FROM bills")
        total_amt = float(cur.fetchone()['s'])
        cur.execute("SELECT COALESCE(SUM(amount), 0) AS s FROM bills WHERE payment_status = 'paid'")
        collected = float(cur.fetchone()['s'])
        cur.close()

        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Total Bills", total)
        col1.metric("Paid Bills", paid)
        col2.metric("Pending Bills", pending)
        col2.metric("Overdue Bills", overdue)
        col3.metric("Total Amount", format_currency(total_amt))
        rate = (collected / total_amt * 100) if total_amt > 0 else 0
        col4.metric("Collected Amount", format_currency(collected))
        col4.metric("Collection Rate", f"{rate:.1f}%")

    # ── Complaints ────────────────────────────────────────────────────────────

    def complaint_management(self):
        st.title("📝 Complaint Management")
        tab1, tab2 = st.tabs(["All Complaints", "Complaint Analytics"])
        with tab1:
            self._view_all_complaints()
        with tab2:
            self._complaint_analytics()

    def _view_all_complaints(self):
        st.subheader("📋 All Complaints")
        col1, col2, col3 = st.columns(3)
        with col1:
            status_filter = st.selectbox("Filter by Status",
                                         ["all", "open", "in_progress", "resolved", "closed"],
                                         key="admin_comp_status")
        with col2:
            priority_filter = st.selectbox("Filter by Priority",
                                           ["all"] + PRIORITY_LEVELS,
                                           key="admin_comp_priority")
        with col3:
            flat_filter = st.text_input("Filter by Flat", key="admin_comp_flat")

        cur = self._cursor()
        cur.execute("SELECT * FROM complaints ORDER BY created_at DESC")
        all_comp = cur.fetchall()

        complaints = []
        for c in all_comp:
            if status_filter != "all" and c['status'] != status_filter:
                continue
            if priority_filter != "all" and c['priority'] != priority_filter:
                continue
            if flat_filter and flat_filter not in c['flat_number']:
                continue
            complaints.append(dict(c))

        if not complaints:
            st.info("No complaints found")
            cur.close()
            return

        for c in complaints:
            with st.expander(f"#{c['complaint_id']} — {c['title']} ({c['priority'].upper()})"):
                col1, col2 = st.columns([2, 1])
                with col1:
                    st.write(f"**Flat:** {c['flat_number']}")
                    st.write(f"**Category:** {c['category']}")
                    st.write(f"**Description:** {c['description']}")
                    if c.get('admin_response'):
                        st.write(f"**Admin Response:** {c['admin_response']}")
                with col2:
                    st.write(f"**Status:** {c['status'].title()}")
                    st.write(f"**Priority:** {c['priority'].title()}")
                    st.write(f"**Created:** {format_datetime(c['created_at'])}")
                    if c.get('resolved_at'):
                        st.write(f"**Resolved:** {format_datetime(c['resolved_at'])}")

                valid_statuses = ["open", "in_progress", "resolved", "closed"]
                curr_status = c['status'] if c['status'] in valid_statuses else "open"
                new_status = st.selectbox("Update Status", valid_statuses,
                                          index=valid_statuses.index(curr_status),
                                          key=f"st_{c['complaint_id']}")
                if st.button("Update Status", key=f"upd_{c['complaint_id']}"):
                    fields = {'status': new_status, 'updated_at': datetime.now()}
                    if new_status == 'resolved':
                        fields['resolved_at'] = datetime.now()
                    self.db.update_complaint(c['complaint_id'], **fields)
                    st.success("✅ Status updated!")
                    st.rerun()

                response = st.text_area("Admin Response", value=c.get('admin_response') or "",
                                        key=f"resp_{c['complaint_id']}")
                if st.button("Save Response", key=f"sav_{c['complaint_id']}"):
                    self.db.update_complaint(c['complaint_id'], admin_response=response,
                                             updated_at=datetime.now())
                    st.success("✅ Response saved!")
                    st.rerun()

                if st.button("🗑️ Delete Complaint", key=f"del_comp_{c['complaint_id']}",
                             type="secondary"):
                    self.db.delete_complaint(c['complaint_id'])
                    st.success("✅ Complaint deleted")
                    st.rerun()

        cur.close()

    def _complaint_analytics(self):
        st.subheader("📊 Complaint Analytics")
        cur = self._cursor()
        cur.execute("SELECT status, COUNT(*) AS count FROM complaints GROUP BY status")
        status_stats = [dict(r) for r in cur.fetchall()]
        cur.execute("SELECT priority, COUNT(*) AS count FROM complaints GROUP BY priority")
        priority_stats = [dict(r) for r in cur.fetchall()]
        cur.close()

        col1, col2 = st.columns(2)
        if status_stats:
            fig = create_pie_chart(status_stats, 'status', 'count', "By Status")
            if fig:
                col1.plotly_chart(fig, use_container_width=True)
        if priority_stats:
            fig = create_bar_chart(priority_stats, 'priority', 'count', "By Priority")
            if fig:
                col2.plotly_chart(fig, use_container_width=True)

    # ── Visitors ──────────────────────────────────────────────────────────────

    def visitor_management(self):
        st.title("🚶 Visitor Management")
        tab1, tab2, tab3 = st.tabs(["Log Visitor", "Current Visitors", "Visitor History"])
        with tab1:
            self._log_visitor_form()
        with tab2:
            self._current_visitors()
        with tab3:
            self._visitor_history()

    def _log_visitor_form(self):
        st.subheader("➕ Log New Visitor")
        try:
            flat_opts = get_flat_display_options(self.db)
            sorted_keys = sorted(flat_opts.keys())
        except Exception as e:
            st.error(f"Error loading flat options: {e}")
            flat_opts = {}
            sorted_keys = []

        with st.form("log_visitor_form"):
            col1, col2 = st.columns(2)
            with col1:
                st.markdown("**Select Visiting Flat:**")
                if flat_opts:
                    sel = st.selectbox("Flat (with resident info)", sorted_keys)
                    flat_number = flat_opts[sel]  # safe lookup, not string split
                    st.info(f"📍 Visiting: **{flat_number}**")
                else:
                    flat_number = st.selectbox("Flat Number", get_allotted_flat_numbers(self.db))
                visitor_name = st.text_input("Visitor Name")
                visitor_phone = st.text_input("Visitor Phone")
                if visitor_phone and not __import__('re').match(r'^\d{10}$',
                                                                visitor_phone.replace(' ', '')):
                    st.warning("⚠️ Phone should be 10 digits")
            with col2:
                purpose = st.text_input("Purpose of Visit")
                vehicle_number = st.text_input("Vehicle Number (Optional)")

            st.markdown("---")
            st.subheader("📸 Visitor Photo (Optional)")
            photo_tab1, photo_tab2 = st.tabs(["📁 Upload Photo", "📷 Take Photo"])
            uploaded_photo = None
            camera_photo = None
            with photo_tab1:
                uploaded_photo = st.file_uploader("Choose photo", type=['png', 'jpg', 'jpeg'])
                if uploaded_photo:
                    st.image(uploaded_photo, caption="Uploaded Photo", width=150)
            with photo_tab2:
                camera_photo = st.camera_input("Take a photo")
                if camera_photo:
                    st.image(camera_photo, caption="Captured Photo", width=150)

            if st.form_submit_button("Log Visitor"):
                if not visitor_name or not flat_number:
                    st.error("Please enter visitor name and select flat number")
                else:
                    try:
                        import base64
                        photo_data = None
                        if uploaded_photo:
                            photo_data = base64.b64encode(uploaded_photo.read()).decode()
                        elif camera_photo:
                            photo_data = base64.b64encode(camera_photo.read()).decode()

                        vid = self.db.log_visitor_with_photo(
                            flat_number=flat_number,
                            visitor_name=visitor_name,
                            visitor_phone=visitor_phone,
                            purpose=purpose,
                            vehicle_number=vehicle_number,
                            logged_by=st.session_state.user['user_id'],
                            visitor_photo=photo_data
                        )
                        st.success(f"✅ Visitor logged! ID: {vid}. Notification sent to Flat {flat_number}.")
                    except Exception as e:
                        st.error(f"Error logging visitor: {e}")

    def _current_visitors(self):
        st.subheader("👥 Current Visitors")
        cur = self._cursor()
        cur.execute("""
            SELECT v.*, u.name AS flat_resident_name
            FROM visitors v
            LEFT JOIN users u ON v.flat_number = u.flat_number AND u.role IN ('owner', 'tenant')
            WHERE v.status = 'in'
            ORDER BY v.entry_time DESC
        """)
        visitors = cur.fetchall()

        if not visitors:
            st.info("No current visitors")
            cur.close()
            return

        for idx, v in enumerate(visitors):
            flat_info = f"Visiting Flat {v['flat_number']}"
            if v.get('flat_resident_name'):
                flat_info += f" ({v['flat_resident_name']})"
            with st.expander(f"🟢 {v['visitor_name']} — {flat_info}"):
                col1, col2, col3 = st.columns([2, 1, 1])
                with col1:
                    st.write(f"**Visitor:** {v['visitor_name']}")
                    st.write(f"**Flat:** {v['flat_number']}")
                    st.write(f"**Phone:** {v.get('visitor_phone') or 'N/A'}")
                    st.write(f"**Purpose:** {v.get('purpose') or 'N/A'}")
                    st.write(f"**Vehicle:** {v.get('vehicle_number') or 'N/A'}")
                    st.write(f"**Entry Time:** {format_datetime(v['entry_time'])}")
                with col2:
                    if v.get('visitor_photo'):
                        try:
                            import base64, io
                            from PIL import Image
                            photo_bytes = base64.b64decode(v['visitor_photo'])
                            st.image(Image.open(io.BytesIO(photo_bytes)), caption="Visitor Photo", width=150)
                        except Exception:
                            st.write("📷 Photo available (error displaying)")
                    else:
                        st.write("📷 No photo")
                with col3:
                    ukey = f"cur_{idx}_{v['visitor_id']}"
                    if st.button("Mark Exit", key=f"exit_{ukey}"):
                        cur2 = self._cursor()
                        cur2.execute("""
                            UPDATE visitors SET status = 'out', exit_time = CURRENT_TIMESTAMP
                            WHERE visitor_id = %s
                        """, (v['visitor_id'],))
                        cur2.close()
                        st.success("✅ Visitor exited!")
                        st.rerun()
                    if st.button("🗑️ Delete", key=f"del_{ukey}", type="secondary"):
                        try:
                            self.db.delete_visitor(v['visitor_id'])
                            st.success("✅ Record deleted")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error: {e}")
        cur.close()

    def _visitor_history(self):
        st.subheader("📜 Visitor History")
        col1, col2, col3 = st.columns(3)
        with col1:
            flat_filter = st.selectbox("Filter by Flat",
                                       ["All Flats"] + get_allotted_flat_numbers(self.db))
        with col2:
            date_filter = st.date_input("Filter by Date", value=None)
        with col3:
            status_filter = st.selectbox("Filter by Status", ["All", "in", "out"])

        query = "SELECT * FROM visitors WHERE 1=1"
        params = []
        if flat_filter != "All Flats":
            query += " AND flat_number = %s"
            params.append(flat_filter)
        if status_filter != "All":
            query += " AND status = %s"
            params.append(status_filter)
        try:
            if date_filter and hasattr(date_filter, 'strftime'):
                query += " AND DATE(entry_time) = %s"
                params.append(date_filter)
        except Exception:
            pass
        query += " ORDER BY entry_time DESC LIMIT 100"

        try:
            cur = self._cursor()
            cur.execute(query, params)
            visitors = cur.fetchall()
            cur.close()

            if not visitors:
                st.info("No visitor records found")
                return

            st.write(f"Found {len(visitors)} visitor records")
            for idx, v in enumerate(visitors):
                status_icon = "🟢" if v['status'] == 'in' else "🔴"
                with st.expander(f"{status_icon} {v['visitor_name']} — Flat {v['flat_number']} ({format_datetime(v['entry_time'])})"):
                    col1, col2, col3 = st.columns([2, 1, 1])
                    with col1:
                        st.write(f"**Visitor:** {v['visitor_name']}")
                        st.write(f"**Flat:** {v['flat_number']}")
                        if v.get('visitor_phone'):
                            st.write(f"**Phone:** {v['visitor_phone']}")
                        if v.get('purpose'):
                            st.write(f"**Purpose:** {v['purpose']}")
                        if v.get('vehicle_number'):
                            st.write(f"**Vehicle:** {v['vehicle_number']}")
                        st.write(f"**Entry:** {format_datetime(v['entry_time'])}")
                        if v.get('exit_time'):
                            st.write(f"**Exit:** {format_datetime(v['exit_time'])}")
                        st.write(f"**Status:** {v['status'].title()}")
                    with col2:
                        if v.get('visitor_photo'):
                            try:
                                import base64, io
                                from PIL import Image
                                photo_bytes = base64.b64decode(v['visitor_photo'])
                                st.image(Image.open(io.BytesIO(photo_bytes)), caption="Photo", width=150)
                            except Exception:
                                st.write("📷 Photo (error displaying)")
                        else:
                            st.write("📷 No photo")
                    with col3:
                        ukey = f"hist_{idx}_{v['visitor_id']}"
                        if v['status'] == 'in':
                            if st.button("Mark Exit", key=f"exit_{ukey}"):
                                cur2 = self._cursor()
                                cur2.execute("""
                                    UPDATE visitors SET status = 'out', exit_time = CURRENT_TIMESTAMP
                                    WHERE visitor_id = %s
                                """, (v['visitor_id'],))
                                cur2.close()
                                st.success("✅ Exited!")
                                st.rerun()
                        if st.button("🗑️ Delete Record", key=f"del_{ukey}", type="secondary"):
                            try:
                                self.db.delete_visitor(v['visitor_id'])
                                st.success("✅ Deleted")
                                st.rerun()
                            except Exception as e:
                                st.error(f"Error: {e}")
        except Exception as e:
            st.error(f"Error fetching visitor history: {e}")

    # ── Notifications ─────────────────────────────────────────────────────────

    def notification_management(self):
        st.title("📢 Notification Management")
        tab1, tab2 = st.tabs(["Send Notification", "Notification History"])
        with tab1:
            self._send_notification_form()
        with tab2:
            self._notification_history()

    def _send_notification_form(self):
        st.subheader("📤 Send New Notification")
        with st.form("send_notification_form"):
            title = st.text_input("Notification Title")
            message = st.text_area("Message", height=150)
            priority = st.selectbox("Priority", NOTIFICATION_PRIORITIES)
            if st.form_submit_button("Send Notification"):
                if title and message:
                    try:
                        cur = self._cursor()
                        cur.execute("""
                            INSERT INTO notifications (title, message, created_by, priority)
                            VALUES (%s, %s, %s, %s) RETURNING notification_id
                        """, (title, message, st.session_state.user['user_id'], priority))
                        nid = cur.fetchone()['notification_id']
                        cur.close()
                        st.success(f"✅ Notification sent! ID: {nid}")
                    except Exception as e:
                        st.error(f"Error: {e}")
                else:
                    st.error("Please enter title and message")

    def _notification_history(self):
        st.subheader("📜 Notification History")
        cur = self._cursor()
        cur.execute("SELECT * FROM notifications ORDER BY created_at DESC")
        notifs = cur.fetchall()

        if not notifs:
            st.info("No notifications found")
            cur.close()
            return

        for n in notifs:
            cur.execute("SELECT COUNT(*) AS c FROM notification_reads WHERE notification_id = %s",
                        (n['notification_id'],))
            read_count = cur.fetchone()['c']
            with st.expander(f"{n['title']} — {format_datetime(n['created_at'])}"):
                st.write(f"**Message:** {n['message']}")
                st.write(f"**Priority:** {n['priority'].title()}")
                st.write(f"**Read by:** {read_count} users")
                col1, col2 = st.columns([3, 1])
                with col2:
                    if st.button("🗑️ Delete", key=f"del_notif_{n['notification_id']}",
                                 type="secondary"):
                        try:
                            self.db.delete_notification(n['notification_id'])
                            st.success("✅ Deleted")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error: {e}")
        cur.close()

    # ── Polls ─────────────────────────────────────────────────────────────────

    def poll_management(self):
        st.title("🗳️ Poll Management")
        tab1, tab2, tab3 = st.tabs(["Create Poll", "Active Polls", "Poll Results"])
        with tab1:
            self._create_poll_form()
        with tab2:
            self._active_polls()
        with tab3:
            self._poll_results()

    def _create_poll_form(self):
        st.subheader("➕ Create New Poll")
        with st.form("create_poll_form"):
            title = st.text_input("Poll Title")
            description = st.text_area("Poll Description")
            end_date = st.date_input("End Date", value=date.today() + timedelta(days=7))
            st.write("**Poll Options** (one per line, minimum 2)")
            options_text = st.text_area("Options", height=150,
                                        placeholder="Option 1\nOption 2\nOption 3")
            if st.form_submit_button("Create Poll"):
                if not title or not options_text:
                    st.error("Please enter title and options")
                else:
                    options = [o.strip() for o in options_text.split('\n') if o.strip()]
                    if len(options) < 2:
                        st.error("Please provide at least 2 options")
                    else:
                        try:
                            cur = self._cursor()
                            cur.execute("""
                                INSERT INTO polls (title, description, created_by, end_date)
                                VALUES (%s, %s, %s, %s) RETURNING poll_id
                            """, (title, description, st.session_state.user['user_id'], end_date))
                            poll_id = cur.fetchone()['poll_id']
                            for opt in options:
                                cur.execute("""
                                    INSERT INTO poll_options (poll_id, option_text)
                                    VALUES (%s, %s)
                                """, (poll_id, opt))
                            cur.close()
                            st.success(f"✅ Poll created! ID: {poll_id}")
                        except Exception as e:
                            st.error(f"Error: {e}")

    def _active_polls(self):
        st.subheader("🗳️ Active Polls")
        cur = self._cursor()
        cur.execute("SELECT * FROM polls WHERE status = 'active' ORDER BY created_at DESC")
        polls = cur.fetchall()

        if not polls:
            st.info("No active polls")
            cur.close()
            return

        for p in polls:
            with st.expander(f"{p['title']} (Ends: {format_date(p['end_date'])})"):
                st.write(f"**Description:** {p.get('description') or 'N/A'}")
                st.write(f"**Created:** {format_datetime(p['created_at'])}")
                cur.execute("SELECT COUNT(*) AS c FROM votes WHERE poll_id = %s", (p['poll_id'],))
                vote_count = cur.fetchone()['c']
                st.write(f"**Total Votes:** {vote_count}")

                col1, col2 = st.columns(2)
                with col1:
                    if st.button("Close Poll", key=f"close_{p['poll_id']}"):
                        cur.execute("UPDATE polls SET status = 'closed' WHERE poll_id = %s",
                                    (p['poll_id'],))
                        st.success("✅ Poll closed!")
                        st.rerun()
                    if st.button("🗑️ Delete Poll", key=f"del_poll_{p['poll_id']}",
                                 type="secondary"):
                        try:
                            self.db.delete_poll(p['poll_id'])
                            st.success("✅ Poll deleted")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error: {e}")
        cur.close()

    def _poll_results(self):
        st.subheader("📊 Poll Results")
        cur = self._cursor()
        cur.execute("SELECT * FROM polls ORDER BY created_at DESC")
        polls = cur.fetchall()

        if not polls:
            st.info("No polls found")
            cur.close()
            return

        for p in polls:
            status_label = p['status'].title()
            st.write(f"### {p['title']}")
            st.write(f"**Status:** {status_label} | **End Date:** {format_date(p['end_date'])}")
            cur.execute("""
                SELECT option_text, vote_count FROM poll_options
                WHERE poll_id = %s ORDER BY vote_count DESC
            """, (p['poll_id'],))
            results = cur.fetchall()
            if results:
                total = sum(r['vote_count'] for r in results)
                col1, col2 = st.columns([1, 2])
                with col1:
                    for i, r in enumerate(results):
                        pct = (r['vote_count'] / total * 100) if total > 0 else 0
                        emoji = ["🥇", "🥈", "🥉"][i] if i < 3 else "•"
                        st.write(f"{emoji} {r['option_text']}: {r['vote_count']} votes ({pct:.1f}%)")
                    st.write(f"**Total Votes:** {total}")
                with col2:
                    if total > 0:
                        df = pd.DataFrame([dict(r) for r in results])
                        fig = create_bar_chart(df, 'option_text', 'vote_count',
                                              f"Results: {p['title']}")
                        if fig:
                            st.plotly_chart(fig, use_container_width=True, theme="streamlit")
            else:
                st.write("No votes yet")
            st.divider()
        cur.close()
