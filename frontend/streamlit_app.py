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
            
        # Render global context-aware chatbot widget
        show_chatbot_widget()

def show_chatbot_widget():
    from frontend.api.client import send_chatbot_message_api
    
    # 1. Floating popover container
    with st.popover("💬 AI Assistant", key="global_chat_assistant_popover"):
        st.markdown("<div style='font-size:18px; font-weight:700; color:#818cf8;'>🤖 WorkForceX Assistant</div>", unsafe_allow_html=True)
        role_title = "Recruiter Assistant" if st.session_state.get("role") == "organization" else "Career Coach"
        st.caption(f"{role_title} | Context-Aware Guidance")
        st.write("---")
        
        # 2. Chat history initialization
        if "chat_history" not in st.session_state:
            st.session_state["chat_history"] = []
            
        # 3. Render previous messages in a clean layout
        chat_container = st.container(height=280)
        with chat_container:
            # Permanent welcome message at the top
            welcome_msg = (
                f"Hi **{st.session_state.get('name', 'User')}**! I am your AI assistant on the "
                f"**{st.session_state.get('role', '').capitalize()} Portal**.\n\n"
                "Ask me how to use features, where to find options, or questions about the active dashboard."
            )
            st.chat_message("assistant").write(welcome_msg)
            
            for msg in st.session_state["chat_history"]:
                if msg["role"] == "user":
                    st.chat_message("user").write(msg["content"])
                else:
                    st.chat_message("assistant").write(msg["content"])
                        
        # 4. User Chat Input
        user_input = st.chat_input("Ask about this page...", key="chat_user_input_field")
        if user_input:
            # Append user message
            st.session_state["chat_history"].append({"role": "user", "content": user_input})
            st.rerun()

        # Handle message response if user message is pending
        if st.session_state["chat_history"] and st.session_state["chat_history"][-1]["role"] == "user":
            user_message = st.session_state["chat_history"][-1]["content"]
            current_choice = st.query_params.get("menu_choice", "Dashboard")
            
            # Show inline helper typing status inside popover body
            with chat_container:
                st.chat_message("user").write(user_message)
                status_placeholder = st.empty()
                status_placeholder.markdown("🤖 *Thinking...*")
                
                # Fetch response from backend
                res, stat = send_chatbot_message_api(
                    message=user_message,
                    current_tab=current_choice,
                    chat_history=st.session_state["chat_history"][:-1]
                )
                status_placeholder.empty()
                
            if stat == 200:
                ai_response = res.get("response", "No response generated.")
            else:
                ai_response = f"I'm offline: {res.get('error', 'API connection failed.')}"
                
            # Append AI response
            st.session_state["chat_history"].append({"role": "assistant", "content": ai_response})
            st.rerun()

if __name__ == "__main__":
    main()
