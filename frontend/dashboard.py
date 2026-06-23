import streamlit as st
import json
import httpx
import time
import pandas as pd
import os
import sqlite3

# Try importing local compiler packages for in-process fallback (useful for serverless cloud deployments)
try:
    from backend.compiler.compiler import AppCompiler
    from backend.compiler.evaluator import Evaluator
    from backend.compiler.execution_simulator import ExecutionSimulator
    HAS_LOCAL_COMPILER = True
except ImportError:
    HAS_LOCAL_COMPILER = False

# Premium UX Configuration & Page Setup
st.set_page_config(layout="wide", page_title="AI-Powered NL-to-App Compiler", page_icon="⚡")

# Direct style injection for a custom slate-neon theme
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@500;600;700;800&family=Inter:wght@300;400;500;600&family=Fira+Code:wght@400;500&display=swap');
    
    /* Font family settings */
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }
    
    h1, h2, h3, h4, h5, h6, .gradient-header {
        font-family: 'Plus Jakarta Sans', sans-serif !important;
        font-weight: 700;
    }
    
    .stCodeBlock, code, pre {
        font-family: 'Fira Code', monospace !important;
    }

    /* Remove default Streamlit page margins and empty paddings */
    .block-container {
        padding-top: 1.5rem !important;
        padding-bottom: 1.5rem !important;
        padding-left: 2.5rem !important;
        padding-right: 2.5rem !important;
        max-width: 100% !important;
    }
    
    /* Squeeze vertical blocks to eliminate empty gaps */
    div[data-testid="stVerticalBlock"] {
        gap: 0.8rem !important;
    }

    /* Vercel/Linear dark background overrides */
    [data-testid="stAppViewContainer"] {
        background: linear-gradient(180deg, #090d16 0%, #0d121f 100%);
        color: #f3f4f6;
    }
    
    [data-testid="stSidebar"] {
        background-color: #060911 !important;
        border-right: 1px solid rgba(255, 255, 255, 0.05);
    }

    /* Style the Tab buttons */
    button[data-baseweb="tab"] {
        font-family: 'Plus Jakarta Sans', sans-serif !important;
        font-size: 15px;
        font-weight: 600;
        color: #9ca3af !important;
        background-color: transparent !important;
        border-bottom-width: 2px !important;
        border-bottom-color: transparent !important;
        padding: 8px 16px !important;
    }
    button[data-baseweb="tab"]:hover {
        color: #f3f4f6 !important;
    }
    button[aria-selected="true"] {
        color: #818cf8 !important;
        border-bottom-color: #818cf8 !important;
    }

    /* Neon Gradient Buttons */
    .stButton>button {
        background: linear-gradient(135deg, #4f46e5 0%, #7c3aed 100%) !important;
        color: white !important;
        font-weight: 600 !important;
        border: none !important;
        border-radius: 8px !important;
        padding: 10px 24px !important;
        transition: all 0.3s ease !important;
        box-shadow: 0 4px 16px rgba(79, 70, 229, 0.25) !important;
    }
    
    .stButton>button:hover {
        background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%) !important;
        transform: translateY(-1.5px) !important;
        box-shadow: 0 6px 20px rgba(79, 70, 229, 0.35) !important;
    }

    /* Custom Glassmorphism Containers */
    .compiler-card {
        background: rgba(17, 24, 39, 0.6);
        backdrop-filter: blur(12px);
        border: 1px solid rgba(255, 255, 255, 0.06);
        border-radius: 12px;
        padding: 20px;
        margin-bottom: 16px;
        box-shadow: 0 10px 25px 0 rgba(0, 0, 0, 0.2);
    }
    
    .glass-header {
        background: linear-gradient(135deg, #4f46e5 0%, #6366f1 50%, #2563eb 100%);
        padding: 20px;
        border-radius: 12px;
        color: white;
        margin-bottom: 16px;
        border: 1px solid rgba(255, 255, 255, 0.1);
        box-shadow: 0 8px 24px rgba(79, 70, 229, 0.15);
    }
    
    /* Status Badges */
    .badge-capsule {
        display: inline-block;
        padding: 4px 12px;
        border-radius: 6px;
        font-size: 12px;
        font-weight: 600;
        margin-right: 6px;
        margin-bottom: 6px;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    
    .badge-role {
        background-color: rgba(99, 102, 241, 0.1);
        color: #818cf8;
        border: 1px solid rgba(99, 102, 241, 0.2);
    }
    
    .badge-feature {
        background-color: rgba(236, 72, 153, 0.1);
        color: #f472b6;
        border: 1px solid rgba(236, 72, 153, 0.2);
    }
    
    .badge-entity {
        background-color: rgba(20, 184, 166, 0.1);
        color: #2dd4bf;
        border: 1px solid rgba(20, 184, 166, 0.2);
    }
    
    .status-pass {
        background: rgba(16, 185, 129, 0.08);
        border: 1px solid rgba(16, 185, 129, 0.2);
        color: #34d399;
        padding: 10px 16px;
        border-radius: 8px;
        font-weight: 600;
        display: flex;
        align-items: center;
        gap: 10px;
        font-size: 14px;
    }
    
    .status-fail {
        background: rgba(239, 68, 68, 0.08);
        border: 1px solid rgba(239, 68, 68, 0.2);
        color: #f87171;
        padding: 10px 16px;
        border-radius: 8px;
        font-weight: 600;
        display: flex;
        align-items: center;
        gap: 10px;
        font-size: 14px;
    }
    
    .terminal-box {
        background-color: #060911;
        border: 1px solid #1e293b;
        border-radius: 8px;
        padding: 14px;
        font-family: 'Fira Code', monospace;
        color: #38bdf8;
        font-size: 12px;
        line-height: 1.5;
        max-height: 280px;
        overflow-y: auto;
    }

    /* Pulsating server indicator */
    @keyframes pulse {
        0% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(52, 211, 153, 0.5); }
        70% { transform: scale(1); box-shadow: 0 0 0 8px rgba(52, 211, 153, 0); }
        100% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(52, 211, 153, 0); }
    }
    .pulse-dot {
        width: 8px;
        height: 8px;
        background-color: #10b981;
        border-radius: 50%;
        display: inline-block;
        box-shadow: 0 0 0 0 rgba(52, 211, 153, 0.5);
        animation: pulse 2s infinite;
        margin-right: 6px;
    }
</style>
""", unsafe_allow_html=True)

BACKEND_URL = "http://127.0.0.1:8000"

# Main Title Header
st.markdown("""
<div class="glass-header">
    <h1 style='margin: 0; font-size: 34px; font-weight: 700; display: flex; align-items: center; gap: 12px;'>
        ⚡ NL-to-App Compiler Platform
    </h1>
    <p style='margin: 8px 0 0 0; opacity: 0.85; font-size: 16px; font-weight: 300;'>
        Transforms requirements into validated schema ASTs, executes targeted repairs, and builds functional deployments.
    </p>
</div>
""", unsafe_allow_html=True)

# Preset examples mapping
preset_prompts = {
    "Select Preset...": "",
    "CRM System with role access & analytics": "Build a CRM with login, contacts, dashboard, role-based access, and premium plan with payments. Admins can see analytics.",
    "Kanban task board with comment threads": "Create a Kanban task management board with workspaces, projects, status cards, and comments. Guest roles are read-only.",
    "E-commerce shop with product list": "Design an e-commerce shop with product catalogs, shopping cart, billing checkouts, and role-based discount permissions.",
    "Short Edge Case Prompt": "CRM. Guest can edit contacts, but Guest is read-only.",
}

# Setup dashboard columns
col_in, col_hist = st.columns([3, 1])

# Check if SQLite DB tables exist or fetch history locally if API offline
history_data = []
try:
    hist_res = httpx.get(f"{BACKEND_URL}/history")
    if hist_res.status_code == 200:
        history_data = hist_res.json()
except Exception:
    # Local fallback query from DB
    current_dir = os.path.dirname(os.path.abspath(__file__))
    db_path = os.path.join(current_dir, '..', 'backend', 'compiler_history.db')
    if os.path.exists(db_path):
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='compilation_runs'")
            if cursor.fetchone():
                cursor.execute("SELECT id, timestamp, prompt, success, latency_ms, repairs, domain, output_json FROM compilation_runs ORDER BY id DESC LIMIT 10")
                for r in cursor.fetchall():
                    history_data.append({
                        "id": r[0], "timestamp": r[1], "prompt": r[2], "success": bool(r[3]), "latency_ms": r[4], "repairs": r[5], "domain": r[6]
                    })
            conn.close()
        except Exception:
            pass

with col_in:
    st.markdown('<div class="compiler-card">', unsafe_allow_html=True)
    st.subheader("💡 Requirement Specification")
    
    selected_preset = st.selectbox("Quick-load example specification:", list(preset_prompts.keys()))
    default_prompt_val = preset_prompts[selected_preset] if selected_preset != "Select Preset..." else ""
    
    prompt_input = st.text_area(
        "Enter your application design specification:",
        value=default_prompt_val,
        height=110,
        placeholder="Type requirements here... (e.g. Build a CRM with payments. Admins can see reports.)"
    )
    
    col_c1, col_c2 = st.columns([1, 2])
    with col_c1:
        trigger_repair_val = st.checkbox("Enable Targeted self-repair", value=True)
    with col_c2:
        compile_btn = st.button("🏁 Compile & Build App", use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

with col_hist:
    st.markdown('<div class="compiler-card" style="height: 100%;">', unsafe_allow_html=True)
    st.subheader("📜 Run History")
    
    if history_data:
        for idx, run in enumerate(history_data[:4]):
            status_symbol = "🟢" if run["success"] else "🔴"
            st.markdown(f"**{status_symbol} {run['domain']}**")
            st.caption(f"{run['timestamp']} | Repairs: {run['repairs']}")
    else:
        st.info("No compilation history found.")
        
    st.markdown("---")
    if st.button("🧪 Run Regression Harness", use_container_width=True):
        with st.spinner("Running 20-prompt test harness..."):
            # Try API first
            eval_done = False
            try:
                eval_res = httpx.post(f"{BACKEND_URL}/evaluate", timeout=120.0)
                if eval_res.status_code == 200:
                    st.success("Test harness run complete!")
                    st.session_state["eval_res"] = eval_res.json()
                    eval_done = True
            except Exception:
                pass
                
            if not eval_done and HAS_LOCAL_COMPILER:
                try:
                    evaluator = Evaluator()
                    res = evaluator.run()
                    st.session_state["eval_res"] = res
                    st.success("Test harness completed locally!")
                except Exception as e:
                    st.error(f"Failed to run evaluator: {str(e)}")
            elif not eval_done:
                st.error("Harness service unavailable.")
    st.markdown('</div>', unsafe_allow_html=True)

# Compiler progress state engine
if compile_btn:
    if not prompt_input.strip():
        st.warning("Please type a requirement spec first.")
    else:
        progress_card = st.empty()
        with progress_card.container():
            st.markdown('<div class="compiler-card">', unsafe_allow_html=True)
            st.subheader("⚙️ Compilation Pipeline Process")
            
            p_bar = st.progress(0)
            logs_box = st.empty()
            
            log_messages = []
            
            def add_log(msg):
                log_messages.append(msg)
                logs_box.markdown(
                    f'<div class="terminal-box">{"<br>".join(log_messages)}</div>', 
                    unsafe_allow_html=True
                )
            
            p_bar.progress(15)
            add_log("🏁 Starting compilation process...")
            time.sleep(0.3)
            
            p_bar.progress(35)
            add_log("[STAGE 1] Running Lexical Analysis & Intent Extraction...")
            time.sleep(0.3)
            
            p_bar.progress(55)
            add_log("[STAGE 2] Converting Intent IR to System Architecture Graph...")
            time.sleep(0.3)
            
            p_bar.progress(70)
            add_log("[STAGE 3] Independently provisioning schemas (DB, API, UI, Auth, Rules)...")
            time.sleep(0.3)
            
            p_bar.progress(85)
            add_log("[STAGE 4] Executing static validation refiner scans...")
            time.sleep(0.2)
            
            p_bar.progress(95)
            add_log("[STAGE 5 & 6] Checking constraints & compiling target artifacts...")
            time.sleep(0.2)
            
            # Call actual compile backend or local process fallback
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
                        st.success("App configuration generated.")
                    else:
                        st.error(f"Pipeline failed: {result.get('errors')}")
                except Exception as e:
                    st.error(f"Local compilation failed: {str(e)}")
            elif not compiled_done:
                st.error("Compiler backend service is not running and local code is missing.")
            st.markdown('</div>', unsafe_allow_html=True)
        progress_card.empty()

# RENDER COMPILED APP VIEWS
comp = st.session_state.get("compilation_result")
if comp and comp.get("success"):
    output = comp["compilationOutput"]
    
    st.markdown('<div class="compiler-card">', unsafe_allow_html=True)
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
            
            # Domain and specs card
            st.markdown(f"**Application Domain:** `{intent_ir.get('domain')}`")
            
            # Badges view
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
                    <div style="display: flex; align-items: center; justify-content: space-between; background: rgba(255,255,255,0.02); border: 1px solid rgba(255,255,255,0.05); padding: 12px 20px; border-radius: 10px; margin-bottom: 10px;">
                        <div style="font-weight: 600; color: #818cf8; font-size: 15px;">📁 {link.get('from')}</div>
                        <div style="color: #94a3b8; font-size: 12px; font-family: monospace; background: rgba(255,255,255,0.05); padding: 2px 10px; border-radius: 4px;">{link.get('type')} ({link.get('foreign_key', 'N/A') or link.get('through', 'N/A')})</div>
                        <div style="font-weight: 600; color: #10b981; font-size: 15px;">📁 {link.get('to')}</div>
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.info("No table relations mapped.")
                
            st.write("---")
            st.markdown("**Data Flow Bindings:**")
            for flow in arch_ir.get("dataFlowTopology", []):
                st.markdown(f"""
                <div style="display: flex; align-items: center; justify-content: space-between; background: rgba(255,255,255,0.02); border: 1px solid rgba(255,255,255,0.05); padding: 12px 20px; border-radius: 10px; margin-bottom: 10px;">
                    <div style="font-weight: 500; color: #e2e8f0; font-size: 14px;">🖥️ {flow.get('source')}</div>
                    <div style="color: #c084fc; font-size: 12px; font-family: monospace;">──[{flow.get('transfers_through')}]──></div>
                    <div style="font-weight: 500; color: #f472b6; font-size: 14px;">🗄️ {flow.get('target')}</div>
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
            db_spec = output.get("database_schema", {})
            st.json(db_spec)
            
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
                <div style="background: rgba(16, 185, 129, 0.05); border: 1px solid rgba(16, 185, 129, 0.15); border-radius: 8px; padding: 15px; margin-top: 10px;">
                    <a href="{ui_url}" target="_blank" style="color: #34d399; font-weight: 600; text-decoration: none; font-size: 16px;">👉 Open Live Deployed Frontend UI (Port 8502) 🌐</a><br>
                    <a href="{api_url}/docs" target="_blank" style="color: #60a5fa; font-weight: 600; text-decoration: none; font-size: 14px; display: inline-block; margin-top: 8px;">👉 Open API Backend docs (Port 8001) 🔌</a>
                </div>
                """, unsafe_allow_html=True)
            elif is_cloud:
                st.markdown('<div style="background: rgba(255, 255, 255, 0.03); border: 1px solid rgba(255, 255, 255, 0.08); border-radius: 8px; padding: 18px;">☁️ running on <b>Serverless Cloud Host</b>. Background subprocess execution is restricted on public clouds. However, you can view the fully generated executable target files below. Copy them to run locally!</div>', unsafe_allow_html=True)
            else:
                st.markdown('<div style="background: rgba(255, 255, 255, 0.03); border: 1px solid rgba(255, 255, 255, 0.08); border-radius: 8px; padding: 18px;">Deployment status: <b>Offline/Ready</b>. Press the trigger to compile and deploy on-demand.</div>', unsafe_allow_html=True)
                
        with col_dep2:
            if is_cloud:
                st.button("⚡ Live Deploy (Disabled in Cloud)", disabled=True, use_container_width=True)
            else:
                if st.button("⚡ Deploy App Live", use_container_width=True):
                    with st.spinner("Compiling target, provisioning SQLite, starting backend (8001) & frontend (8502)..."):
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
        
        # Build layout code inspector
        st.markdown("#### Generated Executable Source Artifacts")
        st.info("The compiler generated these executable source scripts. Inspect them below:")
        
        current_dir = os.path.dirname(os.path.abspath(__file__))
        dist_dir = os.path.join(current_dir, '..', 'dist')
        
        c_file = st.selectbox("Select Generated Source File:", ["app_sqlite.sql", "app_fastapi.py", "app_streamlit.py"])
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
            # Local fallback query from DB
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
else:
    st.info("💡 Enter your specifications in Section 1 and click 'Compile & Build App' to run the compilation pipeline.")
