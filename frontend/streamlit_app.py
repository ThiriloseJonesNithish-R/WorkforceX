import sys
import os
# Ensure workspace root is in path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import streamlit as st

# Configure page layout (Must be the very first Streamlit call)
st.set_page_config(
    page_title="WorkForceX — AI Workforce Liquidity Platform",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

from frontend.views.auth_page import show_auth_page
from frontend.views.professional_dashboard import show_professional_dashboard
from frontend.views.organization_dashboard import show_organization_dashboard
from frontend.views.analytics_page import show_analytics_page
from frontend.views.reports_page import show_reports_page

def main():
    # Restore from query parameters on reload
    q_params = st.query_params
    if "token" in q_params and not st.session_state.get("token"):
        st.session_state["token"] = q_params["token"]
        st.session_state["role"] = q_params["role"]
        st.session_state["email"] = q_params.get("email", "")
        st.session_state["name"] = q_params.get("name", "")

    # Initialize session state for user session
    if "token" not in st.session_state:
        st.session_state["token"] = None
    if "email" not in st.session_state:
        st.session_state["email"] = None
    if "role" not in st.session_state:
        st.session_state["role"] = None
    if "name" not in st.session_state:
        st.session_state["name"] = None
        
    # Synchronize successful logins to query params
    if st.session_state["token"]:
        st.query_params["token"] = st.session_state["token"]
        st.query_params["role"] = st.session_state["role"]
        st.query_params["email"] = st.session_state["email"]
        st.query_params["name"] = st.session_state["name"]
        
    # Check if logged in
    if not st.session_state["token"]:
        from frontend.components.ui import hide_sidebar
        hide_sidebar()
        show_auth_page()
    else:
        # User is logged in, show Sidebar
        st.sidebar.markdown(f"<h2 style='color:#818cf8; text-align:center; margin-bottom:10px;'>⚡ WorkForceX</h2>", unsafe_allow_html=True)
        st.sidebar.markdown(f"<div style='text-align:center; margin-bottom:20px;'>Logged in as: <b>{st.session_state['name']}</b><br><span style='color:#9ca3af; font-size:12px;'>({st.session_state['role'].capitalize()})</span></div>", unsafe_allow_html=True)
        
        # Sidebar Menu
        menu_options = ["🏠 Dashboard", "📈 System Analytics", "📄 Reports Exporter"]
        saved_choice = st.query_params.get("menu_choice", "🏠 Dashboard")
        if saved_choice not in menu_options:
            saved_choice = "🏠 Dashboard"
        choice = st.sidebar.radio("Navigation Menu", menu_options, index=menu_options.index(saved_choice))
        st.query_params["menu_choice"] = choice
        
        st.sidebar.write("---")
        if st.sidebar.button("🚪 Log Out", use_container_width=True):
            st.query_params.clear()
            st.session_state["token"] = None
            st.session_state["email"] = None
            st.session_state["role"] = None
            st.session_state["name"] = None
            st.success("Logged out successfully!")
            st.rerun()
            
        # Page Routing
        if choice == "🏠 Dashboard":
            if st.session_state["role"] == "professional":
                show_professional_dashboard()
            else:
                show_organization_dashboard()
        elif choice == "📈 System Analytics":
            show_analytics_page()
        elif choice == "📄 Reports Exporter":
            show_reports_page()

if __name__ == "__main__":
    main()
