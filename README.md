# WorkForceX

## AI-Powered Workforce Liquidity Platform

WorkForceX is an AI-powered Workforce Liquidity Platform designed to connect workforce supply and workforce demand in real time.

Organizations often face delays in acquiring skilled professionals when project requirements increase. At the same time, many talented individuals remain unemployed, underemployed, or disconnected from relevant opportunities.

WorkForceX aims to bridge this gap by creating a Workforce Liquidity Network where organizations can access deployment-ready professionals quickly while enabling talent to continuously access meaningful work opportunities.

---

## One-Line Pitch

> 💡 **"WorkForceX is the Workforce Liquidity Platform that enables organizations to access project-ready professionals instantly while enabling talent to continuously access work opportunities—making workforce availability as seamless as ordering food or booking a ride."**

---

## Vision

To build the infrastructure layer for workforce availability, allowing organizations to access workforce capacity on demand and helping professionals connect with opportunities faster than traditional hiring models.

---

## Problem Statement

Traditional hiring processes are often:
* ⏳ **Slow and time-consuming**
* 💸 **Expensive to execute**
* 📉 **Difficult to scale**
* 🔄 **Reactive instead of proactive**

Organizations experience talent shortages while skilled professionals remain available but inaccessible.
The problem is not the lack of talent. **The problem is the lack of workforce liquidity.**

WorkForceX addresses this challenge through intelligent workforce matching, workforce readiness validation, workforce inventory management, and AI-powered deployment recommendations.

---

## Core Features

### 🏅 Workforce Readiness Score
Evaluate deployment readiness using technical skills, certifications, assessments, communication ability, and project outcomes.

### 🧠 AI Workforce Matching Engine
Match professionals based on skills, experience, availability, project requirements, and team compatibility.

### 🤝 Smart Team Builder
Automatically assemble optimized project teams for organizational requirements.

### 🔄 Workforce Continuity Engine
Provide workforce replacement recommendations to reduce project disruption.

### 🪪 Candidate Growth Passport
Maintain verified records of skills, certifications, assessments, project history, and workforce performance.

### 📊 Workforce Demand Forecasting
Predict workforce shortages and future workforce requirements using AI-driven analytics.

---

## How to Run the Platform (Step-by-Step)

The platform is designed to be fully self-contained. All dependencies and database engines are stored locally in the workspace.

### 1. Prerequisites
Make sure you have Python installed, then install the required dependencies:
```bash
pip install -r backend/requirements.txt
```

### 2. Launching the Application
Simply run the orchestrator script from the root workspace directory. This will start the database, load seed datasets, launch both backend and frontend servers, and open the browser automatically:
```bash
python app.py
```

Open your browser and navigate to **`http://localhost:8501`** (it will open automatically).
To stop all running services, press `Ctrl+C` in the terminal.

---

## Seed Accounts for Testing & Walkthrough

Use these pre-configured accounts to experience the full end-to-end recruitment cycle:

### 👤 1. Candidate Portal Login
* **Email:** `wesleyroman2@workforcex.com`
* **Password:** `password123`
* **Workflow:** Go to **AI Assessment** tab $\rightarrow$ Take test (e.g. SQL: *Structured Query Language*, HAVING: *HAVING*, corr: *corr()*) $\rightarrow$ Submit to become **Deployment Ready**.

### 🏢 2. Recruiter Portal Login
* **Email:** `hr@techcorp.com`
* **Password:** `password123`
* **Workflow:** Go to **Create New Project** tab $\rightarrow$ Create a Data Scientist project $\rightarrow$ View matches in **Projects & AI Match** $\rightarrow$ Invite Wesley Roman.

---

## Repository Structure

```text
WorkForceX
│
├── backend                 # Flask REST API & Core AI Services
│   ├── database            # MongoDB Connections & Setup
│   ├── routes              # API Endpoints (Auth, Profile, Project, Analytics)
│   ├── services            # AI Matching, Resume Parsing, & Analysis
│   └── requirements.txt    # Backend dependencies
│
├── frontend                # Streamlit Dashboard & Interface
│   ├── views               # Pages (Auth, Organization Dashboard, Professional Dashboard, Reports)
│   ├── components          # Reusable Streamlit components & styled UI cards
│   └── styles              # Custom styling (CSS overrides)
│
├── datasets                # Preprocessed and Cleaned Datasets
│   ├── AI_Resume_Screening_Cleaned.csv
│   └── indian-job-market-dataset-2025_Preprocessed.csv
│
├── mongodb_loader          # Automation scripts to download MongoDB Portable & load seed datasets
│
├── app.py                  # One-click platform orchestrator
├── .gitignore              # Configured Git Exclusions
├── LICENSE                 # License terms
└── README.md               # Project documentation
```

---

## Current Project Phase

**Phase 1 – Research, Documentation, Dataset Preparation, and Project Planning**

Current activities include:
* Problem validation
* Research and market analysis
* Dataset collection
* Data cleaning and preprocessing
* Architecture planning
* Feature definition
* Project documentation

---

## Project Team

| Team Member               | GitHub Profile                                         |
| ------------------------- | ------------------------------------------------------ |
| Thirilose Jones Nithish R | [@thirilose-learn](https://github.com/thirilose-learn) |
| Kalyan G                  | [@kalyan-0911](https://github.com/kalyan-0911)         |
| Sabitha R J               | [@sabitha2311](https://github.com/sabitha2311)         |
| Kavya S                   | [@kavyas0215-bit](https://github.com/kavyas0215-bit)   |
| Sowndaryagowri N          | [@sowndigowri](https://github.com/sowndigowri)         |

### Team Responsibilities
* **Project Lead & Repository Management:** Thirilose Jones Nithish R
* **Research & Documentation:** Team Work
* **Data Collection & Preprocessing:** Team Work
* **Analysis & Development:** Team Work
* **Presentation & Demonstration:** Team Work

---

## Future Roadmap

### Phase 1 – IT Workforce Cloud
* Software Developers
* Data Analysts
* QA Engineers
* UI/UX Designers
* DevOps Engineers

### Phase 2 – Business Workforce Cloud
* HR Professionals
* Sales Teams
* Marketing Specialists
* Customer Support Teams

### Phase 3 – Skilled Workforce Cloud
* Technicians
* Electricians
* Operators
* Field Engineers

### Phase 4 – Global Workforce Liquidity Network
A unified platform enabling organizations to access workforce capacity across industries, locations, and skill categories.

---

## Expected Impact

* Reduce workforce acquisition time
* Improve workforce utilization
* Accelerate project delivery
* Reduce unemployment friction
* Create opportunities for fresh graduates
* Improve workforce mobility
* Build a transparent workforce ecosystem

---

## License

This repository is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

```text
MIT License

Copyright (c) 2026 WorkforceX Contributors

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```
