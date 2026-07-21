from flask import Blueprint, request, jsonify
from backend.database.mongo import Database
from backend.utils.helpers import token_required
from backend.services.matching_service import get_top_matched_candidates
from bson.objectid import ObjectId
from datetime import datetime

project_bp = Blueprint("project", __name__)

@project_bp.route("/create", methods=["POST"])
@token_required("organization")
def create_project():
    data = request.json
    db = Database.get_db()
    org_email = request.current_user["email"]
    org_name = request.current_user["name"]
    
    # Required parameters
    name = data.get("name", "").strip()
    role = data.get("role", "").strip()
    resources_needed = data.get("resources_needed", 1)
    
    if not name or not role:
        return jsonify({"error": "Project Name and Role are required."}), 400
        
    try:
        resources_needed = int(resources_needed)
    except ValueError:
        resources_needed = 1

    project_doc = {
        "organization_email": org_email,
        "organization_name": org_name,
        "name": name,
        "client": data.get("client", "").strip(),
        "department": data.get("department", "").strip(),
        "role": role,
        "job_description": data.get("job_description", "").strip(),
        "experience": data.get("experience", 0),
        "primary_skills": data.get("primary_skills", []),
        "secondary_skills": data.get("secondary_skills", []),
        "certifications": data.get("certifications", []),
        "budget": data.get("budget", ""),
        "duration": data.get("duration", ""),
        "joining_date": data.get("joining_date", ""),
        "priority": data.get("priority", "Medium"),
        "resources_needed": resources_needed,
        "work_mode": data.get("work_mode", "Onsite"),
        "hired_count": 0,
        "status": "Hiring", # Initial status: Hiring
        "created_at": datetime.utcnow()
    }
    
    result = db["projects"].insert_one(project_doc)
    
    # Log Activity
    db["activity_logs"].insert_one({
        "user_email": org_email,
        "action": f"Created Project: {name}",
        "timestamp": datetime.utcnow()
    })
    
    # Send system notification
    db["notifications"].insert_one({
        "recipient_email": org_email,
        "message": f"Project '{name}' created successfully. AI matching is ready.",
        "read": False,
        "created_at": datetime.utcnow()
    })
    
    return jsonify({
        "message": "Project created successfully!",
        "project_id": str(result.inserted_id)
    }), 201

@project_bp.route("/list", methods=["GET"])
@token_required("organization")
def list_projects():
    db = Database.get_db()
    org_email = request.current_user["email"]
    
    projects = list(db["projects"].find({"organization_email": org_email}))
    for proj in projects:
        proj["_id"] = str(proj["_id"])
        
    return jsonify(projects)

@project_bp.route("/<project_id>/matches", methods=["GET"])
@token_required("organization")
def get_project_matches(project_id):
    db = Database.get_db()
    try:
        project = db["projects"].find_one({"_id": ObjectId(project_id)})
    except Exception:
        return jsonify({"error": "Invalid Project ID format."}), 400
        
    if not project:
        return jsonify({"error": "Project not found."}), 404
        
    # Get top 5 matches
    matches = get_top_matched_candidates(project)
    
    # Enrich matches with candidate basic profile details
    enriched_matches = []
    for m in matches:
        cand = db["professionals"].find_one({"email": m["candidate_email"]})
        if cand:
            # Personal & Professional Information
            m["source"] = cand.get("source", m.get("source", "Registered"))
            m["username"] = cand.get("username")
            m["phone"] = cand.get("phone")
            m["state"] = cand.get("state")
            m["education"] = cand.get("education")
            m["linkedin"] = cand.get("linkedin")
            m["github"] = cand.get("github")
            m["spoken_languages"] = cand.get("spoken_languages", ["English"])
            m["certifications"] = cand.get("certifications", [])
            m["skills"] = cand.get("skills", [])
            m["experience"] = cand.get("experience", 0)
            m["domain"] = cand.get("domain", "")
            m["career_objective"] = cand.get("career_objective", "To leverage my skills in domain execution, software quality, and cloud architectures to support rapid scaling.")
            
            # AI Insights & Resume Scores
            scores = db["resume_scores"].find_one({"candidate_email": cand["email"]})
            if scores:
                m["strengths"] = scores.get("strengths", [])
                m["weaknesses"] = scores.get("weaknesses", [])
                # Formulate suitable ATS recommendation matching the user prompt structure
                slist = ", ".join(scores.get("strengths", [])[:3])
                m["recommendation"] = f"This candidate is highly suitable for the {cand.get('domain')} role due to strong {slist} skills. Resume quality and assessment results indicate high deployment readiness."
            else:
                m["strengths"] = cand.get("skills", [])[:3]
                m["weaknesses"] = ["Cloud Computing", "Advanced Statistics"]
                m["recommendation"] = f"This candidate is highly suitable for the {cand.get('domain')} role based on profile matching. Resume quality and assessment results indicate high deployment readiness."
                
            enriched_matches.append(m)
            
    return jsonify(enriched_matches)

@project_bp.route("/invite", methods=["POST"])
@token_required("organization")
def invite_candidate():
    data = request.json
    db = Database.get_db()
    org_email = request.current_user["email"]
    org_name = request.current_user["name"]
    
    project_id = data.get("project_id")
    candidate_email = data.get("candidate_email")
    
    if not project_id or not candidate_email:
        return jsonify({"error": "Project ID and Candidate Email are required."}), 400
        
    try:
        project = db["projects"].find_one({"_id": ObjectId(project_id)})
    except Exception:
        return jsonify({"error": "Invalid Project ID format."}), 400
        
    if not project:
        return jsonify({"error": "Project not found."}), 404
        
    candidate = db["professionals"].find_one({"email": candidate_email})
    if not candidate:
        return jsonify({"error": "Candidate not found."}), 404
        
    # Check if invitation already exists for this project and candidate
    existing = db["invitations"].find_one({
        "project_id": project_id,
        "candidate_email": candidate_email
    })
    if existing:
        return jsonify({"error": "An invitation has already been sent to this candidate for this project."}), 400
        
    # Create Invitation
    invite_doc = {
        "project_id": project_id,
        "project_name": project["name"],
        "project_role": project["role"],
        "organization_email": org_email,
        "organization_name": org_name,
        "candidate_email": candidate_email,
        "candidate_name": candidate["name"],
        "status": "Pending", # Pending / Accepted / Declined / Hired
        "created_at": datetime.utcnow()
    }
    db["invitations"].insert_one(invite_doc)
    
    # Update candidate status to Invitation Pending
    db["professionals"].update_one(
        {"email": candidate_email},
        {"$set": {"status": "Invitation Pending"}}
    )
    
    # Create notification for candidate
    db["notifications"].insert_one({
        "recipient_email": candidate_email,
        "message": f"You have received an interview invitation from {org_name}.",
        "read": False,
        "created_at": datetime.utcnow()
    })
    
    # Log Activity
    db["activity_logs"].insert_one({
        "user_email": org_email,
        "action": f"Sent invitation to {candidate['name']} for project: {project['name']}",
        "timestamp": datetime.utcnow()
    })
    
    return jsonify({"message": "Invitation sent successfully!"})

@project_bp.route("/invitations", methods=["GET"])
@token_required()
def get_invitations():
    db = Database.get_db()
    email = request.current_user["email"]
    role = request.user_role
    
    if role == "professional":
        invitations = list(db["invitations"].find({"candidate_email": email}))
    else: # organization
        invitations = list(db["invitations"].find({"organization_email": email}))
        
    for invite in invitations:
        invite["_id"] = str(invite["_id"])
        
    return jsonify(invitations)

@project_bp.route("/invitation/<invite_id>/respond", methods=["POST"])
@token_required("professional")
def respond_invitation(invite_id):
    data = request.json
    db = Database.get_db()
    email = request.current_user["email"]
    response = data.get("response", "").strip() # "Accept" or "Decline"
    
    if response not in ["Accept", "Decline"]:
        return jsonify({"error": "Response must be either 'Accept' or 'Decline'."}), 400
        
    try:
        invite = db["invitations"].find_one({"_id": ObjectId(invite_id), "candidate_email": email})
    except Exception:
        return jsonify({"error": "Invalid Invitation ID format."}), 400
        
    if not invite:
        return jsonify({"error": "Invitation not found."}), 404
        
    status_map = {
        "Accept": "Accepted",
        "Decline": "Declined"
    }
    
    db["invitations"].update_one(
        {"_id": ObjectId(invite_id)},
        {"$set": {"status": status_map[response], "responded_at": datetime.utcnow()}}
    )
    
    # Update professional status
    if response == "Accept":
        db["professionals"].update_one(
            {"email": email},
            {"$set": {"status": "Invitation Accepted"}} # In-between status
        )
        message = f"{request.current_user['name']} accepted your invitation."
    else:
        # Revert back to Deployment Ready
        db["professionals"].update_one(
            {"email": email},
            {"$set": {"status": "Deployment Ready"}}
        )
        message = f"{request.current_user['name']} declined your invitation."
        
    # Notify organization
    db["notifications"].insert_one({
        "recipient_email": invite["organization_email"],
        "message": message,
        "read": False,
        "created_at": datetime.utcnow()
    })
    
    # Log Activity
    db["activity_logs"].insert_one({
        "user_email": email,
        "action": f"{response}ed invitation for project: {invite['project_name']}",
        "timestamp": datetime.utcnow()
    })
    
    return jsonify({"message": f"Invitation {response}ed successfully!"})

@project_bp.route("/<project_id>/hire", methods=["POST"])
@token_required("organization")
def hire_candidate(project_id):
    data = request.json
    db = Database.get_db()
    org_email = request.current_user["email"]
    org_name = request.current_user["name"]
    hr_contact = request.current_user.get("hr_contact", "HR Manager")
    
    candidate_email = data.get("candidate_email")
    if not candidate_email:
        return jsonify({"error": "Candidate Email is required."}), 400
        
    try:
        project = db["projects"].find_one({"_id": ObjectId(project_id), "organization_email": org_email})
    except Exception:
        return jsonify({"error": "Invalid Project ID format."}), 400
        
    if not project:
        return jsonify({"error": "Project not found or unauthorized access."}), 404
        
    if project["hired_count"] >= project["resources_needed"]:
        return jsonify({"error": "This project is already fully staffed."}), 400
        
    # Check if invitation was accepted
    invite = db["invitations"].find_one({
        "project_id": project_id,
        "candidate_email": candidate_email,
        "status": "Accepted"
    })
    if not invite:
        return jsonify({"error": "No accepted invitation found for this candidate on this project."}), 400
        
    # 1. Update Candidate Status in Professionals
    joining_date = project.get("joining_date", datetime.utcnow().strftime("%Y-%m-%d"))
    db["professionals"].update_one(
        {"email": candidate_email},
        {"$set": {
            "status": "Hired",
            "company": org_name,
            "project": project["name"],
            "role": project["role"],
            "manager": hr_contact,
            "joining_date": joining_date,
            "offer_letter": f"OFFER_LETTER_{project_id[:6]}_{candidate_email[:4].upper()}"
        }}
    )
    
    # 2. Update Invitation status
    db["invitations"].update_one(
        {"_id": invite["_id"]},
        {"$set": {"status": "Hired", "hired_at": datetime.utcnow()}}
    )
    
    # Send Hired Notification to this candidate immediately
    hired_msg = (
        f"🎉 Congratulations!\n\n"
        f"You have been hired.\n\n"
        f"Organization: {org_name}\n"
        f"Project: {project['name']}\n"
        f"Role: {project['role']}\n"
        f"Joining Date: {joining_date}\n"
        f"Status: Hired"
    )
    db["notifications"].insert_one({
        "recipient_email": candidate_email,
        "message": hired_msg,
        "read": False,
        "created_at": datetime.utcnow()
    })
    
    # 3. Update project details
    new_hired_count = project["hired_count"] + 1
    update_proj_data = {"hired_count": new_hired_count}
    
    # If all filled, change project status to Active
    project_became_active = False
    if new_hired_count >= project["resources_needed"]:
        update_proj_data["status"] = "Project Active"
        project_became_active = True
        
    db["projects"].update_one(
        {"_id": ObjectId(project_id)},
        {"$set": update_proj_data}
    )
    
    # 4. If project became active, transition all hired candidates to "Working on Project" and send deployment notification
    if project_became_active:
        # Find all candidates hired on this project (which now includes this candidate)
        hired_invites = list(db["invitations"].find({"project_id": project_id, "status": "Hired"}))
        for h_inv in hired_invites:
            db["professionals"].update_one(
                {"email": h_inv["candidate_email"]},
                {"$set": {"status": "Working on Project"}}
            )
            
            # Send Deployed notification
            deployed_msg = (
                f"🚀 Congratulations!\n\n"
                f"Your project has now started.\n\n"
                f"Project: {project['name']}\n"
                f"Organization: {org_name}\n"
                f"Status: Working on Project\n"
                f"Project Status: Active"
            )
            db["notifications"].insert_one({
                "recipient_email": h_inv["candidate_email"],
                "message": deployed_msg,
                "read": False,
                "created_at": datetime.utcnow()
            })
        
    # Log Activity
    db["activity_logs"].insert_one({
        "user_email": org_email,
        "action": f"Hired {invite['candidate_name']} for project: {project['name']}",
        "timestamp": datetime.utcnow()
    })
    
    return jsonify({
        "message": "Candidate hired successfully!",
        "hired_count": new_hired_count,
        "project_status": "Project Active" if new_hired_count >= project["resources_needed"] else "Hiring"
    })
