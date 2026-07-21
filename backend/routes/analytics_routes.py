from flask import Blueprint, request, jsonify, send_file
from backend.database.mongo import Database
from backend.utils.helpers import token_required
import pandas as pd
import io
from datetime import datetime

analytics_bp = Blueprint("analytics", __name__)

@analytics_bp.route("/dashboard", methods=["GET"])
@token_required()
def get_analytics():
    db = Database.get_db()
    
    # 1. Hiring Funnel Counts
    pipeline_stages = ["Registered", "Resume Uploaded", "Resume Analyzed", "Skills Extracted", "Deployment Ready", "Invitation Pending", "Waiting for Hiring...", "Hired", "Working on Project"]
    funnel = {}
    for stage in pipeline_stages:
        funnel[stage] = db["professionals"].count_documents({"status": stage})
        
    # Cumulative funnel counts (optional but nice)
    # Since a candidate at stage "Hired" has passed previous stages, we can show actual status counts
    
    # 2. Resume Score Distribution
    scores_cursor = db["professionals"].find({}, {"resume_score": 1})
    scores = [doc.get("resume_score", 0) for doc in scores_cursor if doc.get("resume_score") is not None]
    
    score_dist = {"0-50": 0, "51-70": 0, "71-85": 0, "86-100": 0}
    for s in scores:
        if s <= 50:
            score_dist["0-50"] += 1
        elif s <= 70:
            score_dist["51-70"] += 1
        elif s <= 85:
            score_dist["71-85"] += 1
        else:
            score_dist["86-100"] += 1
            
    # 3. Top Skills
    all_prof_skills = db["professionals"].find({}, {"skills": 1})
    skill_counts = {}
    for doc in all_prof_skills:
        for s in doc.get("skills", []):
            skill_counts[s] = skill_counts.get(s, 0) + 1
            
    sorted_skills = sorted(skill_counts.items(), key=lambda x: x[1], reverse=True)[:10]
    top_skills = {k: v for k, v in sorted_skills}
    
    # 4. Project Status Counts
    projects = list(db["projects"].find({}, {"status": 1}))
    project_status = {"Hiring": 0, "Project Active": 0}
    for p in projects:
        status = p.get("status", "Hiring")
        project_status[status] = project_status.get(status, 0) + 1
        
    # 5. Domain Distribution
    domain_cursor = db["professionals"].find({}, {"domain": 1})
    domains = {}
    for doc in domain_cursor:
        dom = doc.get("domain", "Unknown")
        if dom:
            domains[dom] = domains.get(dom, 0) + 1
            
    # 6. State-wise candidates
    state_cursor = db["professionals"].find({}, {"state": 1})
    states = {}
    for doc in state_cursor:
        st = doc.get("state", "Tamil Nadu")
        if st:
            states[st] = states.get(st, 0) + 1
            
    # 7. Average Resume Score & Readiness
    avg_resume_score = 0
    avg_readiness_score = 0
    if scores:
        avg_resume_score = sum(scores) / len(scores)
        
    readiness_cursor = db["professionals"].find({}, {"readiness_score": 1})
    readiness_scores = [doc.get("readiness_score", 0) for doc in readiness_cursor if doc.get("readiness_score") is not None]
    if readiness_scores:
        avg_readiness_score = sum(readiness_scores) / len(readiness_scores)
        
    # 8. Notifications
    email = request.current_user["email"]
    notifications = list(db["notifications"].find({"recipient_email": email}).sort("created_at", -1).limit(10))
    for n in notifications:
        n["_id"] = str(n["_id"])
        
    return jsonify({
        "funnel": funnel,
        "score_distribution": score_dist,
        "top_skills": top_skills,
        "project_status": project_status,
        "domain_distribution": domains,
        "state_distribution": states,
        "kpis": {
            "avg_resume_score": round(avg_resume_score, 1),
            "avg_readiness_score": round(avg_readiness_score, 1),
            "total_candidates": db["professionals"].count_documents({}),
            "total_projects": db["projects"].count_documents({}),
            "hired_count": db["professionals"].count_documents({"status": {"$in": ["Hired", "Working on Project"]}})
        },
        "notifications": notifications
    })

@analytics_bp.route("/notifications/read", methods=["POST"])
@token_required()
def mark_notifications_read():
    db = Database.get_db()
    email = request.current_user["email"]
    db["notifications"].update_many({"recipient_email": email, "read": False}, {"$set": {"read": True}})
    return jsonify({"message": "Notifications marked as read."})

@analytics_bp.route("/reports/export", methods=["GET"])
@token_required()
def export_report():
    report_type = request.args.get("type", "candidate") # candidate, project, hiring, assessment
    format_type = request.args.get("format", "excel") # excel or csv
    db = Database.get_db()
    
    df = None
    filename = f"{report_type}_report_{datetime.now().strftime('%Y%m%d')}"
    
    if report_type == "candidate":
        # Extract candidates
        candidates = list(db["professionals"].find({}, {
            "name": 1, "email": 1, "phone": 1, "state": 1, "domain": 1, 
            "experience": 1, "skills": 1, "education": 1, "resume_score": 1, 
            "readiness_score": 1, "status": 1, "created_at": 1
        }))
        for c in candidates:
            c.pop("_id", None)
            c["skills"] = ", ".join(c.get("skills", []))
        df = pd.DataFrame(candidates) if candidates else pd.DataFrame(columns=["name", "email", "phone", "status"])
        
    elif report_type == "project":
        projects = list(db["projects"].find({}, {
            "name": 1, "organization_name": 1, "role": 1, "department": 1,
            "resources_needed": 1, "hired_count": 1, "status": 1, "priority": 1,
            "joining_date": 1
        }))
        for p in projects:
            p.pop("_id", None)
        df = pd.DataFrame(projects) if projects else pd.DataFrame(columns=["name", "role", "resources_needed", "status"])
        
    elif report_type == "hiring":
        invites = list(db["invitations"].find({}, {
            "project_name": 1, "project_role": 1, "organization_name": 1,
            "candidate_name": 1, "candidate_email": 1, "status": 1, "created_at": 1
        }))
        for invite in invites:
            invite.pop("_id", None)
        df = pd.DataFrame(invites) if invites else pd.DataFrame(columns=["project_name", "candidate_name", "status"])
        
    elif report_type == "assessment":
        attempts = list(db["assessment_attempts"].find({}, {
            "candidate_email": 1, "attempt_number": 1, "score": 1, "status": 1, "timestamp": 1
        }))
        for att in attempts:
            att.pop("_id", None)
        df = pd.DataFrame(attempts) if attempts else pd.DataFrame(columns=["candidate_email", "score", "status"])
        
    else:
        return jsonify({"error": "Invalid report type."}), 400
        
    # Export file
    if format_type == "csv":
        output = io.StringIO()
        df.to_csv(output, index=False)
        output.seek(0)
        return send_file(
            io.BytesIO(output.getvalue().encode('utf-8')),
            mimetype="text/csv",
            as_attachment=True,
            download_name=f"{filename}.csv"
        )
    else: # Excel
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name=report_type.capitalize())
        output.seek(0)
        return send_file(
            output,
            mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            as_attachment=True,
            download_name=f"{filename}.xlsx"
        )
