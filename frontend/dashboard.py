import streamlit as st
import json
import httpx
import time
import pandas as pd
import os
import sqlite3

# Try importing local compiler packages for serverless fallback
try:
    from backend.compiler.compiler import AppCompiler
    from backend.compiler.evaluator import Evaluator
    from backend.compiler.execution_simulator import ExecutionSimulator
    HAS_LOCAL_COMPILER = True
except ImportError:
    HAS_LOCAL_COMPILER = False

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=Inter:wght@300;400;500;600&family=Fira+Code:wght@400;500&display=swap');
    
    /* Custom Slate-Indigo Pastel Theme */
    [data-testid="stAppViewContainer"] {
        background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 60%, #e0f2fe 100%) !important;
        color: #334155 !important;
        font-family: 'Inter', sans-serif;
    }
    
    [data-testid="stHeader"] {
        background-color: transparent !important;
    }
    
    /* Clean Sidebar */
    [data-testid="stSidebar"] {
        background-color: rgba(255, 255, 255, 0.8) !important;
        backdrop-filter: blur(10px);
        border-right: 1px solid rgba(0, 0, 0, 0.05);
    }
    
    .stMarkdown, p, span, label {
        color: #334155 !important;
    }

    /* Page Padding Adjustments */
    .block-container {
        padding-top: 2rem !important;
        padding-bottom: 2rem !important;
        padding-left: 2rem !important;
        padding-right: 2rem !important;
        max-width: 1200px !important;
    }

    /* Custom Centered Header Styling */
    .app-title {
        font-family: 'Plus Jakarta Sans', sans-serif !important;
        font-weight: 800;
        font-size: 46px;
        color: #0f172a;
        text-align: center;
        margin-bottom: 12px;
        letter-spacing: -1.5px;
        line-height: 1.1;
    }
    
    .app-subtitle {
        font-family: 'Inter', sans-serif;
        color: #475569 !important;
        font-size: 17px;
        text-align: center;
        margin-bottom: 35px;
        max-width: 650px;
        margin-left: auto;
        margin-right: auto;
        line-height: 1.5;
    }

    /* Custom Rounded Card Input Box */
    .app-input-card {
        background: #ffffff;
        border-radius: 20px;
        padding: 24px;
        box-shadow: 0 10px 30px rgba(15, 23, 42, 0.06);
        border: 1px solid rgba(226, 232, 240, 0.8);
        margin-bottom: 20px;
    }
    
    /* Remove borders on st.text_area input to match flat note style */
    textarea {
        border: none !important;
        resize: none !important;
        outline: none !important;
        background-color: transparent !important;
        font-size: 16px !important;
        color: #0f172a !important;
    }
    
    /* Preset buttons (Pills) styling */
    div.stButton > button {
        border-radius: 9999px !important;
        background-color: rgba(255, 255, 255, 0.8) !important;
        color: #475569 !important;
        border: 1px solid rgba(0, 0, 0, 0.06) !important;
        padding: 6px 18px !important;
        font-size: 13px !important;
        font-weight: 500 !important;
        transition: all 0.2s ease !important;
        box-shadow: 0 2px 5px rgba(0,0,0,0.01) !important;
    }
    
    div.stButton > button:hover {
        background-color: #ffffff !important;
        border-color: #cbd5e1 !important;
        color: #0f172a !important;
        transform: translateY(-1px) !important;
        box-shadow: 0 4px 10px rgba(0,0,0,0.03) !important;
    }

    /* Sleek Slate-Indigo Submit Button Override */
    .indigo-submit-btn > div > button {
        background: linear-gradient(135deg, #4f46e5 0%, #4338ca 100%) !important;
        color: #ffffff !important;
        border-radius: 9999px !important;
        padding: 10px 30px !important;
        font-weight: 600 !important;
        font-size: 15px !important;
        box-shadow: 0 4px 14px rgba(79, 70, 229, 0.25) !important;
        border: none !important;
    }
    
    .indigo-submit-btn > div > button:hover {
        background: linear-gradient(135deg, #6366f1 0%, #4f46e5 100%) !important;
        box-shadow: 0 6px 20px rgba(79, 70, 229, 0.35) !important;
        transform: translateY(-1px) !important;
        color: #ffffff !important;
    }

    /* Glassmorphic output boxes */
    .output-card {
        background: rgba(255, 255, 255, 0.75) !important;
        backdrop-filter: blur(12px);
        border: 1px solid rgba(255, 255, 255, 0.9);
        border-radius: 16px;
        padding: 24px;
        margin-top: 30px;
        box-shadow: 0 10px 30px rgba(0, 0, 0, 0.03);
    }
    
    h1, h2, h3, h4, h5, h6 {
        font-family: 'Plus Jakarta Sans', sans-serif !important;
        color: #0f172a !important;
        font-weight: 700;
    }

    /* Tabs formatting */
    button[data-baseweb="tab"] {
        font-family: 'Plus Jakarta Sans', sans-serif !important;
        font-size: 14px;
        font-weight: 600;
        color: #64748b !important;
    }
    button[aria-selected="true"] {
        color: #4f46e5 !important;
        border-bottom-color: #4f46e5 !important;
    }

    /* Badge tags */
    .badge-capsule {
        display: inline-block;
        padding: 4px 10px;
        border-radius: 6px;
        font-size: 12px;
        font-weight: 600;
        margin-right: 6px;
        margin-bottom: 6px;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    
    .badge-role {
        background-color: rgba(99, 102, 241, 0.08);
        color: #4f46e5;
        border: 1px solid rgba(99, 102, 241, 0.15);
    }
    
    .badge-feature {
        background-color: rgba(236, 72, 153, 0.08);
        color: #db2777;
        border: 1px solid rgba(236, 72, 153, 0.15);
    }
    
    .badge-entity {
        background-color: rgba(20, 184, 166, 0.08);
        color: #0d9488;
        border: 1px solid rgba(20, 184, 166, 0.15);
    }
    
    .status-pass {
        background: rgba(16, 185, 129, 0.08);
        border: 1px solid rgba(16, 185, 129, 0.2);
        color: #059669;
        padding: 10px 16px;
        border-radius: 8px;
        font-weight: 600;
        display: flex;
        align-items: center;
        gap: 10px;
    }
    
    .status-fail {
        background: rgba(239, 68, 68, 0.08);
        border: 1px solid rgba(239, 68, 68, 0.2);
        color: #dc2626;
        padding: 10px 16px;
        border-radius: 8px;
        font-weight: 600;
        display: flex;
        align-items: center;
        gap: 10px;
    }
    
    .terminal-box {
        background-color: #0f172a;
        border: 1px solid #1e293b;
        border-radius: 8px;
        padding: 14px;
        font-family: 'Fira Code', monospace;
        color: #38bdf8;
        font-size: 12px;
        line-height: 1.5;
        max-height: 250px;
        overflow-y: auto;
    }
</style>
""", unsafe_allow_html=True)

BACKEND_URL = "http://127.0.0.1:8000"

# Sidebar setup
st.sidebar.markdown("### Compiler Configuration")
st.sidebar.caption("compiler: `v1.0.0-prod-python`")

# Load compiler history
history_data = []
try:
    hist_res = httpx.get(f"{BACKEND_URL}/history")
    if hist_res.status_code == 200:
        history_data = hist_res.json()
except Exception:
    # Query sqlite history locally
    current_dir = os.path.dirname(os.path.abspath(__file__))
    db_path = os.path.join(current_dir, '..', 'backend', 'compiler_history.db')
    if os.path.exists(db_path):
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='compilation_runs'")
            if cursor.fetchone():
                cursor.execute("SELECT id, timestamp, prompt, success, latency_ms, repairs, domain FROM compilation_runs ORDER BY id DESC LIMIT 5")
                for r in cursor.fetchall():
                    history_data.append({
                        "id": r[0], "timestamp": r[1], "prompt": r[2], "success": bool(r[3]), "latency_ms": r[4], "repairs": r[5], "domain": r[6]
                    })
            conn.close()
        except Exception:
            pass

# Sidebar history
if history_data:
    st.sidebar.write("Recent compilations:")
    for run in history_data[:3]:
        st.sidebar.caption(f"🟢 {run['domain']} ({run['latency_ms']}ms)")
else:
    st.sidebar.info("No compilation history.")

st.sidebar.write("---")
if st.sidebar.button("Run Regression Test Suite 🧪"):
    with st.spinner("Running 20-prompt test harness..."):
        eval_done = False
        try:
            eval_res = httpx.post(f"{BACKEND_URL}/evaluate", timeout=120.0)
            if eval_res.status_code == 200:
                st.sidebar.success("Test harness run recorded!")
                st.session_state["eval_res"] = eval_res.json()
                eval_done = True
        except Exception:
            pass
            
        if not eval_done and HAS_LOCAL_COMPILER:
            try:
                evaluator = Evaluator()
                res = evaluator.run()
                st.session_state["eval_res"] = res
                st.sidebar.success("Test harness completed locally!")
            except Exception as e:
                st.sidebar.error(f"Failed to run evaluator: {str(e)}")

# Center column for Base44 layout
left_col, center_col, right_col = st.columns([1, 6, 1])

with center_col:
    # 1. Custom Headers
    st.markdown('<div class="app-title">Turn requirements into apps</div>', unsafe_allow_html=True)
    st.markdown('<div class="app-subtitle">Translate natural language requirements into fully validated database schemas, API servers, and UI frontends instantly.</div>', unsafe_allow_html=True)
    
    # Session state to load preset prompt
    if "prompt_text" not in st.session_state:
        st.session_state["prompt_text"] = ""
        
    # Presets rows
    col_p1, col_p2, col_p3 = st.columns(3)
    if col_p1.button("📋 Classroom Portal"):
        st.session_state["prompt_text"] = "Create a classroom learning management system with courses, lessons, student enrollments, quizzes, grades, and teacher analytics."
        st.rerun()
    if col_p2.button("🗂️ Library Loan Manager"):
        st.session_state["prompt_text"] = "Build a library management portal with books catalog, borrowing loans, member profiles, and status updates."
        st.rerun()
    if col_p3.button("🏥 Clinic Appointment Portal"):
        st.session_state["prompt_text"] = "Design a hospital clinic portal with patient profiles, doctor records, appointment schedules, and prescriptions."
        st.rerun()

    # 2. Custom Input Card Box
    with st.container(border=True):
        prompt_input = st.text_area(
            "Natural Language Prompt Requirements", 
            value=st.session_state["prompt_text"], 
            height=130, 
            placeholder="Enter natural language requirements - e.g., Build a CRM with contacts and billing..."
        )
        
        col_card_f1, col_card_f2 = st.columns([2, 1])
        with col_card_f1:
            trigger_repair_val = st.checkbox("Plan / Repair", value=True)
        with col_card_f2:
            st.markdown('<div class="indigo-submit-btn">', unsafe_allow_html=True)
            compile_btn = st.button("Submit →", use_container_width=True)
            st.markdown('</div>', unsafe_allow_html=True)

# Process compiler pipeline
if compile_btn:
    if not prompt_input.strip():
        st.warning("Please enter requirements text first.")
    else:
        progress_card = st.empty()
        with progress_card.container():
            st.markdown('<div class="output-card">', unsafe_allow_html=True)
            st.subheader("⚙️ Compilation Pipeline Process")
            p_bar = st.progress(0)
            logs_box = st.empty()
            log_messages = []
            
            def add_log(msg):
                log_messages.append(msg)
                logs_box.markdown(f'<div class="terminal-box">{"<br>".join(log_messages)}</div>', unsafe_allow_html=True)
                
            p_bar.progress(15)
            add_log("🏁 Starting compilation process...")
            time.sleep(0.2)
            p_bar.progress(40)
            add_log("[STAGE 1] Lexing & Intent Extraction...")
            time.sleep(0.3)
            p_bar.progress(60)
            add_log("[STAGE 2] Converting Intent IR to System Architecture Graph...")
            time.sleep(0.2)
            p_bar.progress(80)
            add_log("[STAGE 3 & 4] Provisioning schemas and executing validations...")
            time.sleep(0.3)
            p_bar.progress(95)
            add_log("[STAGE 5 & 6] Targeted self-repair checks and compiling target code files...")
            time.sleep(0.2)
            
            compiled_done = False
            try:
                payload = {"prompt": prompt_input, "trigger_repair": trigger_repair_val}
                res = httpx.post(f"{BACKEND_URL}/compile", json=payload, timeout=60.0)
                if res.status_code == 200:
                    st.session_state["compilation_result"] = res.json()
                    p_bar.progress(100)
                    add_log("✓ Compilation completed successfully via API backend.")
                    compiled_done = True
            except Exception:
                pass
                
            if not compiled_done and HAS_LOCAL_COMPILER:
                add_log("⚠️ API Backend offline. Falling back to local in-process compiler...")
                try:
                    local_compiler = AppCompiler()
                    result = local_compiler.compile(prompt_input, trigger_repair_val)
                    if result.get("success"):
                        st.session_state["compilation_result"] = {
                            "success": True,
                            "compilationOutput": result["compilationOutput"],
                            "simulationResult": result["simulationResult"]
                        }
                        p_bar.progress(100)
                        add_log("✓ Compilation completed successfully locally!")
                    else:
                        st.error(f"Pipeline failed: {result.get('errors')}")
                except Exception as e:
                    st.error(f"Local compilation failed: {str(e)}")
            elif not compiled_done:
                st.error("Compiler backend service is not running.")
            st.markdown('</div>', unsafe_allow_html=True)
        progress_card.empty()

# RENDER ARTIFACTS AND RESULTS
comp = st.session_state.get("compilation_result")
if comp and comp.get("success"):
    output = comp["compilationOutput"]
    
    with center_col:
        st.markdown('<div class="output-card">', unsafe_allow_html=True)
        st.subheader("🛠️ Compilation Artifacts and Targets")
        
        tab1, tab2, tab3, tab4, tab5 = st.tabs([
            "🔍 Parsing & Architecture IR", 
            "📋 Generated Schemas", 
            "🛠 Validation & Repair", 
            "🚀 Deployment Runtime",
            "📊 Regression Evaluation"
        ])
        
        with tab1:
            col_ir1, col_ir2 = st.columns(2)
            with col_ir1:
                st.markdown("#### Section 2: Intent IR Extraction")
                intent_ir = output.get("intent_ir", {})
                st.markdown(f"**Application Domain:** `{intent_ir.get('domain')}`")
                
                st.markdown("**Extracted Roles:**")
                roles_html = "".join([f'<span class="badge-capsule badge-role">{r}</span>' for r in intent_ir.get("roles", [])])
                st.markdown(roles_html, unsafe_allow_html=True)
                
                st.markdown("**Extracted Features:**")
                feats_html = "".join([f'<span class="badge-capsule badge-feature">{f}</span>' for f in intent_ir.get("features", [])])
                st.markdown(feats_html, unsafe_allow_html=True)
                
                st.markdown("**Extracted Entities:**")
                ents_html = "".join([f'<span class="badge-capsule badge-entity">{e}</span>' for e in intent_ir.get("entities", [])])
                st.markdown(ents_html, unsafe_allow_html=True)
                
                st.write("---")
                st.markdown("#### Section 12: Assumptions & Ambiguities")
                assumptions = output.get("assumptions", [])
                if assumptions:
                    for idx, a in enumerate(assumptions):
                        st.info(f"**Assumption {idx+1} ({a.get('context')})**: {a.get('assumption')}")
                else:
                    st.success("No assumptions needed. Requirements were clear and consistent.")
                
            with col_ir2:
                st.markdown("#### Section 3: Architecture IR Canvas")
                arch_ir = output.get("architecture_ir", {})
                
                st.markdown("**Entity Relationship Visual Flow:**")
                rel_graph = arch_ir.get("relationshipGraph", [])
                if rel_graph:
                    for link in rel_graph:
                        st.markdown(f"""
                        <div style="display: flex; align-items: center; justify-content: space-between; background: rgba(0,0,0,0.02); border: 1px solid rgba(0,0,0,0.05); padding: 10px 15px; border-radius: 8px; margin-bottom: 8px;">
                            <div style="font-weight: 600; color: #4f46e5; font-size: 14px;">📁 {link.get('from')}</div>
                            <div style="color: #64748b; font-size: 11px; font-family: monospace; background: rgba(0,0,0,0.04); padding: 2px 8px; border-radius: 4px;">{link.get('type')} ({link.get('foreign_key', 'N/A') or link.get('through', 'N/A')})</div>
                            <div style="font-weight: 600; color: #059669; font-size: 14px;">📁 {link.get('to')}</div>
                        </div>
                        """, unsafe_allow_html=True)
                else:
                    st.info("No table relations mapped.")
                    
                st.write("---")
                st.markdown("**Data Flow Bindings:**")
                for flow in arch_ir.get("dataFlowTopology", []):
                    st.markdown(f"""
                    <div style="display: flex; align-items: center; justify-content: space-between; background: rgba(0,0,0,0.02); border: 1px solid rgba(0,0,0,0.05); padding: 10px 15px; border-radius: 8px; margin-bottom: 8px;">
                        <div style="font-weight: 500; color: #334155; font-size: 13px;">🖥️ {flow.get('source')}</div>
                        <div style="color: #7c3aed; font-size: 11px; font-family: monospace;">──[{flow.get('transfers_through')}]──></div>
                        <div style="font-weight: 500; color: #db2777; font-size: 13px;">🗄️ {flow.get('target')}</div>
                    </div>
                    """, unsafe_allow_html=True)
                    
        with tab2:
            schema_tabs = st.tabs([
                "🗄️ Database Table Specs", 
                "🔌 API Endpoints", 
                "🖥️ UI Components", 
                "🔒 Security Rules", 
                "🧠 Business Logic"
            ])
            with schema_tabs[0]:
                st.markdown("#### Section 4: Database Columns Spec")
                st.json(output.get("database_schema", {}))
            with schema_tabs[1]:
                st.markdown("#### Section 5: API Endpoint Models")
                st.json(output.get("api_schema", {}))
            with schema_tabs[2]:
                st.markdown("#### Section 6: Component Declarations")
                st.json(output.get("ui_schema", {}))
            with schema_tabs[3]:
                st.markdown("#### Section 7: Authentication / RBAC Matrix")
                st.json(output.get("authentication_rules", {}))
            with schema_tabs[4]:
                st.markdown("#### Business Logic & Gates")
                st.json(output.get("business_logic_rules", {}))
                
        with tab3:
            st.markdown("#### Section 8: Refiner Validation Report")
            val_rep = output.get("validation_reports", {})
            if val_rep.get("valid"):
                st.markdown('<div class="status-pass"><span>✓</span> VALIDATION PASS: 100% Cross-layer schema consistency verified.</div>', unsafe_allow_html=True)
            else:
                st.markdown('<div class="status-fail"><span>✗</span> VALIDATION FAILED: Inconsistencies detected.</div>', unsafe_allow_html=True)
                
            errors = val_rep.get("errors", [])
            if errors:
                st.write("\n**Detailed Static Validation Scan Failures:**")
                for err in errors:
                    st.error(f"[{err.get('layer')}] {err.get('message')} (Target: `{err.get('target')}`)")
            else:
                st.write("Zero validation issues found in this AST configuration.")
                
            st.write("---")
            st.markdown("#### Section 9: AST Targeted Repair Engine Report")
            repair_rep = output.get("repair_reports", {})
            repairs = repair_rep.get("repair_attempts", [])
            if repairs:
                st.warning(f"Repair engine triggered! Resolved {len(repairs)} validation issues:")
                for idx, r in enumerate(repairs):
                    with st.expander(f"🩹 Issue {idx+1}: {r.get('error', 'Type conflict')}"):
                        st.json(r)
            else:
                st.success("No anomalies detected in generated schemas. Skip self-healing stage.")
                
        with tab4:
            st.markdown("#### Section 10: Execution & Live Deployment")
            
            # Check active status of deployment processes
            is_deployed = False
            api_url = "http://127.0.0.1:8001"
            ui_url = "http://localhost:8502"
            is_cloud = "STREAMLIT_SERVER_PORT" in os.environ or "PORT" in os.environ
            
            try:
                status_res = httpx.get(f"{BACKEND_URL}/deploy_status")
                if status_res.status_code == 200:
                    status_data = status_res.json()
                    is_deployed = status_data.get("backend_running", False) and status_data.get("frontend_running", False)
            except Exception:
                pass

            col_dep1, col_dep2 = st.columns([3, 1])
            with col_dep1:
                if is_deployed:
                    st.markdown(f'<div class="status-pass"><span class="pulse-dot"></span> APPLICATION RUNNING LIVE (SQLite, FastAPI, Streamlit)</div>', unsafe_allow_html=True)
                    st.markdown(f"""
                    <div style="background: rgba(79, 70, 229, 0.05); border: 1px solid rgba(79, 70, 229, 0.15); border-radius: 8px; padding: 15px; margin-top: 10px;">
                        <a href="{ui_url}" target="_blank" style="color: #4f46e5; font-weight: 600; text-decoration: none; font-size: 16px;">👉 Open Live Deployed Frontend UI 🌐</a><br>
                        <a href="{api_url}/docs" target="_blank" style="color: #2563eb; font-weight: 600; text-decoration: none; font-size: 14px; display: inline-block; margin-top: 8px;">👉 Open API Backend Documentation 🔌</a>
                    </div>
                    """, unsafe_allow_html=True)
                elif is_cloud:
                    st.markdown('<div style="background: rgba(0, 0, 0, 0.03); border: 1px solid rgba(0, 0, 0, 0.08); border-radius: 8px; padding: 18px;">☁️ running on <b>Serverless Cloud Host</b>. Background subprocess execution is restricted on public clouds. However, you can view the fully generated executable target files below. Copy them to run locally!</div>', unsafe_allow_html=True)
                else:
                    st.markdown('<div style="background: rgba(0, 0, 0, 0.03); border: 1px solid rgba(0, 0, 0, 0.08); border-radius: 8px; padding: 18px;">Deployment status: <b>Offline/Ready</b>. Press the trigger to compile and deploy on-demand.</div>', unsafe_allow_html=True)
                    
            with col_dep2:
                if is_cloud:
                    st.button("⚡ Live Deploy (Disabled in Cloud)", disabled=True, use_container_width=True)
                else:
                    if st.button("⚡ Deploy App Live", use_container_width=True):
                        with st.spinner("Compiling target, provisioning database, starting backend API & frontend application UI..."):
                            try:
                                dep_res = httpx.post(f"{BACKEND_URL}/deploy", timeout=45.0)
                                if dep_res.status_code == 200:
                                    st.success("Application launched live!")
                                    st.rerun()
                                else:
                                    st.error(f"Deployment failed: {dep_res.text}")
                            except Exception as e:
                                st.error(f"Connection failed: {str(e)}")
                            
            st.write("---")
            st.markdown("#### Generated Executable Source Artifacts")
            st.info("The compiler generated these executable source scripts. Inspect them below:")
            
            current_dir = os.path.dirname(os.path.abspath(__file__))
            dist_dir = os.path.join(current_dir, '..', 'dist')
            
            c_file = st.selectbox("Select Generated Source File to Inspect:", ["app_sqlite.sql", "app_fastapi.py", "app_streamlit.py"])
            file_path = os.path.join(dist_dir, c_file)
            
            if os.path.exists(file_path):
                with open(file_path, "r") as f:
                    content = f.read()
                st.code(content, language="sql" if c_file.endswith(".sql") else "python")
            else:
                st.warning(f"File {c_file} not found in dist/ directory.")
                
        with tab5:
            st.markdown("#### Section 11: Evaluation Metrics Dashboard")
            
            # Get evaluation history
            eval_hist = []
            try:
                eval_hist_res = httpx.get(f"{BACKEND_URL}/eval_history")
                if eval_hist_res.status_code == 200:
                    eval_hist = eval_hist_res.json()
            except Exception:
                # Query sqlite history locally
                current_dir = os.path.dirname(os.path.abspath(__file__))
                db_path = os.path.join(current_dir, '..', 'backend', 'compiler_history.db')
                if os.path.exists(db_path):
                    try:
                        conn = sqlite3.connect(db_path)
                        cursor = conn.cursor()
                        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='evaluation_runs'")
                        if cursor.fetchone():
                            cursor.execute("SELECT id, timestamp, total_prompts, success_rate, avg_latency_ms, avg_repairs, detailed_results FROM evaluation_runs ORDER BY id DESC LIMIT 5")
                            for r in cursor.fetchall():
                                eval_hist.append({
                                    "id": r[0], "timestamp": r[1], "total_prompts": r[2], "success_rate": r[3], "avg_latency_ms": r[4], "avg_repairs": r[5], "detailed_results": json.loads(r[6])
                                })
                        conn.close()
                    except Exception:
                        pass
                
            latest_eval = None
            if "eval_res" in st.session_state:
                latest_eval = st.session_state["eval_res"]
            elif eval_hist:
                latest_eval = eval_hist[0]
                
            if latest_eval:
                col_m1, col_m2, col_m3 = st.columns(3)
                with col_m1:
                    st.metric("Harness Success Rate", f"{latest_eval.get('success_rate'):.1f}%")
                with col_m2:
                    st.metric("Avg Compilation Latency", f"{latest_eval.get('avg_latency', latest_eval.get('avg_latency_ms', 0.0)):.1f} ms")
                with col_m3:
                    st.metric("Avg Repair attempts", f"{latest_eval.get('avg_repairs'):.2f}")
                    
                st.write("---")
                st.markdown("**Test Case Resolution Matrix:**")
                results_list = latest_eval.get("results", latest_eval.get("detailed_results", []))
                results_df = pd.DataFrame(results_list)
                st.dataframe(results_df, use_container_width=True)
                
                st.write("---")
                st.markdown("**Compiler Performance Visual Charts:**")
                chart_col1, chart_col2 = st.columns(2)
                with chart_col1:
                    st.caption("Compilation Latency by Prompt (ms)")
                    st.bar_chart(results_df, x="id", y="latency_ms")
                with chart_col2:
                    st.caption("Required Repair Cycles by Prompt")
                    st.bar_chart(results_df, x="id", y="repairs")
            else:
                st.info("No regression evaluations run yet. Click 'Run Regression Harness' to execute and record metrics.")
        st.markdown('</div>', unsafe_allow_html=True)
