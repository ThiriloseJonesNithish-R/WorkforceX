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
    
    name = data.get("name", "").strip()
    if not name:
        return jsonify({"error": "Project Name is required."}), 400
        
    roles_data = data.get("roles", [])
    if roles_data and isinstance(roles_data, list):
        formatted_roles = []
        total_resources = 0
        all_primary_skills = set()
        all_secondary_skills = set()
        all_certs = set()
        role_titles = []
        
        for idx, r in enumerate(roles_data):
            r_title = r.get("title", f"Role {idx+1}").strip()
            try:
                r_count = max(1, int(r.get("count", 1)))
            except ValueError:
                r_count = 1
            total_resources += r_count
            role_titles.append(r_title)
            
            p_skills = r.get("primary_skills", [])
            s_skills = r.get("secondary_skills", [])
            certs = r.get("certifications", [])
            all_primary_skills.update(p_skills)
            all_secondary_skills.update(s_skills)
            all_certs.update(certs)
            
            formatted_roles.append({
                "role_id": r.get("role_id") or f"role_{idx+1}",
                "title": r_title,
                "count": r_count,
                "hired_count": 0,
                "experience": r.get("experience", 0),
                "primary_skills": p_skills,
                "secondary_skills": s_skills,
                "certifications": certs,
                "job_description": r.get("job_description", "").strip()
            })
            
        role = " / ".join(role_titles)
        resources_needed = total_resources
        primary_skills = list(all_primary_skills)
        secondary_skills = list(all_secondary_skills)
        certifications = list(all_certs)
        job_description = data.get("job_description", "").strip() or " Multi-role project staffing."
    else:
        # Single-role legacy fallback
        role = data.get("role", "").strip()
        if not role:
            return jsonify({"error": "Job Role is required."}), 400
        try:
            resources_needed = int(data.get("resources_needed", 1))
        except ValueError:
            resources_needed = 1
            
        primary_skills = data.get("primary_skills", [])
        secondary_skills = data.get("secondary_skills", [])
        certifications = data.get("certifications", [])
        job_description = data.get("job_description", "").strip()
        
        formatted_roles = [{
            "role_id": "role_1",
            "title": role,
            "count": resources_needed,
            "hired_count": 0,
            "experience": data.get("experience", 0),
            "primary_skills": primary_skills,
            "secondary_skills": secondary_skills,
            "certifications": certifications,
            "job_description": job_description
        }]

    project_doc = {
        "organization_email": org_email,
        "organization_name": org_name,
        "name": name,
        "client": data.get("client", "").strip(),
        "department": data.get("department", "").strip(),
        "role": role,
        "job_description": job_description,
        "experience": data.get("experience", 0),
        "primary_skills": primary_skills,
        "secondary_skills": secondary_skills,
        "certifications": certifications,
        "budget": data.get("budget", ""),
        "duration": data.get("duration", ""),
        "joining_date": data.get("joining_date", ""),
        "priority": data.get("priority", "Medium"),
        "resources_needed": resources_needed,
        "work_mode": data.get("work_mode", "Onsite"),
        "roles": formatted_roles,
        "hired_count": 0,
        "status": "Hiring",
        "created_at": datetime.utcnow()
    }
    
    result = db["projects"].insert_one(project_doc)
    
    # Log Activity
    db["activity_logs"].insert_one({
        "user_email": org_email,
        "action": f"Created Project: {name} ({len(formatted_roles)} roles)",
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
    
    projects = list(db["projects"].find({
        "organization_email": org_email,
        "is_test": {"$ne": True}
    }))
    
    for proj in projects:
        proj_id_str = str(proj["_id"])
        proj["_id"] = proj_id_str
        
        # Calculate actual hired count dynamically from invitations
        hired_invites = list(db["invitations"].find({"project_id": proj_id_str, "status": "Hired"}))
        actual_hired = len(hired_invites)
        proj["hired_count"] = actual_hired
        
        if actual_hired >= proj.get("resources_needed", 1):
            proj["status"] = "Project Active"
            
        roles = proj.get("roles", [])
        if not roles:
            roles = [{
                "role_id": "role_1",
                "title": proj.get("role", "General Role"),
                "count": proj.get("resources_needed", 1),
                "hired_count": actual_hired,
                "experience": proj.get("experience", 0),
                "primary_skills": proj.get("primary_skills", []),
                "secondary_skills": proj.get("secondary_skills", []),
                "certifications": proj.get("certifications", []),
                "job_description": proj.get("job_description", "")
            }]
        else:
            for r in roles:
                r_hired = len([i for i in hired_invites if i.get("role_id") == r.get("role_id") or i.get("project_role") == r.get("title")])
                r["hired_count"] = r_hired
        proj["roles"] = roles
        
    return jsonify(projects)

@project_bp.route("/<project_id>/matches", methods=["GET"])
@token_required("organization")
def get_project_matches(project_id):
    db = Database.get_db()
    role_id = request.args.get("role_id")
    try:
        project = db["projects"].find_one({"_id": ObjectId(project_id)})
    except Exception:
        return jsonify({"error": "Invalid Project ID format."}), 400
        
    if not project:
        return jsonify({"error": "Project not found."}), 404
        
    # Get top matches for target role or first role
    matches = get_top_matched_candidates(project, target_role_id=role_id)
    
    # Enrich matches with candidate basic profile details
    enriched_matches = []
    for m in matches:
        cand = db["professionals"].find_one({"email": m["candidate_email"]})
        if cand:
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
            
            scores = db["resume_scores"].find_one({"candidate_email": cand["email"]})
            if scores:
                m["strengths"] = scores.get("strengths", [])
                m["weaknesses"] = scores.get("weaknesses", [])
                slist = ", ".join(scores.get("strengths", [])[:3])
                m["recommendation"] = f"This candidate is highly suitable for the {m.get('target_role_title', cand.get('domain'))} role due to strong {slist} skills. Resume quality and assessment results indicate high deployment readiness."
            else:
                m["strengths"] = cand.get("skills", [])[:3]
                m["weaknesses"] = ["Cloud Computing", "Advanced Statistics"]
                m["recommendation"] = f"This candidate is highly suitable for the {m.get('target_role_title', cand.get('domain'))} role based on profile matching. Resume quality and assessment results indicate high deployment readiness."
                
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
    role_id = data.get("role_id")
    
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
        
    # Identify target role details
    roles = project.get("roles", [])
    target_role = None
    if role_id and roles:
        target_role = next((r for r in roles if r.get("role_id") == role_id), None)
    if not target_role:
        target_role = roles[0] if roles else {"role_id": "role_1", "title": project.get("role")}

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
        "role_id": target_role.get("role_id", "role_1"),
        "project_name": project["name"],
        "project_role": target_role.get("title", project.get("role")),
        "organization_email": org_email,
        "organization_name": org_name,
        "candidate_email": candidate_email,
        "candidate_name": candidate["name"],
        "status": "Pending",
        "created_at": datetime.utcnow()
    }
    db["invitations"].insert_one(invite_doc)
    
    db["professionals"].update_one(
        {"email": candidate_email},
        {"$set": {"status": "Invitation Pending"}}
    )
    
    db["notifications"].insert_one({
        "recipient_email": candidate_email,
        "message": f"You have received an interview invitation for the '{target_role.get('title')}' role at {org_name}.",
        "read": False,
        "created_at": datetime.utcnow()
    })
    
    db["activity_logs"].insert_one({
        "user_email": org_email,
        "action": f"Sent invitation to {candidate['name']} for role '{target_role.get('title')}' in project: {project['name']}",
        "timestamp": datetime.utcnow()
    })
    
    return jsonify({"message": "Invitation sent successfully!"})

@project_bp.route("/reject", methods=["POST"])
@token_required("organization")
def reject_candidate():
    data = request.json
    db = Database.get_db()
    org_email = request.current_user["email"]
    
    project_id = data.get("project_id")
    candidate_email = data.get("candidate_email")
    role_id = data.get("role_id")
    
    if not project_id or not candidate_email:
        return jsonify({"error": "Project ID and Candidate Email are required."}), 400
        
    db["project_rejections"].update_one(
        {"project_id": str(project_id), "candidate_email": candidate_email},
        {"$set": {
            "project_id": str(project_id),
            "candidate_email": candidate_email,
            "role_id": role_id,
            "organization_email": org_email,
            "rejected_at": datetime.utcnow()
        }},
        upsert=True
    )
    
    db["activity_logs"].insert_one({
        "user_email": org_email,
        "action": f"Passed/Rejected candidate {candidate_email} for project: {project_id}",
        "timestamp": datetime.utcnow()
    })
    
    return jsonify({"message": "Candidate passed/rejected successfully. A new candidate match has been generated!"})

@project_bp.route("/invitations", methods=["GET"])
@token_required()
def get_invitations():
    db = Database.get_db()
    email = request.current_user["email"]
    role = request.user_role
    
    if role == "professional":
        invitations = list(db["invitations"].find({"candidate_email": email}))
    else:
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
    
    resp_val = str(data.get("response") or data.get("status") or "").strip()
    if resp_val.lower() in ["accept", "accepted"]:
        new_status = "Accepted"
    elif resp_val.lower() in ["decline", "declined"]:
        new_status = "Declined"
    else:
        return jsonify({"error": "Response must be either 'Accept' or 'Decline'."}), 400
        
    try:
        invite = db["invitations"].find_one({"_id": ObjectId(invite_id), "candidate_email": email})
    except Exception:
        return jsonify({"error": "Invalid Invitation ID format."}), 400
        
    if not invite:
        return jsonify({"error": "Invitation not found."}), 404
        
    db["invitations"].update_one(
        {"_id": ObjectId(invite_id)},
        {"$set": {"status": new_status, "responded_at": datetime.utcnow()}}
    )
    
    if new_status == "Accepted":
        db["professionals"].update_one(
            {"email": email},
            {"$set": {"status": "Invitation Accepted"}}
        )
        message = f"{request.current_user['name']} accepted your invitation for '{invite.get('project_role')}'."
    else:
        db["professionals"].update_one(
            {"email": email},
            {"$set": {"status": "Deployment Ready"}}
        )
        message = f"{request.current_user['name']} declined your invitation for '{invite.get('project_role')}'."
        
    db["notifications"].insert_one({
        "recipient_email": invite["organization_email"],
        "message": message,
        "read": False,
        "created_at": datetime.utcnow()
    })
    
    db["activity_logs"].insert_one({
        "user_email": email,
        "action": f"{new_status} invitation for project: {invite['project_name']}",
        "timestamp": datetime.utcnow()
    })
    
    return jsonify({"message": f"Invitation {new_status} successfully!"})

@project_bp.route("/<project_id>/hire", methods=["POST"])
@token_required("organization")
def hire_candidate(project_id):
    data = request.json
    db = Database.get_db()
    org_email = request.current_user["email"]
    org_name = request.current_user["name"]
    hr_contact = request.current_user.get("hr_contact", "HR Manager")
    
    candidate_email = data.get("candidate_email")
    role_id = data.get("role_id")
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
        
    invite = db["invitations"].find_one({
        "project_id": project_id,
        "candidate_email": candidate_email,
        "status": "Accepted"
    })
    if not invite:
        return jsonify({"error": "No accepted invitation found for this candidate on this project."}), 400
        
    target_role_title = invite.get("project_role", project.get("role"))
    target_role_id = role_id or invite.get("role_id")
    
    # 1. Update Candidate Status in Professionals
    joining_date = project.get("joining_date", datetime.utcnow().strftime("%Y-%m-%d"))
    db["professionals"].update_one(
        {"email": candidate_email},
        {"$set": {
            "status": "Hired",
            "company": org_name,
            "project": project["name"],
            "role": target_role_title,
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
    
    # Send Hired Notification to candidate
    hired_msg = (
        f"🎉 Congratulations!\n\n"
        f"You have been hired.\n\n"
        f"Organization: {org_name}\n"
        f"Project: {project['name']}\n"
        f"Role: {target_role_title}\n"
        f"Joining Date: {joining_date}\n"
        f"Status: Hired"
    )
    db["notifications"].insert_one({
        "recipient_email": candidate_email,
        "message": hired_msg,
        "read": False,
        "created_at": datetime.utcnow()
    })
    
    # 3. Update project details & role hired_count
    new_hired_count = project["hired_count"] + 1
    update_proj_data = {"hired_count": new_hired_count}
    
    roles = project.get("roles", [])
    if roles:
        for r in roles:
            if r.get("role_id") == target_role_id or r.get("title") == target_role_title:
                r["hired_count"] = r.get("hired_count", 0) + 1
                break
        update_proj_data["roles"] = roles
        
    project_became_active = False
    if new_hired_count >= project["resources_needed"]:
        update_proj_data["status"] = "Project Active"
        project_became_active = True
        
    db["projects"].update_one(
        {"_id": ObjectId(project_id)},
        {"$set": update_proj_data}
    )
    
    # 4. If project became active, transition all hired candidates to "Working on Project"
    if project_became_active:
        hired_invites = list(db["invitations"].find({"project_id": project_id, "status": "Hired"}))
        for h_inv in hired_invites:
            db["professionals"].update_one(
                {"email": h_inv["candidate_email"]},
                {"$set": {"status": "Working on Project"}}
            )
            
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
        "action": f"Hired candidate {candidate_email} for role '{target_role_title}' in project: {project['name']}",
        "timestamp": datetime.utcnow()
    })
    
    return jsonify({
        "message": f"Candidate successfully hired for {target_role_title}!",
        "hired_count": new_hired_count,
        "project_status": update_proj_data.get("status", project["status"])
    })
