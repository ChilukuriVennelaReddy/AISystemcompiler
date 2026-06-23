import os
import sqlite3
import json
import subprocess
from fastapi import FastAPI, HTTPException, Body
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, Any, List, Optional

from backend.compiler.compiler import AppCompiler
from backend.compiler.evaluator import Evaluator

app = FastAPI(title="NL-to-App Compiler Backend API")

# Enable CORS for Streamlit
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

compiler = AppCompiler()

class CompileRequest(BaseModel):
    prompt: str
    trigger_repair: bool = False

@app.post("/compile")
def compile_prompt(req: CompileRequest):
    try:
        result = compiler.compile(req.prompt, req.trigger_repair)
        
        # Save compilation run to sqlite
        db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'compiler_history.db')
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Create table if not exists
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS compilation_runs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT,
                prompt TEXT,
                success INTEGER,
                latency_ms INTEGER,
                repairs INTEGER,
                domain TEXT,
                output_json TEXT
            )
        ''')
        
        if result.get("success", False):
            metadata = result["compilationOutput"].get("metadata", {})
            intent = result["compilationOutput"].get("intent_ir", {})
            repairs = result["compilationOutput"].get("repair_reports", {}).get("total_repairs_needed", 0)
            
            cursor.execute('''
                INSERT INTO compilation_runs (timestamp, prompt, success, latency_ms, repairs, domain, output_json)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                metadata.get("timestamp"),
                req.prompt,
                1,
                metadata.get("compilation_time_ms"),
                repairs,
                intent.get("domain"),
                json.dumps(result["compilationOutput"])
            ))
            conn.commit()
        conn.close()
        
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Compilation failed: {str(e)}")

@app.post("/simulate")
def run_simulation(ast: Dict[str, Any] = Body(...)):
    try:
        from backend.compiler.execution_simulator import ExecutionSimulator
        sim = ExecutionSimulator()
        res = sim.simulate(ast)
        return res
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Simulation failed: {str(e)}")

@app.post("/evaluate")
def run_evaluation():
    try:
        ev = Evaluator()
        res = ev.run()
        return res
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Evaluation failed: {str(e)}")

@app.get("/history")
def get_history(limit: int = 10):
    try:
        db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'compiler_history.db')
        if not os.path.exists(db_path):
            return []
            
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Test if table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='compilation_runs'")
        if not cursor.fetchone():
            conn.close()
            return []
            
        cursor.execute("SELECT id, timestamp, prompt, success, latency_ms, repairs, domain, output_json FROM compilation_runs ORDER BY id DESC LIMIT ?", (limit,))
        rows = cursor.fetchall()
        
        runs = []
        for r in rows:
            runs.append({
                "id": r[0],
                "timestamp": r[1],
                "prompt": r[2],
                "success": bool(r[3]),
                "latency_ms": r[4],
                "repairs": r[5],
                "domain": r[6],
                "output_json": json.loads(r[7]) if r[7] else None
            })
        conn.close()
        return runs
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch history: {str(e)}")

@app.get("/eval_history")
def get_eval_history(limit: int = 5):
    try:
        db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'compiler_history.db')
        if not os.path.exists(db_path):
            return []
            
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Test if table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='evaluation_runs'")
        if not cursor.fetchone():
            conn.close()
            return []
            
        cursor.execute("SELECT id, timestamp, total_prompts, success_rate, avg_latency_ms, avg_repairs, detailed_results FROM evaluation_runs ORDER BY id DESC LIMIT ?", (limit,))
        rows = cursor.fetchall()
        
        history = []
        for r in rows:
            history.append({
                "id": r[0],
                "timestamp": r[1],
                "total_prompts": r[2],
                "success_rate": r[3],
                "avg_latency_ms": r[4],
                "avg_repairs": r[5],
                "detailed_results": json.loads(r[6]) if r[6] else []
            })
        conn.close()
        return history
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch evaluation history: {str(e)}")

deployed_processes = {
    "backend": None,
    "frontend": None
}

@app.post("/deploy")
def deploy_compiled_app():
    global deployed_processes
    
    current_dir = os.path.dirname(os.path.abspath(__file__))
    dist_dir = os.path.join(current_dir, "..", "dist")
    
    # 1. Kill old processes safely
    if deployed_processes["backend"] and deployed_processes["backend"].poll() is None:
        try:
            deployed_processes["backend"].terminate()
            deployed_processes["backend"].wait(timeout=2.0)
        except Exception:
            try:
                deployed_processes["backend"].kill()
            except Exception:
                pass
            
    if deployed_processes["frontend"] and deployed_processes["frontend"].poll() is None:
        try:
            deployed_processes["frontend"].terminate()
            deployed_processes["frontend"].wait(timeout=2.0)
        except Exception:
            try:
                deployed_processes["frontend"].kill()
            except Exception:
                pass
            
    # Remove old DB file to start clean
    db_file_path = os.path.join(dist_dir, "app.db")
    if os.path.exists(db_file_path):
        try:
            os.remove(db_file_path)
        except Exception:
            pass

    # 2. Run SQL script to pre-initialize the tables
    sql_script_path = os.path.join(dist_dir, "app_sqlite.sql")
    if os.path.exists(sql_script_path):
        with open(sql_script_path, "r") as f:
            schema = f.read()
        try:
            with sqlite3.connect(db_file_path) as conn:
                conn.executescript(schema)
                conn.commit()
        except Exception as e:
            print("DB init error during deployment:", str(e))
            
    # 3. Start generated API Server on port 8001
    try:
        env = os.environ.copy()
        deployed_processes["backend"] = subprocess.Popen(
            ["python3", "-m", "uvicorn", "app_fastapi:app", "--port", "8001", "--host", "127.0.0.1"],
            cwd=dist_dir,
            env=env
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to spawn backend process: {str(e)}")
        
    # 4. Start Streamlit UI on port 8502
    try:
        deployed_processes["frontend"] = subprocess.Popen(
            ["python3", "-m", "streamlit", "run", "app_streamlit.py", "--server.port", "8502", "--server.headless", "true"],
            cwd=dist_dir,
            env=env
        )
    except Exception as e:
        if deployed_processes["backend"]:
            try:
                deployed_processes["backend"].kill()
            except Exception:
                pass
        raise HTTPException(status_code=500, detail=f"Failed to spawn Streamlit UI process: {str(e)}")
        
    return {
        "status": "Deployed",
        "api_url": "http://127.0.0.1:8001",
        "ui_url": "http://localhost:8502"
    }

@app.get("/deploy_status")
def get_deploy_status():
    global deployed_processes
    backend_running = deployed_processes["backend"] is not None and deployed_processes["backend"].poll() is None
    frontend_running = deployed_processes["frontend"] is not None and deployed_processes["frontend"].poll() is None
    return {
        "backend_running": backend_running,
        "frontend_running": frontend_running
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.app:app", host="127.0.0.1", port=8000, reload=True)
