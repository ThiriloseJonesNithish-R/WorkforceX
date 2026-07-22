import requests
import streamlit as st

API_URL = "http://localhost:5000/api"

def get_headers():
    headers = {}
    if "token" in st.session_state and st.session_state["token"]:
        headers["Authorization"] = f"Bearer {st.session_state['token']}"
    return headers

# Authentication
def login_professional_api(username, password):
    try:
        res = requests.post(f"{API_URL}/auth/login-professional", json={"username": username, "password": password})
        return res.json(), res.status_code
    except Exception as e:
        return {"error": f"Connection error: {str(e)}"}, 500

def login_organization_api(username, password):
    try:
        res = requests.post(f"{API_URL}/auth/login-organization", json={"username": username, "password": password})
        return res.json(), res.status_code
    except Exception as e:
        return {"error": f"Connection error: {str(e)}"}, 500

def register_professional_api(data):
    try:
        res = requests.post(f"{API_URL}/auth/register-professional", json=data)
        return res.json(), res.status_code
    except Exception as e:
        return {"error": f"Connection error: {str(e)}"}, 500

def register_organization_api(data):
    try:
        res = requests.post(f"{API_URL}/auth/register-organization", json=data)
        return res.json(), res.status_code
    except Exception as e:
        return {"error": f"Connection error: {str(e)}"}, 500

def forgot_password_api(username):
    try:
        res = requests.post(f"{API_URL}/auth/forgot-password", json={"username": username})
        return res.json(), res.status_code
    except Exception as e:
        return {"error": f"Connection error: {str(e)}"}, 500

# Professional Profile
def get_my_profile_api():
    try:
        res = requests.get(f"{API_URL}/profile/me", headers=get_headers())
        return res.json(), res.status_code
    except Exception as e:
        return {"error": f"Connection error: {str(e)}"}, 500

def update_my_profile_api(data):
    try:
        res = requests.put(f"{API_URL}/profile/me", json=data, headers=get_headers())
        return res.json(), res.status_code
    except Exception as e:
        return {"error": f"Connection error: {str(e)}"}, 500

def upload_resume_api(file_bytes, filename):
    try:
        files = {"file": (filename, file_bytes, "application/pdf")}
        res = requests.post(f"{API_URL}/profile/upload-resume", files=files, headers=get_headers())
        return res.json(), res.status_code
    except Exception as e:
        return {"error": f"Connection error: {str(e)}"}, 500

def get_resume_insights_api():
    try:
        res = requests.get(f"{API_URL}/profile/resume-insights", headers=get_headers())
        return res.json(), res.status_code
    except Exception as e:
        return {"error": f"Connection error: {str(e)}"}, 500

def get_skills_api():
    try:
        res = requests.get(f"{API_URL}/profile/skills")
        if res.status_code == 200:
            return res.json().get("skills", [])
        return []
    except Exception:
        return []

# Assessments
def get_assessment_api():
    try:
        res = requests.get(f"{API_URL}/assessment/generate", headers=get_headers())
        return res.json(), res.status_code
    except Exception as e:
        return {"error": f"Connection error: {str(e)}"}, 500

def submit_assessment_api(answers):
    try:
        res = requests.post(f"{API_URL}/assessment/submit", json={"answers": answers}, headers=get_headers())
        return res.json(), res.status_code
    except Exception as e:
        return {"error": f"Connection error: {str(e)}"}, 500

def get_assessment_attempts_api():
    try:
        res = requests.get(f"{API_URL}/assessment/attempts", headers=get_headers())
        return res.json(), res.status_code
    except Exception as e:
        return {"error": f"Connection error: {str(e)}"}, 500

# Projects & Matches
def create_project_api(data):
    try:
        res = requests.post(f"{API_URL}/project/create", json=data, headers=get_headers())
        return res.json(), res.status_code
    except Exception as e:
        return {"error": f"Connection error: {str(e)}"}, 500

def list_projects_api():
    try:
        res = requests.get(f"{API_URL}/project/list", headers=get_headers())
        return res.json(), res.status_code
    except Exception as e:
        return {"error": f"Connection error: {str(e)}"}, 500

@st.cache_data(ttl=15, show_spinner=False)
def get_project_matches_api(project_id, role_id=None):
    try:
        params = {"role_id": role_id} if role_id else {}
        res = requests.get(f"{API_URL}/project/{project_id}/matches", params=params, headers=get_headers())
        return res.json(), res.status_code
    except Exception as e:
        return {"error": f"Connection error: {str(e)}"}, 500

def invite_candidate_api(project_id, candidate_email, role_id=None):
    try:
        payload = {
            "project_id": project_id,
            "candidate_email": candidate_email
        }
        if role_id:
            payload["role_id"] = role_id
        res = requests.post(f"{API_URL}/project/invite", json=payload, headers=get_headers())
        st.cache_data.clear()
        return res.json(), res.status_code
    except Exception as e:
        return {"error": f"Connection error: {str(e)}"}, 500

def reject_candidate_api(project_id, candidate_email, role_id=None):
    try:
        payload = {
            "project_id": project_id,
            "candidate_email": candidate_email
        }
        if role_id:
            payload["role_id"] = role_id
        res = requests.post(f"{API_URL}/project/reject", json=payload, headers=get_headers())
        st.cache_data.clear()
        return res.json(), res.status_code
    except Exception as e:
        return {"error": f"Connection error: {str(e)}"}, 500

def get_invitations_api():
    try:
        res = requests.get(f"{API_URL}/project/invitations", headers=get_headers())
        return res.json(), res.status_code
    except Exception as e:
        return {"error": f"Connection error: {str(e)}"}, 500

def respond_invitation_api(invite_id, response):
    try:
        res = requests.post(f"{API_URL}/project/invitation/{invite_id}/respond", json={
            "response": response
        }, headers=get_headers())
        st.cache_data.clear()
        return res.json(), res.status_code
    except Exception as e:
        return {"error": f"Connection error: {str(e)}"}, 500

def hire_candidate_api(project_id, candidate_email, role_id=None):
    try:
        payload = {
            "candidate_email": candidate_email
        }
        if role_id:
            payload["role_id"] = role_id
        res = requests.post(f"{API_URL}/project/{project_id}/hire", json=payload, headers=get_headers())
        st.cache_data.clear()
        return res.json(), res.status_code
    except Exception as e:
        return {"error": f"Connection error: {str(e)}"}, 500

# Analytics & Notifications
def get_analytics_api():
    try:
        res = requests.get(f"{API_URL}/analytics/dashboard", headers=get_headers())
        return res.json(), res.status_code
    except Exception as e:
        return {"error": f"Connection error: {str(e)}"}, 500

def mark_notifications_read_api():
    try:
        res = requests.post(f"{API_URL}/analytics/notifications/read", headers=get_headers())
        return res.json(), res.status_code
    except Exception as e:
        return {"error": f"Connection error: {str(e)}"}, 500

def send_chatbot_message_api(message, current_tab="", chat_history=None):
    try:
        payload = {
            "message": message,
            "current_tab": current_tab,
            "chat_history": chat_history or []
        }
        res = requests.post(f"{API_URL}/chatbot", json=payload, headers=get_headers())
        return res.json(), res.status_code
    except Exception as e:
        return {"error": f"Connection error: {str(e)}"}, 500
