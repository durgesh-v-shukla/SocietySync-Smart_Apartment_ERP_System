import streamlit as st
import pandas as pd
from datetime import datetime, date, timedelta
from utils import (
    create_pie_chart, create_bar_chart, format_currency, 
    format_date, format_datetime, create_data_table,
    validate_email, validate_phone, get_flat_numbers, get_allotted_flat_numbers,
    generate_unique_key, get_flat_display_options, get_available_flat_numbers
)

class AdminDashboard:
    def __init__(self, db):
        self.db = db
    
    def show_dashboard(self):
        st.title("🏠 Vishwakarma Apartment")
        st.caption("📍 Pune | Admin Dashboard")
        
        # Get society statistics
        stats = self.db.get_society_stats()
        
        st.markdown("### 📊 Quick Overview")
        col1, col2, col3, col4, col5 = st.columns(5)
        
        col1.metric("Total Owners", stats['total_owners'])
        col2.metric("Total Tenants", stats['total_tenants'])
        col3.metric("Pending Bills", stats['pending_bills'])
        col4.metric("Open Complaints", stats['open_complaints'])
        col5.metric("Current Visitors", stats['current_visitors'])
        
        # Flat Occupancy Overview
        st.markdown("### 🏢 Flat Occupancy Status")
        
        # Import the new function
        from utils import get_flats_with_occupants
        flats_info = get_flats_with_occupants()
        
        if flats_info:
            # Summary statistics
            owner_occupied = sum(1 for info in flats_info.values() if info['primary_occupancy'] == 'Owner-Occupied')
            tenant_occupied = sum(1 for info in flats_info.values() if info['primary_occupancy'] == 'Tenant-Occupied')
            total_occupied = len(flats_info)
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("🏠 Owner-Occupied", owner_occupied)
            with col2:
                st.metric("🏘️ Tenant-Occupied", tenant_occupied)
            with col3:
                st.metric("📊 Total Occupied", total_occupied)
            
            # Detailed view in expander
            with st.expander("🔍 View Detailed Flat Information", expanded=False):
                for flat_num, info in sorted(flats_info.items()):
                    if info['primary_occupancy'] == 'Owner-Occupied':
                        icon = "🏠"
                        status_color = "#22c55e"  # green
                    else:
                        icon = "🏘️"
                        status_color = "#3b82f6"  # blue
                    
                    residents = ", ".join([f"{r['name']} ({r['role'].title()})" for r in info['residents']])
                    
                    if info['owner_name'] and info['primary_occupancy'] == 'Tenant-Occupied':
                        display_text = f"{icon} **{flat_num}** - {residents} | Owner: {info['owner_name']}"
                    else:
                        display_text = f"{icon} **{flat_num}** - {residents}"
                    
                    st.markdown(f"<p style='color: {status_color}; margin: 0.2rem 0;'>{display_text}</p>", 
                              unsafe_allow_html=True)
        else:
            st.info("ℹ️ No flat occupancy data available. Please add owners and tenants to flats.")
        
        st.divider()
        
        # Charts
        col1, col2 = st.columns(2)
        
        with col1:
            # Bill payment statistics - FIXED
            if stats.get('bill_stats') and len(stats['bill_stats']) > 0:
                fig = create_pie_chart(
                    stats['bill_stats'], 
                    'payment_status', 
                    'count', 
                    "Bill Payment Status"
                )
                if fig is not None:
                    st.plotly_chart(fig, use_container_width=True, theme="streamlit")
            else:
                st.info("No bill statistics available")
        
        with col2:
            # Complaint statistics - FIXED
            if stats.get('complaint_stats') and len(stats['complaint_stats']) > 0:
                fig = create_bar_chart(
                    stats['complaint_stats'], 
                    'status', 
                    'count', 
                    "Complaint Status"
                )
                if fig is not None:
                    st.plotly_chart(fig, use_container_width=True, theme="streamlit")
            else:
                st.info("No complaint statistics available")
        
        st.markdown("### 📋 Recent Activities")
        cursor = self.db.connection.cursor()
        cursor.execute("SELECT * FROM complaints ORDER BY created_at DESC LIMIT 5")
        complaints = cursor.fetchall()
        cursor.close()
        
        if complaints:
            for c in complaints:
                st.write(f"• {c[3]} - Flat {c[2]} - {format_datetime(c[8])}")
        else:
            st.info("No recent complaints")
        
    def manage_users(self):
        st.title("👥 Manage Users")
        tab1, tab2, tab3 = st.tabs(["Add New User", "View Users", "User Details"])
        
        with tab1:
            self.add_user_form()
        with tab2:
            self.view_users()
        with tab3:
            self.user_details()
    
    def add_user_form(self):
        st.subheader("➕ Add New User")
        
        with st.form("add_user_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                role = st.selectbox("User Role", ["owner", "tenant"], key="user_role_select")
                name = st.text_input("Full Name", key="user_name_input")
                email = st.text_input("Email", key="user_email_input")
                phone = st.text_input("Phone Number", key="user_phone_input")
                
                # Show flat selection with current occupancy info
                st.markdown("**Flat Assignment:**")
                available_flats = get_available_flat_numbers()
                
                if role == "owner":
                    if available_flats and available_flats[0] != "No flats available":
                        flat_number = st.selectbox(
                            "Flat Number (for Owner)", 
                            available_flats, 
                            key="user_flat_select",
                            help="Only showing available (unassigned) flats"
                        )
                    else:
                        st.warning("⚠️ No available flats for new owner")
                        flat_number = None
                else:  # tenant
                    st.info("💡 **For Tenants:** Select an available flat where the tenant will live.")
                    if available_flats and available_flats[0] != "No flats available":
                        flat_number = st.selectbox(
                            "Flat Number (for Tenant)", 
                            available_flats, 
                            key="user_flat_select",
                            help="Only showing available (unassigned) flats"
                        )
                    else:
                        st.warning("⚠️ No available flats for new tenant")
                        flat_number = None
            
            with col2:
                if role == "owner":
                    ownership_start_date = st.date_input("Ownership Start Date", value=date.today(), key="owner_start_date")
                    emergency_contact = st.text_input("Emergency Contact", key="owner_emergency_contact")
                else:  # tenant
                    # Get available owners - Simple query
                    cursor = self.db.connection.cursor()
                    cursor.execute("SELECT * FROM owners ORDER BY flat_number")
                    owners_data = cursor.fetchall()
                    cursor.close()
                    
                    # Convert to list
                    owners = []
                    for o in owners_data:
                        # Get owner name
                        cursor2 = self.db.connection.cursor()
                        cursor2.execute("SELECT name, flat_number FROM users WHERE user_id = %s", (o[1],))
                        user_data = cursor2.fetchone()
                        cursor2.close()
                        
                        if user_data:
                            owners.append({
                                'owner_id': o[0],
                                'name': user_data[0],
                                'flat_number': user_data[1]
                            })
                    
                    owner_options = {f"{owner['name']} (Flat {owner['flat_number']})": owner['owner_id'] 
                                   for owner in owners}
                    
                    if owner_options:
                        selected_owner = st.selectbox("Owner", list(owner_options.keys()), key="tenant_owner_select")
                        owner_id = owner_options[selected_owner]
                    else:
                        st.error("No owners available. Please add an owner first.")
                        owner_id = None
                    
                    rent_amount = st.number_input("Monthly Rent", min_value=0.0, value=0.0, key="tenant_rent")
                    lease_start_date = st.date_input("Lease Start Date", value=date.today(), key="tenant_lease_start")
                    lease_end_date = st.date_input("Lease End Date", value=date.today() + timedelta(days=365), key="tenant_lease_end")
                    security_deposit = st.number_input("Security Deposit", min_value=0.0, value=0.0, key="tenant_deposit")
            
            submit = st.form_submit_button("Create User", key="create_user_submit")
            
            if submit:
                # Validation
                if not name or not email or not phone:
                    st.error("Please fill all required fields")
                elif not flat_number:
                    st.error("No available flats. All flats are currently assigned.")
                elif not validate_email(email):
                    st.error("Please enter a valid email address")
                elif not validate_phone(phone):
                    st.error("Please enter a valid 10-digit phone number")
                else:
                    try:
                        # Prepare kwargs based on role
                        kwargs = {}
                        if role == "owner":
                            kwargs = {
                                'ownership_start_date': ownership_start_date,
                                'emergency_contact': emergency_contact
                            }
                        else:  # tenant
                            if owner_id is None:
                                st.error("Please select an owner")
                                return
                            
                            kwargs = {
                                'owner_id': owner_id,
                                'rent_amount': rent_amount,
                                'lease_start_date': lease_start_date,
                                'lease_end_date': lease_end_date,
                                'security_deposit': security_deposit
                            }
                        
                        # Create user
                        result = self.db.create_user(role, name, email, phone, flat_number, **kwargs)
                        
                        st.success(f"User created successfully!")
                        st.info(f"**Username:** {result['username']}")
                        st.info(f"**Initial Password:** {result['initial_password']}")
                        st.warning("Please share these credentials with the user. The initial password is also stored in the system for your reference.")
                        
                    except Exception as e:
                        st.error(f"Error creating user: {e}")
    
    def view_users(self):
        """View all users with detailed information"""
        st.subheader("👥 All Users")
        
        # Filter options
        col1, col2 = st.columns(2)
        with col1:
            # Check for session state filter
            default_role = "all"
            if hasattr(st.session_state, 'user_filter') and st.session_state.user_filter:
                default_role = st.session_state.user_filter
                st.session_state.user_filter = None
            # make sure default_role is valid
            if default_role not in ["all", "owner", "tenant"]:
                default_role = "all"
            role_filter = st.selectbox("Filter by Role", ["all", "owner", "tenant"],
                                     index=["all", "owner", "tenant"].index(default_role), key="user_role_filter")
        with col2:
            search_text = st.text_input("Search by Name or Flat", key="user_search_text")
        
        # Get users - Simple query
        cursor = self.db.connection.cursor()
        
        # Build simple query
        cursor.execute("SELECT * FROM users WHERE role != 'admin' ORDER BY created_at DESC")
        users_data = cursor.fetchall()
        cursor.close()
        
        # Convert to list of dictionaries
        users = []
        for u in users_data:
            # Filter by role if needed
            if role_filter != "all" and u[3] != role_filter:
                continue
            
            # Filter by search text if needed
            if search_text:
                name_match = u[5] and search_text.lower() in u[5].lower()
                flat_match = u[4] and search_text in u[4]
                if not name_match and not flat_match:
                    continue
            
            users.append({
                'user_id': u[0],
                'username': u[1],
                'role': u[3],
                'flat_number': u[4],
                'name': u[5],
                'email': u[6],
                'phone': u[7],
                'created_at': u[9],  # index 9 is created_at
                'last_login': u[10] if len(u) > 10 else None,  # index 10 is last_login
                'password_changed': u[11] if len(u) > 11 and u[11] is not None else False,  # index 11 is password_changed
                'initial_password': u[12] if len(u) > 12 else None  # index 12 is initial_password
            })
        
        if users and len(users) > 0:
            # Display users in a table format
            users_data = []
            for user in users:
                users_data.append({
                    'Name': user['name'],
                    'Role': user['role'].title(),
                    'Flat': user['flat_number'],
                    'Email': user['email'],
                    'Phone': user['phone'],
                    'Username': user['username'],
                    'Password Changed': '✅' if user['password_changed'] else '❌',
                    'Last Login': format_datetime(user['last_login']),
                    'Created': format_datetime(user['created_at'])
                })
            
            df = pd.DataFrame(users_data)
            st.dataframe(df, width='stretch')
            
            unchanged = [u for u in users if not u['password_changed']]
            if unchanged:
                st.subheader("🔑 Initial Passwords")
                for u in unchanged:
                    st.write(f"**{u['name']}**: `{u['initial_password']}`")

            st.markdown("---")
            st.subheader("🗑️ Delete User")
            if users:
                del_opts = {f"{u['name']} ({u['flat_number']})": u['user_id'] for u in users}
                sel = st.selectbox("Select user", list(del_opts.keys()), key="del_user")
                uid = del_opts[sel]
                st.warning("⚠️ This will delete all user data")
                if st.button("🗑️ Delete", key="del_btn"):
                    if st.session_state.user.get('user_id') == uid:
                        st.error("Cannot delete logged in user")
                    else:
                        self.db.delete_user(uid)
                        st.success("User deleted!")
                        st.rerun()
        else:
            st.info("No users found")
    
    def user_details(self):
        st.subheader("👤 User Details")
        cursor = self.db.connection.cursor()
        cursor.execute("SELECT user_id, name, username, flat_number FROM users WHERE role != 'admin' ORDER BY name")
        users = [{'user_id': u[0], 'name': u[1], 'username': u[2], 'flat_number': u[3]} for u in cursor.fetchall()]
        
        if users and len(users) > 0:
            user_options = {f"{user['name']} ({user['flat_number']})": user['user_id'] for user in users}
            selected_user = st.selectbox("Select User", list(user_options.keys()), key="user_details_select")
            user_id = user_options[selected_user]
            
            # Get user details
            cursor.execute("""
                SELECT * FROM users WHERE user_id = %s
            """, (user_id,))
            user_data = cursor.fetchone()
            
            if user_data:
                # Convert tuple to dict
                user = {
                    'user_id': user_data[0],
                    'username': user_data[1],
                    'password_hash': user_data[2],
                    'role': user_data[3],
                    'flat_number': user_data[4],
                    'name': user_data[5],
                    'email': user_data[6],
                    'phone': user_data[7],
                    'profile_picture': user_data[8],
                    'created_at': user_data[9],
                    'last_login': user_data[10] if len(user_data) > 10 else None,
                    'password_changed': user_data[11] if len(user_data) > 11 and user_data[11] is not None else False,
                    'initial_password': user_data[12] if len(user_data) > 12 else None
                }
                
                col1, col2 = st.columns(2)
                with col1:
                    st.write("**Basic Info**")
                    for k, v in [('Name', user['name']), ('Role', user['role'].title()), ('Flat', user['flat_number']), ('Email', user['email']), ('Phone', user['phone']), ('Username', user['username'])]:
                        st.write(f"{k}: {v}")
                with col2:
                    st.write("**Account Info**")
                    st.write(f"Created: {format_datetime(user['created_at'])}")
                    st.write(f"Last Login: {format_datetime(user['last_login'])}")
                    st.write(f"Password Changed: {'Yes' if user['password_changed'] else 'No'}")
                    if not user['password_changed']:
                        st.write(f"Initial Password: `{user['initial_password']}`")
                
                if user['role'] == 'owner':
                    cursor.execute("SELECT * FROM owners WHERE user_id = %s", (user_id,))
                    owner_data = cursor.fetchone()
                    if owner_data:
                        st.write(f"**Owner Info** - Start: {format_date(owner_data[3])}, Emergency: {owner_data[4]}")
                elif user['role'] == 'tenant':
                    cursor.execute("SELECT * FROM tenants WHERE user_id = %s", (user_id,))
                    tenant_data = cursor.fetchone()
                    if tenant_data:
                        st.write(f"**Tenant Info** - Rent: {format_currency(tenant_data[3])}, Lease: {format_date(tenant_data[4])} to {format_date(tenant_data[5])}, Deposit: {format_currency(tenant_data[6])}")
        
        cursor.close()
    
    def billing_management(self):
        """Billing management interface"""
        st.title("💰 Billing Management")
        
        # Check for session state tab selection
        default_tab_index = 0
        if hasattr(st.session_state, 'bill_tab') and st.session_state.bill_tab:
            tab_mapping = {"Create Bills": 0, "View Bills": 1, "Payment Tracking": 2}
            default_tab_index = tab_mapping.get(st.session_state.bill_tab, 0)
            st.session_state.bill_tab = None
        
        tab1, tab2, tab3 = st.tabs(["Create Bills", "View Bills", "Payment Tracking"])
        
        with tab1:
            self.create_bill_form()
        with tab2:
            self.view_bills()
        with tab3:
            self.payment_tracking()
    
    def create_bill_form(self):
        """Create new bill form"""
        st.subheader("📄 Create New Bill")
        
        # Add option to choose between single or bulk bill generation
        bill_mode = st.radio(
            "Select Bill Creation Mode",
            ["Single Flat", "All Flats (Bulk)"],
            horizontal=True,
            key="bill_creation_mode"
        )
        
        if bill_mode == "Single Flat":
            # Original single flat bill creation
            with st.form("create_bill_form"):
                col1, col2 = st.columns(2)
                
                with col1:
                    # Enhanced flat selection with occupant information
                    flat_options = get_flat_display_options()
                    if flat_options:
                        selected_flat_display = st.selectbox(
                            "Billing Flat (with resident info)", 
                            options=list(flat_options.keys()),
                            key="bill_flat_select",
                            help="Select the flat to bill. Shows current residents and their roles."
                        )
                        flat_number = flat_options[selected_flat_display]
                        
                        # Show selected flat info
                        st.info(f"💰 Billing: **{flat_number}**")
                    else:
                        st.error("No occupied flats found. Please ensure residents are assigned to flats.")
                        flat_number = st.selectbox("Flat Number", get_allotted_flat_numbers(), key="bill_flat_fallback")
                    
                    bill_type = st.selectbox("Bill Type", [
                        "Maintenance",
                        "Electricity",
                        "Water",
                        "Parking",
                        "Security",
                        "Other"
                    ], key="bill_type_select")
                    amount = st.number_input("Amount", min_value=0.0, value=0.0, key="bill_amount_input")
                
                with col2:
                    due_date = st.date_input("Due Date", value=date.today() + timedelta(days=30), key="bill_due_date")
                    description = st.text_area("Description (Optional)", key="bill_description")
                
                submit = st.form_submit_button("Create Bill", key="create_bill_submit")
                
                if submit:
                    if amount <= 0:
                        st.error("Amount must be greater than 0")
                    else:
                        try:
                            cursor = self.db.connection.cursor()
                            cursor.execute("""
                                INSERT INTO bills (flat_number, bill_type, amount, due_date, created_by)
                                VALUES (%s, %s, %s, %s, %s)
                                RETURNING bill_id
                            """, (flat_number, bill_type, amount, due_date, st.session_state.user['user_id']))
                            
                            bill_id = cursor.fetchone()[0]
                            cursor.close()
                            
                            st.success(f"✅ Bill created successfully! Bill ID: {bill_id}")
                            
                        except Exception as e:
                            st.error(f"❌ Error creating bill: {e}")
        
        else:
            # Bulk bill generation for all flats or users
            bill_target = st.radio(
                "Generate Bills For:",
                ["All Flats (40 bills)", "All Residents (78 bills)"],
                horizontal=True,
                help="Flats: One bill per flat (shared by owner & tenant). Residents: One bill per person.",
                key="bill_target_select"
            )
            
            with st.form("bulk_bill_form"):
                col1, col2 = st.columns(2)
                
                with col1:
                    bill_type = st.selectbox("Bill Type", [
                        "Maintenance",
                        "Electricity",
                        "Water",
                        "Parking",
                        "Security",
                        "Other"
                    ], key="bulk_bill_type_select")
                    amount = st.number_input("Amount (Same for All)", min_value=0.0, value=0.0, key="bulk_amount_input")
                
                with col2:
                    due_date = st.date_input("Due Date", value=date.today() + timedelta(days=30), key="bulk_due_date")
                    description = st.text_area("Description (Optional)", key="bulk_description")
                
                if st.form_submit_button("🚀 Generate Bills"):
                    if amount <= 0:
                        st.error("Amount must be greater than 0")
                    else:
                        cursor = self.db.connection.cursor()
                        if "All Flats" in bill_target:
                            cursor.execute("SELECT DISTINCT flat_number FROM owners ORDER BY flat_number")
                        else:
                            cursor.execute("SELECT DISTINCT flat_number FROM users WHERE flat_number IS NOT NULL AND role IN ('owner', 'tenant')")
                        targets = cursor.fetchall()
                        
                        for t in targets:
                            cursor.execute("INSERT INTO bills (flat_number, bill_type, amount, due_date, created_by) VALUES (%s, %s, %s, %s, %s)",
                                         (t[0], bill_type, amount, due_date, st.session_state.user['user_id']))
                        cursor.close()
                        st.success(f"✅ Generated {len(targets)} bills!")
    
    def view_bills(self):
        st.subheader("📋 All Bills")
        col1, col2, col3 = st.columns(3)
        with col1:
            default_status = st.session_state.get('bill_filter', 'all')
            st.session_state.bill_filter = None
            # make sure default_status is valid
            if default_status not in ["all", "pending", "paid", "overdue"]:
                default_status = "all"
            status_filter = st.selectbox("Filter by Status", ["all", "pending", "paid", "overdue"], 
                                       index=["all", "pending", "paid", "overdue"].index(default_status), key="bill_status_filter")
        with col2:
            bill_type_filter = st.selectbox("Filter by Type", ["all", "Maintenance", "Electricity", "Water", "Parking", "Security", "Other"], key="bill_type_filter")
        with col3:
            flat_filter = st.text_input("Filter by Flat Number", key="bill_flat_filter")
        
        # Get bills - Simple query
        cursor = self.db.connection.cursor()
        cursor.execute("SELECT * FROM bills ORDER BY created_at DESC")
        bills_data = cursor.fetchall()
        cursor.close()
        
        # Convert to list and apply filters
        bills = []
        for b in bills_data:
            # Apply filters
            if status_filter != "all" and b[5] != status_filter:
                continue
            if bill_type_filter != "all" and b[2] != bill_type_filter:
                continue
            if flat_filter and flat_filter not in b[1]:
                continue
            
            bills.append({
                'bill_id': b[0],
                'flat_number': b[1],
                'bill_type': b[2],
                'amount': b[3],
                'due_date': b[4],
                'payment_status': b[5],
                'created_by': b[6] if len(b) > 6 else None,
                'created_at': b[7] if len(b) > 7 else None,
                'paid_at': b[8] if len(b) > 8 else None,
                'payment_date': b[8] if len(b) > 8 else None,
                'payment_method': b[9] if len(b) > 9 else None,
                'resident_name': 'Resident',
                'resident_type': 'User'
            })
        
        # Check for and remove duplicates
        unique_bills = []
        seen_bill_ids = set()
        for bill in bills:
            if bill['bill_id'] not in seen_bill_ids:
                unique_bills.append(bill)
                seen_bill_ids.add(bill['bill_id'])
        
        if len(bills) != len(unique_bills):
            st.warning(f"Filtered out {len(bills) - len(unique_bills)} duplicate bills")
            bills = unique_bills
        
        if bills and len(bills) > 0:
            st.write(f"**Found {len(bills)} bills**")
            
            # Display bills with detailed information
            for i, bill in enumerate(bills):
                status_color = "🟡" if bill['payment_status'] == 'pending' else ("🟢" if bill['payment_status'] == 'paid' else "🔴")
                resident_info = f"{bill['resident_name']} ({bill['resident_type'].title()})" if bill['resident_name'] else "No Resident"
                
                with st.expander(f"{status_color} #{bill['bill_id']} - {bill['bill_type']} - {format_currency(bill['amount'])} - Flat {bill['flat_number']}"):
                    col1, col2 = st.columns([2, 1])
                    
                    with col1:
                        st.write(f"**Resident:** {resident_info}")
                        st.write(f"**Flat Number:** {bill['flat_number']}")
                        st.write(f"**Bill Type:** {bill['bill_type']}")
                        st.write(f"**Amount:** {format_currency(bill['amount'])}")
                        st.write(f"**Due Date:** {format_date(bill['due_date'])}")
                        st.write(f"**Created:** {format_datetime(bill['created_at'])}")
                        
                        if bill['payment_date']:
                            st.write(f"**Payment Date:** {format_date(bill['payment_date'])}")
                            st.write(f"**Payment Method:** {bill['payment_method']}")
                    
                    with col2:
                        st.write(f"**Status:** {bill['payment_status'].title()}")
                        
                        if bill['payment_status'] == 'pending':
                            st.warning("⏳ Payment Pending")
                        elif bill['payment_status'] == 'overdue':
                            st.error("🚨 Overdue!")
                        else:
                            st.success("✅ Paid")
                        
                        # Admin actions for pending bills
                        if bill['payment_status'] in ['pending', 'overdue']:
                            # Create a truly unique key
                            unique_key = generate_unique_key("mark_paid", bill, i)
                            
                            if st.button("Mark as Paid", key=unique_key):
                                try:
                                    cursor = self.db.connection.cursor()
                                    cursor.execute("""
                                        UPDATE bills 
                                        SET payment_status = 'paid', payment_date = CURRENT_DATE, 
                                            payment_method = 'Admin Override'
                                        WHERE bill_id = %s
                                    """, (bill['bill_id'],))
                                    cursor.close()
                                    st.success("Bill marked as paid!")
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"Error: {e}")

                        # Admin delete bill option (available for any bill)
                        st.markdown("---")
                        st.write("**Delete Bill:**")
                        
                        col_del1, col_del2 = st.columns([1, 3])
                        with col_del1:
                            if st.button("🗑️ Delete", key=f"delete_bill_{bill['bill_id']}", type="secondary"):
                                try:
                                    self.db.delete_bill(bill['bill_id'])
                                    st.success("✅ Bill deleted successfully")
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"❌ Error deleting bill: {e}")

        else:
            st.info("No bills found with the selected filters")
    
    def payment_tracking(self):
        """Payment tracking and analytics"""
        st.subheader("📊 Payment Analytics")
        
        cursor = self.db.connection.cursor()
        
        # Payment statistics - using simple queries
        cursor.execute("SELECT COUNT(*) FROM bills")
        total_bills = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM bills WHERE payment_status = 'paid'")
        paid_bills = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM bills WHERE payment_status = 'pending'")
        pending_bills = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM bills WHERE payment_status = 'overdue'")
        overdue_bills = cursor.fetchone()[0]
        
        cursor.execute("SELECT SUM(amount) FROM bills")
        total_amount = cursor.fetchone()[0] or 0
        
        cursor.execute("SELECT SUM(amount) FROM bills WHERE payment_status = 'paid'")
        collected_amount = cursor.fetchone()[0] or 0
        
        stats = {
            'total_bills': total_bills,
            'paid_bills': paid_bills,
            'pending_bills': pending_bills,
            'overdue_bills': overdue_bills,
            'total_amount': total_amount,
            'collected_amount': collected_amount
        }
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Bills", stats['total_bills'] or 0)
            st.metric("Paid Bills", stats['paid_bills'] or 0)
        
        with col2:
            st.metric("Pending Bills", stats['pending_bills'] or 0)
            st.metric("Overdue Bills", stats['overdue_bills'] or 0)
        
        with col3:
            st.metric("Total Amount", format_currency(stats['total_amount'] or 0))
        
        with col4:
            st.metric("Collected Amount", format_currency(stats['collected_amount'] or 0))
            collection_rate = (stats['collected_amount'] or 0) / (stats['total_amount'] or 1) * 100
            st.metric("Collection Rate", f"{collection_rate:.1f}%")
        
        cursor.close()
    
    def complaint_management(self):
        """Complaint management interface"""
        st.title("📝 Complaint Management")
        
        tab1, tab2 = st.tabs(["All Complaints", "Complaint Analytics"])
        
        with tab1:
            self.view_all_complaints()
        with tab2:
            self.complaint_analytics()
    
    def view_all_complaints(self):
        """View and manage all complaints"""
        st.subheader("📋 All Complaints")
        
        # Filter options
        col1, col2, col3 = st.columns(3)
        with col1:
            # Check for session state filter
            default_status = "all"
            if hasattr(st.session_state, 'complaint_filter') and st.session_state.complaint_filter:
                default_status = st.session_state.complaint_filter
                st.session_state.complaint_filter = None
            # make sure default_status is valid
            if default_status not in ["all", "open", "in_progress", "resolved", "closed"]:
                default_status = "all"
            status_filter = st.selectbox("Filter by Status", ["all", "open", "in_progress", "resolved", "closed"],
                                       index=["all", "open", "in_progress", "resolved", "closed"].index(default_status), key="complaint_status_filter")
        with col2:
            priority_filter = st.selectbox("Filter by Priority", ["all", "low", "medium", "high", "urgent"], key="complaint_priority_filter")
        with col3:
            flat_filter = st.text_input("Filter by Flat", key="complaint_flat_filter")
        
        # Get complaints - Simple query
        cursor = self.db.connection.cursor()
        cursor.execute("SELECT * FROM complaints ORDER BY created_at DESC")
        complaints_data = cursor.fetchall()
        
        # Convert to list and apply filters
        complaints = []
        for c in complaints_data:
            # Apply filters
            if status_filter != "all" and c[7] != status_filter:
                continue
            if priority_filter != "all" and c[6] != priority_filter:
                continue
            if flat_filter and flat_filter not in c[2]:
                continue
            
            complaints.append({
                'complaint_id': c[0],
                'user_id': c[1],
                'flat_number': c[2],
                'title': c[3],
                'description': c[4],
                'category': c[5],
                'priority': c[6],
                'status': c[7],
                'created_at': c[8],
                'resolved_at': c[9] if len(c) > 9 else None,
                'admin_response': c[10] if len(c) > 10 else None,
                'updated_at': c[8],
                'user_name': 'User'
            })
        
        if complaints and len(complaints) > 0:
            for complaint in complaints:
                with st.expander(f"#{complaint['complaint_id']} - {complaint['title']} ({complaint['priority'].upper()})"):
                    col1, col2 = st.columns([2, 1])
                    
                    with col1:
                        st.write(f"**Complainant:** {complaint['user_name']}")
                        st.write(f"**Flat:** {complaint['flat_number']}")
                        st.write(f"**Category:** {complaint['category']}")
                        st.write(f"**Description:** {complaint['description']}")
                        if complaint['admin_response']:
                            st.write(f"**Admin Response:** {complaint['admin_response']}")
                    
                    with col2:
                        st.write(f"**Status:** {complaint['status'].title()}")
                        st.write(f"**Priority:** {complaint['priority'].title()}")
                        st.write(f"**Created:** {format_datetime(complaint['created_at'])}")
                        if complaint['resolved_at']:
                            st.write(f"**Resolved:** {format_datetime(complaint['resolved_at'])}")
                    
                    # make sure complaint status is valid
                    current_status = complaint['status'] if complaint['status'] in ["open", "in_progress", "resolved", "closed"] else "open"
                    new_status = st.selectbox("Update Status", ["open", "in_progress", "resolved", "closed"],
                                            index=["open", "in_progress", "resolved", "closed"].index(current_status),
                                            key=f"st_{complaint['complaint_id']}")
                    if st.button("Update", key=f"upd_{complaint['complaint_id']}"):
                        cursor.execute("UPDATE complaints SET status = %s WHERE complaint_id = %s", (new_status, complaint['complaint_id']))
                        st.success("Updated!")
                        st.rerun()
                    
                    response = st.text_area("Response", value=complaint['admin_response'] or "", key=f"resp_{complaint['complaint_id']}")
                    if st.button("Save", key=f"sav_{complaint['complaint_id']}"):
                        cursor.execute("UPDATE complaints SET admin_response = %s WHERE complaint_id = %s", (response, complaint['complaint_id']))
                        st.success("Saved!")
                        st.rerun()
                    
                    if st.button("🗑️ Delete", key=f"del_{complaint['complaint_id']}"):
                        self.db.delete_complaint(complaint['complaint_id'])
                        st.rerun()
        else:
            st.info("No complaints found")
        
        cursor.close()
    
    def complaint_analytics(self):
        st.subheader("📊 Complaint Analytics")
        cursor = self.db.connection.cursor()
        
        cursor.execute("SELECT status, COUNT(*) FROM complaints GROUP BY status")
        status_stats = [{'status': r[0], 'count': r[1]} for r in cursor.fetchall()]
        
        cursor.execute("SELECT priority, COUNT(*) FROM complaints GROUP BY priority")
        priority_stats = [{'priority': r[0], 'count': r[1]} for r in cursor.fetchall()]
        
        col1, col2 = st.columns(2)
        if status_stats:
            fig = create_pie_chart(status_stats, 'status', 'count', "By Status")
            if fig:
                col1.plotly_chart(fig, width='stretch')
        if priority_stats:
            fig = create_bar_chart(priority_stats, 'priority', 'count', "By Priority")
            if fig:
                col2.plotly_chart(fig, width='stretch')
        cursor.close()
    
    def visitor_management(self):
        """Visitor management interface"""
        st.title("🚶 Visitor Management")
        
        tab1, tab2, tab3 = st.tabs(["Log Visitor", "Current Visitors", "Visitor History"])
        
        with tab1:
            self.log_visitor_form()
        with tab2:
            self.current_visitors()
        with tab3:
            self.visitor_history()
    
    def log_visitor_form(self):
        """Log new visitor form"""
        st.subheader("➕ Log New Visitor")
        
        # Pre-load flat options outside the form to avoid re-computation
        try:
            flat_options = get_flat_display_options()
            if flat_options:
                sorted_options = sorted(flat_options.keys())
            else:
                flat_options = {}
                sorted_options = []
        except Exception as e:
            st.error(f"Error loading flat options: {e}")
            flat_options = {}
            sorted_options = []
        
        with st.form("log_visitor_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                # Enhanced flat selection with occupant information
                st.markdown("**Select Visiting Flat:**")
                
                if flat_options and len(flat_options) > 0:
                    selected_flat_display = st.selectbox(
                        "Flat (with resident info)", 
                        options=sorted_options,
                        key="visitor_flat_select",
                        help="Select the flat to visit. Shows current residents and their roles."
                    )
                    
                    # Extract flat number directly from the selected display string
                    flat_number = selected_flat_display.split(' - ')[0] if ' - ' in selected_flat_display else selected_flat_display
                    
                    # All detailed breakdown code has been removed to fix display issues
                    # with st.container():
                        # Removed detailed breakdown to fix display bug
                        
                        # Extract and display residents properly
                        # if " - 🏠 Owner: " in selected_flat_display:
                            # residents_part = selected_flat_display.split(" - 🏠 Owner: ")[1]
                            # st.write(f"👥 **Residents:** {residents_part}")
                        # elif " - 🏘️ Tenant: " in selected_flat_display:
                            # residents_part = selected_flat_display.split(" - 🏘️ Tenant: ")[1]
                            # if " (Owner: " in residents_part:
                                # owner_part = residents_part.split(" (Owner: ")[1].replace(")", "")
                                # residents_part = residents_part.split(" (Owner: ")[0]
                                # st.write(f"👥 **Current Residents:** {residents_part}")
                                # st.write(f"� **Property Owner:** {owner_part}")
                            # else:
                            # st.write(f"👥 **Residents:** {residents_part}")
                            # st.markdown("---")
                    
                else:
                    st.warning("⚠️ Enhanced flat selection not available. Using basic selection.")
                    flat_number = st.selectbox(
                        "Visiting Flat (Basic)", 
                        get_allotted_flat_numbers(), 
                        key="visitor_flat_fallback"
                    )
                
                visitor_name = st.text_input("Visitor Name", key="visitor_name_input")
                visitor_phone = st.text_input("Visitor Phone", key="visitor_phone_input")
            
            with col2:
                purpose = st.text_input("Purpose of Visit", key="visitor_purpose_input")
                vehicle_number = st.text_input("Vehicle Number (Optional)", key="visitor_vehicle_input")
            
            # Photo upload section
            st.markdown("---")
            st.subheader("📸 Visitor Photo (Optional)")
            
            # Create tabs for different photo input methods
            photo_tab1, photo_tab2 = st.tabs(["📁 Upload Photo", "📷 Take Photo"])
            
            uploaded_photo = None
            camera_photo = None
            
            with photo_tab1:
                st.markdown("### 📁 File Upload Instructions:")
                st.info("📋 **Supported formats:** PNG, JPG, JPEG\n📏 **Recommended:** Clear, well-lit photos for security purposes")
                
                uploaded_photo = st.file_uploader(
                    "📁 Choose visitor photo file", 
                    type=['png', 'jpg', 'jpeg'],
                    key="visitor_photo_upload",
                    help="Upload a photo of the visitor for security purposes"
                )
                
                # Enhanced feedback when photo is uploaded
                if uploaded_photo is not None:
                    st.success("✅ **Photo Uploaded Successfully!**")
                    col1, col2 = st.columns([1, 2])
                    with col1:
                        st.image(uploaded_photo, caption="📁 Uploaded Photo", width=150)
                    with col2:
                        st.markdown("**📋 File Details:**")
                        st.write(f"✓ Filename: {uploaded_photo.name}")
                        st.write(f"✓ Size: {uploaded_photo.size} bytes")
                        st.write(f"✓ Type: {uploaded_photo.type}")
                        st.write(f"✓ Status: ✅ Ready for upload")
                        st.markdown("**This photo will be saved when you submit the form**")
                else:
                    st.info("📁 File uploader ready. Choose a photo file using the button above.")
            
            with photo_tab2:
                st.markdown("### 📷 Camera Instructions:")
                st.info("🎯 **How to capture photo:**\n1. Click the camera icon below to open camera\n2. Position the visitor in frame\n3. Click the **'Take Photo'** button when ready\n4. The photo will be automatically captured and preview will appear")
                
                camera_photo = st.camera_input(
                    "📸 Click to open camera and take photo",
                    key="visitor_camera_input",
                    help="This opens your device camera. Click 'Take Photo' button to capture the image."
                )
                
                # Enhanced feedback when photo is captured
                if camera_photo is not None:
                    st.success("✅ **Photo Captured Successfully!**")
                    col1, col2 = st.columns([1, 2])
                    with col1:
                        st.image(camera_photo, caption="📷 Captured Photo", width=150)
                    with col2:
                        st.markdown("**📋 Photo Details:**")
                        st.write(f"✓ Source: Camera capture")
                        st.write(f"✓ Status: ✅ Ready for upload")
                        st.write(f"✓ Size: {len(camera_photo.getvalue())} bytes")
                        st.markdown("**This photo will be saved when you submit the form**")
                else:
                    st.info("📸 Camera ready. Click the camera icon above to take a photo.")
            
            submit = st.form_submit_button("Log Visitor", key="log_visitor_submit")
            
            if submit:
                if visitor_name and flat_number:
                    try:
                        # Process photo if uploaded or captured
                        visitor_photo_data = None
                        photo_source = None
                        
                        if uploaded_photo is not None:
                            import base64
                            # Convert uploaded photo to base64 string for storage
                            visitor_photo_data = base64.b64encode(uploaded_photo.read()).decode()
                            photo_source = "uploaded"
                        elif camera_photo is not None:
                            import base64
                            # Convert camera photo to base64 string for storage
                            visitor_photo_data = base64.b64encode(camera_photo.read()).decode()
                            photo_source = "camera"
                        
                        # Use the new database function with photo support
                        visitor_id = self.db.log_visitor_with_photo(
                            flat_number=flat_number,
                            visitor_name=visitor_name,
                            visitor_phone=visitor_phone,
                            purpose=purpose,
                            vehicle_number=vehicle_number,
                            logged_by=st.session_state.user['user_id'],
                            visitor_photo=visitor_photo_data
                        )
                        
                        success_msg = f"✅ Visitor logged successfully! (ID: {visitor_id})"
                        if visitor_photo_data:
                            if photo_source == "uploaded":
                                success_msg += " � Photo uploaded."
                            elif photo_source == "camera":
                                success_msg += " 📷 Photo captured."
                        success_msg += f" 🔔 Notification sent to Flat {flat_number} residents."
                        st.success(success_msg)
                        st.info(f"The residents of Flat {flat_number} have been notified about the visitor.")
                        
                    except Exception as e:
                        st.error(f"Error logging visitor: {e}")
                else:
                    st.error("Please enter visitor name and select flat number")
    
    def current_visitors(self):
        """View current visitors"""
        st.subheader("👥 Current Visitors")
        
        cursor = self.db.connection.cursor()
        # Simple query for visitors who are currently 'in'
        cursor.execute("""
            SELECT * FROM visitors
            WHERE status = 'in'
            ORDER BY entry_time DESC
        """)
        visitors_data = cursor.fetchall()
        
        # Get flat owner names separately
        current_visitors = []
        for v in visitors_data:
            cursor.execute("SELECT name FROM users WHERE flat_number = %s AND role IN ('owner', 'tenant') LIMIT 1", (v[1],))
            owner_name_result = cursor.fetchone()
            current_visitors.append({
                'visitor_id': v[0],
                'flat_number': v[1],
                'visitor_name': v[2],
                'visitor_phone': v[3],
                'purpose': v[4],
                'entry_time': v[5],
                'exit_time': v[6],
                'vehicle_number': v[7],
                'logged_by': v[8],
                'status': v[9],
                'visitor_photo': v[10] if len(v) > 10 else None,
                'flat_owner_name': owner_name_result[0] if owner_name_result else None
            })
        
        if current_visitors and len(current_visitors) > 0:
            for idx, visitor in enumerate(current_visitors):
                # Create a more informative title showing both visitor and flat info
                flat_info = f"Visiting Flat {visitor['flat_number']}"
                if visitor['flat_owner_name']:
                    flat_info += f" ({visitor['flat_owner_name']})"
                
                with st.expander(f"🟢 {visitor['visitor_name']} - {flat_info}"):
                    col1, col2, col3 = st.columns([2, 1, 1])
                    
                    with col1:
                        st.write(f"**Visitor Name:** {visitor['visitor_name']}")
                        st.write(f"**📍 Visiting Flat:** {visitor['flat_number']}")
                        if visitor['flat_owner_name']:
                            st.write(f"**🏠 Flat Resident:** {visitor['flat_owner_name']}")
                        st.write(f"**📞 Phone:** {visitor['visitor_phone']}")
                        st.write(f"**🎯 Purpose:** {visitor['purpose']}")
                        st.write(f"**🚗 Vehicle:** {visitor['vehicle_number']}")
                        st.write(f"**⏰ Entry Time:** {format_datetime(visitor['entry_time'])}")
                    
                    with col2:
                        # Display visitor photo if available
                        if visitor.get('visitor_photo'):
                            try:
                                import base64
                                import io
                                from PIL import Image
                                
                                # Decode base64 photo
                                photo_bytes = base64.b64decode(visitor['visitor_photo'])
                                photo_image = Image.open(io.BytesIO(photo_bytes))
                                
                                st.image(photo_image, caption="Visitor Photo", width=150)
                            except Exception as e:
                                st.write("📷 Photo available (Error displaying)")
                        else:
                            st.write("📷 No photo")
                    
                    with col3:
                        # Use index + visitor_id + entry_time hash for guaranteed unique keys
                        unique_key = f"current_{idx}_{visitor['visitor_id']}_{hash(str(visitor['entry_time']))}"
                        if st.button("Mark Exit", key=f"exit_{unique_key}"):
                            cursor.execute("""
                                UPDATE visitors 
                                SET status = 'out', exit_time = CURRENT_TIMESTAMP
                                WHERE visitor_id = %s
                            """, (visitor['visitor_id'],))
                            st.success("Visitor marked as exited!")
                            st.rerun()
                        # Delete visitor
                        if st.button("🗑️ Delete Visitor", key=f"delete_{unique_key}", type="secondary"):
                            try:
                                self.db.delete_visitor(visitor['visitor_id'])
                                st.success("Visitor record deleted")
                                st.rerun()
                            except Exception as e:
                                st.error(f"Error deleting visitor: {e}")
        else:
            st.info("No current visitors")
        
        cursor.close()

    def visitor_history(self):
        """View visitor history"""
        st.subheader("📜 Visitor History")
        
        # Filter options
        col1, col2, col3 = st.columns(3)
        with col1:
            flat_filter = st.selectbox("Filter by Flat", ["All Flats"] + get_allotted_flat_numbers(), key="visitor_history_flat_filter")
        with col2:
            date_filter = st.date_input("Filter by Date", value=None, key="visitor_history_date_filter")
        with col3:
            status_filter = st.selectbox("Filter by Status", ["All", "in", "out"], key="visitor_history_status_filter")
        
        cursor = self.db.connection.cursor()
        
        query = "SELECT * FROM visitors WHERE 1=1"
        params = []
        
        # Handle flat filter
        if flat_filter and flat_filter.strip() and flat_filter != "All Flats":
            query += " AND flat_number = %s"
            params.append(flat_filter.strip())
        
        # Handle status filter
        if status_filter and status_filter != "All":
            query += " AND status = %s"
            params.append(status_filter)
        
        # Handle date filter - more robust version
        try:
            if (date_filter is not None and 
                hasattr(date_filter, 'strftime') and  # Check if it's a date-like object
                not pd.isnull(date_filter)):  # Check if it's not a pandas null
                
                query += " AND DATE(entry_time) = %s"
                params.append(date_filter)
        except (AttributeError, TypeError):
            # If date_filter is not a proper date object, skip the filter
            pass
        
        query += " ORDER BY entry_time DESC LIMIT 100"
        
        try:
            cursor.execute(query, params)
            visitors_data = cursor.fetchall()
            
            # Convert to dictionary format
            visitors = []
            for v in visitors_data:
                # Get flat owner name
                cursor.execute("SELECT name FROM users WHERE flat_number = %s AND role IN ('owner', 'tenant') LIMIT 1", (v[1],))
                owner_name_result = cursor.fetchone()
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
                    'flat_owner_name': owner_name_result[0] if owner_name_result else None
                })
            
            if visitors and len(visitors) > 0:
                st.write(f"Found {len(visitors)} visitor records")
                
                for idx, visitor in enumerate(visitors):
                    status_icon = "🟢" if visitor['status'] == 'out' else "🔴"
                    
                    # Create a more informative title showing both visitor and flat info
                    flat_info = f"Visiting Flat {visitor['flat_number']}"
                    if visitor['flat_owner_name']:
                        flat_info += f" ({visitor['flat_owner_name']})"
                    
                    with st.expander(f"{status_icon} {visitor['visitor_name']} - {flat_info} ({format_datetime(visitor['entry_time'])})"):
                        col1, col2, col3 = st.columns([2, 1, 1])
                        
                        with col1:
                            st.write(f"**Visitor Name:** {visitor['visitor_name']}")
                            st.write(f"**📍 Visiting Flat:** {visitor['flat_number']}")
                            if visitor['flat_owner_name']:
                                st.write(f"**🏠 Flat Resident:** {visitor['flat_owner_name']}")
                            if visitor['visitor_phone']:
                                st.write(f"**📞 Phone:** {visitor['visitor_phone']}")
                            if visitor['purpose']:
                                st.write(f"**🎯 Purpose:** {visitor['purpose']}")
                            if visitor['vehicle_number']:
                                st.write(f"**🚗 Vehicle:** {visitor['vehicle_number']}")
                            st.write(f"**⏰ Entry Time:** {format_datetime(visitor['entry_time'])}")
                            if visitor['exit_time']:
                                st.write(f"**🚪 Exit Time:** {format_datetime(visitor['exit_time'])}")
                            st.write(f"**📊 Status:** {visitor['status'].title()}")
                        
                        with col2:
                            # Display visitor photo if available
                            if visitor.get('visitor_photo'):
                                try:
                                    import base64
                                    import io
                                    from PIL import Image
                                    
                                    # Decode base64 photo
                                    photo_bytes = base64.b64decode(visitor['visitor_photo'])
                                    photo_image = Image.open(io.BytesIO(photo_bytes))
                                    
                                    st.image(photo_image, caption="Visitor Photo", width=150)
                                except Exception as e:
                                    st.write("📷 Photo available (Error displaying)")
                            else:
                                st.write("📷 No photo")
                        
                        with col3:
                            # Action buttons for visitor records
                            # Use index + visitor_id + entry_time hash for guaranteed unique keys
                            unique_key = f"history_{idx}_{visitor['visitor_id']}_{hash(str(visitor['entry_time']))}"
                            if visitor['status'] == 'in':
                                if st.button("Mark Exit", key=f"exit_{unique_key}"):
                                    cursor = self.db.connection.cursor()
                                    cursor.execute("""
                                        UPDATE visitors 
                                        SET status = 'out', exit_time = CURRENT_TIMESTAMP
                                        WHERE visitor_id = %s
                                    """, (visitor['visitor_id'],))
                                    cursor.close()
                                    st.success("Visitor marked as exited!")
                                    st.rerun()
                            
                            # Delete visitor record
                            if st.button("🗑️ Delete Record", key=f"delete_{unique_key}", type="secondary"):
                                try:
                                    self.db.delete_visitor(visitor['visitor_id'])
                                    st.success("Visitor record deleted")
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"Error deleting visitor: {e}")
            else:
                st.info("No visitor records found")
        
        except Exception as e:
            st.error(f"Error fetching visitor history: {e}")
        
        finally:
            cursor.close()
    

    
    def notification_management(self):
        """Notification management interface"""
        st.title("📢 Notification Management")
        
        tab1, tab2 = st.tabs(["Send Notification", "Notification History"])
        
        with tab1:
            self.send_notification_form()
        with tab2:
            self.notification_history()
    
    def send_notification_form(self):
        """Send notification form"""
        st.subheader("📤 Send New Notification")
        
        with st.form("send_notification_form"):
            title = st.text_input("Notification Title", key="notification_title_input")
            message = st.text_area("Message", height=150, key="notification_message_input")
            priority = st.selectbox("Priority", ["low", "normal", "high"], key="notification_priority_select")
            
            submit = st.form_submit_button("Send Notification", key="send_notification_submit")
            
            if submit:
                if title and message:
                    try:
                        cursor = self.db.connection.cursor()
                        cursor.execute("""
                                                        INSERT INTO notifications (title, message, created_by, priority)
                            VALUES (%s, %s, %s, %s)
                            RETURNING notification_id
                        """, (title, message, st.session_state.user['user_id'], priority))
                        
                        notification_id = cursor.fetchone()[0]
                        cursor.close()
                        
                        st.success(f"Notification sent successfully! Notification ID: {notification_id}")
                        
                    except Exception as e:
                        st.error(f"Error sending notification: {e}")
                else:
                    st.error("Please enter title and message")
    
    def notification_history(self):
        """View notification history"""
        st.subheader("📜 Notification History")
        
        cursor = self.db.connection.cursor()
        cursor.execute("SELECT * FROM notifications ORDER BY created_at DESC")
        notifications_data = cursor.fetchall()
        
        # Convert to list
        notifications = []
        for n in notifications_data:
            # get read count from notification_reads table
            cursor.execute("SELECT COUNT(*) FROM notification_reads WHERE notification_id = %s", (n[0],))
            read_count_result = cursor.fetchone()
            read_count = read_count_result[0] if read_count_result else 0
            
            notifications.append({
                'notification_id': n[0],
                'title': n[1],
                'message': n[2],
                'created_by': n[3],
                'created_at': n[4],
                'type': n[5] if len(n) > 5 else 'general',
                'priority': n[6] if len(n) > 6 else 'normal',
                'created_by_name': 'Admin',
                'read_count': read_count
            })
        
        if notifications and len(notifications) > 0:
            for notification in notifications:
                with st.expander(f"{notification['title']} - {format_datetime(notification['created_at'])}"):
                    st.write(f"**Message:** {notification['message']}")
                    st.write(f"**Priority:** {notification['priority'].title()}")
                    st.write(f"**Created by:** {notification['created_by_name']}")
                    st.write(f"**Read by:** {notification['read_count']} users")
                    col1, col2 = st.columns([3,1])
                    with col2:
                        if st.button("🗑️ Delete", key=f"delete_notification_{notification['notification_id']}", type="secondary"):
                            try:
                                self.db.delete_notification(notification['notification_id'])
                                st.success("Notification deleted")
                                st.rerun()
                            except Exception as e:
                                st.error(f"Error deleting notification: {e}")
        else:
            st.info("No notifications found")
        
        cursor.close()
    
    def poll_management(self):
        """Poll management interface"""
        st.title("🗳️ Poll Management")
        
        tab1, tab2, tab3 = st.tabs(["Create Poll", "Active Polls", "Poll Results"])
        
        with tab1:
            self.create_poll_form()
        with tab2:
            self.active_polls()
        with tab3:
            self.poll_results()
    
    def create_poll_form(self):
        """Create poll form"""
        st.subheader("➕ Create New Poll")
        
        with st.form("create_poll_form"):
            title = st.text_input("Poll Title", key="poll_title_input")
            description = st.text_area("Poll Description", key="poll_description_input")
            end_date = st.date_input("End Date", value=date.today() + timedelta(days=7), key="poll_end_date")
            
            st.write("**Poll Options** (Enter each option on a new line)")
            options_text = st.text_area("Options", height=150, 
                                       placeholder="Option 1\nOption 2\nOption 3",
                                       key="poll_options_input")
            
            submit = st.form_submit_button("Create Poll", key="create_poll_submit")
            
            if submit:
                if title and options_text:
                    options = [opt.strip() for opt in options_text.split('\n') if opt.strip()]
                    
                    if len(options) >= 2:
                        try:
                            cursor = self.db.connection.cursor()
                            
                            # Create poll
                            cursor.execute("""
                                INSERT INTO polls (title, description, created_by, end_date)
                                VALUES (%s, %s, %s, %s)
                                RETURNING poll_id
                            """, (title, description, st.session_state.user['user_id'], end_date))
                            
                            poll_id = cursor.fetchone()[0]
                            
                            # Create poll options
                            for option in options:
                                cursor.execute("""
                                    INSERT INTO poll_options (poll_id, option_text)
                                    VALUES (%s, %s)
                                """, (poll_id, option))
                            
                            cursor.close()
                            
                            st.success(f"Poll created successfully! Poll ID: {poll_id}")
                            
                        except Exception as e:
                            st.error(f"Error creating poll: {e}")
                    else:
                        st.error("Please provide at least 2 options")
                else:
                    st.error("Please enter poll title and options")
    
    def active_polls(self):
        """View active polls"""
        st.subheader("🗳️ Active Polls")
        
        cursor = self.db.connection.cursor()
        cursor.execute("SELECT * FROM polls WHERE is_active = TRUE ORDER BY created_at DESC")
        polls_data = cursor.fetchall()
        
        # Convert to list
        polls = []
        for p in polls_data:
            polls.append({
                'poll_id': p[0],
                'title': p[1],
                'description': p[2],
                'created_by': p[3],
                'created_at': p[4],
                'end_date': p[5],
                'is_active': p[6] if len(p) > 6 else True,
                'status': 'active',
                'created_by_name': 'Admin'
            })
        
        if polls and len(polls) > 0:
            for poll in polls:
                with st.expander(f"{poll['title']} (Ends: {format_date(poll['end_date'])})"):
                    st.write(f"**Description:** {poll['description']}")
                    st.write(f"**Created by:** {poll['created_by_name']}")
                    st.write(f"**Created:** {format_datetime(poll['created_at'])}")
                    
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        if st.button("Close Poll", key=f"close_{poll['poll_id']}"):
                            cursor.execute("""
                                UPDATE polls SET status = 'closed' WHERE poll_id = %s
                            """, (poll['poll_id'],))
                            st.success("Poll closed!")
                            st.rerun()
                        if st.button("🗑️ Delete Poll", key=f"delete_poll_{poll['poll_id']}", type="secondary"):
                            try:
                                self.db.delete_poll(poll['poll_id'])
                                st.success("Poll deleted")
                                st.rerun()
                            except Exception as e:
                                st.error(f"Error deleting poll: {e}")
                    
                    with col2:
                        cursor.execute("SELECT COUNT(*) FROM votes WHERE poll_id = %s", (poll['poll_id'],))
                        vote_count = cursor.fetchone()[0]
                        st.write(f"**Total Votes:** {vote_count}")
        else:
            st.info("No active polls")
        
        cursor.close()
    
    def poll_results(self):
        """View poll results"""
        st.subheader("📊 Poll Results")
        
        cursor = self.db.connection.cursor()
        cursor.execute("SELECT * FROM polls ORDER BY created_at DESC")
        polls_data = cursor.fetchall()
        
        # Convert to list
        polls = []
        for p in polls_data:
            polls.append({
                'poll_id': p[0],
                'title': p[1],
                'description': p[2],
                'created_by': p[3],
                'created_at': p[4],
                'end_date': p[5],
                'is_active': p[6] if len(p) > 6 else True,
                'status': 'active' if (p[6] if len(p) > 6 else True) else 'closed'
            })
        
        # FIXED: Check length instead of truthiness
        if polls and len(polls) > 0:
            for poll in polls:
                st.write(f"### {poll['title']}")
                st.write(f"**Status:** {poll['status'].title()}")
                st.write(f"**End Date:** {format_date(poll['end_date'])}")
                
                cursor.execute("""
                    SELECT option_text, vote_count 
                    FROM poll_options 
                    WHERE poll_id = %s
                    ORDER BY vote_count DESC
                """, (poll['poll_id'],))
                
                results = cursor.fetchall()
                
                if results and len(results) > 0:
                    total_votes = sum(r[1] for r in results)
                    
                    col1, col2 = st.columns([1, 2])
                    
                    with col1:
                        st.write("**Results:**")
                        for i, r in enumerate(results):
                            percentage = (r[1] / total_votes * 100) if total_votes > 0 else 0
                            rank_emoji = ["🥇", "🥈", "🥉"][i] if i < 3 else "•"
                            st.write(f"{rank_emoji} {r[0]}: {r[1]} votes ({percentage:.1f}%)")
                        
                        st.write(f"**Total Votes:** {total_votes}")
                    
                    with col2:
                        if len(results) > 0 and total_votes > 0:
                            results_df = pd.DataFrame([{'option_text': r[0], 'vote_count': r[1]} for r in results])
                            fig = create_bar_chart(results_df, 'option_text', 'vote_count', f"Results: {poll['title']}")
                            if fig is not None:
                                st.plotly_chart(fig, use_container_width=True, theme="streamlit")
                else:
                    st.write("No votes yet")
                
                st.divider()
        else:
            st.info("No polls found")
        
        cursor.close()