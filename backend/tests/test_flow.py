import requests
import sys

API_URL = "http://localhost:5000/api"

def run_test():
    print("="*60)
    print("STARTING WORKFORCEX INTEGRATION TEST FLOW")
    print("="*60)
    
    # 1. Professional Login
    print("\nStep 1: Logging in as candidate (Wesley Roman)...")
    login_data = {
        "username": "wesleyroman2",
        "password": "password123"
    }
    res = requests.post(f"{API_URL}/auth/login-professional", json=login_data)
    assert res.status_code == 200, f"Login failed: {res.json()}"
    prof_token = res.json()["token"]
    prof_headers = {"Authorization": f"Bearer {prof_token}"}
    print("SUCCESS: Candidate logged in successfully.")
    
    # Check current candidate profile
    res = requests.get(f"{API_URL}/profile/me", headers=prof_headers)
    assert res.status_code == 200
    candidate = res.json()
    print(f"Candidate Current Status: {candidate['status']}")
    print(f"Candidate Skills: {candidate['skills']}")
    
    # 2. Get Assessment Questions
    print("\nStep 2: Retrieving custom skill assessment...")
    res = requests.get(f"{API_URL}/assessment/generate", headers=prof_headers)
    assert res.status_code == 200, f"Failed to generate assessment: {res.json()}"
    questions = res.json()["questions"]
    print(f"SUCCESS: Generated {len(questions)} questions on skill topic: {res.json()['skill']}")
    
    # 3. Submit Answers
    print("\nStep 3: Submitting correct answers to pass assessment...")
    answers = {}
    for q in questions:
        # Simple mapping to get correct answers for data analyst seeded questions
        if "SQL stand for" in q["question"]:
            answers[q["_id"]] = "Structured Query Language"
        elif "filter records in a group" in q["question"]:
            answers[q["_id"]] = "HAVING"
        elif "pairwise correlation of columns" in q["question"]:
            answers[q["_id"]] = "corr()"
        else:
            # Fallback to the first option if questions vary
            answers[q["_id"]] = q["options"][0]
            
    submit_data = {"answers": answers}
    res = requests.post(f"{API_URL}/assessment/submit", json=submit_data, headers=prof_headers)
    assert res.status_code == 200, f"Submit failed: {res.json()}"
    submit_res = res.json()
    print(f"SUCCESS: Assessment graded. Score: {submit_res['score']}% | Result: {submit_res['status']}")
    
    # Verify candidate is now Deployment Ready
    res = requests.get(f"{API_URL}/profile/me", headers=prof_headers)
    candidate = res.json()
    print(f"Candidate Updated Status: {candidate['status']}")
    assert candidate["status"] == "Deployment Ready", f"Expected Deployment Ready, got {candidate['status']}"
    print("SUCCESS: Status successfully transitioned to Deployment Ready!")
    
    # 4. Organization Login
    print("\nStep 4: Logging in as Organization HR (TechCorp Solutions)...")
    org_login_data = {
        "username": "techcorp",
        "password": "password123"
    }
    res = requests.post(f"{API_URL}/auth/login-organization", json=org_login_data)
    assert res.status_code == 200, f"Org login failed: {res.json()}"
    org_token = res.json()["token"]
    org_headers = {"Authorization": f"Bearer {org_token}"}
    print("SUCCESS: HR logged in successfully.")
    
    # 5. Create Staffing Project
    print("\nStep 5: Launching a new staffing project...")
    project_data = {
        "name": "E-Commerce Recommendation Engine",
        "client": "Retail Giant Corp",
        "department": "AI & Advanced Analytics",
        "role": "Data Scientist",
        "job_description": "Build high-throughput deep learning recommenders using Python, SQL, and Machine Learning.",
        "experience": 3,
        "primary_skills": ["Python", "SQL", "Machine Learning"],
        "secondary_skills": ["Deep Learning"],
        "certifications": ["Google ML"],
        "budget": "$150,000",
        "duration": "8 Months",
        "joining_date": "2026-08-01",
        "priority": "High",
        "resources_needed": 1,
        "work_mode": "Hybrid"
    }
    res = requests.post(f"{API_URL}/project/create", json=project_data, headers=org_headers)
    assert res.status_code == 201, f"Project creation failed: {res.json()}"
    project_id = res.json()["project_id"]
    print(f"SUCCESS: Project launched with ID: {project_id}")
    
    # 6. Run AI Matching Exporter
    print("\nStep 6: Running AI Candidate Matcher...")
    res = requests.get(f"{API_URL}/project/{project_id}/matches", headers=org_headers)
    assert res.status_code == 200, f"Matching failed: {res.json()}"
    matches = res.json()
    print("SUCCESS: AI Matcher finished. Top candidates:")
    for idx, match in enumerate(matches):
        print(f"  #{idx+1}: {match['candidate_name']} ({match['candidate_email']}) - Match Score: {match['match_score']}%")
        
    # Verify Wesley Roman is in matches
    matched_emails = [m["candidate_email"] for m in matches]
    assert "wesleyroman2@workforcex.com" in matched_emails, "Target candidate not found in matches!"
    print("SUCCESS: Wesley Roman matches the requirements and is returned as a top match.")
    
    # 7. Send Invitation
    print("\nStep 7: Sending project invitation to candidate...")
    invite_data = {
        "project_id": project_id,
        "candidate_email": "wesleyroman2@workforcex.com"
    }
    res = requests.post(f"{API_URL}/project/invite", json=invite_data, headers=org_headers)
    assert res.status_code == 200, f"Failed to send invitation: {res.json()}"
    print("SUCCESS: Project invitation sent successfully.")
    
    # Check Candidate Status -> should be Invitation Pending
    res = requests.get(f"{API_URL}/profile/me", headers=prof_headers)
    assert res.json()["status"] == "Invitation Pending"
    print("SUCCESS: Candidate status transitioned to: Invitation Pending.")
    
    # 8. Accept Invitation
    print("\nStep 8: Candidate accepting the project invitation...")
    # Fetch professional invitations list
    res = requests.get(f"{API_URL}/project/invitations", headers=prof_headers)
    assert res.status_code == 200
    invitations = res.json()
    target_invite = next(i for i in invitations if i["project_id"] == project_id)
    invite_id = target_invite["_id"]
    
    res = requests.post(f"{API_URL}/project/invitation/{invite_id}/respond", json={"response": "Accept"}, headers=prof_headers)
    assert res.status_code == 200, f"Decline/Accept failed: {res.json()}"
    
    # Verify Candidate Status is now Invitation Accepted
    res = requests.get(f"{API_URL}/profile/me", headers=prof_headers)
    assert res.json()["status"] == "Invitation Accepted"
    print("SUCCESS: Candidate accepted invitation. Status: Invitation Accepted")
    
    # 9. Hire Candidate
    print("\nStep 9: HR confirmed candidate and click Hire Candidate...")
    hire_data = {"candidate_email": "wesleyroman2@workforcex.com"}
    res = requests.post(f"{API_URL}/project/{project_id}/hire", json=hire_data, headers=org_headers)
    assert res.status_code == 200, f"Hiring failed: {res.json()}"
    hire_res = res.json()
    print(f"SUCCESS: Hiring response: {hire_res['message']} | Project Status: {hire_res['project_status']}")
    
    # 10. Check Final Candidate Status
    print("\nStep 10: Verifying final candidate status...")
    res = requests.get(f"{API_URL}/profile/me", headers=prof_headers)
    assert res.status_code == 200
    candidate = res.json()
    print(f"Candidate Final Status: {candidate['status']}")
    print(f"Hired Details: Company: {candidate.get('company')}, Project: {candidate.get('project')}, Role: {candidate.get('role')}")
    
    assert candidate["status"] == "Working on Project", f"Expected Working on Project, got {candidate['status']}"
    print("\n" + "="*60)
    print("ALL END-TO-END WORKFLOW INTEGRATION TESTS PASSED SUCCESSFULLY!")
    print("="*60)

if __name__ == "__main__":
    try:
        run_test()
    except AssertionError as e:
        print(f"TEST FAILED: {e}")
        sys.exit(1)
