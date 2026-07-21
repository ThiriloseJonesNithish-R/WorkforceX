from flask import Blueprint, request, jsonify
from backend.database.mongo import Database
from backend.utils.helpers import token_required
from datetime import datetime

assessment_bp = Blueprint("assessment", __name__)

@assessment_bp.route("/generate", methods=["GET"])
@token_required("professional")
def generate_assessment():
    db = Database.get_db()
    email = request.current_user["email"]
    
    # Check attempts count
    candidate = db["professionals"].find_one({"email": email})
    attempts_count = db["assessment_attempts"].count_documents({"candidate_email": email})
    
    if attempts_count >= 3:
        return jsonify({
            "error": "You have exceeded the maximum of 3 assessment attempts. The assessment portal is locked.",
            "locked": True,
            "attempts_count": attempts_count
        }), 403
        
    # Get domain or skills
    domain = candidate.get("domain", "Python")
    
    # Map domain to seeded assessment categories
    category_map = {
        "data scientist": "Data Analyst",
        "data analyst": "Data Analyst",
        "ai engineer": "Machine Learning",
        "machine learning engineer": "Machine Learning",
        "software engineer": "Python",
        "cloud architect": "SQL",
        "cybersecurity analyst": "Cybersecurity"
    }
    
    assessment_skill = category_map.get(domain.lower(), "Python")
    
    # Query 3 questions for this skill (Easy, Medium, Hard)
    questions = list(db["assessments"].find({"skill": assessment_skill}))
    if not questions:
        # Fallback to general Python if no questions found
        questions = list(db["assessments"].find({"skill": "Python"}))
        
    # Sanitize questions (remove answer field)
    sanitized_questions = []
    for q in questions:
        q_copy = q.copy()
        q_copy["_id"] = str(q_copy["_id"])
        q_copy.pop("answer", None)
        sanitized_questions.append(q_copy)
        
    return jsonify({
        "questions": sanitized_questions,
        "skill": assessment_skill,
        "attempts_left": 3 - attempts_count,
        "attempts_count": attempts_count
    })

@assessment_bp.route("/submit", methods=["POST"])
@token_required("professional")
def submit_assessment():
    data = request.json
    db = Database.get_db()
    email = request.current_user["email"]
    answers = data.get("answers", {}) # Format: { "question_id": "Selected Answer" }
    
    # Check attempts count
    attempts_count = db["assessment_attempts"].count_documents({"candidate_email": email})
    if attempts_count >= 3:
        return jsonify({"error": "Assessment is locked. Maximum attempts reached."}), 403
        
    # Calculate score
    correct_count = 0
    total_count = 0
    
    db_questions = list(db["assessments"].find({}))
    questions_dict = {str(q["_id"]): q for q in db_questions}
    
    for q_id, selected_ans in answers.items():
        if q_id in questions_dict:
            total_count += 1
            correct_ans = questions_dict[q_id]["answer"]
            if str(selected_ans).strip().lower() == str(correct_ans).strip().lower():
                correct_count += 1
                
    if total_count == 0:
        return jsonify({"error": "No valid answers submitted."}), 400
        
    score_pct = int((correct_count / total_count) * 100)
    passed = score_pct >= 60 # Passed if answered at least 3 out of 5 correctly (60%+)
    status = "Passed" if passed else "Failed"
    
    # Register attempt
    attempt = {
        "candidate_email": email,
        "attempt_number": attempts_count + 1,
        "score": score_pct,
        "status": status,
        "timestamp": datetime.utcnow()
    }
    db["assessment_attempts"].insert_one(attempt)
    
    # Update candidate profile in professionals
    new_attempts_count = attempts_count + 1
    update_data = {
        "assessment_attempts_count": new_attempts_count
    }
    
    if passed:
        # Candidate status updates to "Deployment Ready" following the timeline
        update_data["status"] = "Deployment Ready"
        update_data["source"] = "Registered"
        update_data["assessment_passed"] = True
        
        # Log activity
        db["activity_logs"].insert_one({
            "user_email": email,
            "action": "Passed Assessment",
            "timestamp": datetime.utcnow()
        })
    else:
        if new_attempts_count >= 3:
            update_data["status"] = "Assessment Locked"
            update_data["assessment_passed"] = False
            
            # Log activity
            db["activity_logs"].insert_one({
                "user_email": email,
                "action": "Assessment Portal Locked",
                "timestamp": datetime.utcnow()
            })
        else:
            update_data["status"] = "Assessment Completed" # Keep trying
            
    db["professionals"].update_one({"email": email}, {"$set": update_data})
    
    return jsonify({
        "score": score_pct,
        "passed": passed,
        "status": status,
        "attempts_left": 3 - new_attempts_count,
        "attempts_count": new_attempts_count,
        "locked": new_attempts_count >= 3 and not passed
    })

@assessment_bp.route("/attempts", methods=["GET"])
@token_required("professional")
def get_attempts():
    db = Database.get_db()
    email = request.current_user["email"]
    
    attempts = list(db["assessment_attempts"].find({"candidate_email": email}))
    for att in attempts:
        att.pop("_id", None)
        
    return jsonify(attempts)
