import streamlit as st
from database import Database
from auth import AuthManager
from admin_dashboard import AdminDashboard
from owner_dashboard import OwnerDashboard
from tenant_dashboard import TenantDashboard
from utils import create_sidebar_navigation, display_notification_badge

st.set_page_config(
    page_title="Vishwakarma Apartment - SocietySync ERP",
    page_icon="🏢",
    layout="wide",
    initial_sidebar_state="expanded"
)


def load_css():
    try:
        with open("assets/style.css", "r") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
    except Exception:
        pass


def add_background_image():
    try:
        import base64
        with open("assets/vishwakarma_apartment.png", "rb") as f:
            encoded = base64.b64encode(f.read()).decode()
        st.markdown(
            f"<style>.stApp::before {{background-image: url(data:image/jpeg;base64,{encoded});}}</style>",
            unsafe_allow_html=True
        )
    except Exception:
        pass


@st.cache_resource
def get_database_connection():
    try:
        return Database()
    except Exception as e:
        st.error(f"Database connection failed: {e}")
        return None


# ── Session state initialisation ──────────────────────────────────────────────
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.user = None
    st.session_state.selected_tab = None


def main():
    load_css()
    add_background_image()

    db = get_database_connection()
    if db is None:
        st.error("Database connection failed. Check PostgreSQL is running.")
        if st.button("🔄 Try Again"):
            st.cache_resource.clear()
            st.rerun()
        return

    auth_manager = AuthManager()

    if not auth_manager.check_authentication():
        auth_manager.login_form()
        return

    user = auth_manager.get_current_user()

    # Force password change on first login
    if not user.get('password_changed', True):
        st.title("🔒 Password Change Required")
        if not auth_manager.password_change_form():
            return

    unread = db.get_unread_notifications(user['user_id'])
    display_notification_badge(len(unread))

    selected = create_sidebar_navigation(user['role'], auth_manager)

    if st.session_state.selected_tab:
        selected = st.session_state.selected_tab
        st.session_state.selected_tab = None

    if getattr(st.session_state, 'navigate_to', None):
        selected = st.session_state.navigate_to
        st.session_state.navigate_to = None

    if user['role'] == 'admin':
        dashboard = AdminDashboard(db)
        handle_admin_navigation(dashboard, selected, auth_manager)
    elif user['role'] == 'owner':
        dashboard = OwnerDashboard(db)
        handle_owner_navigation(dashboard, selected, auth_manager)
    elif user['role'] == 'tenant':
        dashboard = TenantDashboard(db)
        handle_tenant_navigation(dashboard, selected, auth_manager)


def handle_admin_navigation(admin_dashboard, selected, auth_manager):
    if selected == "🏠 Dashboard":
        admin_dashboard.show_dashboard()
    elif selected == "👥 Manage Users":
        admin_dashboard.manage_users()
    elif selected == "💰 Billing":
        admin_dashboard.billing_management()
    elif selected == "📝 Complaints":
        admin_dashboard.complaint_management()
    elif selected == "🚶 Visitors":
        admin_dashboard.visitor_management()
    elif selected == "📢 Notifications":
        admin_dashboard.notification_management()
    elif selected == "🗳️ Polls":
        admin_dashboard.poll_management()
    elif selected == "👤 Profile":
        auth_manager.profile_management()


def handle_owner_navigation(owner_dashboard, selected, auth_manager):
    if selected == "🏠 Dashboard":
        owner_dashboard.show()
    elif selected == "💰 My Bills":
        owner_dashboard.show_bills()
    elif selected == "📝 My Complaints":
        owner_dashboard.show_complaints()
    elif selected == "👥 My Visitors":
        owner_dashboard.show_visitors()
    elif selected == "🔔 Notifications":
        owner_dashboard.show_notifications()
    elif selected == "🗳️ Polls":
        owner_dashboard.show_polls()
    elif selected == "👤 Profile":
        auth_manager.profile_management()


def handle_tenant_navigation(tenant_dashboard, selected, auth_manager):
    if selected == "🏠 Dashboard":
        tenant_dashboard.show()
    elif selected == "💰 My Bills":
        tenant_dashboard.show_bills()
    elif selected == "📝 My Complaints":
        tenant_dashboard.show_complaints()
    elif selected == "👥 My Visitors":
        tenant_dashboard.show_visitors()
    elif selected == "🔔 Notifications":
        tenant_dashboard.show_notifications()
    elif selected == "🗳️ Polls":
        tenant_dashboard.show_polls()
    elif selected == "👤 Profile":
        auth_manager.profile_management()


if __name__ == "__main__":
    main()
