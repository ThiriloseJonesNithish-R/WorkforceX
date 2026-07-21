import os
import pandas as pd
import pymongo
from datetime import datetime
import hashlib
import bcrypt

def hash_password(password: str) -> str:
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

def load_data():
    client = pymongo.MongoClient(os.environ.get("MONGO_URI", "mongodb+srv://sowndi_gowri:sowndi_gowri@unicorn.vduucnx.mongodb.net/?appName=Unicorn"))
    db = client["WorkForceX"]
    
    # 1. Clear existing collections
    collections_to_drop = [
        "professionals", "organizations", "projects", "assessments", 
        "assessment_attempts", "skills", "jobs", "resume_scores", 
        "candidate_match", "invitations", "notifications", "reports", 
        "courses", "activity_logs"
    ]
    for col in collections_to_drop:
        db[col].drop()
    print("Dropped existing collections to start fresh.")

    # 2. Seed Skills Set
    skills_set = set()

    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    # Load AI Resume Screening
    resume_path = os.path.join(base_dir, "datasets", "AI_Resume_Screening_Cleaned.csv")
    if os.path.exists(resume_path):
        resumes_df = pd.read_csv(resume_path)
        print(f"Loaded {len(resumes_df)} resumes from CSV.")
        
        professionals_list = []
        for idx, row in resumes_df.iterrows():
            skills_raw = str(row['Skills']) if not pd.isna(row['Skills']) else ""
            skills_list = [s.strip() for s in skills_raw.split(',') if s.strip()]
            for s in skills_list:
                skills_set.add(s)
                
            name = str(row['Name']).strip()
            username = name.lower().replace(' ', '') + str(row['Resume_ID'])
            email = f"{username}@workforcex.com"
            
            prof = {
                "resume_id": int(row['Resume_ID']),
                "name": name,
                "username": username,
                "email": email,
                "phone": f"+9198765{int(row['Resume_ID']):05d}",
                "state": "Tamil Nadu",
                "domain": str(row['Job Role']).strip(),
                "experience": int(row['Experience (Years)']) if not pd.isna(row['Experience (Years)']) else 0,
                "skills": skills_list,
                "spoken_languages": ["English", "Tamil", "Hindi"],
                "linkedin": f"https://linkedin.com/in/{name.lower().replace(' ', '-')}",
                "github": f"https://github.com/{name.lower().replace(' ', '-')}",
                "education": str(row['Education']).strip() if not pd.isna(row['Education']) else "Bachelor's Degree",
                "certifications": [str(row['Certifications']).strip()] if not pd.isna(row['Certifications']) else [],
                "projects_count": int(row['Projects Count']) if not pd.isna(row['Projects Count']) else 0,
                "resume_text": f"Resume of {name}. Experience: {row['Experience (Years)']} years. Skills: {skills_raw}. Certifications: {row['Certifications']}.",
                "resume_score": int(row['AI Score (0-100)']) if not pd.isna(row['AI Score (0-100)']) else 70,
                "readiness_score": int(row['AI Score (0-100)']) - 5 if not pd.isna(row['AI Score (0-100)']) else 65,
                "status": "Deployment Ready",
                "source": "Database",
                "password": hash_password("password123"),
                "created_at": datetime.utcnow()
            }
            professionals_list.append(prof)
            
            # Seed resume details in resume_scores too
            db["resume_scores"].insert_one({
                "candidate_username": username,
                "candidate_email": email,
                "score": prof["resume_score"],
                "strengths": skills_list[:3],
                "weaknesses": ["Cloud Computing" if "Cloud" not in skills_raw else "System Design"],
                "missing_skills": ["AWS", "Docker"],
                "suggestions": "Build projects using cloud providers and improve system design concepts.",
                "career_recommendation": f"Suitable for {prof['domain']}",
                "readiness_score": prof["readiness_score"],
                "updated_at": datetime.utcnow()
            })
            
        if professionals_list:
            db["professionals"].insert_many(professionals_list)
            print(f"Imported {len(professionals_list)} professionals into MongoDB.")
    else:
        print("Error: AI_Resume_Screening_Cleaned.csv not found!")

    # Load Indian Job Market Dataset
    jobs_path = os.path.join(base_dir, "datasets", "indian-job-market-dataset-2025_Preprocessed.csv")
    if os.path.exists(jobs_path):
        jobs_df = pd.read_csv(jobs_path)
        print(f"Loaded {len(jobs_df)} jobs from CSV.")
        
        jobs_list = []
        for idx, row in jobs_df.iterrows():
            skills_raw = str(row['tagsAndSkills']) if not pd.isna(row['tagsAndSkills']) else ""
            skills_list = [s.strip() for s in skills_raw.split(',') if s.strip()]
            for s in skills_list:
                skills_set.add(s)
                
            job = {
                "job_id": str(row['jobId']),
                "title": str(row['title']).strip(),
                "company_name": str(row['companyName']).strip() if not pd.isna(row['companyName']) else "Confidential",
                "tags_and_skills": skills_list,
                "experience_range": str(row['experience']).strip(),
                "salary": str(row['salary']).strip(),
                "location": str(row['location']).strip(),
                "description": str(row['jobDescription']).strip(),
                "min_salary": float(row['minimumSalary']) if not pd.isna(row['minimumSalary']) else 0.0,
                "max_salary": float(row['maximumSalary']) if not pd.isna(row['maximumSalary']) else 0.0,
                "min_experience": int(row['minimumExperience']) if not pd.isna(row['minimumExperience']) else 0,
                "max_experience": int(row['maximumExperience']) if not pd.isna(row['maximumExperience']) else 0,
                "created_at": datetime.utcnow()
            }
            jobs_list.append(job)
            
        if jobs_list:
            db["jobs"].insert_many(jobs_list[:1000])
            print(f"Imported {min(len(jobs_list), 1000)} jobs into MongoDB.")
    else:
        print("Error: indian-job-market-dataset-2025_Preprocessed.csv not found!")

    # 3. Seed Skills collection
    if skills_set:
        db["skills"].insert_many([{"name": s} for s in sorted(list(skills_set))])
        print(f"Imported {len(skills_set)} unique skills into MongoDB.")

    # 4. Seed Assessments
    assessments_seed = [
        {"skill": "Data Analyst", "difficulty": "Easy", "question": "What does SQL stand for?", "options": ["Structured Query Language", "Sequential Query Language", "Structured Question Language", "Simple Query Language"], "answer": "Structured Query Language"},
        {"skill": "Data Analyst", "difficulty": "Medium", "question": "Which SQL clause is used to filter records in a group?", "options": ["WHERE", "HAVING", "GROUP BY", "ORDER BY"], "answer": "HAVING"},
        {"skill": "Data Analyst", "difficulty": "Hard", "question": "In pandas, which function is used to compute the pairwise correlation of columns?", "options": ["corr()", "cov()", "describe()", "std()"], "answer": "corr()"},
        {"skill": "Data Analyst", "difficulty": "Medium", "question": "Which SQL command is used to remove a table's structure and data?", "options": ["DROP TABLE", "DELETE TABLE", "REMOVE TABLE", "TRUNCATE TABLE"], "answer": "DROP TABLE"},
        {"skill": "Data Analyst", "difficulty": "Easy", "question": "Which pandas function is used to check for missing values?", "options": ["isna()", "isnull()", "missing()", "check_null()"], "answer": "isnull()"},
        
        {"skill": "Machine Learning", "difficulty": "Easy", "question": "Which of the following is a type of supervised learning?", "options": ["K-Means Clustering", "Linear Regression", "Apriori Algorithm", "PCA"], "answer": "Linear Regression"},
        {"skill": "Machine Learning", "difficulty": "Medium", "question": "What is the primary purpose of regularization (L1/L2) in Machine Learning?", "options": ["To increase training speed", "To prevent overfitting", "To perform feature selection only", "To increase bias to 0"], "answer": "To prevent overfitting"},
        {"skill": "Machine Learning", "difficulty": "Hard", "question": "What does Gini impurity measure in a Decision Tree?", "options": ["The entropy of the split", "The probability of misclassifying a chosen element", "The depth of the tree", "The leaf node count"], "answer": "The probability of misclassifying a chosen element"},
        {"skill": "Machine Learning", "difficulty": "Medium", "question": "Which metric is commonly used to evaluate a classification model's performance on imbalanced datasets?", "options": ["Accuracy", "F1-Score", "Mean Squared Error", "R-Squared"], "answer": "F1-Score"},
        {"skill": "Machine Learning", "difficulty": "Easy", "question": "What is overfitting in machine learning?", "options": ["Model performs well on training data but poorly on unseen test data", "Model performs poorly on both training and test data", "Model performs well on both training and test data", "None of the above"], "answer": "Model performs well on training data but poorly on unseen test data"},

        {"skill": "Python", "difficulty": "Easy", "question": "Which keyword is used to define a function in Python?", "options": ["func", "define", "def", "function"], "answer": "def"},
        {"skill": "Python", "difficulty": "Medium", "question": "What is the output of `print([1, 2] * 2)`?", "options": ["`[2, 4]`", "`[1, 2, 1, 2]`", "Error", "`[1, 2, 2, 4]`"], "answer": "`[1, 2, 1, 2]`"},
        {"skill": "Python", "difficulty": "Hard", "question": "What is the difference between `__init__` and `__new__` in Python?", "options": ["__init__ is the initializer, __new__ is the actual creator of the object", "__new__ is the initializer, __init__ is the creator", "They are identical", "None of the above"], "answer": "__init__ is the initializer, __new__ is the actual creator of the object"},
        {"skill": "Python", "difficulty": "Easy", "question": "How do you insert an element at a specific index in a Python list?", "options": ["insert()", "append()", "add()", "push()"], "answer": "insert()"},
        {"skill": "Python", "difficulty": "Easy", "question": "Which of the following data types is immutable in Python?", "options": ["List", "Dictionary", "Tuple", "Set"], "answer": "Tuple"},

        {"skill": "SQL", "difficulty": "Easy", "question": "Which SQL statement is used to retrieve data?", "options": ["GET", "OPEN", "SELECT", "EXTRACT"], "answer": "SELECT"},
        {"skill": "SQL", "difficulty": "Medium", "question": "Which join returns all rows when there is a match in one of the tables?", "options": ["INNER JOIN", "LEFT JOIN", "RIGHT JOIN", "FULL OUTER JOIN"], "answer": "FULL OUTER JOIN"},
        {"skill": "SQL", "difficulty": "Hard", "question": "What is the difference between TRUNCATE and DELETE in SQL?", "options": ["DELETE is a DDL command, TRUNCATE is DML", "DELETE removes rows one by one and logs them, TRUNCATE deallocates pages and is faster", "They perform the exact same operation with no internal differences", "TRUNCATE can have a WHERE clause"], "answer": "DELETE removes rows one by one and logs them, TRUNCATE deallocates pages and is faster"},
        {"skill": "SQL", "difficulty": "Easy", "question": "Which SQL constraint uniquely identifies each record in a database table?", "options": ["FOREIGN KEY", "UNIQUE", "PRIMARY KEY", "CHECK"], "answer": "PRIMARY KEY"},
        {"skill": "SQL", "difficulty": "Easy", "question": "Which aggregate function is used to find the average value in SQL?", "options": ["AVG()", "MEAN()", "SUM()", "COUNT()"], "answer": "AVG()"},

        {"skill": "Cybersecurity", "difficulty": "Easy", "question": "What is phishing?", "options": ["A method to scan network ports", "A form of social engineering to steal sensitive data", "A software testing technique", "An encryption algorithm"], "answer": "A form of social engineering to steal sensitive data"},
        {"skill": "Cybersecurity", "difficulty": "Medium", "question": "What does CIA triad stand for in security?", "options": ["Central Intelligence Agency", "Confidentiality, Integrity, Availability", "Control, Integrity, Authorization", "Cryptographic Integrity Algorithm"], "answer": "Confidentiality, Integrity, Availability"},
        {"skill": "Cybersecurity", "difficulty": "Hard", "question": "Which of the following describes a 'Man-in-the-Middle' (MitM) attack?", "options": ["An attacker guessing passwords sequentially", "An attacker relaying and possibly altering communication between two parties who believe they are directly communicating", "An attacker flooding a server with requests to bring it down", "An attacker breaking physical locks to enter server rooms"], "answer": "An attacker relaying and possibly altering communication between two parties who believe they are directly communicating"},
        {"skill": "Cybersecurity", "difficulty": "Easy", "question": "What does HTTPS stand for?", "options": ["Hypertext Transfer Protocol Secure", "Hypertext Transfer Protocol Standard", "High-security Text Transfer Protocol", "None of the above"], "answer": "Hypertext Transfer Protocol Secure"},
        {"skill": "Cybersecurity", "difficulty": "Easy", "question": "Which type of malware replicates itself to spread to other computers?", "options": ["Trojan Horse", "Worm", "Spyware", "Adware"], "answer": "Worm"}
    ]
    db["assessments"].insert_many(assessments_seed)
    print(f"Imported {len(assessments_seed)} MCQ assessment questions.")

    # 5. Seed Organizations
    organizations_seed = [
        {
            "name": "TechCorp Solutions",
            "username": "techcorp",
            "email": "hr@techcorp.com",
            "password": hash_password("password123"),
            "industry": "Software Engineering",
            "hr_contact": "John Doe",
            "logo": "https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe?w=150",
            "last_login": datetime.utcnow(),
            "created_at": datetime.utcnow()
        },
        {
            "name": "Innovate Analytics",
            "username": "innovate",
            "email": "hr@innovate.com",
            "password": hash_password("password123"),
            "industry": "Data Science & AI",
            "hr_contact": "Sarah Smith",
            "logo": "https://images.unsplash.com/photo-1542744094-3a31f103e35f?w=150",
            "last_login": datetime.utcnow(),
            "created_at": datetime.utcnow()
        }
    ]
    db["organizations"].insert_many(organizations_seed)
    print("Imported default Organizations (TechCorp Solutions & Innovate Analytics).")

    # 6. Seed Courses
    courses_seed = [
        {"name": "Python for Data Science and AI", "provider": "Coursera (IBM)", "url": "https://www.coursera.org/learn/python-for-applied-data-science-ai", "skills": ["Python", "Data Science"]},
        {"name": "Microsoft Certified: Azure Data Scientist Associate", "provider": "Microsoft Learn", "url": "https://learn.microsoft.com/en-us/credentials/certifications/azure-data-scientist", "skills": ["Azure", "Machine Learning"]},
        {"name": "The Ultimate MySQL Bootcamp", "provider": "Udemy", "url": "https://www.udemy.com/course/the-ultimate-mysql-bootcamp-go-from-sql-beginner-to-expert/", "skills": ["SQL", "Databases"]},
        {"name": "Machine Learning Specialization", "provider": "Coursera (DeepLearning.AI)", "url": "https://www.coursera.org/specializations/machine-learning-introduction", "skills": ["Machine Learning", "Scikit-Learn"]},
        {"name": "Google Cybersecurity Professional Certificate", "provider": "Coursera (Google)", "url": "https://www.coursera.org/professional-certificates/google-cybersecurity", "skills": ["Cybersecurity", "Network Security"]}
    ]
    db["courses"].insert_many(courses_seed)
    print("Imported Career Guidance courses.")

if __name__ == "__main__":
    load_data()
