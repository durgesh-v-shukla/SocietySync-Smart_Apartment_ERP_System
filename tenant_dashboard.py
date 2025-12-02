import streamlit as st
import pandas as pd
from datetime import datetime, date
from utils import (
    format_currency, format_date, format_datetime, create_data_table,
    get_status_color, create_notification_display, create_poll_display
)

class TenantDashboard:
    def __init__(self, db):
        self.db = db
    
    def show(self):
        user = st.session_state.user
        st.title("🔑 Vishwakarma Apartment")
        st.caption(f"📍 Pune | Tenant Dashboard | Welcome, {user['name']} | Flat: {user['flat_number']}")
        
        # Get tenant information
        tenant_info = self.get_tenant_info(user['user_id'])
        
        if tenant_info:
            # Display tenant-specific information
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("🏠 Rental Information")
                st.write(f"**Owner:** {tenant_info['owner_name']}")
                st.write(f"**Monthly Rent:** {format_currency(tenant_info['rent_amount'])}")
                st.write(f"**Security Deposit:** {format_currency(tenant_info['security_deposit'])}")
            
            with col2:
                st.subheader("📅 Lease Details")
                st.write(f"**Lease Start:** {format_date(tenant_info['lease_start_date'])}")
                st.write(f"**Lease End:** {format_date(tenant_info['lease_end_date'])}")
                
                # Calculate remaining lease days
                if tenant_info['lease_end_date']:
                    remaining_days = (tenant_info['lease_end_date'] - date.today()).days
                    if remaining_days > 0:
                        st.write(f"**Days Remaining:** {remaining_days}")
                    else:
                        st.error(f"**Lease Expired:** {abs(remaining_days)} days ago")
            
            st.divider()
        
        # Get tenant statistics (same as owner)
        stats = self.get_tenant_stats(user['flat_number'])
        
        # Display key metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Pending Bills", stats['pending_bills'])
        
        with col2:
            st.metric("Open Complaints", stats['open_complaints'])
        
        with col3:
            st.metric("Unread Notifications", stats['unread_notifications'])
        
        with col4:
            st.metric("Active Polls", stats['active_polls'])
        
        st.divider()
        
        # Recent activities in styled containers
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("💰 Recent Bills")
            recent_bills = self.get_recent_bills(user['flat_number'], limit=5)
            if recent_bills:
                for bill in recent_bills:
                    st.write(f"{get_status_color(bill['payment_status'])} {bill['bill_type']} - {format_currency(bill['amount'])} (Due: {format_date(bill['due_date'])})")
            else:
                st.info("No recent bills")
        
        with col2:
            st.subheader("📝 Recent Complaints")
            recent_complaints = self.get_recent_complaints(user['user_id'], limit=5)
            if recent_complaints:
                for complaint in recent_complaints:
                    st.write(f"{get_status_color(complaint['status'])} {complaint['title']} - {complaint['status'].title()}")
            else:
                st.info("No recent complaints")
        
        st.subheader("⚡ Quick Actions")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("💰 Pay Bills", width='stretch'):
                st.session_state.selected_tab = "💰 My Bills"
                st.rerun()
        
        with col2:
            if st.button("📝 Raise Complaint", width='stretch'):
                st.session_state.selected_tab = "📝 My Complaints"
                st.rerun()
        
        with col3:
            if st.button("🗳️ Vote in Polls", width='stretch'):
                st.session_state.selected_tab = "🗳️ Polls"
                st.rerun()
    
    def get_tenant_info(self, user_id):
        """Get tenant-specific information"""
        cursor = self.db.connection.cursor()
        
        # Get tenant info - Simple query
        cursor.execute("SELECT * FROM tenants WHERE user_id = %s", (user_id,))
        tenant_data = cursor.fetchone()
        
        if not tenant_data:
            cursor.close()
            return None
        
        # Get owner name - basic join
        owner_name = None
        if tenant_data[7]:  # owner_id
            cursor.execute("SELECT u.name FROM owners o JOIN users u ON o.user_id = u.user_id WHERE o.owner_id = %s", (tenant_data[7],))
            owner_result = cursor.fetchone()
            if owner_result:
                owner_name = owner_result[0]
        
        cursor.close()
        
        # Return as dictionary
        return {
            'tenant_id': tenant_data[0],
            'user_id': tenant_data[1],
            'flat_number': tenant_data[2],
            'rent_amount': tenant_data[3],
            'lease_start_date': tenant_data[4],
            'lease_end_date': tenant_data[5],
            'security_deposit': tenant_data[6],
            'owner_id': tenant_data[7],
            'created_at': tenant_data[8],
            'owner_name': owner_name
        }
    
    def get_tenant_stats(self, flat_number):
        """Get tenant statistics (same as owner stats)"""
        cursor = self.db.connection.cursor()
        
        stats = {}
        
        # count pending bills
        cursor.execute("SELECT COUNT(*) FROM bills WHERE flat_number = %s AND payment_status = 'pending'", (flat_number,))
        stats['pending_bills'] = cursor.fetchone()[0]
        
        # count open complaints
        cursor.execute("SELECT COUNT(*) FROM complaints WHERE flat_number = %s AND (status = 'open' OR status = 'in_progress')", (flat_number,))
        stats['open_complaints'] = cursor.fetchone()[0]
        
        # get unread notifications count
        user_id = st.session_state.user['user_id']
        unread_notifs = self.db.get_unread_notifications(user_id)
        stats['unread_notifications'] = len(unread_notifs)
        
        # check active polls
        cursor.execute("SELECT COUNT(*) FROM polls WHERE is_active = TRUE")
        stats['active_polls'] = cursor.fetchone()[0]
        
        cursor.close()
        return stats
    
    def get_recent_bills(self, flat_number, limit=5):
        """Get recent bills for the flat"""
        # Use the simplified database method
        return self.db.get_user_bills(flat_number)[:limit]
    
    def get_recent_complaints(self, user_id, limit=5):
        """Get recent complaints by the user"""
        # Use the simplified database method
        return self.db.get_user_complaints(user_id)[:limit]
    
    def show_bills(self):
        """Show bills management (same as owner)"""
        user = st.session_state.user
        
        # Title in styled container
        st.markdown("""
            <div style='
                background: white;
                border-radius: 15px;
                padding: 2rem;
                margin-bottom: 2rem;
                box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
                border: 1px solid #e5e7eb;
                text-align: center;
            '>
                <h1 style='font-size: 2.2rem; color: #111827; font-weight: 700; margin: 0;'>
                    💰 My Bills
                </h1>
            </div>
        """, unsafe_allow_html=True)
        
        # Check for overdue bills
        from utils import check_overdue_bills
        check_overdue_bills(self.db)
        
        # Get all bills for the flat
        bills = self.db.get_user_bills(user['flat_number'])
        
        if bills:
            # Summary metrics
            total_pending = sum(float(bill['amount']) for bill in bills if bill['payment_status'] == 'pending')
            total_overdue = sum(float(bill['amount']) for bill in bills if bill['payment_status'] == 'overdue')
            total_paid = sum(float(bill['amount']) for bill in bills if bill['payment_status'] == 'paid')
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Pending Amount", format_currency(total_pending))
            
            with col2:
                st.metric("Overdue Amount", format_currency(total_overdue))
            
            with col3:
                st.metric("Paid Amount", format_currency(total_paid))
            
            st.divider()
            
            # Filter options
            col1, col2 = st.columns(2)
            with col1:
                status_filter = st.selectbox("Filter by Status", ["all", "pending", "paid", "overdue"])
            with col2:
                bill_type_filter = st.selectbox("Filter by Type", ["all", "Maintenance", "Electricity", "Water", "Parking", "Security", "Other"])
            
            # Apply filters
            filtered_bills = bills
            if status_filter != "all":
                filtered_bills = [bill for bill in filtered_bills if bill['payment_status'] == status_filter]
            if bill_type_filter != "all":
                filtered_bills = [bill for bill in filtered_bills if bill['bill_type'] == bill_type_filter]
            
            # Display bills
            if filtered_bills:
                for bill in filtered_bills:
                    with st.expander(f"{get_status_color(bill['payment_status'])} {bill['bill_type']} - {format_currency(bill['amount'])} (Due: {format_date(bill['due_date'])})"):
                        col1, col2 = st.columns([2, 1])
                        
                        with col1:
                            st.write(f"**Bill ID:** {bill['bill_id']}")
                            st.write(f"**Type:** {bill['bill_type']}")
                            st.write(f"**Amount:** {format_currency(bill['amount'])}")
                            st.write(f"**Due Date:** {format_date(bill['due_date'])}")
                            st.write(f"**Status:** {bill['payment_status'].title()}")
                            if bill['payment_date']:
                                st.write(f"**Payment Date:** {format_date(bill['payment_date'])}")
                                st.write(f"**Payment Method:** {bill['payment_method']}")
                        
                        with col2:
                            if bill['payment_status'] in ['pending', 'overdue']:
                                st.subheader("💳 Pay Now")
                                
                                payment_method = st.selectbox(
                                    "Payment Method",
                                    ["Online Banking", "UPI", "Credit Card", "Debit Card", "Cash"],
                                    key=f"payment_method_{bill['bill_id']}"
                                )
                                
                                if st.button("Pay Bill", key=f"pay_{bill['bill_id']}"):
                                    try:
                                        self.db.pay_bill(bill['bill_id'], payment_method)
                                        st.success("Payment successful!")
                                        st.rerun()
                                    except Exception as e:
                                        st.error(f"Payment failed: {e}")
            else:
                st.info("No bills found with the selected filters")
        else:
            st.info("No bills found for your flat")
    
    def show_complaints(self):
        """Show complaints management (same as owner)"""
        user = st.session_state.user
        
        # Title in styled container
        st.markdown("""
            <div style='
                background: white;
                border-radius: 15px;
                padding: 2rem;
                margin-bottom: 2rem;
                box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
                border: 1px solid #e5e7eb;
                text-align: center;
            '>
                <h1 style='font-size: 2.2rem; color: #111827; font-weight: 700; margin: 0;'>
                    📝 My Complaints
                </h1>
            </div>
        """, unsafe_allow_html=True)
        
        tab1, tab2 = st.tabs(["Raise New Complaint", "My Complaints"])
        
        with tab1:
            self.raise_complaint_form()
        
        with tab2:
            self.view_my_complaints()
    
    def raise_complaint_form(self):
        """Raise new complaint form (same as owner)"""
        user = st.session_state.user
        
        st.subheader("➕ Raise New Complaint")
        
        with st.form("raise_complaint_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                title = st.text_input("Complaint Title")
                category = st.selectbox("Category", [
                    "Maintenance",
                    "Plumbing",
                    "Electrical",
                    "Security",
                    "Noise",
                    "Parking",
                    "Cleanliness",
                    "Elevator",
                    "Water Supply",
                    "Other"
                ])
            
            with col2:
                priority = st.selectbox("Priority", ["low", "medium", "high", "urgent"])
            
            description = st.text_area("Description", height=150)
            
            submit = st.form_submit_button("Submit Complaint")
            
            if submit:
                if title and description and category:
                    try:
                        complaint_id = self.db.create_complaint(
                            user['user_id'], 
                            user['flat_number'], 
                            title, 
                            description, 
                            category, 
                            priority
                        )
                        st.success(f"Complaint submitted successfully! Complaint ID: {complaint_id}")
                    except Exception as e:
                        st.error(f"Error submitting complaint: {e}")
                else:
                    st.error("Please fill all required fields")
    
    def view_my_complaints(self):
        """View user's complaints (same as owner)"""
        user = st.session_state.user
        
        complaints = self.db.get_user_complaints(user['user_id'])
        
        if complaints:
            # Filter options
            status_filter = st.selectbox("Filter by Status", ["all", "open", "in_progress", "resolved", "closed"])
            
            # Apply filter
            filtered_complaints = complaints
            if status_filter != "all":
                filtered_complaints = [c for c in complaints if c['status'] == status_filter]
            
            if filtered_complaints:
                for complaint in filtered_complaints:
                    with st.expander(f"{get_status_color(complaint['status'])} #{complaint['complaint_id']} - {complaint['title']} ({complaint['priority'].upper()})"):
                        col1, col2 = st.columns([2, 1])
                        
                        with col1:
                            st.write(f"**Category:** {complaint['category']}")
                            st.write(f"**Description:** {complaint['description']}")
                            if complaint['admin_response']:
                                st.write(f"**Admin Response:** {complaint['admin_response']}")
                        
                        with col2:
                            st.write(f"**Status:** {complaint['status'].title()}")
                            st.write(f"**Priority:** {complaint['priority'].title()}")
                            st.write(f"**Created:** {format_datetime(complaint['created_at'])}")
                            st.write(f"**Updated:** {format_datetime(complaint['updated_at'])}")
                            if complaint['resolved_at']:
                                st.write(f"**Resolved:** {format_datetime(complaint['resolved_at'])}")
            else:
                st.info("No complaints found with the selected filter")
        else:
            st.info("You haven't raised any complaints yet")
    
    def show_notifications(self):
        """Show notifications (same as owner)"""
        user = st.session_state.user
        
        # Title in styled container
        st.markdown("""
            <div style='
                background: white;
                border-radius: 15px;
                padding: 2rem;
                margin-bottom: 2rem;
                box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
                border: 1px solid #e5e7eb;
                text-align: center;
            '>
                <h1 style='font-size: 2.2rem; color: #111827; font-weight: 700; margin: 0;'>
                    📢 Notifications
                </h1>
            </div>
        """, unsafe_allow_html=True)
        
        # Get unread notifications
        unread_notifications = self.db.get_unread_notifications(user['user_id'])
        
        if unread_notifications:
            st.subheader("🔴 Unread Notifications")
            create_notification_display(unread_notifications, self.db, user['user_id'])
            st.divider()
        
        # Get all notifications (read and unread) - Simple query
        cursor = self.db.connection.cursor()
        cursor.execute("""
            SELECT * FROM notifications 
            ORDER BY created_at DESC 
            LIMIT 20
        """, ())
        notifs_data = cursor.fetchall()
        
        # check if each notification is read or not
        all_notifications = []
        for n in notifs_data:
            cursor.execute("SELECT read_at FROM notification_reads WHERE notification_id = %s AND user_id = %s", (n[0], user['user_id']))
            read_result = cursor.fetchone()
            all_notifications.append({
                'notification_id': n[0],
                'title': n[1],
                'message': n[2],
                'created_at': n[3],
                'read_at': read_result[0] if read_result else None
            })
        cursor.close()
        
        if all_notifications:
            st.subheader("📜 All Notifications")
            
            for notification in all_notifications:
                read_status = "✅ Read" if notification['read_at'] else "🔴 Unread"
                
                with st.expander(f"{notification['title']} - {read_status} - {format_datetime(notification['created_at'])}"):
                    st.write(notification['message'])
                    if notification['read_at']:
                        st.write(f"*Read on: {format_datetime(notification['read_at'])}*")
                    else:
                        if st.button(f"Mark as Read", key=f"read_all_{notification['notification_id']}"):
                            self.db.mark_notification_read(notification['notification_id'], user['user_id'])
                            st.success("Marked as read!")
                            st.rerun()
        else:
            if not unread_notifications:
                st.info("No notifications")
    
    def show_polls(self):
        """Show polls and voting (same as owner)"""
        user = st.session_state.user
        
        # Title in styled container
        st.markdown("""
            <div style='
                background: white;
                border-radius: 15px;
                padding: 2rem;
                margin-bottom: 2rem;
                box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
                border: 1px solid #e5e7eb;
                text-align: center;
            '>
                <h1 style='font-size: 2.2rem; color: #111827; font-weight: 700; margin: 0;'>
                    🗳️ Polls & Voting
                </h1>
            </div>
        """, unsafe_allow_html=True)
        
        # Get active polls - Simple query
        cursor = self.db.connection.cursor()
        cursor.execute("SELECT * FROM polls WHERE status = 'active' ORDER BY created_at DESC")
        polls_data = cursor.fetchall()
        active_polls = [{
            'poll_id': p[0],
            'title': p[1],
            'description': p[2],
            'created_at': p[4],
            'status': p[6]
        } for p in polls_data]
        
        if active_polls:
            st.subheader("🗳️ Active Polls")
            create_poll_display(active_polls, self.db, user['user_id'])
        
        # Get closed polls with results
        cursor.execute("SELECT * FROM polls WHERE status = 'closed' ORDER BY created_at DESC LIMIT 10")
        closed_polls = cursor.fetchall()
        
        if closed_polls:
            st.subheader("📊 Recent Poll Results")
            
            for poll in closed_polls:
                with st.expander(f"📊 {poll['title']} (Closed)"):
                    st.write(poll['description'])
                    st.write(f"**End Date:** {format_date(poll['end_date'])}")
                    
                    # Get results
                    cursor.execute("SELECT option_text, vote_count FROM poll_options WHERE poll_id = %s ORDER BY vote_count DESC", (poll['poll_id'],))
                    
                    results = cursor.fetchall()
                    if results:
                        total_votes = sum(r[1] for r in results)
                        
                        st.write("**Results:**")
                        for i, r in enumerate(results):
                            percentage = (r[1] / total_votes * 100) if total_votes > 0 else 0
                            rank_emoji = ["🥇", "🥈", "🥉"][i] if i < 3 else "•"
                            st.write(f"{rank_emoji} {r[0]}: {r[1]} votes ({percentage:.1f}%)")
                        
                        st.write(f"**Total Votes:** {total_votes}")
                        
                        # Check if user voted
                        cursor.execute("""
                            SELECT po.option_text 
                            FROM votes v
                            JOIN poll_options po ON v.option_id = po.option_id
                            WHERE v.poll_id = %s AND v.user_id = %s
                        """, (poll['poll_id'], user['user_id']))
                        
                        user_vote = cursor.fetchone()
                        if user_vote:
                            st.info(f"✅ You voted for: {user_vote['option_text']}")
        
        if not active_polls and not closed_polls:
            st.info("No polls available")
        
        cursor.close()
    
    def show_rental_agreement(self):
        """Show rental agreement details"""
        user = st.session_state.user
        st.title("📄 Rental Agreement")
        
        tenant_info = self.get_tenant_info(user['user_id'])
        
        if tenant_info:
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("🏠 Property Details")
                st.write(f"**Flat Number:** {user['flat_number']}")
                st.write(f"**Owner:** {tenant_info['owner_name']}")
                st.write(f"**Property Type:** Apartment")
                
                st.subheader("💰 Financial Details")
                st.write(f"**Monthly Rent:** {format_currency(tenant_info['rent_amount'])}")
                st.write(f"**Security Deposit:** {format_currency(tenant_info['security_deposit'])}")
                
                # Calculate total paid and pending rent
                current_date = date.today()
                lease_start = tenant_info['lease_start_date']
                
                if lease_start and lease_start <= current_date:
                    months_elapsed = (current_date.year - lease_start.year) * 12 + (current_date.month - lease_start.month)
                    total_rent_due = months_elapsed * float(tenant_info['rent_amount'])
                    
                    # Get total rent paid from bills - Simple query
                    cursor = self.db.connection.cursor()
                    cursor.execute("""
                        SELECT COALESCE(SUM(amount), 0)
                        FROM bills
                        WHERE flat_number = %s AND payment_status = 'paid' AND bill_type = 'Rent'
                    """, (user['flat_number'],))
                    result = cursor.fetchone()
                    total_rent_paid = float(result[0]) if result else 0
                    cursor.close()
                    
                    st.write(f"**Total Rent Due:** {format_currency(total_rent_due)}")
                    st.write(f"**Total Rent Paid:** {format_currency(total_rent_paid)}")
                    
                    if total_rent_paid < total_rent_due:
                        st.error(f"**Outstanding Rent:** {format_currency(total_rent_due - total_rent_paid)}")
                    else:
                        st.success("✅ Rent payments up to date")
            
            with col2:
                st.subheader("📅 Lease Terms")
                st.write(f"**Lease Start Date:** {format_date(tenant_info['lease_start_date'])}")
                st.write(f"**Lease End Date:** {format_date(tenant_info['lease_end_date'])}")
                
                if tenant_info['lease_start_date'] and tenant_info['lease_end_date']:
                    lease_duration = (tenant_info['lease_end_date'] - tenant_info['lease_start_date']).days
                    st.write(f"**Lease Duration:** {lease_duration} days ({lease_duration // 30} months)")
                    
                    # Calculate remaining lease time
                    remaining_days = (tenant_info['lease_end_date'] - date.today()).days
                    if remaining_days > 0:
                        st.success(f"**Days Remaining:** {remaining_days}")
                        
                        # Renewal reminder
                        if remaining_days <= 60:
                            st.warning(f"⏰ Lease expires in {remaining_days} days. Consider renewal!")
                    else:
                        st.error(f"**Lease Expired:** {abs(remaining_days)} days ago")
                
                st.subheader("📋 Agreement Status")
                st.write(f"**Status:** Active" if remaining_days > 0 else "**Status:** Expired")
                st.write(f"**Created:** {format_date(tenant_info['created_at'])}")
            
            # Additional lease information
            st.divider()
            st.subheader("📝 Lease Terms & Conditions")
            
            # This could be expanded to include actual lease terms from the database
            lease_terms = [
                "Rent must be paid by the 5th of each month",
                "No subletting without owner's written consent", 
                "Tenant is responsible for utility bills",
                "Security deposit will be refunded after deducting any damages",
                "30 days notice required for lease termination",
                "No pets allowed without prior approval",
                "Maintenance requests must be submitted through the system"
            ]
            
            for i, term in enumerate(lease_terms, 1):
                st.write(f"{i}. {term}")
            
        else:
            st.error("No rental agreement information found")

    def show_visitors(self):
        """Show visitors for the tenant's flat"""
        user = st.session_state.user
        
        # Title in styled container
        st.markdown("""
            <div style='
                background: white;
                border-radius: 15px;
                padding: 2rem;
                margin-bottom: 2rem;
                box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
                border: 1px solid #e5e7eb;
                text-align: center;
            '>
                <h1 style='font-size: 2.2rem; color: #111827; font-weight: 700; margin: 0;'>
                    🚶 My Visitors
                </h1>
            </div>
        """, unsafe_allow_html=True)
        
        # Get visitors for this flat
        visitors = self.db.get_visitors_for_flat(user['flat_number'], limit=20)
        
        if visitors:
            st.subheader(f"Recent Visitors to Flat {user['flat_number']}")
            
            for visitor in visitors:
                status_icon = "🟢" if visitor['status'] == 'out' else "🔴"
                with st.expander(f"{status_icon} {visitor['visitor_name']} - {format_datetime(visitor['entry_time'])}"):
                    col1, col2, col3 = st.columns([2, 1, 1])
                    
                    with col1:
                        st.write(f"**Name:** {visitor['visitor_name']}")
                        st.write(f"**Phone:** {visitor['visitor_phone']}")
                        st.write(f"**Purpose:** {visitor['purpose']}")
                        st.write(f"**Vehicle:** {visitor['vehicle_number']}")
                        st.write(f"**Entry Time:** {format_datetime(visitor['entry_time'])}")
                        if visitor['exit_time']:
                            st.write(f"**Exit Time:** {format_datetime(visitor['exit_time'])}")
                        st.write(f"**Status:** {visitor['status'].title()}")
                        if visitor['logged_by_name']:
                            st.write(f"**Logged by:** {visitor['logged_by_name']}")
                    
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
                        st.write("**Visitor Info**")
                        if visitor['status'] == 'in':
                            st.success("Currently Inside")
                        else:
                            st.info("Exited")
        else:
            st.info(f"No visitor records found for Flat {user['flat_number']}")
