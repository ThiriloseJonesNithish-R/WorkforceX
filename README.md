# WorkForceX - AI-Powered Workforce Liquidity Platform

WorkForceX is a modern, AI-powered workforce recruitment and liquification platform. It utilizes a Flask REST API backend, Streamlit dark-mode frontend, and MongoDB database to manage professional profile matching, automated resume parsing, MCQ skill testing, and corporate project hiring.

---

## Workspace Setup

The platform is designed to be fully self-contained. All dependencies and database engines are stored locally in the workspace.

### Prerequisites
Make sure the required Python dependencies are installed:
```bash
pip install -r backend/requirements.txt
```

---

## How to Run the Platform (Step-by-Step)

Simply run the orchestrator script from the root workspace directory. This will start the database, load seed files, launch both backend and frontend servers, and open the browser automatically:

```bash
python app.py
```

That's it! Open your browser and go to:
**`http://localhost:8501`** (it will open automatically).

To stop all services, simply press `Ctrl+C` in the terminal running `app.py`.

---

## Testing & Verification
To run the automated end-to-end recruitment integration tests, verify that the backend server is running and execute:
```bash
python "c:\Work Force X\backend\tests\test_flow.py"
```

---

## Seed Accounts for Testing

### 1. Candidate Portal Login
* **Email:** `wesleyroman2@workforcex.com`
* **Password:** `password123`
* **Workflow:** Go to **AI Assessment** tab $\rightarrow$ Take test (SQL: *Structured Query Language*, HAVING: *HAVING*, corr: *corr()*) $\rightarrow$ Submit to become **Deployment Ready**.

### 2. Recruiter Portal Login
* **Email:** `hr@techcorp.com`
* **Password:** `password123`
* **Workflow:** Go to **Create New Project** tab $\rightarrow$ Create a Data Scientist project $\rightarrow$ View matches in **Projects & AI Match** $\rightarrow$ Invite Wesley Roman.
