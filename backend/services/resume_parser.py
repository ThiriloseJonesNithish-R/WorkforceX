import pdfplumber
import re
import os
from backend.database.mongo import Database

def extract_text_from_pdf(pdf_path: str) -> str:
    text = ""
    try:
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
    except Exception as e:
        print(f"Error parsing PDF: {e}")
    return text

def parse_resume_details(pdf_path: str) -> dict:
    text = extract_text_from_pdf(pdf_path)
    
    # 1. Clean Text for matching
    cleaned_text = re.sub(r'\s+', ' ', text)
    cleaned_text_lower = cleaned_text.lower()
    
    # 2. Extract Skills dynamically from MongoDB skills collection
    extracted_skills = []
    try:
        db = Database.get_db()
        # Fetch all skills from the collection
        all_skills = [s["name"] for s in db["skills"].find({}, {"name": 1})]
        for skill in all_skills:
            # Match word boundary to avoid partial matches (e.g. 'C' matching 'Cloud')
            pattern = r'\b' + re.escape(skill.lower()) + r'\b'
            if re.search(pattern, cleaned_text_lower):
                extracted_skills.append(skill)
    except Exception as e:
        print(f"Error loading skills from database for parser: {e}")
        # Basic fallback list of typical skills
        fallback_skills = ["Python", "SQL", "Machine Learning", "Deep Learning", "Power BI", "Cybersecurity", "Java", "C++", "Docker", "AWS", "Git"]
        for skill in fallback_skills:
            if skill.lower() in cleaned_text_lower:
                extracted_skills.append(skill)

    # 3. Extract Experience Years
    # Look for patterns like "5 years", "3+ years", "experience of 4 years", etc.
    exp_pattern = re.compile(r'(\d+)\+?\s*years?\s+(?:of\s+)?experience|experience\s+(?:of\s+)?(\d+)\+?\s*years?', re.IGNORECASE)
    match = exp_pattern.search(cleaned_text_lower)
    experience_years = 0
    if match:
        experience_years = int(match.group(1) or match.group(2))
    else:
        # Fallback check for single digits before "years"
        simple_pattern = re.compile(r'\b(\d{1,2})\b\s*years?', re.IGNORECASE)
        match_simple = simple_pattern.search(cleaned_text_lower)
        if match_simple:
            experience_years = int(match_simple.group(1))

    # 4. Extract Education
    education = "Bachelor's Degree" # Default fallback
    edu_keywords = {
        "phd": "PhD / Doctorate",
        "doctorate": "PhD / Doctorate",
        "master": "Master's Degree (MBA/MS/MTech)",
        "mba": "Master's Degree (MBA)",
        "m.tech": "Master's Degree (MTech)",
        "mtech": "Master's Degree (MTech)",
        "b.tech": "Bachelor's Degree (BTech)",
        "btech": "Bachelor's Degree (BTech)",
        "bachelor": "Bachelor's Degree",
        "b.sc": "Bachelor's Degree (BSc)",
        "bsc": "Bachelor's Degree (BSc)",
        "b.e": "Bachelor's Degree (BE)",
        "be": "Bachelor's Degree (BE)"
    }
    for keyword, label in edu_keywords.items():
        if keyword in cleaned_text_lower:
            education = label
            break

    # 5. Extract Certifications
    certifications = []
    cert_keywords = [
        "AWS Certified", "Google Cloud", "Microsoft Certified", "Azure", 
        "PMP", "Certified ScrumMaster", "CSM", "CISSP", "CEH", "CCNA",
        "TensorFlow Developer", "Google ML", "Deep Learning Specialization"
    ]
    for cert in cert_keywords:
        if cert.lower() in cleaned_text_lower:
            certifications.append(cert)

    return {
        "skills": list(set(extracted_skills)),
        "experience": experience_years,
        "education": education,
        "certifications": certifications,
        "resume_text": text
    }
