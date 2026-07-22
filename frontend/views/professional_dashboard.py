import streamlit as st
from datetime import datetime
from frontend.api.client import (
    get_my_profile_api,
    update_my_profile_api,
    upload_resume_api,
    get_resume_insights_api,
    get_assessment_api,
    submit_assessment_api,
    get_assessment_attempts_api,
    get_invitations_api,
    respond_invitation_api,
    get_skills_api,
    get_analytics_api
)
from frontend.components.ui import card_start, card_end, render_kpi, render_timeline, load_css

INDIAN_STATES = [
    "Andhra Pradesh", "Delhi", "Gujarat", "Karnataka", "Kerala", 
    "Maharashtra", "Tamil Nadu", "Telangana", "Uttar Pradesh", "West Bengal"
]

DOMAINS = [
    "Data Scientist", "Data Analyst", "AI Engineer", 
    "Cybersecurity Analyst", "Software Engineer", "Cloud Architect"
]

LANGUAGES = ["English", "Hindi", "Tamil", "Telugu", "Kannada", "Malayalam", "Bengali", "Marathi", "French", "Spanish"]

def show_professional_dashboard():
    load_css()
    
    # Page Header
    st.markdown(f"<h1 style='color: #818cf8; margin-bottom: 25px;'>👤 Candidate Workspace</h1>", unsafe_allow_html=True)
    
    # 1. Fetch Profile
    profile, status_code = get_my_profile_api()
    if status_code != 200:
        st.error("Failed to load profile details. Please log in again.")
        return
        
    current_status = profile.get("status", "Registered")
    st.session_state["status"] = current_status
    email = profile["email"]
    username = profile["username"]
    
    # 2. Layout Columns: Left (Insights & Scores) vs Right (Timeline & Workspace Tools)
    col_left, col_right = st.columns([1, 1])
    
    # ==================== LEFT COLUMN: SCORES & AI RECOMMENDATIONS ====================
    with col_left:
        st.markdown(f"### Welcome back, **{profile['name']}**! 👋")
        st.write(f"Username: `{username}` | Email: `{email}`")
        
        # Resume Upload Panel (Always visible on left for convenience)
        card_start()
        st.subheader("📄 Upload Resume (PDF only)")
        uploaded_file = st.file_uploader("Drop your resume PDF to trigger AI scoring & extraction", type=["pdf"])
        if uploaded_file is not None:
            if st.button("Process with AI Parser", use_container_width=True):
                with st.spinner("AI parsing and analyzing..."):
                    res, status = upload_resume_api(uploaded_file.getvalue(), uploaded_file.name)
                    if status == 200:
                        st.success("Resume analyzed successfully!")
                        st.rerun()
                    else:
                        st.error(res.get("error", "Error uploading resume."))
        card_end()
        
        # Scores Metrics
        k_col1, k_col2 = st.columns(2)
        with k_col1:
            render_kpi(f"{profile.get('resume_score', 0)}%", "Resume Score")
        with k_col2:
            render_kpi(f"{profile.get('readiness_score', 0)}%", "Readiness Index")
            
        # AI Recommendations
        insights, i_status = get_resume_insights_api()
        if i_status == 200:
            card_start()
            st.subheader("💡 AI Career Recommendations")
            st.write(f"**Recommended Career Role:** `{insights.get('career_recommendation')}`")
            
            c_str, c_weak = st.columns(2)
            with c_str:
                st.markdown("<span style='color: #10b981; font-weight: bold;'>Strengths:</span>", unsafe_allow_html=True)
                for strength in insights.get("strengths", []):
                    st.markdown(f"- {strength}")
            with c_weak:
                st.markdown("<span style='color: #fbbf24; font-weight: bold;'>Weaknesses:</span>", unsafe_allow_html=True)
                for weakness in insights.get("weaknesses", []):
                    st.markdown(f"- {weakness}")
                    
            st.write("")
            st.markdown(f"**AI Suggestions:**\n{insights.get('suggestions')}")
            
            # Roles recommendations display
            st.write("")
            st.markdown(f"**Recommended Roles:** `{insights.get('career_recommendation')}`, Junior {insights.get('career_recommendation')}, Associate Engineer")
            card_end()
        else:
            card_start()
            st.info("Upload a resume PDF to trigger AI profile scoring, strengths/weaknesses mapping, and targeted career role recommendations.")
            card_end()

    # ==================== RIGHT COLUMN: TIMELINE & RECRUITMENT ACTIONS ====================
    with col_right:
        # A. Horizontal Timeline Tracker
        card_start()
        render_timeline(current_status)
        card_end()
        
        # B. Hiring & Placement Confirmation Success Box
        if current_status == "Hired":
            st.balloons()
            st.markdown(f"""
                <div style="background: rgba(16, 185, 129, 0.1); border: 1px solid #10b981; border-radius: 12px; padding: 20px; margin-bottom: 20px;">
                    <h3 style="color: #34d399; margin-top: 0; margin-bottom: 10px;">🎉 Congratulations!</h3>
                    <p style="margin-bottom: 15px; font-weight: bold; color: #34d399; font-size: 16px;">You have been hired.</p>
                    <p style="margin-bottom: 5px;"><b>Organization:</b> {profile.get('company', 'TechCorp Solutions')}</p>
                    <p style="margin-bottom: 5px;"><b>Project:</b> {profile.get('project', 'AI Analytics Portal')}</p>
                    <p style="margin-bottom: 5px;"><b>Role:</b> {profile.get('role', 'Machine Learning Engineer')}</p>
                    <p style="margin-bottom: 5px;"><b>Joining Date:</b> {profile.get('joining_date', '15 August 2026')}</p>
                    <p style="margin-bottom: 0;"><b>Status:</b> <span style="color: #3b82f6; font-weight: bold;">Hired</span></p>
                </div>
            """, unsafe_allow_html=True)
        elif current_status == "Working on Project":
            st.markdown(f"""
                <div style="background: rgba(139, 92, 246, 0.1); border: 1px solid #8b5cf6; border-radius: 12px; padding: 20px; margin-bottom: 20px;">
                    <h3 style="color: #a78bfa; margin-top: 0; margin-bottom: 10px;">🚀 Congratulations!</h3>
                    <p style="margin-bottom: 15px; font-weight: bold; color: #a78bfa; font-size: 16px;">Your project has now started.</p>
                    <p style="margin-bottom: 5px;"><b>Project:</b> {profile.get('project', 'AI Analytics Portal')}</p>
                    <p style="margin-bottom: 5px;"><b>Organization:</b> {profile.get('company', 'TechCorp Solutions')}</p>
                    <p style="margin-bottom: 5px;"><b>Status:</b> <span style="color: #8b5cf6; font-weight: bold;">Working on Project</span></p>
                    <p style="margin-bottom: 0;"><b>Project Status:</b> <span style="color: #10b981; font-weight: bold;">Active</span></p>
                </div>
            """, unsafe_allow_html=True)
            
        # C. Project Invitations
        card_start()
        st.subheader("✉️ Project Invitations")
        invites, inv_status = get_invitations_api()
        pending_invites = [i for i in invites if i.get("status") == "Pending"] if inv_status == 200 else []
        accepted_invites = [i for i in invites if i.get("status") == "Accepted"] if inv_status == 200 else []
        
        if pending_invites:
            for invite in pending_invites:
                st.write(f"**Company:** {invite['organization_name']} | **Project:** {invite['project_name']}")
                st.write(f"**Role Requested:** `{invite['project_role']}`")
                
                ib1, ib2 = st.columns(2)
                with ib1:
                    if st.button("Accept Invitation", key=f"acc_{invite['_id']}", use_container_width=True):
                        res, stat = respond_invitation_api(invite["_id"], "Accept")
                        if stat == 200:
                            st.success("Invitation accepted!")
                            st.rerun()
                        else:
                            st.error(res.get("error"))
                with ib2:
                    if st.button("Decline Invitation", key=f"dec_{invite['_id']}", use_container_width=True):
                        res, stat = respond_invitation_api(invite["_id"], "Decline")
                        if stat == 200:
                            st.warning("Invitation declined.")
                            st.rerun()
                        else:
                            st.error(res.get("error"))
                st.markdown("---")
        elif accepted_invites:
            st.info("You have accepted project invitations. Waiting for HR to finalize hiring process...")
            for invite in accepted_invites:
                st.write(f"📍 **Project:** {invite['project_name']} ({invite['organization_name']}) — Status: `Accepted, Pending HR Hire`")
        else:
            st.write("No invitations pending at this time.")
        card_end()
        
        # D. MCQ Assessment & Premium Career Guidance
        card_start()
        st.subheader("🎯 Skill MCQ Assessment")
        
        if profile.get("assessment_passed"):
            st.success("✅ **Assessment Passed!** You are now marked as **Deployment Ready** and are visible inside the Recruiter Portal.")
            attempts, a_status = get_assessment_attempts_api()
            if a_status == 200 and attempts:
                for att in attempts:
                    st.caption(f"Attempt #{att['attempt_number']}: Score: {att['score']}% - Result: {att['status']} ({att['timestamp'][:10]})")
        else:
            res, status = get_assessment_api()
            
            if status == 403:
                # Locked (failed 3 times) - Auto-render Career Guidance portal here
                st.error("🔒 **Assessment Portal Locked (Maximum attempts reached).**")
                st.write("---")
                st.subheader("🎓 Career Guidance Roadmap")
                st.markdown("<p style='color: #fbbf24; font-weight: bold;'>🔓 Premium Career Guidance Unlocked (BRIDGE SKILL GAPS):</p>", unsafe_allow_html=True)
                
                # Weak Skills from insights
                st.write("**Identified Gaps:**")
                if i_status == 200 and insights.get("weaknesses"):
                    for gap in insights.get("weaknesses", []):
                        st.markdown(f"- 🚩 {gap}")
                else:
                    st.markdown("- 🚩 System Design")
                    st.markdown("- 🚩 Cloud Deployments")
                    
                # Roadmap Table
                st.write("**Structured 4-Week Plan:**")
                st.markdown("""
                | Week | Focus Area | Activities |
                | :--- | :--- | :--- |
                | **Week 1** | Syntax & Fundamentals | Code basic scripts and explore documentation. |
                | **Week 2** | Bridge Gaps | Focus on identified weaknesses. |
                | **Week 3** | System Architectures | Study API building and scaling rules. |
                | **Week 4** | Build & Deploy | Deploy project portfolio on GitHub. |
                """)
                
                # Seeded Courses
                st.write("**Recommended Courses:**")
                st.markdown("""
                * **IBM Python for Data Science and AI** (Coursera) — [Link](https://www.coursera.org/learn/python-for-applied-data-science-ai)
                * **Microsoft Certified: Azure Data Scientist Associate** (Microsoft Learn) — [Link](https://learn.microsoft.com/en-us/credentials/certifications/azure-data-scientist)
                * **The Ultimate MySQL Bootcamp** (Udemy) — [Link](https://www.udemy.com/course/the-ultimate-mysql-bootcamp-go-from-sql-beginner-to-expert/)
                """)
        attempts, a_status = get_assessment_attempts_api()
        user_attempts = [att for att in attempts if att.get("candidate_email") == profile.get("email")] if a_status == 200 else []
        passed_attempts = [att for att in user_attempts if att.get("status") == "Passed"]
        
        if passed_attempts:
            st.success("✔ Assessment Passed! You are now marked as **Deployment Ready** and are visible inside the Recruiter Portal.")
        else:
            attempts_left = 3 - len(user_attempts)
            if attempts_left > 0:
                ass_data, ass_status = get_assessment_api()
                if ass_status == 200 and ass_data:
                    st.caption(f"**Topic:** {ass_data.get('topic', 'Python')} | **Attempts Left:** {attempts_left}")
                    
                    user_answers = {}
                    for idx, q in enumerate(ass_data.get("questions", [])):
                        q_id = str(q.get("_id") or q.get("id") or f"q_{idx}")
                        st.markdown(f"**{q['question']}** ({q.get('difficulty', 'Medium')})")
                        user_answers[q_id] = st.radio(
                            "Options:",
                            q["options"],
                            key=f"mcq_{q_id}",
                            index=None
                        )
                        st.write("")
                        
                    if st.button("Submit Assessment", key="sub_mcq_btn", use_container_width=True):
                        if None in user_answers.values():
                            st.warning("Please answer all questions before submitting.")
                        else:
                            with st.spinner("Scoring assessment..."):
                                payload = {
                                    "assessment_id": ass_data.get("assessment_id"),
                                    "answers": user_answers
                                }
                                res, stat = submit_assessment_api(payload)
                                if stat == 200:
                                    if res.get("status") == "Passed":
                                        st.balloons()
                                        st.success(f"🎉 Congratulations! You Passed with score {res.get('score')}%!")
                                    else:
                                        st.error(f"Assessment score: {res.get('score')}%. Passing score is 70%. You have {res.get('attempts_left')} attempts left.")
                                    st.rerun()
                                else:
                                    st.error(res.get("error", "Failed to submit assessment."))
                else:
                    st.info("Assessment ready.")
            else:
                st.error("No assessment attempts remaining.")
        card_end()
        
        # E. Profile Editing (Collapsible container)
        with st.expander("📝 Edit Profile Details (Fully Editable)", expanded=False):
            phone_val = st.text_input("Phone Number", value=profile.get("phone", "+91"), key="prof_edit_phone")
            state_val = st.selectbox("State", INDIAN_STATES, index=INDIAN_STATES.index(profile.get("state")) if profile.get("state") in INDIAN_STATES else 0, key="prof_edit_state")
            domain_val = st.selectbox("Domain", DOMAINS, index=DOMAINS.index(profile.get("domain")) if profile.get("domain") in DOMAINS else 0, key="prof_edit_domain")
            experience_val = st.selectbox("Experience (Years)", [str(i) for i in range(11)], index=int(profile.get("experience", 0)) if int(profile.get("experience", 0)) <= 10 else 10, key="prof_edit_exp")
            
            db_skills = get_skills_api() or []
            cand_skills = profile.get("skills", [])
            all_skills_options = list(dict.fromkeys(db_skills + cand_skills + ["Python", "SQL", "Machine Learning", "Html5", "Css", "Figma Tool", "JavaScript", "React", "TypeScript", "UI/UX Design", "C++", "Java", "Docker", "AWS", "Git"]))
            
            skills_sel = st.multiselect("Select Skills", all_skills_options, default=cand_skills, key="prof_edit_skills_sel")
            skills_val = st.text_input("Skills List (Separate with commas, fully editable)", value=", ".join(skills_sel), key="prof_edit_skills_edit")
            
            langs_sel = st.multiselect("Spoken Languages", LANGUAGES, default=profile.get("spoken_languages", ["English"]), key="prof_edit_langs_sel")
            langs_val = st.text_input("Spoken Languages (Separate with commas, fully editable)", value=", ".join(langs_sel), key="prof_edit_langs_edit")
            
            linkedin_val = st.text_input("LinkedIn Profile URL", value=profile.get("linkedin", ""), key="prof_edit_li")
            github_val = st.text_input("GitHub Profile URL", value=profile.get("github", ""), key="prof_edit_gh")
            
            if st.button("Save Profile Changes", key="prof_edit_save_btn", use_container_width=True):
                s_list = [s.strip() for s in skills_val.split(",") if s.strip()]
                l_list = [l.strip() for l in langs_val.split(",") if l.strip()]
                
                if not phone_val.startswith("+91") or not phone_val[3:].isdigit():
                    st.error("Phone number must start with +91 followed by digits.")
                else:
                    data = {
                        "phone": phone_val,
                        "state": state_val,
                        "domain": domain_val,
                        "experience": int(experience_val),
                        "skills": s_list,
                        "spoken_languages": l_list,
                        "linkedin": linkedin_val,
                        "github": github_val
                    }
                    res, status = update_my_profile_api(data)
                    if status == 200:
                        st.success("Profile saved successfully!")
                        st.rerun()
                    else:
                        st.error(res.get("error", "Error saving profile."))
                        
        # F. Notifications Feed
        card_start()
        analytics, an_status = get_analytics_api()
        notifications = analytics.get("notifications", []) if an_status == 200 else []
        unread_count = len([n for n in notifications if not n.get("read")])
        
        st.subheader(f"🔔 Notification Feed ({unread_count} Unread)")
        if notifications:
            for notif in notifications:
                # Replace newlines with markdown breaks so they print formatted
                formatted_msg = notif['message'].replace("\n", "<br>")
                st.markdown(f"<div style='background: rgba(255,255,255,0.02); padding: 12px; border-radius: 6px; border: 1px solid rgba(255,255,255,0.05); margin-bottom: 10px;'>{formatted_msg}</div>", unsafe_allow_html=True)
                st.caption(f"Received: {notif['created_at'][:10]} {notif['created_at'][11:16]}")
                st.markdown("---")
        else:
            st.write("No system notifications.")
        card_end()
