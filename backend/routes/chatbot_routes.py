from flask import Blueprint, request, jsonify
from backend.utils.helpers import token_required
from backend.services.chatbot_service import ChatbotService
from backend.database.mongo import Database

chatbot_bp = Blueprint("chatbot", __name__)

@chatbot_bp.route("", methods=["POST"])
@token_required()
def chatbot_message():
    data = request.json or {}
    user_message = data.get("message", "").strip()
    
    if not user_message:
        return jsonify({"error": "Message is required."}), 400
        
    portal_type = request.user_role # "organization" or "professional"
    current_tab = data.get("current_tab", "")
    chat_history = data.get("chat_history", [])
    
    user_name = request.current_user.get("name", "User")
    user_email = request.current_user.get("email")
    
    db = Database.get_db()
    db_context = ""
    
    if portal_type == "organization":
        # Fetch active/existing projects for this organization recruiter
        projects = list(db["projects"].find({"organization_email": user_email}))
        projects_summary = []
        for p in projects:
            projects_summary.append(
                f"- Project: '{p.get('name')}' | Status: {p.get('status', 'Hiring')} | "
                f"Hired: {p.get('hired_count', 0)}/{p.get('resources_needed', 1)} | "
                f"Client: {p.get('client', 'N/A')} | Department: {p.get('department', 'N/A')}"
            )
        db_context = "Active Recruiter's Project List in DB:\n" + ("\n".join(projects_summary) if projects_summary else "- No active projects created yet.")
    else:
        # Fetch candidate profile details
        profile = db["professionals"].find_one({"email": user_email}) or {}
        invitations = list(db["invitations"].find({"candidate_email": user_email}))
        
        inv_summary = []
        for inv in invitations:
            inv_summary.append(
                f"- Project Invite: '{inv.get('project_name')}' | Role: '{inv.get('role_title')}' | Status: {inv.get('status')}"
            )
            
        db_context = (
            f"Candidate Profile Info in DB:\n"
            f"- Stage Status: {profile.get('status', 'Registered')}\n"
            f"- Resume Score: {profile.get('resume_readiness_index', 'Not Evaluated') or 'Not Evaluated'}%\n"
            f"- Extracted Skills: {', '.join(profile.get('skills', [])) if profile.get('skills') else 'None'}\n"
            f"Active Invitations list:\n" + ("\n".join(inv_summary) if inv_summary else "- No invitations received.")
        )

    # Call service layer to generate AI response
    response_text = ChatbotService.generate_response(
        portal_type=portal_type,
        current_tab=current_tab,
        chat_history=chat_history,
        user_message=user_message,
        user_name=user_name,
        db_context=db_context
    )
    
    return jsonify({"response": response_text})
