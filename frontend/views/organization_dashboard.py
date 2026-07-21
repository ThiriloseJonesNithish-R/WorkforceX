import streamlit as st
from datetime import datetime
from frontend.api.client import (
    list_projects_api,
    create_project_api,
    get_project_matches_api,
    invite_candidate_api,
    hire_candidate_api,
    get_invitations_api,
    get_skills_api,
    get_analytics_api
)
from frontend.components.ui import card_start, card_end, render_kpi, load_css

PRIORITIES = ["Low", "Medium", "High"]
WORK_MODES = ["Onsite", "Remote", "Hybrid"]

def show_organization_dashboard():
    load_css()
    
    st.markdown("<h1 style='color: #818cf8;'>🏢 Organization Portal</h1>", unsafe_allow_html=True)
    
    # 1. Fetch organization analytics
    projects, p_status = list_projects_api()
    invitations, i_status = get_invitations_api()
    
    if p_status != 200 or i_status != 200:
        st.error("Failed to load organization data.")
        return
        
    # Calculate counts dynamically from MongoDB synchronized lists
    candidates_invited = len(invitations)
    candidates_accepted = len([i for i in invitations if i.get("status") in ["Accepted", "Hired"]])
    candidates_hired = len([i for i in invitations if i.get("status") == "Hired"])
    active_projects = len([p for p in projects if p.get("status") == "Project Active"])
    
    # 2. Display KPI Cards
    col_kpi1, col_kpi2, col_kpi3, col_kpi4 = st.columns(4)
    with col_kpi1:
        render_kpi(str(candidates_invited), "Candidates Invited")
    with col_kpi2:
        render_kpi(str(candidates_accepted), "Candidates Accepted")
    with col_kpi3:
        render_kpi(str(candidates_hired), "Candidates Hired")
    with col_kpi4:
        render_kpi(str(active_projects), "Active Projects")
        
    # Layout tabs
    tab1, tab2, tab3 = st.tabs(["📋 Projects & AI Match", "➕ Create New Project", "✉️ Invitation Manager"])
    
    # ------------------ Tab 1: Projects & AI Candidate Matching ------------------
    with tab1:
        projects, p_status = list_projects_api()
        
        if p_status == 200 and projects:
            st.subheader("Select Project to run AI Matching:")
            
            project_names = [p["name"] for p in projects]
            saved_proj = st.query_params.get("selected_project")
            default_idx = project_names.index(saved_proj) if saved_proj in project_names else 0
            selected_proj_name = st.selectbox("Select Project", project_names, index=default_idx, key="org_proj_select")
            st.query_params["selected_project"] = selected_proj_name
            
            # Find selected project doc
            selected_proj = next(p for p in projects if p["name"] == selected_proj_name)
            
            col_p1, col_p2 = st.columns([1, 2])
            with col_p1:
                card_start()
                st.markdown(f"### 📄 {selected_proj['name']}")
                st.write(f"**Client:** {selected_proj.get('client', 'N/A')}")
                st.write(f"**Department:** {selected_proj.get('department', 'N/A')}")
                st.write(f"**Role:** {selected_proj['role']}")
                st.write(f"**Staffing Goal:** `{selected_proj['hired_count']} / {selected_proj['resources_needed']} filled`")
                
                # Progress Bar
                progress = selected_proj['hired_count'] / selected_proj['resources_needed']
                st.progress(progress)
                
                status_color = "green" if selected_proj['status'] == "Project Active" else "orange"
                st.markdown(f"**Status:** <span style='color:{status_color}; font-weight:bold;'>{selected_proj['status']}</span>", unsafe_allow_html=True)
                st.write(f"**Priority:** {selected_proj.get('priority', 'Medium')}")
                st.write(f"**Budget:** {selected_proj.get('budget', 'N/A')}")
                st.write(f"**Duration:** {selected_proj.get('duration', 'N/A')}")
                st.write(f"**Work Mode:** {selected_proj.get('work_mode', 'Onsite')}")
                st.write(f"**Primary Skills:** {', '.join(selected_proj.get('primary_skills', []))}")
                card_end()
            
            with col_p2:
                st.markdown(f"### 🤖 Top AI Matched Candidates")
                matches, m_status = get_project_matches_api(selected_proj["_id"])
                
                if m_status == 200 and matches:
                    # Fetch all invitations for project to check invitation states
                    invitations, i_status = get_invitations_api()
                    proj_invites = [i for i in invitations if i.get("project_id") == selected_proj["_id"]] if i_status == 200 else []
                    
                    # 1. Check if currently viewing a detailed candidate profile
                    if st.session_state.get("viewing_candidate"):
                        cand = st.session_state["viewing_candidate"]
                        proj = st.session_state["viewing_candidate_project"]
                        score = cand["match_score"]
                        
                        # Find current invitation status specifically
                        cand_invite = next((i for i in proj_invites if i["candidate_email"] == cand["candidate_email"]), None)
                        
                        # Return to matching candidate list
                        if st.button("← Back to Candidates List", key="ats_back_btn_top"):
                            st.session_state["viewing_candidate"] = None
                            st.session_state["viewing_candidate_project"] = None
                            st.rerun()
                            
                        # Determine current status badge
                        if not cand_invite:
                            status_badge = "Deployment Ready"
                            badge_color = "#10b981" # Green
                        else:
                            invite_status = cand_invite.get("status")
                            if invite_status == "Pending":
                                status_badge = "Pending"
                                badge_color = "#fbbf24" # Yellow
                            elif invite_status == "Accepted":
                                status_badge = "Accepted"
                                badge_color = "#3b82f6" # Blue
                            elif invite_status == "Hired":
                                # Show active or hired based on project status
                                if proj.get("status") == "Project Active" or cand.get("status") == "Working on Project":
                                    status_badge = "Working on Project"
                                    badge_color = "#8b5cf6" # Purple
                                else:
                                    status_badge = "Hired"
                                    badge_color = "#10b981" # Green
                            elif invite_status == "Declined":
                                status_badge = "Declined"
                                badge_color = "#ef4444" # Red
                            else:
                                status_badge = invite_status
                                badge_color = "#6b7280"
                                
                        src_type = cand.get("source", "Registered")
                        is_registered_cand = (src_type != "Database")
                        src_badge = "Registered Candidate" if is_registered_cand else "Database Candidate"
                        src_color = "#059669" if is_registered_cand else "#3b82f6"

                        # Profile Header Card
                        st.markdown(f"""
                            <div style="background: rgba(255,255,255,0.03); border: 1px solid rgba(255,255,255,0.08); border-radius: 12px; padding: 20px; margin-bottom: 25px; display: flex; justify-content: space-between; align-items: center;">
                                <div>
                                    <h2 style="margin: 0; color: white;">{cand['candidate_name']} <span style="background-color: {src_color}; color: white; padding: 3px 10px; border-radius: 12px; font-size: 12px; font-weight: bold; vertical-align: middle; margin-left: 10px;">{src_badge}</span></h2>
                                    <p style="margin: 5px 0 0 0; color: #9ca3af; font-size: 14px;">{cand.get('domain', 'Candidate Domain')} | Experience: {cand.get('candidate_experience', cand.get('experience', 0))} Years</p>
                                </div>
                                <div style="background-color: {badge_color}; color: white; padding: 6px 16px; border-radius: 20px; font-weight: bold; font-size: 13px; box-shadow: 0 0 10px {badge_color}44;">
                                    {status_badge}
                                </div>
                            </div>
                        """, unsafe_allow_html=True)
                        
                        # ATS Two-Column Layout
                        ats_left, ats_right = st.columns([1.2, 1])
                        
                        with ats_left:
                            # 1. Personal & Professional Details Card
                            card_start()
                            st.subheader("📋 Personal & Professional Details")
                            st.write(f"**Full Name:** {cand['candidate_name']}")
                            st.write(f"**Email Address:** {cand['candidate_email']}")
                            st.write(f"**Phone Number:** {cand.get('phone', 'N/A')}")
                            st.write(f"**State / Location:** {cand.get('state', 'N/A')}")
                            st.write("---")
                            st.write(f"**Career Objective:**\n*{cand.get('career_objective', 'To utilize technical skills to drive project milestones and platform efficiency.')}*")
                            st.write("---")
                            st.write(f"**Education:** {cand.get('education', 'Bachelor\'s Degree')}")
                            st.write(f"**Certifications:** {', '.join(cand.get('certifications', [])) if cand.get('certifications') else 'None Listed'}")
                            st.write(f"**Skills:** {', '.join(cand.get('skills', [])) if cand.get('skills') else 'None Listed'}")
                            st.write(f"**Spoken Languages:** {', '.join(cand.get('spoken_languages', [])) if cand.get('spoken_languages') else 'English'}")
                            card_end()
                            
                            # 2. Mock Projects List Card
                            card_start()
                            st.subheader("💼 Featured Engineering Projects")
                            st.write("• **Project 1: Core System Architecture Implementation**")
                            st.caption("Engineered a multi-threaded data broker pipeline, boosting throughput performance by 40%.")
                            st.write("• **Project 2: Legacy Infrastructure Re-architecting**")
                            st.caption("Migrated relational databases to MongoDB, scaling document store querying capacity.")
                            card_end()
                            
                            # 3. Resume File Download View
                            card_start()
                            st.subheader("🔗 Links & Attachments")
                            st.write("**Resume Attachment:** `Candidate_Resume_CV.pdf` (540 KB)")
                            st.button("📥 Download Resume File", key="ats_resume_fake_dl", use_container_width=True)
                            
                            st.write("")
                            l_col, g_col = st.columns(2)
                            with l_col:
                                if cand.get("linkedin"):
                                    st.markdown(f"[🔗 Candidate LinkedIn Profile]({cand['linkedin']})")
                            with g_col:
                                if cand.get("github"):
                                    st.markdown(f"[🔗 Candidate GitHub Portfolio]({cand['github']})")
                            card_end()
                            
                        with ats_right:
                            # 1. AI Analysis Scores Card
                            card_start()
                            st.subheader("🎯 AI Match & Analysis Scores")
                            st.metric("AI Compatibility Match Score", f"{score}%")
                            
                            sc_col1, sc_col2 = st.columns(2)
                            with sc_col1:
                                st.write(f"**Resume Score:** `{cand['resume_score']}%`")
                                st.write(f"**Skill Match Score:** `{cand['skill_match_score']}%`")
                            with sc_col2:
                                st.write(f"**Assessment Score:** `{cand['assessment_score']}%`")
                                st.write(f"**Experience Match:** `High`")
                            card_end()
                            
                            # 2. Resume Insights Card
                            card_start()
                            st.subheader("💡 AI Resume Insights")
                            
                            # Strengths
                            st.markdown("<span style='color: #10b981; font-weight: bold;'>Strengths:</span>", unsafe_allow_html=True)
                            for strength in cand.get("strengths", ["Python", "SQL", "Machine Learning"]):
                                st.markdown(f"- {strength}")
                                
                            # Weaknesses
                            st.write("")
                            st.markdown("<span style='color: #fbbf24; font-weight: bold;'>Weaknesses:</span>", unsafe_allow_html=True)
                            for weakness in cand.get("weaknesses", ["Cloud Computing", "Advanced Statistics"]):
                                st.markdown(f"- {weakness}")
                                
                            # Recommendation text box
                            st.write("")
                            st.markdown("**ATS Recommendation:**")
                            st.info(cand.get("recommendation", f"Highly suitable for the {cand.get('domain')} role."))
                            card_end()
                            
                        # 3. Action Buttons Section (ATS bottom action center)
                        card_start()
                        st.subheader("⚡ ATS Action Center")
                        
                        if not cand_invite:
                            # Status = Deployment Ready -> Send Invitation
                            if st.button("📧 Send Invitation", key=f"ats_invite_btn_{proj['_id']}", use_container_width=True):
                                res, stat = invite_candidate_api(proj["_id"], cand["candidate_email"])
                                if stat == 200:
                                    st.success("Invitation sent successfully!")
                                    st.rerun()
                                else:
                                    st.error(res.get("error"))
                        else:
                            invite_status = cand_invite.get("status")
                            
                            if invite_status == "Pending":
                                # Status = Pending -> Display invitation sent text, disable button
                                st.warning("✉️ Invitation Sent (Pending Response)")
                                st.button("📧 Send Invitation", disabled=True, key="ats_invite_disabled", use_container_width=True)
                            elif invite_status == "Accepted":
                                # Status = Accepted -> Show Hire Candidate button
                                st.success("🎉 Candidate Accepted Invitation!")
                                if st.button("🤝 Hire Candidate", key=f"ats_hire_btn_{proj['_id']}", use_container_width=True):
                                    res, stat = hire_candidate_api(proj["_id"], cand["candidate_email"])
                                    if stat == 200:
                                        st.balloons()
                                        st.success("✔ Candidate Hired")
                                        st.rerun()
                                    else:
                                        st.error(res.get("error"))
                            elif invite_status == "Hired":
                                # Status = Hired -> Display Hired checkmark
                                st.success("✔ Hired")
                            elif invite_status == "Declined":
                                # Status = Declined -> Show badge & Invite Another Candidate button
                                st.error("❌ Candidate Declined Invitation")
                                if st.button("Invite Another Candidate", key="ats_invite_another", use_container_width=True):
                                    st.session_state["viewing_candidate"] = None
                                    st.session_state["viewing_candidate_project"] = None
                                    st.rerun()
                        card_end()
                        
                        # Back Button at bottom
                        if st.button("← Back to Candidates List", key="ats_back_btn_bottom"):
                            st.session_state["viewing_candidate"] = None
                            st.session_state["viewing_candidate_project"] = None
                            st.rerun()
                            
                    else:
                        # 2. Render normal matching candidate list
                        for idx, cand in enumerate(matches):
                            score = cand["match_score"]
                            cand_invite = next((i for i in proj_invites if i["candidate_email"] == cand["candidate_email"]), None)
                            
                            # Determine current invitation status label for row display
                            status_label = "Deployment Ready"
                            if cand_invite:
                                invite_status = cand_invite.get("status")
                                if invite_status == "Pending":
                                    status_label = "Pending"
                                elif invite_status == "Accepted":
                                    status_label = "Invitation Accepted"
                                elif invite_status == "Hired":
                                    status_label = "Hired"
                                elif invite_status == "Declined":
                                    status_label = "Declined"
                                    
                            src_type = cand.get("source", "Registered")
                            is_registered_cand = (src_type != "Database")
                            src_badge = "Registered Candidate" if is_registered_cand else "Database Candidate"
                            src_color = "#059669" if is_registered_cand else "#3b82f6"

                            # Candidate Card Row
                            st.markdown(f"""
                                <div style="background: rgba(255,255,255,0.02); border: 1px solid rgba(255,255,255,0.05); border-radius: 8px; padding: 15px; margin-bottom: 12px; display: flex; justify-content: space-between; align-items: center;">
                                    <div>
                                        <b style="color: white; font-size: 15px;">{cand['candidate_name']}</b>
                                        <span style="background-color: {src_color}; color: white; padding: 2px 8px; border-radius: 10px; font-size: 10px; font-weight: bold; margin-left: 8px;">{src_badge}</span>
                                        <div style="font-size: 12px; color: #9ca3af; margin-top: 4px;">AI Match: <b>{score}%</b> | Status: <b>{status_label}</b></div>
                                    </div>
                                </div>
                            """, unsafe_allow_html=True)
                            
                            # Action buttons
                            col_act1, col_act2 = st.columns(2)
                            with col_act1:
                                if st.button(f"🔍 View Candidate Profile", key=f"view_profile_{idx}_{cand['candidate_email']}", use_container_width=True):
                                    st.session_state["viewing_candidate"] = cand
                                    st.session_state["viewing_candidate_project"] = selected_proj
                                    st.rerun()
                            with col_act2:
                                if status_label == "Invitation Accepted":
                                    if st.button("🤝 Hire Candidate", key=f"quick_hire_{idx}_{cand['candidate_email']}", use_container_width=True):
                                        res, stat = hire_candidate_api(selected_proj["_id"], cand["candidate_email"])
                                        if stat == 200:
                                            st.balloons()
                                            st.success("✔ Candidate Hired")
                                            st.rerun()
                                        else:
                                            st.error(res.get("error"))
                            st.write("")
                else:
                    st.write("No 'Deployment Ready' candidates match your project requirements. Make sure candidates have completed and passed their assessments.")
        else:
            st.info("No active projects found. Navigate to the 'Create New Project' tab to launch a project.")
            
    # ------------------ Tab 2: Create Project ------------------
    with tab2:
        card_start()
        st.subheader("Create a New Staffing Project")
        
        db_skills = get_skills_api()
        if not db_skills:
            db_skills = ["Python", "SQL", "Machine Learning", "Deep Learning", "Power BI", "Cybersecurity", "Java", "C++", "Docker", "AWS", "Git"]
            
        proj_name = st.text_input("Project Name *", key="new_proj_name")
        client = st.text_input("Client Client Name", key="new_proj_client")
        dept = st.text_input("Department / Business Unit", key="new_proj_dept")
        role = st.text_input("Job Role * (e.g. Data Scientist, AI Engineer)", key="new_proj_role")
        desc = st.text_area("Job Description", key="new_proj_desc")
        
        col_f1, col_f2 = st.columns(2)
        with col_f1:
            exp_req = st.selectbox("Required Experience (Min Years)", [str(i) for i in range(11)], key="new_proj_exp")
            primary_skills = st.multiselect("Primary Required Skills", db_skills, key="new_proj_pskills")
            secondary_skills = st.multiselect("Secondary Skills", db_skills, key="new_proj_sskills")
            certifications = st.multiselect("Required Certifications", ["AWS Certified", "Google Cloud", "Microsoft Certified", "Azure", "PMP", "CISSP", "CEH", "Google ML", "Deep Learning Specialization"], key="new_proj_certs")
            budget = st.text_input("Budget (e.g., $100K or Not Disclosed)", key="new_proj_budget")
            
        with col_f2:
            duration = st.text_input("Project Duration (e.g., 6 Months, 1 Year)", key="new_proj_duration")
            joining_date = st.date_input("Target Joining Date", value=datetime.today(), key="new_proj_joining")
            priority = st.selectbox("Priority Level", PRIORITIES, index=1, key="new_proj_priority")
            resources = st.number_input("Resources Needed (Staff Count) *", min_value=1, max_value=20, value=1, key="new_proj_resources")
            work_mode = st.selectbox("Work Mode", WORK_MODES, key="new_proj_work_mode")
            
        if st.button("Launch Project & Run Matcher", use_container_width=True):
            if not proj_name or not role:
                st.error("Project Name and Role are required fields.")
            else:
                data = {
                    "name": proj_name,
                    "client": client,
                    "department": dept,
                    "role": role,
                    "job_description": desc,
                    "experience": int(exp_req),
                    "primary_skills": primary_skills,
                    "secondary_skills": secondary_skills,
                    "certifications": certifications,
                    "budget": budget,
                    "duration": duration,
                    "joining_date": joining_date.strftime("%Y-%m-%d"),
                    "priority": priority,
                    "resources_needed": int(resources),
                    "work_mode": work_mode
                }
                res, status = create_project_api(data)
                if status == 201:
                    st.success("Project launched successfully! Redirecting to matcher...")
                    st.rerun()
                else:
                    st.error(res.get("error", "Error creating project."))
        card_end()
        
    # ------------------ Tab 3: Invitation Manager ------------------
    with tab3:
        st.subheader("All Project Invitations Sent")
        invites, inv_status = get_invitations_api()
        
        if inv_status == 200 and invites:
            for idx, inv in enumerate(invites):
                card_start()
                c_status = inv["status"]
                
                # Header showing Project & Candidate Name
                st.markdown(f"#### 📄 {inv['project_name']} — {inv['project_role']}")
                st.write(f"**Candidate Name:** {inv['candidate_name']} ({inv['candidate_email']})")
                st.write(f"**Sent Date:** {inv['created_at'][:10]} | **Status:** `{c_status}`")
                
                # If status is Accepted, render the Hire Candidate button!
                if c_status == "Accepted":
                    st.success("🎉 Candidate Accepted Invitation!")
                    if st.button("🤝 Hire Candidate", key=f"mgr_hire_{idx}_{inv['project_id']}_{inv['candidate_email']}", use_container_width=True):
                        res, stat = hire_candidate_api(inv["project_id"], inv["candidate_email"])
                        if stat == 200:
                            st.balloons()
                            st.success("✔ Candidate Hired")
                            st.rerun()
                        else:
                            st.error(res.get("error"))
                elif c_status == "Hired":
                    st.success("✔ Hired")
                elif c_status == "Pending":
                    st.info("✉️ Invitation Sent (Pending Response)")
                elif c_status == "Declined":
                    st.error("❌ Candidate Declined Invitation")
                    
                card_end()
                st.write("")
        else:
            st.write("No invitations sent yet.")
            
        # Organization Notifications Box
        card_start()
        st.subheader("🔔 HR Notifications Feed")
        analytics, status_code = get_analytics_api()
        if status_code == 200 and analytics.get("notifications"):
            for notif in analytics["notifications"]:
                st.markdown(f"📝 {notif['message']}")
                st.caption(f"{notif['created_at'][:10]} {notif['created_at'][11:16]}")
                st.markdown("---")
        else:
            st.write("No notifications.")
        card_end()
