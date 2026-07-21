import re
from backend.database.mongo import Database

def calculate_match_score(candidate: dict, project: dict, attempts_by_email: dict = None) -> dict:
    """
    Candidate fields:
        resume_score (0-100)
        skills (list)
        experience (years, int)
        certifications (list)
        email (string)
    Project fields:
        primary_skills (list)
        secondary_skills (list)
        experience (min years, int/str)
        certifications (list)
    Weighted Formula:
        Resume Score: 30%
        Assessment Score: 25%
        Skill Match: 25%
        Experience: 10%
        Certifications: 10%
    """
    db = Database.get_db()
    
    # 1. Resume Score (30%)
    resume_score = candidate.get("resume_score", 70)
    
    # 2. Assessment Score (25%)
    # Retrieve the assessment attempt score for skills relevant to this project
    # Fallback to candidate's readiness score or default to 80 if not taken
    assessment_score = 80
    email = candidate.get("email")
    if attempts_by_email is not None:
        attempts = attempts_by_email.get(email, [])
    else:
        attempts = list(db["assessment_attempts"].find({"candidate_email": email}))
        
    if attempts:
        # Find passed attempts, return highest score
        passed_attempts = [att for att in attempts if att.get("status") == "Passed"]
        if passed_attempts:
            assessment_score = max([att.get("score", 70) for att in passed_attempts])
        else:
            assessment_score = max([att.get("score", 0) for att in attempts])
            
    # 3. Skill Match (25%)
    project_skills = project.get("primary_skills", []) + project.get("secondary_skills", [])
    project_skills = [s.lower() for s in project_skills if s]
    candidate_skills = [s.lower() for s in candidate.get("skills", []) if s]
    
    if project_skills:
        matched_skills = [s for s in project_skills if s in candidate_skills]
        skill_match_pct = len(matched_skills) / len(project_skills)
        skill_match_score = skill_match_pct * 100
    else:
        skill_match_score = 75.0 # Base score if project specifies no skills
        matched_skills = []
        
    # 4. Experience Match (10%)
    # Parse project required experience
    proj_exp_req = project.get("experience", 0)
    try:
        proj_exp_req = int(proj_exp_req)
    except Exception:
        # If it's a string like "3-5 Yrs", extract the first number
        match_digits = re.search(r'\d+', str(proj_exp_req))
        proj_exp_req = int(match_digits.group(0)) if match_digits else 0
        
    cand_exp = candidate.get("experience", 0)
    if proj_exp_req > 0:
        if cand_exp >= proj_exp_req:
            experience_score = 100.0
        else:
            experience_score = (cand_exp / proj_exp_req) * 100
    else:
        # Default experience scoring if no project requirements
        experience_score = min(100.0, (cand_exp / 5) * 100)
        
    # 5. Certifications Match (10%)
    proj_certs = [c.lower() for c in project.get("certifications", []) if c]
    cand_certs = [c.lower() for c in candidate.get("certifications", []) if c]
    
    if proj_certs:
        matched_certs = [c for c in proj_certs if c in cand_certs]
        cert_score = (len(matched_certs) / len(proj_certs)) * 100
    else:
        # If project has no certification requirement, candidate gets 100 if they have any, else 75
        cert_score = 100.0 if cand_certs else 75.0
        
    # Overall Weighted Score
    overall_match_score = (
        0.30 * resume_score +
        0.25 * assessment_score +
        0.25 * skill_match_score +
        0.10 * experience_score +
        0.10 * cert_score
    )
    
    return {
        "candidate_email": email,
        "candidate_name": candidate.get("name"),
        "match_score": round(overall_match_score, 1),
        "resume_score": resume_score,
        "assessment_score": assessment_score,
        "skill_match_score": round(skill_match_score, 1),
        "experience_score": round(experience_score, 1),
        "certifications_score": round(cert_score, 1),
        "matched_skills": [s for s in candidate.get("skills", []) if s.lower() in project_skills],
        "candidate_skills": candidate.get("skills", []),
        "candidate_experience": cand_exp,
        "candidate_certifications": candidate.get("certifications", [])
    }

def get_top_matched_candidates(project: dict) -> list:
    db = Database.get_db()
    
    # 0. Pre-fetch all assessment attempts in ONE query to eliminate N+1 network queries over MongoDB Atlas
    all_attempts = list(db["assessment_attempts"].find({}))
    attempts_by_email = {}
    for att in all_attempts:
        c_email = att.get("candidate_email")
        if c_email:
            attempts_by_email.setdefault(c_email, []).append(att)
    
    # 1. Fetch registered candidates who completed workflow (source != "Database")
    # Eligible statuses: Deployment Ready, Invitation Pending, Invitation Accepted, Hired
    eligible_statuses = ["Deployment Ready", "Invitation Pending", "Invitation Accepted", "Hired"]
    
    registered_candidates = list(db["professionals"].find({
        "source": {"$ne": "Database"},
        "status": {"$in": eligible_statuses}
    }))
    
    registered_matches = []
    for cand in registered_candidates:
        match_details = calculate_match_score(cand, project, attempts_by_email)
        match_details["source"] = "Registered"
        registered_matches.append(match_details)
        
    registered_matches.sort(key=lambda x: x["match_score"], reverse=True)
    
    # If 3 or more registered candidates match, return top 3 registered candidates (no dataset candidates)
    if len(registered_matches) >= 3:
        return registered_matches[:3]
        
    # 2. If fewer than 3 registered candidates match, fallback to imported dataset candidates (source == "Database")
    needed = 3 - len(registered_matches)
    
    # Pre-filter by candidate domain/role to avoid unnecessary network payload
    proj_role = project.get("role", "")
    query = {
        "source": "Database",
        "status": {"$ne": "Working on Project"}
    }
    if proj_role:
        query["domain"] = {"$regex": re.escape(proj_role), "$options": "i"}
        
    db_candidates = list(db["professionals"].find(query))
    if not db_candidates:
        db_candidates = list(db["professionals"].find({
            "source": "Database",
            "status": {"$ne": "Working on Project"}
        }))
    
    db_matches = []
    for cand in db_candidates:
        match_details = calculate_match_score(cand, project, attempts_by_email)
        match_details["source"] = "Database"
        db_matches.append(match_details)
        
    db_matches.sort(key=lambda x: x["match_score"], reverse=True)
    
    return registered_matches + db_matches[:needed]
