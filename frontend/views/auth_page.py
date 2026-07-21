import streamlit as st
import re
import os
from frontend.api.client import (
    login_professional_api,
    login_organization_api,
    register_professional_api,
    register_organization_api,
    forgot_password_api,
    get_skills_api
)
from frontend.components.ui import card_start, card_end, load_css

INDIAN_STATES = [
    "Andhra Pradesh", "Delhi", "Gujarat", "Karnataka", "Kerala", 
    "Maharashtra", "Tamil Nadu", "Telangana", "Uttar Pradesh", "West Bengal"
]

DOMAINS = [
    "Data Scientist", "Data Analyst", "AI Engineer", 
    "Cybersecurity Analyst", "Software Engineer", "Cloud Architect"
]

LANGUAGES = ["English", "Hindi", "Tamil", "Telugu", "Kannada", "Malayalam", "Bengali", "Marathi", "French", "Spanish"]

def show_auth_page():
    load_css()
    
    # Initialize page state
    if "page_state" not in st.session_state:
        st.session_state["page_state"] = "landing"
        
    page_state = st.session_state["page_state"]
    
    # ------------------ Page State: Landing Page ------------------
    if page_state == "landing":
        st.markdown("""
            <div style='display: flex; align-items: center; margin-bottom: 20px;'>
                <h1 style='color: #818cf8; margin-right: 15px;'>⚡ WorkForceX</h1>
                <span style='font-size: 16px; color: #9ca3af; padding-top: 15px;'>AI Powered Workforce Liquidity Platform</span>
            </div>
            <hr style='border-color: rgba(255,255,255,0.08); margin-bottom: 40px;'>
        """, unsafe_allow_html=True)
        
        col_left, col_right = st.columns([1, 1])
        
        with col_left:
            st.markdown("""
                <h2 style='font-size: 38px; font-weight: 700; margin-bottom: 20px; line-height: 1.2;'>
                    Borderless Talent Liquidity, <br><span style='color: #818cf8;'>Powered by AI.</span>
                </h2>
                <p style='color: #9ca3af; font-size: 16px; margin-bottom: 30px; line-height: 1.6;'>
                    WorkForceX connects professionals and corporate projects through smart resume analytics, MCQ skill testing, and a 5-factor weighted matching algorithm. Build high-performance teams or land your next project role instantly.
                </p>
                <div style='margin-bottom: 40px;'>
                    <h4 style='color: white; margin-bottom: 15px;'>Platform Key Features:</h4>
                    <ul style='list-style-type: none; padding-left: 0; color: #d1d5db; line-height: 2;'>
                        <li>⚡ <b>AI Resume Screener:</b> Automatic skill extraction & matching index.</li>
                        <li>🎯 <b>Domain MCQ Testing:</b> Attempts-tracked skill verification.</li>
                        <li>🧠 <b>Weighted Project Matcher:</b> Multi-dimensional candidate compatibility ranks.</li>
                        <li>📈 <b>Funnel Analytics:</b> Full-lifecycle transparency direct from MongoDB.</li>
                    </ul>
                </div>
            """, unsafe_allow_html=True)
            
        with col_right:
            hero_image_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "assets", "recruitment_hero.jpg"))
            if os.path.exists(hero_image_path):
                st.image(hero_image_path, use_container_width=True)
            else:
                # Fallback if image not found
                st.markdown("""
                    <div style='background: rgba(255,255,255,0.02); border: 2px dashed rgba(255,255,255,0.1); height: 350px; border-radius: 12px; display: flex; align-items: center; justify-content: center; margin-bottom: 20px;'>
                        <span style='color: #4b5563;'>Visual Network Illustration Placeholder</span>
                    </div>
                """, unsafe_allow_html=True)
                
            st.markdown("<br>", unsafe_allow_html=True)
            
            # Position Get Started Button on the right side
            if st.button("🚀 Get Started", key="get_started_btn", use_container_width=True):
                st.session_state["page_state"] = "choose_portal"
                st.rerun()
                
    # ------------------ Page State: Choose Portal ------------------
    elif page_state == "choose_portal":
        st.markdown("<h2 style='text-align: center; color: #818cf8; margin-top: 40px; margin-bottom: 40px;'>💼 Choose Your Portal</h2>", unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        
        with col1:
            card_start()
            st.markdown("<div style='text-align: center; padding: 20px;'>", unsafe_allow_html=True)
            st.markdown("<h2 style='font-size: 50px;'>👤</h2>", unsafe_allow_html=True)
            st.markdown("<h3>Candidate Portal</h3>", unsafe_allow_html=True)
            st.markdown("<p style='color: #9ca3af; min-height: 80px;'>Upload your resume, get scored, take customized skill assessments, and unlock match potential for open project roles.</p>", unsafe_allow_html=True)
            if st.button("Candidate Login", key="c_portal_btn", use_container_width=True):
                st.session_state["page_state"] = "login_candidate"
                st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)
            card_end()
            
        with col2:
            card_start()
            st.markdown("<div style='text-align: center; padding: 20px;'>", unsafe_allow_html=True)
            st.markdown("<h2 style='font-size: 50px;'>🏢</h2>", unsafe_allow_html=True)
            st.markdown("<h3>Organization Portal</h3>", unsafe_allow_html=True)
            st.markdown("<p style='color: #9ca3af; min-height: 80px;'>Create staffing requirements, run matching algorithms against deployment-ready talent, and send direct project invites.</p>", unsafe_allow_html=True)
            if st.button("Organization Login", key="o_portal_btn", use_container_width=True):
                st.session_state["page_state"] = "login_organization"
                st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)
            card_end()
            
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("← Back to Home", key="portal_back_home", use_container_width=True):
            st.session_state["page_state"] = "landing"
            st.rerun()

    # ------------------ Page State: Candidate Login ------------------
    elif page_state == "login_candidate":
        st.markdown("<h2 style='text-align: center; color: #818cf8; margin-top: 30px; margin-bottom: 20px;'>👤 Candidate Access Portal</h2>", unsafe_allow_html=True)
        
        st.columns([1, 2, 1])[1]
        col_main = st.columns([1, 2, 1])[1]
        with col_main:
            card_start()
            st.subheader("Login to Your Account")
            username = st.text_input("Username or Email", key="c_login_username")
            password = st.text_input("Password", type="password", key="c_login_pass")
            
            if st.button("Log In", key="c_login_action", use_container_width=True):
                if not username or not password:
                    st.error("Please fill in all fields.")
                else:
                    res, status = login_professional_api(username, password)
                    if status == 200:
                        st.session_state["token"] = res["token"]
                        st.session_state["username"] = res["username"]
                        st.session_state["name"] = res["name"]
                        st.session_state["role"] = "professional"
                        st.session_state["status"] = res["status"]
                        st.success(f"Welcome back, {res['name']}!")
                        st.rerun()
                    else:
                        st.error(res.get("error", "Failed to login. Incorrect username or password."))
                        
            st.write("---")
            st.write("Don't have an account?")
            if st.button("Register Now", key="c_go_reg", use_container_width=True):
                st.session_state["page_state"] = "register_candidate"
                st.rerun()
                
            st.write("")
            c_help1, c_help2 = st.columns(2)
            with c_help1:
                if st.button("Forgot Password?", key="c_go_forgot", use_container_width=True):
                    st.session_state["page_state"] = "forgot_password_candidate"
                    st.rerun()
            with c_help2:
                if st.button("Back to Portals", key="c_go_portals", use_container_width=True):
                    st.session_state["page_state"] = "choose_portal"
                    st.rerun()
            card_end()

    # ------------------ Page State: Organization Login ------------------
    elif page_state == "login_organization":
        st.markdown("<h2 style='text-align: center; color: #818cf8; margin-top: 30px; margin-bottom: 20px;'>🏢 Recruiter / HR Access Portal</h2>", unsafe_allow_html=True)
        
        col_main = st.columns([1, 2, 1])[1]
        with col_main:
            card_start()
            st.subheader("Login to Your Account")
            username = st.text_input("Username or Email", key="o_login_username")
            password = st.text_input("Password", type="password", key="o_login_pass")
            
            if st.button("Log In", key="o_login_action", use_container_width=True):
                if not username or not password:
                    st.error("Please fill in all fields.")
                else:
                    res, status = login_organization_api(username, password)
                    if status == 200:
                        st.session_state["token"] = res["token"]
                        st.session_state["username"] = res["username"]
                        st.session_state["name"] = res["name"]
                        st.session_state["role"] = "organization"
                        st.success(f"Welcome back, {res['name']}!")
                        st.rerun()
                    else:
                        st.error(res.get("error", "Failed to login. Incorrect username or password."))
                        
            st.write("---")
            st.write("Don't have an account?")
            if st.button("Register Organization", key="o_go_reg", use_container_width=True):
                st.session_state["page_state"] = "register_organization"
                st.rerun()
                
            st.write("")
            o_help1, o_help2 = st.columns(2)
            with o_help1:
                if st.button("Forgot Password?", key="o_go_forgot", use_container_width=True):
                    st.session_state["page_state"] = "forgot_password_organization"
                    st.rerun()
            with o_help2:
                if st.button("Back to Portals", key="o_go_portals", use_container_width=True):
                    st.session_state["page_state"] = "choose_portal"
                    st.rerun()
            card_end()

    # ------------------ Page State: Candidate Register ------------------
    elif page_state == "register_candidate":
        st.markdown("<h2 style='text-align: center; color: #818cf8; margin-top: 20px; margin-bottom: 20px;'>👤 Candidate Registration</h2>", unsafe_allow_html=True)
        
        card_start()
        col1, col2 = st.columns(2)
        with col1:
            name = st.text_input("Full Name * (Alphabets and spaces only)", key="c_reg_name")
            username_val = st.text_input("Username * (3-20 characters, lowercase alphanumeric or _)", key="c_reg_username")
            email = st.text_input("Email Address *", key="c_reg_email")
            phone = st.text_input("Phone Number * (e.g. +919876543210)", value="+91", key="c_reg_phone")
            state = st.selectbox("State", INDIAN_STATES, key="c_reg_state")
            domain = st.selectbox("Domain", DOMAINS, key="c_reg_domain")
            
        with col2:
            experience = st.selectbox("Experience (Years)", [str(i) for i in range(11)], key="c_reg_exp")
            
            # Fetch dynamic skills list
            db_skills = get_skills_api()
            if not db_skills:
                db_skills = ["Python", "SQL", "Machine Learning", "Deep Learning", "Power BI", "Cybersecurity", "Java", "C++", "Docker", "AWS", "Git"]
                
            selected_skills = st.multiselect("Select Skills from List", db_skills, key="c_reg_skills_sel")
            # Skills input is fully editable textbox! (NO read-only display)
            skills_val = st.text_input("Skills List (Separate with commas, fully editable)", value=", ".join(selected_skills), key="c_reg_skills_edit")
            
            selected_langs = st.multiselect("Spoken Languages", LANGUAGES, default=["English"], key="c_reg_langs_sel")
            langs_val = st.text_input("Spoken Languages (Separate with commas, fully editable)", value=", ".join(selected_langs), key="c_reg_langs_edit")
            
            linkedin = st.text_input("LinkedIn Profile URL", key="c_reg_li")
            github = st.text_input("GitHub Profile URL", key="c_reg_gh")
            password = st.text_input("Password (Min 6 chars)", type="password", key="c_reg_pass")
            confirm_pass = st.text_input("Confirm Password", type="password", key="c_reg_confirm")
            
        col_b1, col_b2 = st.columns(2)
        with col_b1:
            if st.button("Register Candidate Account", key="c_reg_action", use_container_width=True):
                # Validate inputs
                skills_list = [s.strip() for s in skills_val.split(",") if s.strip()]
                langs_list = [l.strip() for l in langs_val.split(",") if l.strip()]
                
                if not name or not re.match(r"^[A-Za-z\s]+$", name):
                    st.error("Name must contain only alphabets and spaces.")
                elif not username_val or not re.match(r"^[a-z0-9_]{3,20}$", username_val):
                    st.error("Username must be 3-20 lowercase alphanumeric characters or underscores.")
                elif not email or not re.match(r"^[^@]+@[^@]+\.[^@]+$", email):
                    st.error("Please enter a valid email address.")
                elif not phone or not phone.startswith("+91") or not phone[3:].isdigit():
                    st.error("Phone number must start with +91 followed by digits.")
                elif len(password) < 6:
                    st.error("Password must be at least 6 characters long.")
                elif password != confirm_pass:
                    st.error("Passwords do not match.")
                else:
                    data = {
                        "name": name,
                        "username": username_val,
                        "email": email,
                        "phone": phone,
                        "state": state,
                        "domain": domain,
                        "experience": int(experience),
                        "skills": skills_list,
                        "spoken_languages": langs_list,
                        "linkedin": linkedin,
                        "github": github,
                        "password": password
                    }
                    res, status = register_professional_api(data)
                    if status == 201:
                        st.session_state["token"] = res["token"]
                        st.session_state["username"] = res["username"]
                        st.session_state["name"] = name
                        st.session_state["role"] = "professional"
                        st.session_state["status"] = "Registered"
                        st.session_state["page_state"] = "dashboard"
                        st.success("Account created successfully!")
                        st.rerun()
                    else:
                        st.error(res.get("error", "Registration failed."))
        with col_b2:
            if st.button("Back to Login", key="c_reg_back", use_container_width=True):
                st.session_state["page_state"] = "login_candidate"
                st.rerun()
        card_end()

    # ------------------ Page State: Organization Register ------------------
    elif page_state == "register_organization":
        st.markdown("<h2 style='text-align: center; color: #818cf8; margin-top: 20px; margin-bottom: 20px;'>🏢 Recruiter Profile Registration</h2>", unsafe_allow_html=True)
        
        card_start()
        col1, col2 = st.columns(2)
        with col1:
            name = st.text_input("Organization Name *", key="o_reg_name")
            username_val = st.text_input("Username * (3-20 characters, lowercase alphanumeric or _)", key="o_reg_username")
            email = st.text_input("HR Email Address *", key="o_reg_email")
            hr_contact = st.text_input("HR Contact Person", key="o_reg_hr")
        with col2:
            industry = st.selectbox("Industry", ["Technology", "Finance", "Healthcare", "E-commerce", "Consulting"], key="o_reg_ind")
            logo = st.text_input("Logo Image URL", value="https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe?w=150", key="o_reg_logo")
            password = st.text_input("Password * (Min 6 chars)", type="password", key="o_reg_pass")
            confirm_pass = st.text_input("Confirm Password", type="password", key="o_reg_confirm")
            
        col_b1, col_b2 = st.columns(2)
        with col_b1:
            if st.button("Register Recruiter Account", key="o_reg_action", use_container_width=True):
                if not name or not username_val or not email or not password:
                    st.error("Name, username, email, and password are required.")
                elif not re.match(r"^[a-z0-9_]{3,20}$", username_val):
                    st.error("Username must be 3-20 lowercase alphanumeric characters or underscores.")
                elif not re.match(r"^[^@]+@[^@]+\.[^@]+$", email):
                    st.error("Please enter a valid email address.")
                elif len(password) < 6:
                    st.error("Password must be at least 6 characters long.")
                elif password != confirm_pass:
                    st.error("Passwords do not match.")
                else:
                    data = {
                        "name": name,
                        "username": username_val,
                        "email": email,
                        "password": password,
                        "industry": industry,
                        "hr_contact": hr_contact,
                        "logo": logo
                    }
                    res, status = register_organization_api(data)
                    if status == 201:
                        st.session_state["token"] = res["token"]
                        st.session_state["username"] = res["username"]
                        st.session_state["name"] = name
                        st.session_state["role"] = "organization"
                        st.session_state["page_state"] = "dashboard"
                        st.success("Organization registered successfully!")
                        st.rerun()
                    else:
                        st.error(res.get("error", "Failed to register organization."))
        with col_b2:
            if st.button("Back to Login", key="o_reg_back", use_container_width=True):
                st.session_state["page_state"] = "login_organization"
                st.rerun()
        card_end()

    # ------------------ Page State: Forgot Password Candidate ------------------
    elif page_state == "forgot_password_candidate":
        st.markdown("<h2 style='text-align: center; color: #818cf8; margin-top: 30px; margin-bottom: 20px;'>👤 Reset Password</h2>", unsafe_allow_html=True)
        
        col_main = st.columns([1, 2, 1])[1]
        with col_main:
            card_start()
            st.subheader("Account Password Recovery")
            username = st.text_input("Enter your Username", key="c_forgot_username")
            if st.button("Retrieve Recovery Instructions", key="c_forgot_action", use_container_width=True):
                if not username:
                    st.error("Please enter your username.")
                else:
                    res, status = forgot_password_api(username)
                    if status == 200:
                        st.success(res["message"])
                    else:
                        st.error(res.get("error", "Username not found."))
                        
            if st.button("Back to Candidate Login", key="c_forgot_back", use_container_width=True):
                st.session_state["page_state"] = "login_candidate"
                st.rerun()
            card_end()

    # ------------------ Page State: Forgot Password Org ------------------
    elif page_state == "forgot_password_organization":
        st.markdown("<h2 style='text-align: center; color: #818cf8; margin-top: 30px; margin-bottom: 20px;'>🏢 Reset Password</h2>", unsafe_allow_html=True)
        
        col_main = st.columns([1, 2, 1])[1]
        with col_main:
            card_start()
            st.subheader("HR Account Recovery")
            username = st.text_input("Enter your Username", key="o_forgot_username")
            if st.button("Retrieve Recovery Instructions", key="o_forgot_action", use_container_width=True):
                if not username:
                    st.error("Please enter your username.")
                else:
                    res, status = forgot_password_api(username)
                    if status == 200:
                        st.success(res["message"])
                    else:
                        st.error(res.get("error", "Username not found."))
                        
            if st.button("Back to Organization Login", key="o_forgot_back", use_container_width=True):
                st.session_state["page_state"] = "login_organization"
                st.rerun()
            card_end()
