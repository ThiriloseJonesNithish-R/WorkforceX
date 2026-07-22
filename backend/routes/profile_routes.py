from flask import Blueprint, request, jsonify
from backend.database.mongo import Database
from backend.utils.helpers import token_required
from backend.services.resume_parser import parse_resume_details
from backend.services.resume_analyzer import analyze_resume
from datetime import datetime
from werkzeug.utils import secure_filename
import os

profile_bp = Blueprint("profile", __name__)

ALLOWED_EXTENSIONS = {"pdf"}

def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

@profile_bp.route("/me", methods=["GET"])
@token_required("professional")
def get_my_profile():
    # Remove password from response
    user = request.current_user
    user.pop("password", None)
    if "_id" in user:
        user["_id"] = str(user["_id"])
    return jsonify(user)

@profile_bp.route("/me", methods=["PUT"])
@token_required("professional")
def update_my_profile():
    data = request.json
    db = Database.get_db()
    email = request.current_user["email"]
    
    update_fields = {}
    
    # Allow update of typical fields
    allowed_keys = ["phone", "state", "domain", "experience", "skills", "spoken_languages", "linkedin", "github", "education", "certifications"]
    for key in allowed_keys:
        if key in data:
            if key == "experience":
                try:
                    update_fields[key] = int(data[key])
                except ValueError:
                    pass
            else:
                update_fields[key] = data[key]
                
    # If candidate updates domain or skills, let's recalculate their readiness score slightly or update status
    if "skills" in data or "experience" in data:
        # Check if they have resume text to re-analyze
        current_prof = db["professionals"].find_one({"email": email})
        if current_prof and current_prof.get("resume_text"):
            # Mock details to re-run analyzer
            details = {
                "resume_text": current_prof.get("resume_text"),
                "skills": data.get("skills", current_prof.get("skills")),
                "experience": int(data.get("experience", current_prof.get("experience", 0))),
                "certifications": data.get("certifications", current_prof.get("certifications", [])),
                "education": data.get("education", current_prof.get("education", "Bachelor's Degree")),
                "projects_count": current_prof.get("projects_count", 0)
            }
            analysis = analyze_resume(details)
            update_fields["resume_score"] = analysis["score"]
            update_fields["readiness_score"] = analysis["readiness_score"]
            
            db["resume_scores"].update_one(
                {"candidate_email": email},
                {"$set": {
                    "score": analysis["score"],
                    "strengths": analysis["strengths"],
                    "weaknesses": analysis["weaknesses"],
                    "missing_skills": analysis["missing_skills"],
                    "suggestions": analysis["suggestions"],
                    "career_recommendation": analysis["career_recommendation"],
                    "readiness_score": analysis["readiness_score"],
                    "updated_at": datetime.utcnow()
                }},
                upsert=True
            )
            
    if update_fields:
        db["professionals"].update_one({"email": email}, {"$set": update_fields})
        
    # Log Activity
    db["activity_logs"].insert_one({
        "user_email": email,
        "action": "Update Profile",
        "timestamp": datetime.utcnow()
    })
    
    updated_user = db["professionals"].find_one({"email": email})
    updated_user.pop("password", None)
    if "_id" in updated_user:
        updated_user["_id"] = str(updated_user["_id"])
        
    return jsonify({"message": "Profile updated successfully!", "user": updated_user})

@profile_bp.route("/upload-resume", methods=["POST"])
@token_required("professional")
def upload_resume():
    if "file" not in request.files:
        return jsonify({"error": "No file part in the request."}), 400
        
    file = request.files["file"]
    if file.filename == "":
        return jsonify({"error": "No file selected."}), 400
        
    if not allowed_file(file.filename):
        return jsonify({"error": "Only PDF files are allowed."}), 400
        
    db = Database.get_db()
    email = request.current_user["email"]
    
    from backend.config import Config
    upload_dir = Config.UPLOAD_FOLDER
    if not os.path.exists(upload_dir):
        os.makedirs(upload_dir)
        
    filename = secure_filename(f"{email.replace('@', '_')}_{file.filename}")
    file_path = os.path.join(upload_dir, filename)
    file.save(file_path)
    
    try:
        # Update stage to: Resume Uploaded
        db["professionals"].update_one({"email": email}, {"$set": {"status": "Resume Uploaded"}})
        
        # 1. Parse Resume text and details
        parsed = parse_resume_details(file_path)
        
        # Update stage to: Resume Analyzed
        db["professionals"].update_one({"email": email}, {"$set": {"status": "Resume Analyzed"}})
        
        # 2. Analyze Resume details
        analysis = analyze_resume(parsed)
        
        # Update stage to: Skills Extracted
        db["professionals"].update_one({"email": email}, {"$set": {"status": "Skills Extracted"}})
        
        # 3. Update candidate document in Professionals collection
        db["professionals"].update_one(
            {"email": email},
            {"$set": {
                "skills": parsed["skills"],
                "experience": parsed["experience"],
                "education": parsed["education"],
                "certifications": parsed["certifications"],
                "resume_text": parsed["resume_text"],
                "resume_score": analysis["score"],
                "readiness_score": analysis["readiness_score"],
                "domain": analysis["career_recommendation"] # Recommended role becomes their domain
            }}
        )
        
        # 4. Insert or update analysis record in resume_scores
        db["resume_scores"].update_one(
            {"candidate_email": email},
            {"$set": {
                "score": analysis["score"],
                "strengths": analysis["strengths"],
                "weaknesses": analysis["weaknesses"],
                "missing_skills": analysis["missing_skills"],
                "suggestions": analysis["suggestions"],
                "career_recommendation": analysis["career_recommendation"],
                "readiness_score": analysis["readiness_score"],
                "updated_at": datetime.utcnow()
            }},
            upsert=True
        )
        
        # Log Activity
        db["activity_logs"].insert_one({
            "user_email": email,
            "action": "Upload Resume",
            "timestamp": datetime.utcnow()
        })
        
        return jsonify({
            "message": "Resume uploaded and analyzed successfully!",
            "skills": parsed["skills"],
            "experience": parsed["experience"],
            "education": parsed["education"],
            "certifications": parsed["certifications"],
            "analysis": analysis
        })
    except Exception as e:
        print(f"Error during resume processing: {e}")
        return jsonify({"error": f"Failed to analyze resume: {str(e)}"}), 500

@profile_bp.route("/resume-insights", methods=["GET"])
@token_required("professional")
def get_resume_insights():
    db = Database.get_db()
    email = request.current_user["email"]
    
    insights = db["resume_scores"].find_one({"candidate_email": email})
    if not insights:
        return jsonify({"error": "No resume analysis available. Please upload a resume first."}), 404
        
    insights.pop("_id", None)
    return jsonify(insights)

@profile_bp.route("/skills", methods=["GET"])
def get_skills():
    db = Database.get_db()
    skills_docs = list(db["skills"].find({}, {"name": 1}))
    db_skills = [s["name"] for s in skills_docs if "name" in s]
    
    # Aggregate skills from professionals collection
    prof_skills = db["professionals"].distinct("skills")
    
    default_skills = [
        "Python", "SQL", "Machine Learning", "Deep Learning", "Power BI", 
        "Cybersecurity", "Java", "C++", "Docker", "AWS", "Git", "Html5", 
        "Css", "Figma Tool", "JavaScript", "React", "TypeScript", "UI/UX Design"
    ]
    
    combined_skills = sorted(list(set(db_skills + prof_skills + default_skills)))
    return jsonify({"skills": combined_skills})
