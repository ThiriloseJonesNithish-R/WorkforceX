import streamlit as st
import os

def load_css():
    css_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "styles", "custom.css"))
    with open(css_path) as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

def hide_sidebar():
    st.markdown("""
        <style>
            [data-testid="stSidebar"] {
                display: none !important;
            }
            [data-testid="collapsedControl"] {
                display: none !important;
            }
        </style>
    """, unsafe_allow_html=True)

def card_start():
    pass

def card_end():
    pass

def render_kpi(value, label):
    st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-val">{value}</div>
            <div class="kpi-label">{label}</div>
        </div>
    """, unsafe_allow_html=True)

def render_timeline(current_status):
    stages = [
        "Resume Uploaded",
        "Resume Analyzed",
        "Skills Extracted",
        "Assessment Completed",
        "Deployment Ready",
        "Invitation Received",
        "Invitation Accepted",
        "Hired",
        "Working on Project"
    ]
    
    labels = {
        "Resume Uploaded": "Uploaded",
        "Resume Analyzed": "Analyzed",
        "Skills Extracted": "Extracted",
        "Assessment Completed": "Assessed",
        "Deployment Ready": "Ready",
        "Invitation Received": "Invited",
        "Invitation Accepted": "Accepted",
        "Hired": "Hired",
        "Working on Project": "Deployed"
    }

    current_status_lower = current_status.lower() if current_status else ""
    
    # Custom status map indices
    status_map = {
        "registered": -1,
        "resume uploaded": 0,
        "resume analyzed": 1,
        "skills extracted": 2,
        "assessment completed": 3,
        "assessment locked": 3,
        "deployment ready": 4,
        "invitation pending": 5,
        "invitation accepted": 6,
        "waiting for hiring...": 6,
        "hired": 7,
        "working on project": 9
    }
    
    active_idx = status_map.get(current_status_lower, 0)
    
    # Render horizontal timeline
    st.markdown("<h3 style='margin-bottom: 20px;'>📍 Career Progress Timeline</h3>", unsafe_allow_html=True)
    
    # Compile the HTML string as a single compact line to prevent Markdown indentation parser bugs
    html_timeline = '<div style="display:flex;align-items:center;justify-content:space-between;width:100%;padding:15px 0;overflow-x:auto;min-width:600px;">'
    
    for idx, stage in enumerate(stages):
        label = labels[stage]
        
        # Determine status styling
        if idx < active_idx:
            bg_color = "#10b981"
            border_color = "#10b981"
            text_color = "#10b981"
            content = "✓"
            box_shadow = "0 0 10px rgba(16,185,129,0.4)"
        elif idx == active_idx:
            bg_color = "#3b82f6"
            border_color = "#3b82f6"
            text_color = "#60a5fa"
            content = str(idx + 1)
            box_shadow = "0 0 15px rgba(59,130,246,0.8)"
        else:
            bg_color = "#1f2937"
            border_color = "#4b5563"
            text_color = "#9ca3af"
            content = str(idx + 1)
            box_shadow = "none"
            
        # Append elements inline with no spaces or newlines
        html_timeline += f'<div style="display:flex;flex-direction:column;align-items:center;flex:1;position:relative;">'
        html_timeline += f'<div style="width:32px;height:32px;border-radius:50%;background-color:{bg_color};border:2px solid {border_color};color:white;display:flex;align-items:center;justify-content:center;font-weight:bold;font-size:14px;box-shadow:{box_shadow};z-index:2;transition:all 0.3s ease;">{content}</div>'
        html_timeline += f'<div style="margin-top:8px;font-size:11px;color:{text_color};font-weight:{"bold" if idx == active_idx else "normal"};text-align:center;">{label}</div>'
        html_timeline += '</div>'
        
        if idx < len(stages) - 1:
            line_color = "#10b981" if idx < active_idx else "#4b5563"
            html_timeline += f'<div style="height:3px;background-color:{line_color};flex-grow:1;margin-top:-20px;min-width:15px;z-index:1;"></div>'
            
    html_timeline += '</div>'
    st.markdown(html_timeline, unsafe_allow_html=True)
