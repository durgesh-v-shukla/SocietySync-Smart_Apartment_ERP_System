import streamlit as st
from database import Database

class AuthManager:
    def __init__(self):
        self.db = Database()
    
    def login_form(self):
        """Display login form with beautiful design"""
        # Center the login form
        col1, col2, col3 = st.columns([1, 2, 1])
        
        with col2:
            # ONE BIG DIV for entire login card
            st.markdown("""
            <div style='
                background: white;
                border-radius: 20px;
                padding: 3rem 2.5rem;
                box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
                border: 1px solid #e5e7eb;
                margin: 2rem 0;
            '>
                <div style='text-align: center; margin-bottom: 2rem;'>
                    <h1 style='font-size: 3.5rem; margin-bottom: 0.5rem;'>&#127970;</h1>
                    <h1 style='color: #111827; font-weight: 700; margin-bottom: 0.5rem; font-size: 2.2rem;'>Vishwakarma Apartment</h1>
                    <p style='color: #4b5563; font-size: 1.3rem; font-weight: 500; margin: 0.5rem 0;'>📍 Pune</p>
                    <p style='color: #6b7280; font-size: 0.95rem; margin-top: 0.5rem;'>Powered by SocietySync ERP</p>
                </div>
                <h3 style='color: #111827; text-align: center; margin-bottom: 1.5rem; font-weight: 600;'>🔐 Login to Your Account</h3>
            </div>
            """, unsafe_allow_html=True)
            
            # Login form (streamlit inputs appear after the header div)
            with st.form("login_form"):
                
                username = st.text_input("👤 Username", placeholder="Enter your username", key="login_username")
                password = st.text_input("🔑 Password", type="password", placeholder="Enter your password", key="login_password")
                
                st.markdown("<br>", unsafe_allow_html=True)
                submit = st.form_submit_button("🚀 Login", width='stretch')
                
                if submit:
                    if username and password:
                        user = self.db.authenticate_user(username, password)
                        if user:
                            st.session_state.user = user
                            st.session_state.logged_in = True
                            
                            # Check if password needs to be changed
                            if not user['password_changed']:
                                st.session_state.force_password_change = True
                                st.warning("⚠️ You must change your initial password!")
                            else:
                                st.success(f"✅ Welcome back, {user['name']}!")
                            st.rerun()
                        else:
                            st.error("❌ Invalid username or password")
                    else:
                        st.error("⚠️ Please enter both username and password")
            
            # Demo Credentials
            st.markdown("<br>", unsafe_allow_html=True)
            with st.expander("📋 Demo Credentials"):
                st.markdown("""
                    **Admin Account:**
                    - Username: `admin`
                    - Password: `admin123`
                    
                    **Sample Users:**
                    - Username: `firstname_lastname` (e.g., `durgesh_shukla`)
                    - Password: `password123`
                """)
            
            # Footer with white text
            st.markdown("""
                <div class='footer' style='text-align: center; margin-top: 2rem; padding: 1rem 0;'>
                    <p style='color: white; font-weight: 600; margin: 0.5rem 0;'>© 2025 SocietySync ERP | All Rights Reserved</p>
                    <p style='font-size: 0.95rem; color: white; font-weight: 600; margin: 0.5rem 0;'>
                        🔒 Secure • ✅ Reliable • ⚡ Efficient
                    </p>
                </div>
            """, unsafe_allow_html=True)
    
    def logout(self):
        st.session_state.clear()
        st.rerun()
    
    def check_authentication(self):
        return st.session_state.get('logged_in', False)
    
    def get_current_user(self):
        return st.session_state.get('user', None)
    
    def password_change_form(self):
        user = self.get_current_user()
        
        if not user['password_changed']:
            st.error("🔒 Security Alert: You must change your initial password before proceeding.")
            st.info(f"💡 Your current password is: **{user['initial_password']}**")
            
            with st.form("password_change_form"):
                st.markdown("### 🔐 Create New Password")
                new_pw = st.text_input("🔑 New Password", type="password", placeholder="Enter new password (min 6 characters)")
                confirm_pw = st.text_input("✅ Confirm New Password", type="password", placeholder="Re-enter new password")
                
                submit = st.form_submit_button("🔄 Change Password", width='stretch')
                
                if submit:
                    if not new_pw or not confirm_pw:
                        st.error("⚠️ Please enter both password fields")
                    elif new_pw != confirm_pw:
                        st.error("❌ Passwords do not match")
                    elif len(new_pw) < 6:
                        st.error("⚠️ Password must be at least 6 characters long")
                    elif new_pw == user['initial_password']:
                        st.error("⚠️ New password cannot be the same as initial password")
                    else:
                        success = self.db.change_password(user['user_id'], new_pw)
                        if success:
                            st.success("✅ Password changed successfully!")
                            st.session_state.user['password_changed'] = True
                            st.session_state.force_password_change = False
                            st.balloons()
                            st.rerun()
                        else:
                            st.error("❌ Failed to change password")
            return False
        return True
    
    def profile_management(self):
        """Profile management form"""
        user = self.get_current_user()
        
        st.subheader("👤 Profile Management")
        
        with st.form("profile_form"):
            name = st.text_input("Name", value=user['name'])
            email = st.text_input("Email", value=user['email'] or "")
            phone = st.text_input("Phone", value=user['phone'] or "")
            
            # Show flat number but make it read-only
            st.text_input("Flat Number", value=user['flat_number'], disabled=True,
                         help="Flat number cannot be changed")
            
            submit = st.form_submit_button("Update Profile")
            
            if submit:
                try:
                    cursor = self.db.connection.cursor()
                    cursor.execute("""
                        UPDATE users 
                        SET name = %s, email = %s, phone = %s
                        WHERE user_id = %s
                    """, (name, email, phone, user['user_id']))
                    cursor.close()
                    
                    # Update session
                    st.session_state.user['name'] = name
                    st.session_state.user['email'] = email
                    st.session_state.user['phone'] = phone
                    
                    st.success("Profile updated successfully!")
                except Exception as e:
                    st.error(f"Error updating profile: {e}")
        
        # Password change section
        st.subheader("🔒 Change Password")
        with st.form("change_password_form"):
            current_password = st.text_input("Current Password", type="password")
            new_password = st.text_input("New Password", type="password")
            confirm_new_password = st.text_input("Confirm New Password", type="password")
            submit_password = st.form_submit_button("Change Password")
            
            if submit_password:
                if current_password and new_password and confirm_new_password:
                    # Verify current password
                    if self.db.authenticate_user(user['username'], current_password):
                        if new_password == confirm_new_password:
                            if len(new_password) >= 6:
                                self.db.change_password(user['user_id'], new_password)
                                st.success("Password changed successfully!")
                            else:
                                st.error("New password must be at least 6 characters long")
                        else:
                            st.error("New passwords do not match")
                    else:
                        st.error("Current password is incorrect")
                else:
                    st.error("Please fill all password fields")
