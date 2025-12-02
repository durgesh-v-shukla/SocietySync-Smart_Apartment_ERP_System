import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from datetime import datetime, date
import hashlib

def create_sidebar_navigation(user_role, auth_manager):
    """Create sidebar navigation based on user role"""
    st.sidebar.title("🏢 Vishwakarma Apartment")
    st.sidebar.caption("📍 Pune | Powered by SocietySync")
    
    user = auth_manager.get_current_user()
    
    # User info in a plain white div box
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
    
    # Navigation options based on role
    if user_role == 'admin':
        options = [
            "🏠 Dashboard",
            "👥 Manage Users",
            "💰 Billing",
            "📝 Complaints",
            "🚶 Visitors",
            "📢 Notifications",
            "🗳️ Polls",
            "👤 Profile"
        ]
    else:  # owner or tenant
        options = [
            "🏠 Dashboard",
            "💰 My Bills",
            "📝 My Complaints",
            "👥 My Visitors",
            "🔔 Notifications",
            "🗳️ Polls",
            "👤 Profile"
        ]
    
    selected = st.sidebar.radio("Navigation", options)
    
    st.sidebar.divider()
    
    if st.sidebar.button("🚪 Logout"):
        auth_manager.logout()
    
    return selected

def create_pie_chart(data, names, values, title):
    if data is None or (isinstance(data, list) and len(data) == 0):
        return None
    try:
        df = pd.DataFrame(data) if not isinstance(data, pd.DataFrame) else data
        if df.empty:
            return None
        fig = px.pie(df, names=names, values=values, title=title)
        fig.update_traces(textposition='inside', textinfo='percent+label')
        return fig
    except:
        return None

def create_bar_chart(data, x, y, title):
    if data is None or (isinstance(data, list) and len(data) == 0):
        return None
    try:
        df = pd.DataFrame(data) if not isinstance(data, pd.DataFrame) else data
        if df.empty:
            return None
        fig = px.bar(df, x=x, y=y, title=title)
        fig.update_layout(showlegend=False)
        return fig
    except:
        return None

def display_notification_badge(unread_count):
    """Display notification badge"""
    if unread_count > 0:
        st.sidebar.error(f"🔴 {unread_count} unread notifications")
    else:
        st.sidebar.success("✅ No unread notifications")

def format_currency(amount):
    """Format currency display"""
    if amount is None:
        return "₹0.00"
    try:
        return f"₹{float(amount):,.2f}"
    except (ValueError, TypeError):
        return "₹0.00"

def format_date(date_obj):
    if not date_obj or isinstance(date_obj, str):
        return date_obj or "N/A"
    try:
        return date_obj.strftime("%d-%m-%Y")
    except:
        return "N/A"

def format_datetime(datetime_obj):
    if not datetime_obj or isinstance(datetime_obj, str):
        return datetime_obj or "N/A"
    try:
        return datetime_obj.strftime("%d-%m-%Y %H:%M")
    except:
        return "N/A"

def get_status_color(status):
    colors = {'pending': '🟡', 'paid': '🟢', 'overdue': '🔴', 'open': '🟡', 
              'in_progress': '🟠', 'resolved': '🟢', 'closed': '⚫', 'active': '🟢', 'inactive': '🔴'}
    return colors.get(status.lower(), '⚪')

def create_data_table(data, columns=None):
    """Create formatted data table"""
    if data is None or len(data) == 0:
        st.info("No data available")
        return
        
    try:
        df = pd.DataFrame(data)
        if df.empty:
            st.info("No data available")
            return
        
        # Format specific columns
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

def validate_email(email):
    """Basic email validation"""
    import re
    if not email:
        return False
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def validate_phone(phone):
    """Basic phone validation"""
    import re
    if not phone:
        return False
    # Remove spaces and special characters
    clean_phone = re.sub(r'[^0-9]', '', phone)
    pattern = r'^[0-9]{10}$'
    return re.match(pattern, clean_phone) is not None

def get_flat_numbers():
    """Generate flat numbers: 4 blocks × 5 floors × 5 units = 100 flats total"""
    flats = []
    for block in ['A', 'B', 'C', 'D']:
        for floor in range(1, 6):  # Floors 1-5
            for unit in range(1, 6):  # Units 01-05
                flats.append(f"{block}{floor}{unit:02d}")
    return flats

def get_available_flat_numbers():
    """Get only unassigned flat numbers for new user registration"""
    from database import Database
    try:
        db = Database()
        cursor = db.connection.cursor()
        # Get all flat numbers
        all_flats = get_flat_numbers()
        
        # Get assigned flat numbers (where someone is living)
        cursor.execute("SELECT DISTINCT flat_number FROM users WHERE flat_number IS NOT NULL AND role != 'admin'")
        assigned_flats = [f[0] for f in cursor.fetchall()]
        cursor.close()
        
        # Return only unassigned flats
        available = [f for f in all_flats if f not in assigned_flats]
        return available if available else ["No flats available"]
    except Exception as e:
        print(f"Error getting available flats: {e}")
        return get_flat_numbers()

def get_allotted_flat_numbers():
    from database import Database
    try:
        db = Database()
        cursor = db.connection.cursor()
        cursor.execute("SELECT DISTINCT flat_number FROM users WHERE flat_number IS NOT NULL ORDER BY flat_number")
        flats = cursor.fetchall()
        cursor.close()
        return [f[0] for f in flats]
    except:
        return get_flat_numbers()

def get_flats_with_occupants():
    """Get detailed information about flat occupants including owner/tenant status"""
    from database import Database
    try:
        db = Database()
        cursor = db.connection.cursor()
        
        # Get all flats with their occupants - using basic join
        cursor.execute("SELECT DISTINCT u.flat_number, u.name, u.role, u.user_id FROM users u WHERE u.flat_number IS NOT NULL AND u.role != 'admin' ORDER BY u.flat_number, u.role DESC")
        
        flats_data = cursor.fetchall()
        
        # Organize data by flat number
        flats_info = {}
        for flat_data in flats_data:
            flat_number = flat_data[0]
            name = flat_data[1]
            role = flat_data[2]
            user_id = flat_data[3]
            
            # simple if else for occupancy type
            if role == 'owner':
                occupancy_type = 'Owner-Occupied'
            elif role == 'tenant':
                occupancy_type = 'Tenant-Occupied'
            else:
                occupancy_type = 'Unknown'
            
            # get owner name if tenant - basic join
            owner_name = None
            if role == 'tenant':
                cursor.execute("SELECT u.name FROM tenants t JOIN owners o ON t.owner_id = o.owner_id JOIN users u ON o.user_id = u.user_id WHERE t.user_id = %s", (user_id,))
                owner_result = cursor.fetchone()
                if owner_result:
                    owner_name = owner_result[0]
            
            flat_data = (flat_number, name, role, occupancy_type, owner_name)
            flat_num = flat_data[0]
            resident_name = flat_data[1]
            role = flat_data[2]
            occupancy_type = flat_data[3]
            owner_name = flat_data[4]
            
            if flat_num not in flats_info:
                flats_info[flat_num] = {
                    'flat_number': flat_num,
                    'residents': [],
                    'primary_occupancy': occupancy_type,
                    'owner_name': owner_name
                }
            
            flats_info[flat_num]['residents'].append({
                'name': resident_name,
                'role': role
            })
        
        return flats_info
        
    except Exception as e:
        print(f"Error getting flats with occupants: {e}")
        return {}

def get_flat_display_options():
    """Get flat options for dropdown with occupant information"""
    try:
        flats_info = get_flats_with_occupants()
        options = {}
        
        for flat_num, info in flats_info.items():
            # Skip admin flat
            if flat_num == 'ADMIN':
                continue
                
            # Create display string
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
            
            # Ensure the mapping is correct
            options[display_text] = flat_num
        
        # Print first few options for debugging
        if len(options) > 0:
            print(f"First 3 flat options:")
            for i, (display, flat_num) in enumerate(list(options.items())[:3]):
                print(f"  {i+1}. '{display}' -> '{flat_num}'")
        
        return options
        
    except Exception as e:
        print(f"Error in get_flat_display_options: {e}")
        import traceback
        traceback.print_exc()
        return {}

def check_overdue_bills(db):
    """Check and update overdue bills"""
    try:
        cursor = db.connection.cursor()
        cursor.execute("""
            UPDATE bills 
            SET payment_status = 'overdue' 
            WHERE payment_status = 'pending' AND due_date < CURRENT_DATE
        """)
        cursor.close()
    except Exception as e:
        st.error(f"Error checking overdue bills: {e}")

def create_notification_display(notifications, db, user_id):
    """Display notifications with read tracking"""
    if not notifications or len(notifications) == 0:
        st.info("No new notifications")
        return
    
    for notification in notifications:
        with st.expander(f"📢 {notification['title']} - {format_datetime(notification['created_at'])}"):
            st.write(notification['message'])
            
            col1, col2 = st.columns([3, 1])
            with col2:
                if st.button(f"Mark as Read", key=f"read_{notification['notification_id']}"):
                    db.mark_notification_read(notification['notification_id'], user_id)
                    st.success("Marked as read!")
                    st.rerun()

def generate_unique_key(prefix, obj, index=None):
    """
    Generate a unique key for Streamlit elements
    prefix: string prefix for the key
    obj: dictionary containing the data
    index: optional index to ensure uniqueness
    """
    key_parts = [prefix]
    
    # Include unique identifiers from the object
    for field in ['bill_id', 'complaint_id', 'visitor_id', 'notification_id', 'poll_id']:
        if field in obj:
            key_parts.append(str(obj[field]))
            break
    
    # Include additional identifying fields
    for field in ['flat_number', 'bill_type', 'created_at']:
        if field in obj and obj[field]:
            key_parts.append(str(obj[field]).replace(' ', '_'))
    
    # Include index if provided for extra uniqueness
    if index is not None:
        key_parts.append(str(index))
    
    # Include a hash of the object for absolute uniqueness
    obj_str = str(sorted(obj.items()))
    obj_hash = hashlib.md5(obj_str.encode()).hexdigest()[:8]
    key_parts.append(obj_hash)
    
    return "_".join(key_parts)

def create_poll_display(polls, db, user_id):
    """Display polls with voting interface"""
    if not polls or len(polls) == 0:
        st.info("No active polls")
        return
    
    for poll in polls:
        st.subheader(f"🗳️ {poll['title']}")
        st.write(poll['description'])
        
        # Check if user has already voted
        cursor = db.connection.cursor()
        cursor.execute("""
            SELECT * FROM votes WHERE poll_id = %s AND user_id = %s
        """, (poll['poll_id'], user_id))
        
        has_voted = cursor.fetchone() is not None
        
        if has_voted:
            st.info("✅ You have already voted in this poll")
            
            # Show results
            cursor.execute("""
                SELECT option_text, vote_count 
                FROM poll_options 
                WHERE poll_id = %s
                ORDER BY vote_count DESC
            """, (poll['poll_id'],))
            
            results = cursor.fetchall()
            if results and len(results) > 0:
                results_df = pd.DataFrame(results, columns=['Option', 'Votes'])
                fig = create_bar_chart(results_df, 'Option', 'Votes', "Poll Results")
                if fig:
                    st.plotly_chart(fig, use_container_width=True)
        else:
            # Show voting options
            cursor.execute("SELECT option_id, option_text FROM poll_options WHERE poll_id = %s", (poll['poll_id'],))
            
            options = cursor.fetchall()
            if options and len(options) > 0:
                option_texts = [opt[1] for opt in options]
                selected_option = st.radio(
                    "Select your choice:",
                    option_texts,
                    key=f"poll_{poll['poll_id']}"
                )
                
                if st.button(f"Vote", key=f"vote_{poll['poll_id']}"):
                    # Find selected option_id
                    selected_option_id = next(opt[0] for opt in options if opt[1] == selected_option)
                    
                    # Record vote
                    cursor.execute("INSERT INTO votes (poll_id, option_id, user_id) VALUES (%s, %s, %s)", (poll['poll_id'], selected_option_id, user_id))
                    
                    # Update vote count
                    cursor.execute("UPDATE poll_options SET vote_count = vote_count + 1 WHERE option_id = %s", (selected_option_id,))
                    
                    st.success("Vote recorded successfully!")
                    st.rerun()
        
        cursor.close()
        st.divider()


def get_status_badge(status):
    """Get colored status badge HTML"""
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
    
    bg_color, text_color, icon = status_colors.get(status.lower(), ('#e5e7eb', '#374151', '•'))
    
    return f"""
        <span style='
            background-color: {bg_color};
            color: {text_color};
            padding: 0.3rem 0.8rem;
            border-radius: 20px;
            font-weight: 600;
            font-size: 0.85rem;
            display: inline-block;
            margin: 0.2rem;
        '>
            {icon} {status.upper()}
        </span>
    """


def get_priority_badge(priority):
    """Get colored priority badge HTML"""
    priority_colors = {
        'low': ('#d1fae5', '#065f46', '🟢'),
        'medium': ('#fef3c7', '#92400e', '🟡'),
        'high': ('#fed7aa', '#9a3412', '🟠'),
        'urgent': ('#fee2e2', '#991b1b', '🔴'),
    }
    
    bg_color, text_color, icon = priority_colors.get(priority.lower(), ('#e5e7eb', '#374151', '⚪'))
    
    return f"""
        <span style='
            background-color: {bg_color};
            color: {text_color};
            padding: 0.3rem 0.8rem;
            border-radius: 20px;
            font-weight: 600;
            font-size: 0.85rem;
            display: inline-block;
            margin: 0.2rem;
        '>
            {icon} {priority.upper()}
        </span>
    """


def show_success_animation(message):
    """Show success message with animation"""
    st.success(f"✅ {message}")


def show_error_animation(message):
    """Show error message"""
    st.error(f"❌ {message}")


def create_info_card(title, content, icon="ℹ️"):
    """Create an information card"""
    st.markdown(f"""
        <div class='card'>
            <h3>{icon} {title}</h3>
            <p style='color: #64748b; font-size: 1.1rem;'>{content}</p>
        </div>
    """, unsafe_allow_html=True)