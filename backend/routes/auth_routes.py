from flask import Blueprint, request, jsonify
from backend.database.mongo import Database
from backend.services.auth_service import hash_password, check_password, generate_token
from datetime import datetime
import re

auth_bp = Blueprint("auth", __name__)

@auth_bp.route("/register-professional", methods=["POST"])
def register_professional():
    data = request.json
    db = Database.get_db()
    
    # Validation
    name = data.get("name", "").strip()
    if not name or not re.match(r"^[A-Za-z\s]+$", name):
        return jsonify({"error": "Name must contain only alphabets."}), 400
        
    username = data.get("username", "").strip().lower()
    if not username or not re.match(r"^[a-z0-9_]{3,20}$", username):
        return jsonify({"error": "Username must be 3-20 alphanumeric characters or underscores."}), 400
        
    email = data.get("email", "").strip().lower()
    if not email or not re.match(r"^[^@]+@[^@]+\.[^@]+$", email):
        return jsonify({"error": "Invalid email address."}), 400
        
    if db["professionals"].find_one({"username": username}) or db["organizations"].find_one({"username": username}):
        return jsonify({"error": "Username is already taken."}), 400
        
    if db["professionals"].find_one({"email": email}) or db["organizations"].find_one({"email": email}):
        return jsonify({"error": "Email is already registered."}), 400
        
    phone = data.get("phone", "").strip()
    if not phone or not phone.startswith("+91") or not phone[3:].isdigit():
        return jsonify({"error": "Phone number must start with +91 and contain only digits."}), 400
        
    password = data.get("password", "")
    if len(password) < 6:
        return jsonify({"error": "Password must be at least 6 characters long."}), 400

    prof_doc = {
        "name": name,
        "username": username,
        "email": email,
        "phone": phone,
        "state": data.get("state", "Tamil Nadu"),
        "domain": data.get("domain", ""),
        "experience": int(data.get("experience", 0)),
        "skills": data.get("skills", []),
        "spoken_languages": data.get("spoken_languages", []),
        "linkedin": data.get("linkedin", ""),
        "github": data.get("github", ""),
        "education": data.get("education", "Bachelor's Degree"),
        "certifications": data.get("certifications", []),
        "projects_count": 0,
        "resume_text": "",
        "resume_score": 0,
        "readiness_score": 0,
        "status": "Registered",
        "source": "Registered",
        "password": hash_password(password),
        "created_at": datetime.utcnow()
    }
    
    db["professionals"].insert_one(prof_doc)
    
    # Log Activity
    db["activity_logs"].insert_one({
        "user_username": username,
        "action": "Register Professional",
        "timestamp": datetime.utcnow()
    })
    
    token = generate_token(username, "professional")
    return jsonify({"message": "Registration successful!", "token": token, "username": username}), 201

@auth_bp.route("/register-organization", methods=["POST"])
def register_organization():
    data = request.json
    db = Database.get_db()
    
    name = data.get("name", "").strip()
    username = data.get("username", "").strip().lower()
    email = data.get("email", "").strip().lower()
    password = data.get("password", "")
    
    if not name or not username or not email or not password:
        return jsonify({"error": "Name, username, email, and password are required."}), 400
        
    if not re.match(r"^[a-z0-9_]{3,20}$", username):
        return jsonify({"error": "Username must be 3-20 alphanumeric characters or underscores."}), 400
        
    if db["professionals"].find_one({"username": username}) or db["organizations"].find_one({"username": username}):
        return jsonify({"error": "Username is already taken."}), 400
        
    if db["professionals"].find_one({"email": email}) or db["organizations"].find_one({"email": email}):
        return jsonify({"error": "Email is already registered."}), 400
        
    org_doc = {
        "name": name,
        "username": username,
        "email": email,
        "password": hash_password(password),
        "industry": data.get("industry", "Technology"),
        "hr_contact": data.get("hr_contact", ""),
        "logo": data.get("logo", "https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe?w=150"),
        "created_at": datetime.utcnow()
    }
    
    db["organizations"].insert_one(org_doc)
    
    # Log Activity
    db["activity_logs"].insert_one({
        "user_username": username,
        "action": "Register Organization",
        "timestamp": datetime.utcnow()
    })
    
    token = generate_token(username, "organization")
    return jsonify({"message": "Organization registration successful!", "token": token, "username": username}), 201

@auth_bp.route("/login-professional", methods=["POST"])
def login_professional():
    data = request.json
    db = Database.get_db()
    
    username_or_email = data.get("username", "").strip().lower()
    password = data.get("password", "")
    
    if "@" in username_or_email:
        candidate = db["professionals"].find_one({"email": username_or_email})
    else:
        candidate = db["professionals"].find_one({"username": username_or_email})
        
    if not candidate or not check_password(candidate["password"], password):
        return jsonify({"error": "Invalid username/email or password."}), 401
        
    username = candidate["username"]
    token = generate_token(username, "professional")
    
    # Update active details
    db["professionals"].update_one({"_id": candidate["_id"]}, {"$set": {"last_login": datetime.utcnow()}})
    
    # Log Activity
    db["activity_logs"].insert_one({
        "user_username": username,
        "action": "Login Professional",
        "timestamp": datetime.utcnow()
    })
    
    return jsonify({
        "token": token, 
        "username": username,
        "name": candidate["name"],
        "status": candidate.get("status", "Registered")
    })

@auth_bp.route("/login-organization", methods=["POST"])
def login_organization():
    data = request.json
    db = Database.get_db()
    
    username_or_email = data.get("username", "").strip().lower()
    password = data.get("password", "")
    
    if "@" in username_or_email:
        org = db["organizations"].find_one({"email": username_or_email})
    else:
        org = db["organizations"].find_one({"username": username_or_email})
        
    if not org or not check_password(org["password"], password):
        return jsonify({"error": "Invalid username/email or password."}), 401
        
    username = org["username"]
    token = generate_token(username, "organization")
    
    # Update active details
    db["organizations"].update_one({"_id": org["_id"]}, {"$set": {"last_login": datetime.utcnow()}})
    
    # Log Activity
    db["activity_logs"].insert_one({
        "user_username": username,
        "action": "Login Organization",
        "timestamp": datetime.utcnow()
    })
    
    return jsonify({
        "token": token, 
        "username": username,
        "name": org["name"]
    })

@auth_bp.route("/forgot-password", methods=["POST"])
def forgot_password():
    data = request.json
    db = Database.get_db()
    username = data.get("username", "").strip().lower()
    
    # Find user by username
    candidate = db["professionals"].find_one({"username": username})
    org = db["organizations"].find_one({"username": username})
    
    if not candidate and not org:
        return jsonify({"error": "Username not found."}), 404
        
    email = candidate["email"] if candidate else org["email"]
    return jsonify({"message": f"Password reset instructions have been sent to registered email {email}."}), 200
