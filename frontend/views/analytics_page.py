import streamlit as st
import pandas as pd
import altair as alt
from frontend.api.client import get_analytics_api
from frontend.components.ui import card_start, card_end, render_kpi, load_css

def show_analytics_page():
    load_css()
    
    st.markdown("<h1 style='color: #818cf8;'>📈 Talent & Recruitment Analytics</h1>", unsafe_allow_html=True)
    st.write("Real-time workforce stats and intelligence aggregated directly from MongoDB.")
    
    # 1. Fetch Analytics data
    res, status_code = get_analytics_api()
    if status_code != 200:
        st.error("Failed to load analytics data.")
        return
        
    kpis = res.get("kpis", {})
    
    # 2. KPI Cards
    col_kpi1, col_kpi2, col_kpi3, col_kpi4 = st.columns(4)
    with col_kpi1:
        render_kpi(f"{kpis.get('avg_resume_score', 0)}%", "Avg Resume Score")
    with col_kpi2:
        render_kpi(f"{kpis.get('avg_readiness_score', 0)}%", "Avg Readiness")
    with col_kpi3:
        render_kpi(str(kpis.get("total_candidates", 0)), "Total Candidates")
    with col_kpi4:
        render_kpi(str(kpis.get("total_projects", 0)), "Staffing Projects")
        
    col_left, col_right = st.columns(2)
    
    with col_left:
        # A. Hiring Funnel
        card_start()
        st.subheader("📊 Hiring Funnel Status")
        funnel_data = res.get("funnel", {})
        if funnel_data:
            funnel_df = pd.DataFrame(list(funnel_data.items()), columns=["Stage", "Count"])
            
            # Draw Altair bar chart
            chart = alt.Chart(funnel_df).mark_bar(color='#6366f1', cornerRadiusEnd=4).encode(
                x=alt.X('Count:Q', title='Count'),
                y=alt.Y('Stage:N', sort=list(funnel_data.keys()), title='Stage'),
                tooltip=['Stage', 'Count']
            ).properties(height=300)
            
            st.altair_chart(chart, use_container_width=True)
        else:
            st.write("No funnel data available.")
        card_end()
        
        # B. Skills Distribution
        card_start()
        st.subheader("🛠️ Top 10 In-Demand Skills")
        skills_data = res.get("top_skills", {})
        if skills_data:
            skills_df = pd.DataFrame(list(skills_data.items()), columns=["Skill", "Count"])
            
            chart = alt.Chart(skills_df).mark_bar(color='#a855f7', cornerRadiusEnd=4).encode(
                x=alt.X('Count:Q', title='Number of Candidates'),
                y=alt.Y('Skill:N', sort='-x', title='Skill'),
                tooltip=['Skill', 'Count']
            ).properties(height=300)
            
            st.altair_chart(chart, use_container_width=True)
        else:
            st.write("No skill data available.")
        card_end()
        
    with col_right:
        # C. Resume Score Distribution
        card_start()
        st.subheader("🎯 Resume Score Distribution")
        score_data = res.get("score_distribution", {})
        if score_data:
            score_df = pd.DataFrame(list(score_data.items()), columns=["Score Range", "Count"])
            
            chart = alt.Chart(score_df).mark_bar(color='#06b6d4', cornerRadiusEnd=4).encode(
                x=alt.X('Score Range:N', title='Score Range'),
                y=alt.Y('Count:Q', title='Number of Resumes'),
                tooltip=['Score Range', 'Count']
            ).properties(height=300)
            
            st.altair_chart(chart, use_container_width=True)
        else:
            st.write("No score data available.")
        card_end()
        
        # D. Domain Distribution
        card_start()
        st.subheader("💼 Domain/Role Distribution")
        domain_data = res.get("domain_distribution", {})
        if domain_data:
            domain_df = pd.DataFrame(list(domain_data.items()), columns=["Domain", "Count"])
            
            # Pie/Donut Chart using Altair
            chart = alt.Chart(domain_df).mark_arc(innerRadius=50).encode(
                theta=alt.Theta(field="Count", type="quantitative"),
                color=alt.Color(field="Domain", type="nominal", scale=alt.Scale(scheme='category20')),
                tooltip=["Domain", "Count"]
            ).properties(height=300)
            
            st.altair_chart(chart, use_container_width=True)
        else:
            st.write("No domain distribution data.")
        card_end()
        
    # E. Regional Candidate mapping
    card_start()
    st.subheader("🗺️ State-wise Candidate Distribution")
    state_data = res.get("state_distribution", {})
    if state_data:
        state_df = pd.DataFrame(list(state_data.items()), columns=["State", "Count"])
        
        chart = alt.Chart(state_df).mark_bar(color='#10b981', cornerRadiusEnd=4).encode(
            x=alt.X('State:N', sort='-y', title='State'),
            y=alt.Y('Count:Q', title='Number of Candidates'),
            tooltip=['State', 'Count']
        ).properties(height=250)
        
        st.altair_chart(chart, use_container_width=True)
    else:
        st.write("No state distribution data.")
    card_end()
