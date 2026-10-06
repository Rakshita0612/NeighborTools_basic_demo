"""
NeighborTools - Community Tool Library Web Application.
Main entry point for the Streamlit application.
"""

import streamlit as st
from config import APP_NAME, APP_ICON, is_supabase_configured
from styles import apply_custom_styles
from components.header import render_header
from components.auth_modal import render_auth_section
from pages_ui.home_view import render_home_page
from pages_ui.browse_view import render_browse_page
from pages_ui.list_tool_view import render_list_tool_page
from pages_ui.my_reservations_view import render_my_reservations_page
from pages_ui.tool_requests_view import render_tool_requests_page
from pages_ui.profile_view import render_profile_page

# 1. Page Configuration
st.set_page_config(
    page_title=f"{APP_NAME} - Community Tool Library",
    page_icon=APP_ICON,
    layout="wide",
    initial_sidebar_state="expanded",
)

# 2. Inject Custom Theme & Forest Green Stylesheet
apply_custom_styles()

# 3. Session State Initialization
if "current_user" not in st.session_state:
    st.session_state["current_user"] = None

if "access_token" not in st.session_state:
    st.session_state["access_token"] = None

if "nav_selection" not in st.session_state:
    st.session_state["nav_selection"] = "Home"

if "selected_tool_id" not in st.session_state:
    st.session_state["selected_tool_id"] = None


# 4. Sidebar Navigation
with st.sidebar:
    st.markdown(
        f"""
        <div style="display: flex; align-items: center; gap: 0.6rem; margin-bottom: 1.25rem;">
            <div style="font-size: 1.8rem;">🌱</div>
            <div>
                <h2 style="font-size: 1.35rem; font-weight: 800; color: #1b4332; margin: 0; line-height: 1.1;">
                    {APP_NAME}
                </h2>
                <span style="font-size: 0.75rem; color: #52665a; font-weight: 600;">LEND & BORROW LOCALLY</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    nav_options = [
        "Home",
        "Browse Tools",
        "List a Tool",
        "My Reservations",
        "Requests for My Tools",
        "My Profile",
    ]

    icons = {
        "Home": "🏡",
        "Browse Tools": "🔍",
        "List a Tool": "➕",
        "My Reservations": "📅",
        "Requests for My Tools": "📥",
        "My Profile": "👤",
    }

    current_nav = st.session_state["nav_selection"]
    if current_nav not in nav_options:
        current_nav = "Home"

    # Radio navigation
    selected_nav = st.radio(
        "Navigation",
        options=nav_options,
        index=nav_options.index(current_nav),
        format_func=lambda x: f"{icons.get(x, '•')} {x}",
        label_visibility="collapsed",
        # Give each destination its own widget key so button-driven navigation
        # can select a new page without the radio restoring its previous value.
        key=f"sidebar_nav_radio_{current_nav}",
    )

    if selected_nav != st.session_state["nav_selection"]:
        st.session_state["nav_selection"] = selected_nav
        # Clear selected tool if switching tabs
        if selected_nav != "Browse Tools":
            st.session_state["selected_tool_id"] = None
        st.rerun()

    st.markdown("<hr style='margin: 1.5rem 0; border: none; border-top: 1px solid #e5e2d9;' />", unsafe_allow_html=True)

    # Sidebar Member Quick Info
    current_user = st.session_state.get("current_user")
    if current_user:
        st.markdown(f"**Signed in as:** `{current_user.get('display_name')}`")
        st.caption(f"📍 {current_user.get('neighborhood', 'Community')}")
        if st.button("Sign Out", key="sidebar_logout_btn", use_container_width=True):
            st.session_state["current_user"] = None
            st.session_state["access_token"] = None
            st.session_state["nav_selection"] = "Home"
            st.rerun()
    else:
        st.markdown("👋 **Guest Visitor**")
        st.caption("Sign in to request tools or create listings.")
        if st.button("Sign In / Join", key="sidebar_signin_btn", type="primary", use_container_width=True):
            st.session_state["nav_selection"] = "My Profile"
            st.rerun()

    st.markdown("<div style='height: 2rem;'></div>", unsafe_allow_html=True)
    if is_supabase_configured():
        st.caption("🟢 Supabase Connected")
    else:
        st.caption("🟡 Interactive Preview Mode")


# 5. Header Bar
render_header()


# 6. Page View Routing
current_page = st.session_state["nav_selection"]

if current_page == "Home":
    render_home_page()
elif current_page == "Browse Tools":
    render_browse_page()
elif current_page == "List a Tool":
    render_list_tool_page()
elif current_page == "My Reservations":
    render_my_reservations_page()
elif current_page == "Requests for My Tools":
    render_tool_requests_page()
elif current_page == "My Profile":
    render_profile_page()
else:
    render_home_page()
