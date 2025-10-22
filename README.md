# 🧮 Underwriting Dashboard — AI-Assisted Risk Engine (MVP)

A modular underwriting workflow prototype that automates intake, extraction, and rule validation for insurance submissions.  
Built with **Python + Streamlit + SQLModel**, this dashboard demonstrates how AI can streamline underwriting while preserving transparency and auditability.

---

## 🚀 Current Features

### ✅ Step 0 — Scaffold & Repo Hygiene
- Clean modular structure (`app/`, `rules/`, `data/`, `db/`)
- `.env`, `.gitignore`, `.pre-commit-config.yaml` for reproducibility  
- Virtual environment support (`.venv`) and dependency locking (`requirements.txt`)

### 📥 Step 1 — Document Extraction
- Upload a PDF submission (application, report, etc.)
- Text extraction via **pdfplumber**
- Deterministic regex parser (`crude_parse`) for quick field mapping
- Pydantic validation (`Applicant` model) for data consistency

### 🧩 Step 2 — Rules Engine
- YAML-defined underwriting rules (human-readable)
- Safe AST evaluator (no `eval`)
- Streamlit UI for **“Rules & Flags”** tab:
  - ✅/⚠️ per-rule indicators  
  - Aggregated pass/fail summary  
  - Fully auditable logic

---

## 🔮 Coming Next (Roadmap)

| Phase | Focus | Goal |
|:------|:------|:-----|
| **Step 3** | **Risk Score & Triage** | Hybrid scoring (rule × learned multiplier) for dynamic yet interpretable risk assessment |
| **Step 4** | **Decision Support** | AI-generated case summaries + recommended actions & premium modifiers |
| **Step 5** | **Audit Trail** | Full transparency log (who / what / when) for compliance and governance |

---

## ⚙️ Quickstart

```bash
# 1️⃣  Create & activate venv (Windows)
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# 2️⃣  Install dependencies
pip install -r requirements.txt

# 3️⃣  Initialize local database
python app\db_init.py


Project Sturcture
underwriting-dashboard/
│
├── app/
│   ├── main.py            # Streamlit UI entrypoint
│   ├── extract.py         # PDF parsing & validation
│   ├── db_init.py         # SQLModel setup
│   ├── schemas.py         # Pydantic/SQLModel models
│   ├── rules_engine.py    # Safe rule evaluator
│   └── risk_engine.py     # (WIP) hybrid risk scoring
│
├── rules/
│   └── base.yaml          # Human-readable underwriting rules
│
├── data/                  # Auto-generated case payloads (ignored by Git)
├── pdfs_mock/             # Sample PDFs for testing
├── db/                    # SQLite database
├── .env
├── .gitignore
├── requirements.txt
└── README.md


# 4️⃣  Launch the dashboard
streamlit run app\main.py
