import re
from backend.database.mongo import Database

def tokenize(text: str) -> set:
    if not text:
        return set()
    text = text.lower().strip()
    text = text.replace("html5", "html").replace("css3", "css").replace("ml", "machine learning").replace("js", "javascript")
    tokens = set(re.findall(r'\b[a-z0-9+#]+\b', text))
    return tokens

def match_skills(project_skills: list, candidate_skills: list) -> tuple:
    if not project_skills:
        return (75.0, [])
    
    cand_tokens_all = set()
    cand_skills_lower = [cs.lower().strip() for cs in candidate_skills if cs]
    for cs in candidate_skills:
        cand_tokens_all.update(tokenize(cs))
        
    matched_skills = []
    matched_count = 0
    
    for ps in project_skills:
        ps_tokens = tokenize(ps)
        ps_lower = ps.lower().strip()
        
        # 1. Exact or normalized full skill match
        exact_match = (ps_lower in cand_skills_lower)
        
        # 2. Tokenized subset match
        token_match = bool(ps_tokens and ps_tokens.issubset(cand_tokens_all))
        
        if exact_match or token_match:
            matched_skills.append(ps)
            matched_count += 1
            
    skill_match_pct = matched_count / len(project_skills)
    skill_match_score = skill_match_pct * 100.0
    return (skill_match_score, matched_skills)

def calculate_match_score(candidate: dict, project: dict, attempts_by_email: dict = None) -> dict:
    db = Database.get_db()
    
    # 1. Resume Score (30%)
    resume_score = candidate.get("resume_score", 70)
    
    # 2. Assessment Score (25%)
    assessment_score = 80
    email = candidate.get("email")
    if attempts_by_email is not None:
        attempts = attempts_by_email.get(email, [])
    else:
        attempts = list(db["assessment_attempts"].find({"candidate_email": email}))
        
    if attempts:
        passed_attempts = [att for att in attempts if att.get("status") == "Passed"]
        if passed_attempts:
            assessment_score = max([att.get("score", 70) for att in passed_attempts])
        else:
            assessment_score = max([att.get("score", 0) for att in attempts])
            
    # 3. Tokenized Skill Match (25%)
    primary_skills = [s.strip() for s in project.get("primary_skills", []) if s and s.strip()]
    secondary_skills = [s.strip() for s in project.get("secondary_skills", []) if s and s.strip()]
    project_skills = primary_skills + secondary_skills
    candidate_skills = candidate.get("skills", [])
    
    skill_match_score, matched_skills = match_skills(project_skills, candidate_skills)
    primary_match_score, primary_matched = match_skills(primary_skills, candidate_skills) if primary_skills else (100.0, [])
        
    # 4. Experience Match (10%)
    proj_exp_req = project.get("experience", 0)
    try:
        proj_exp_req = int(proj_exp_req)
    except Exception:
        match_digits = re.search(r'\d+', str(proj_exp_req))
        proj_exp_req = int(match_digits.group(0)) if match_digits else 0
        
    cand_exp = candidate.get("experience", 0)
    if proj_exp_req > 0:
        if cand_exp >= proj_exp_req:
            experience_score = 100.0
        else:
            experience_score = (cand_exp / proj_exp_req) * 100
    else:
        experience_score = min(100.0, (cand_exp / 5) * 100)
        
    # 5. Certifications Match (10%)
    proj_certs = [c.lower() for c in project.get("certifications", []) if c]
    cand_certs = [c.lower() for c in candidate.get("certifications", []) if c]
    
    if proj_certs:
        matched_certs = [c for c in proj_certs if c in cand_certs]
        cert_score = (len(matched_certs) / len(proj_certs)) * 100
    else:
        cert_score = 100.0 if cand_certs else 75.0
        
    # Overall Weighted Score
    overall_match_score = (
        0.30 * resume_score +
        0.25 * assessment_score +
        0.25 * skill_match_score +
        0.10 * experience_score +
        0.10 * cert_score
    )
    
    # Candidate Domain & Role Title Alignment check
    cand_domain = (candidate.get("domain") or candidate.get("Job Role") or "").lower().strip()
    role_title = (project.get("title") or project.get("role") or "").lower().strip()
    
    domain_match = False
    if cand_domain and role_title:
        d_tokens = tokenize(cand_domain)
        rt_tokens = tokenize(role_title)
        if d_tokens and rt_tokens and len(d_tokens.intersection(rt_tokens)) > 0:
            domain_match = True
            
    # Apply gating penalty for complete skill or domain mismatch on technical roles
    if primary_skills and primary_match_score == 0.0:
        if not domain_match:
            # 0% primary skill match AND mismatched domain -> severe penalty
            overall_match_score = overall_match_score * 0.20
        else:
            overall_match_score = overall_match_score * 0.50
        
    return {
        "candidate_email": email,
        "candidate_name": candidate.get("name"),
        "match_score": round(overall_match_score, 1),
        "resume_score": resume_score,
        "assessment_score": assessment_score,
        "skill_match_score": round(skill_match_score, 1),
        "experience_score": round(experience_score, 1),
        "certifications_score": round(cert_score, 1),
        "matched_skills": matched_skills,
        "candidate_skills": candidate.get("skills", []),
        "candidate_experience": cand_exp,
        "candidate_certifications": candidate.get("certifications", [])
    }

def get_top_matched_candidates(project: dict, target_role_id: str = None) -> list:
    db = Database.get_db()
    
    project_id_str = str(project.get("_id", ""))
    
    # 0. Anti-Duplication & Rejections Filter
    existing_invites = list(db["invitations"].find({"project_id": project_id_str}))
    invited_emails = set(inv["candidate_email"] for inv in existing_invites)
    
    existing_rejections = list(db["project_rejections"].find({"project_id": project_id_str}))
    rejected_emails = set(rej["candidate_email"] for rej in existing_rejections)
    
    excluded_emails = invited_emails.union(rejected_emails)
    
    # Identify target role & all roles in project
    roles = project.get("roles", [])
    target_role = None
    if target_role_id and roles:
        target_role = next((r for r in roles if r.get("role_id") == target_role_id), None)
        
    if not target_role:
        if roles:
            target_role = roles[0]
            target_role_id = target_role.get("role_id", "role_1")
        else:
            target_role = {
                "role_id": "role_1",
                "title": project.get("role", "General Role"),
                "count": project.get("resources_needed", 1),
                "hired_count": project.get("hired_count", 0),
                "experience": project.get("experience", 0),
                "primary_skills": project.get("primary_skills", []),
                "secondary_skills": project.get("secondary_skills", []),
                "certifications": project.get("certifications", []),
                "job_description": project.get("job_description", "")
            }
            target_role_id = "role_1"
            roles = [target_role]

    target_role_id = target_role.get("role_id", target_role_id or "role_1")
    
    # Calculate role hired count accurately from role field & invitations
    hired_in_role = len([
        inv for inv in existing_invites
        if inv.get("status") == "Hired" and (
            inv.get("role_id") == target_role_id or
            inv.get("project_role") == target_role.get("title")
        )
    ])
    role_hired_count = max(int(target_role.get("hired_count", 0)), hired_in_role)
    role_total_count = int(target_role.get("count", 1))
    needed_count = max(0, role_total_count - role_hired_count)
    
    if needed_count <= 0:
        return []

    # 1. Pre-fetch assessment attempts in ONE query
    all_attempts = list(db["assessment_attempts"].find({}))
    attempts_by_email = {}
    for att in all_attempts:
        c_email = att.get("candidate_email")
        if c_email:
            attempts_by_email.setdefault(c_email, []).append(att)
    
    # 2. Fetch registered candidates
    eligible_statuses = ["Deployment Ready", "Invitation Pending", "Invitation Accepted", "Hired"]
    registered_candidates = list(db["professionals"].find({
        "source": {"$ne": "Database"},
        "status": {"$in": eligible_statuses}
    }))
    
    registered_matches = []
    for cand in registered_candidates:
        cand_email = cand.get("email")
        if cand_email in excluded_emails:
            continue
            
        # Multi-role best fit evaluation: Assign candidate to their highest scoring role slot in this project
        if len(roles) > 1:
            best_role_eval = max(
                roles,
                key=lambda r: calculate_match_score(cand, r, attempts_by_email)["match_score"]
            )
            if best_role_eval.get("role_id") != target_role_id:
                continue
                
        match_details = calculate_match_score(cand, target_role, attempts_by_email)
        
        # Minimum Match Quality Gate: Candidate must score >= 40% and match primary skills if required
        primary_skills = target_role.get("primary_skills", [])
        if match_details["match_score"] < 40.0 or (primary_skills and match_details["skill_match_score"] == 0.0):
            continue
            
        match_details["source"] = "Registered"
        match_details["role_id"] = target_role_id
        match_details["target_role_title"] = target_role.get("title", project.get("role"))
        registered_matches.append(match_details)
        
    registered_matches.sort(key=lambda x: x["match_score"], reverse=True)
    
    if len(registered_matches) >= needed_count:
        return registered_matches[:needed_count]
        
    # 3. Dataset candidates fallback if needed
    db_needed = needed_count - len(registered_matches)
    proj_role = target_role.get("title", project.get("role", ""))
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
        cand_email = cand.get("email")
        if cand_email in excluded_emails:
            continue
            
        if len(roles) > 1:
            best_role_eval = max(
                roles,
                key=lambda r: calculate_match_score(cand, r, attempts_by_email)["match_score"]
            )
            if best_role_eval.get("role_id") != target_role_id:
                continue
                
        match_details = calculate_match_score(cand, target_role, attempts_by_email)
        
        # Minimum Match Quality Gate: Candidate must score >= 40% and match primary skills if required
        primary_skills = target_role.get("primary_skills", [])
        if match_details["match_score"] < 40.0 or (primary_skills and match_details["skill_match_score"] == 0.0):
            continue
            
        match_details["source"] = "Database"
        match_details["role_id"] = target_role_id
        match_details["target_role_title"] = target_role.get("title", project.get("role"))
        db_matches.append(match_details)
        
    db_matches.sort(key=lambda x: x["match_score"], reverse=True)
    
    all_matches = registered_matches + db_matches
    return all_matches[:needed_count]
