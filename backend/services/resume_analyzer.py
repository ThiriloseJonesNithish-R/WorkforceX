import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from datetime import datetime
from backend.database.mongo import Database

# Define standard role profiles with their descriptions and core skills
ROLE_PROFILES = {
    "Data Scientist": {
        "description": "data science python machine learning deep learning sql statistics r pandas scikit-learn predictive modeling neural networks data visualization tensorflow pytorch",
        "skills": ["Python", "Machine Learning", "Deep Learning", "SQL", "Statistics", "R", "Pandas", "Scikit-Learn", "TensorFlow", "PyTorch"]
    },
    "Data Analyst": {
        "description": "data analysis sql python power bi excel tableau statistics dashboard metrics reports business intelligence data cleansing data modeling",
        "skills": ["SQL", "Python", "Power BI", "Excel", "Tableau", "Data Analysis", "Statistics"]
    },
    "AI Engineer": {
        "description": "artificial intelligence python deep learning machine learning nlp tensorflow pytorch generative ai llm computer vision neural networks transformer models",
        "skills": ["Python", "Deep Learning", "Machine Learning", "NLP", "TensorFlow", "PyTorch", "Generative AI", "LLM"]
    },
    "Cybersecurity Analyst": {
        "description": "cybersecurity ethical hacking linux network security cryptography penetration testing firewalls vulnerability assessment siem owasp threat hunting information security",
        "skills": ["Ethical Hacking", "Cybersecurity", "Linux", "Network Security", "Cryptography", "Penetration Testing", "Firewalls", "Vulnerability Assessment"]
    },
    "Software Engineer": {
        "description": "software development engineering java python c++ c# git data structures algorithms docker rest api backend frontend system design agile databases web",
        "skills": ["Java", "Python", "C++", "C#", "Git", "Data Structures", "Algorithms", "Docker", "REST API"]
    },
    "Cloud Architect": {
        "description": "cloud architect computing aws azure google cloud docker kubernetes devops terraform networking infrastructure security lambda microservices serverless",
        "skills": ["AWS", "Azure", "Cloud Computing", "Docker", "Kubernetes", "DevOps", "Terraform"]
    }
}

def analyze_resume(parsed_details: dict) -> dict:
    resume_text = parsed_details.get("resume_text", "")
    skills = parsed_details.get("skills", [])
    experience = parsed_details.get("experience", 0)
    certifications = parsed_details.get("certifications", [])
    education = parsed_details.get("education", "Bachelor's Degree")
    
    if not resume_text:
        resume_text = " ".join(skills) + " " + str(education) + " " + " ".join(certifications)

    # 1. Semantic Matching for Recommended Role
    role_names = list(ROLE_PROFILES.keys())
    profiles_text = [ROLE_PROFILES[role]["description"] for role in role_names]
    
    # We combine resume text with standard profiles to perform TF-IDF cosine similarity
    corpus = [resume_text] + profiles_text
    vectorizer = TfidfVectorizer(stop_words='english')
    tfidf_matrix = vectorizer.fit_transform(corpus)
    
    # Calculate similarity between resume (index 0) and all profiles (index 1 to N)
    similarities = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:]).flatten()
    
    # Get index of best matching role
    best_idx = int(np.argmax(similarities))
    recommended_role = role_names[best_idx]
    role_match_score = float(similarities[best_idx])
    
    # 2. Extract Strengths and Weaknesses/Missing Skills
    role_required_skills = ROLE_PROFILES[recommended_role]["skills"]
    
    strengths = [s for s in skills if s.lower() in [rs.lower() for rs in role_required_skills]]
    # Other general skills are also strengths
    other_strengths = [s for s in skills if s.lower() not in [rs.lower() for rs in role_required_skills]]
    all_strengths = list(set(strengths + other_strengths[:2]))
    
    missing_skills = [rs for rs in role_required_skills if rs.lower() not in [s.lower() for s in skills]]
    weaknesses = missing_skills[:3]
    if not weaknesses:
        weaknesses = ["System Design", "Cloud Projects"] # Default general gaps if perfect fit
        
    # 3. Calculate Scores
    # Skill match score: percentage of recommended role's required skills present in candidate's skills
    role_skills_present = [rs for rs in role_required_skills if rs.lower() in [s.lower() for s in skills]]
    skill_match_pct = len(role_skills_present) / len(role_required_skills) if role_required_skills else 0.5
    
    # Scale components
    skills_points = min(30, len(skills) * 3) # Max 30
    experience_points = min(15, experience * 1.5) # Max 15
    certifications_points = min(15, len(certifications) * 5) # Max 15
    
    # Education weight
    edu_points = 10
    edu_lower = education.lower()
    if "phd" in edu_lower or "doctorate" in edu_lower:
        edu_points = 15
    elif "master" in edu_lower or "mba" in edu_lower:
        edu_points = 13
        
    # Role match points: cosine similarity * 25
    role_match_points = min(25, role_match_score * 40)
    
    # Additional projects points
    projects_points = min(5, parsed_details.get("projects_count", 0) * 1.0)
    
    # Total Score out of 100
    resume_score = int(np.clip(skills_points + experience_points + certifications_points + edu_points + role_match_points + projects_points, 30, 100))
    
    # Readiness Score out of 100
    readiness_score = int(np.clip(resume_score - 5, 20, 98))
    
    # 4. Suggestions
    suggestions_list = []
    if missing_skills:
        suggestions_list.append(f"Acquire missing skills: {', '.join(missing_skills[:3])}.")
    if not certifications:
        suggestions_list.append("Obtain professional certifications in your domain (e.g. AWS, Azure, Google Cloud, or Cisco) to boost profile visibility.")
    if experience < 3:
        suggestions_list.append("Work on more hands-on github projects to showcase practical experience.")
    
    suggestions = " ".join(suggestions_list) if suggestions_list else "Your profile looks excellent! Focus on keeping up with current industry trends."

    return {
        "score": resume_score,
        "strengths": all_strengths if all_strengths else ["General Competence"],
        "weaknesses": weaknesses,
        "missing_skills": missing_skills,
        "suggestions": suggestions,
        "career_recommendation": recommended_role,
        "readiness_score": readiness_score
    }
