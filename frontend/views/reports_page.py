import streamlit as st
import requests
from frontend.api.client import get_headers, API_URL
from frontend.components.ui import card_start, card_end, load_css

def show_reports_page():
    load_css()
    
    st.markdown("<h1 style='color: #818cf8;'>📄 Recruitment & System Reports</h1>", unsafe_allow_html=True)
    st.write("Generate and download comprehensive system reports in Microsoft Excel or CSV format.")
    
    card_start()
    st.subheader("Select Report Type")
    
    report_type = st.selectbox("Report Name", [
        ("Candidate Profile Report", "candidate"),
        ("Project Staffing Report", "project"),
        ("Hiring & Invitations Report", "hiring"),
        ("Assessment Attempt Report", "assessment")
    ], format_func=lambda x: x[0], key="report_select")
    
    format_type = st.radio("Export Format", ["Excel (.xlsx)", "CSV (.csv)"], horizontal=True, key="report_format")
    
    # Map selection
    rep_key = report_type[1]
    fmt_key = "excel" if "Excel" in format_type else "csv"
    mime_type = (
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        if fmt_key == "excel"
        else "text/csv"
    )
    ext = "xlsx" if fmt_key == "excel" else "csv"
    
    if st.button("Generate & Download Report", use_container_width=True):
        with st.spinner("Compiling report data from MongoDB..."):
            try:
                # Trigger HTTP request directly to Flask endpoint to stream the file
                headers = get_headers()
                res = requests.get(
                    f"{API_URL}/analytics/reports/export?type={rep_key}&format={fmt_key}", 
                    headers=headers, 
                    stream=True
                )
                
                if res.status_code == 200:
                    st.success("Report generated successfully!")
                    
                    # Store file contents in bytes
                    file_bytes = res.content
                    filename = f"workforcex_{rep_key}_report.{ext}"
                    
                    st.download_button(
                        label=f"💾 Click to Save {filename}",
                        data=file_bytes,
                        file_name=filename,
                        mime=mime_type,
                        use_container_width=True
                    )
                else:
                    st.error(f"Error generating report: {res.json().get('error', 'Unknown error')}")
            except Exception as e:
                st.error(f"Failed to connect to backend service: {str(e)}")
                
    card_end()
    
    # Display details about the reports
    st.markdown("""
    ### ℹ️ Report Definitions
    * **Candidate Profile Report:** Complete details of registered professionals (contact information, state, domain, experience years, skills, resume score, status).
    * **Project Staffing Report:** Overview of corporate projects (hiring goals, resource counts filled, project status, joining dates, budget, priority).
    * **Hiring & Invitations Report:** Logs of invitations sent, pending, accepted, declined, and final hires.
    * **Assessment Attempt Report:** Candidate scores on dynamic MCQs, attempt numbers, passing state, and timestamps.
    """)
