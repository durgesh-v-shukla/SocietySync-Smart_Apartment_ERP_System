from datetime import datetime
import streamlit as st
from database import Database
from config import MIN_PASSWORD_LENGTH


class AuthManager:
    def __init__(self):
        self.db = Database()

    # ──────────────────────────────────────────────────────────────────────────
    # Login
    # ──────────────────────────────────────────────────────────────────────────

    def login_form(self):
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
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

            with st.form("login_form"):
                username = st.text_input("👤 Username", placeholder="Enter your username", key="login_username")
                password = st.text_input("🔑 Password", type="password", placeholder="Enter your password", key="login_password")
                st.markdown("<br>", unsafe_allow_html=True)
                submit = st.form_submit_button("🚀 Login", use_container_width=True)

                if submit:
                    if username and password:
                        user = self.db.authenticate_user(username, password)
                        if user:
                            st.session_state.user = user
                            st.session_state.logged_in = True
                            if not user['password_changed']:
                                st.warning("⚠️ You must change your initial password before continuing!")
                            else:
                                st.success(f"✅ Welcome back, {user['name']}!")
                            st.rerun()
                        else:
                            st.error("❌ Invalid username or password")
                    else:
                        st.error("⚠️ Please enter both username and password")

            st.markdown("<br>", unsafe_allow_html=True)
            with st.expander("📋 Demo Credentials"):
                st.markdown("""
**Admin Account:**
- Username: `admin`
- Password: `admin123`

**Owner Account (example):**
- Username: `owner_durgesh_shukla`
- Password: provided at account creation

**Tenant Account (example):**
- Username: `tenant_rahul_joshi`
- Password: provided at account creation
                """)

            st.markdown(f"""
                <div style='text-align: center; margin-top: 2rem; padding: 1rem 0;'>
                    <p style='color: white; font-weight: 600; margin: 0.5rem 0;'>© {datetime.now().year} SocietySync ERP | All Rights Reserved</p>
                    <p style='font-size: 0.95rem; color: white; font-weight: 600; margin: 0.5rem 0;'>
                        🔒 Secure • ✅ Reliable • ⚡ Efficient
                    </p>
                </div>
            """, unsafe_allow_html=True)

    # ──────────────────────────────────────────────────────────────────────────
    # Session helpers
    # ──────────────────────────────────────────────────────────────────────────

    def logout(self):
        st.session_state.clear()
        st.rerun()

    def check_authentication(self):
        return st.session_state.get('logged_in', False)

    def get_current_user(self):
        return st.session_state.get('user', None)

    # ──────────────────────────────────────────────────────────────────────────
    # Forced password change on first login
    # ──────────────────────────────────────────────────────────────────────────

    def password_change_form(self):
        user = self.get_current_user()
        if user['password_changed']:
            return True

        st.error("🔒 Security Alert: You must change your password before continuing.")

        with st.form("password_change_form"):
            st.markdown("### 🔐 Create New Password")
            new_pw = st.text_input("🔑 New Password", type="password",
                                   placeholder=f"At least {MIN_PASSWORD_LENGTH} characters")
            confirm_pw = st.text_input("✅ Confirm New Password", type="password",
                                       placeholder="Re-enter new password")
            submit = st.form_submit_button("🔄 Change Password", use_container_width=True)

            if submit:
                if not new_pw or not confirm_pw:
                    st.error("⚠️ Please fill both fields")
                elif new_pw != confirm_pw:
                    st.error("❌ Passwords do not match")
                elif len(new_pw) < MIN_PASSWORD_LENGTH:
                    st.error(f"⚠️ Password must be at least {MIN_PASSWORD_LENGTH} characters")
                else:
                    if self.db.change_password(user['user_id'], new_pw):
                        st.session_state.user['password_changed'] = True
                        st.success("✅ Password changed successfully!")
                        st.balloons()
                        st.rerun()
                    else:
                        st.error("❌ Failed to change password. Please try again.")
        return False

    # ──────────────────────────────────────────────────────────────────────────
    # Profile management
    # ──────────────────────────────────────────────────────────────────────────

    def profile_management(self):
        user = self.get_current_user()
        st.subheader("👤 Profile Management")

        with st.form("profile_form"):
            name = st.text_input("Name", value=user['name'])
            email = st.text_input("Email", value=user['email'] or "")
            phone = st.text_input("Phone", value=user['phone'] or "")
            st.text_input("Flat Number", value=user['flat_number'], disabled=True,
                          help="Flat number cannot be changed")
            submit = st.form_submit_button("Update Profile")

            if submit:
                try:
                    cur = self.db.connection.cursor()
                    cur.execute(
                        "UPDATE users SET name = %s, email = %s, phone = %s WHERE user_id = %s",
                        (name, email, phone, user['user_id'])
                    )
                    cur.close()
                    st.session_state.user['name'] = name
                    st.session_state.user['email'] = email
                    st.session_state.user['phone'] = phone
                    st.success("✅ Profile updated successfully!")
                except Exception as e:
                    st.error(f"Error updating profile: {e}")

        st.subheader("🔒 Change Password")
        with st.form("change_password_form"):
            current_password = st.text_input("Current Password", type="password")
            new_password = st.text_input("New Password", type="password")
            confirm_new_password = st.text_input("Confirm New Password", type="password")
            submit_password = st.form_submit_button("Change Password")

            if submit_password:
                if not (current_password and new_password and confirm_new_password):
                    st.error("Please fill all password fields")
                elif not self.db.authenticate_user(user['username'], current_password):
                    st.error("Current password is incorrect")
                elif new_password != confirm_new_password:
                    st.error("New passwords do not match")
                elif len(new_password) < MIN_PASSWORD_LENGTH:
                    st.error(f"Password must be at least {MIN_PASSWORD_LENGTH} characters")
                else:
                    self.db.change_password(user['user_id'], new_password)
                    st.success("✅ Password changed successfully!")
