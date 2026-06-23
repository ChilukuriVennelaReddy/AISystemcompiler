# AI-Powered NL-to-App Compiler ⚡

An enterprise-grade, production-ready AI compiler platform that transforms natural language application requirements into validated, executable configurations and deploys fully functional runtime applications (SQLite, FastAPI backend, and Streamlit client frontend).

---

## 🏗️ Compiler Pipeline Architecture

Rather than relying on raw code generation which is prone to drift, this compiler adopts classical compiler stages to guarantee 100% type-safety and consistency across layers:

```
[User Specification] -> [Stage 1: Intent Extraction] 
                           -> Intent IR
                        -> [Stage 2: System Architecture Design] 
                           -> Architecture IR
                        -> [Stage 3: Layer Schema Generator] 
                           -> Raw Config (DB, API, UI, Auth, Logic)
                        -> [Stage 4: Cross-Layer Static Validation]
                           -> If Errors -> [Stage 5: AST Targeted Self-Repair]
                        -> [Stage 6: Execution Plan (DAG) Scheduler]
                        -> [Stage 7: Target Artifact Generator]
                           -> Executable App (SQL, FastAPI, Streamlit UI)
                        -> [Stage 8: Live Deployment & Runtime Runner]
```

1. **Intent Extraction**: Parses unstructured specifications into an Intent Intermediate Representation (IR).
2. **System Architecture Design**: Converts Intent IR into an Architecture IR (Entity-Relationship graphs, Routing, and Dataflow maps).
3. **Schema Generation**: Provisions configurations for DB, API, UI Components, Authorization Rules, and Business Logic constraints.
4. **Validation (Refiner)**: Static analysis type-checker checking that UI fields point to API routes, API routes reference existing DB columns with matching types, and auth rules align with active endpoints.
5. **Targeted Repair**: Localized subtree patch cycle that corrects validation issues without regenerating the entire configuration.
6. **Artifact Generator**: Emits `app_sqlite.sql`, `app_fastapi.py`, and `app_streamlit.py`.
7. **Deployment & Execution Simulation**: Spawns Uvicorn (FastAPI target app on port 8001) and Streamlit (target frontend on port 8502) live.

---

## 🛠️ Project Structure & Directory Layout

```
.
├── backend/
│   ├── app.py                     # FastAPI Compiler Backend Server (Port 8000)
│   ├── compiler_history.db        # SQLite metrics & compilation log database
│   └── compiler/
│       ├── __init__.py
│       ├── compiler.py            # Orchestrator core
│       ├── llm_client.py          # OpenAI / Gemini API JSON Client with mock fallbacks
│       ├── intent_extractor.py    # Parsing stage
│       ├── system_designer.py     # ER mapping stage
│       ├── schema_generator.py    # Schema builder stage
│       ├── refiner.py             # Type check static validation engine
│       ├── repair_engine.py       # Local AST self-healing loop
│       ├── execution_simulator.py  # Stage 6 execution check
│       ├── artifact_generator.py  # Emits SQL, FastAPI and Streamlit code
│       └── evaluator.py           # Evaluates 20 regression test cases
├── frontend/
│   └── dashboard.py               # Streamlit Dashboard UI (Port 8501)
├── dist/                          # Generated Runtime Artifacts
│   ├── app_configuration.json     # Compiled JSON AST config build file
│   ├── app_sqlite.sql             # Executable SQLite table migrations
│   ├── app_fastapi.py             # Executable FastAPI target server
│   └── app_streamlit.py           # Executable Streamlit UI target client
├── test_prompts.json              # Regression dataset (10 standard + 10 edge cases)
├── .gitignore
└── README.md
```

---

## 🚀 How to Run the Compiler Locally

### Prerequisites
Make sure Python 3.12+ is installed, then install the dependencies:
```bash
pip3 install fastapi uvicorn streamlit httpx pandas openai google-generativeai
```

### 1. Launch the FastAPI Compiler Backend
```bash
python3 -m backend.app
```
*The server will run on `http://127.0.0.1:8000`*

### 2. Launch the Streamlit Web Dashboard
```bash
streamlit run frontend/dashboard.py
```
*The UI will open on `http://localhost:8501`*

---

## 🕹️ Compilation, Deployment, & Execution

1. Load or type your spec in **Section 1** on the dashboard and click **`Compile & Build App`**.
2. Go to the **`Deployment Runtime`** tab and click **`Deploy Application Live 🚀`**.
   - This spins up Uvicorn running `app_fastapi.py` on port `8001` and Streamlit running `app_streamlit.py` on port `8502`.
   - Your compiled frontend makes real HTTP calls to the backend on port `8001`!
3. Click the link **`Open App Interface 🌐`** to interact with your live deployed application.

---

## 🧪 Regression Test Harness

You can run the regression evaluator directly from the sidebar of the dashboard or using the command line:
```bash
python3 -m backend.compiler.evaluator
```
This runs 20 test inputs (covering standard and edge cases like circular references, vague prompts, conflicting roles) and records stats (Latency, Repair cycles, Success rate) in the `compiler_history.db` SQLite database, which is visualized in the **Evaluation Metrics** tab.
