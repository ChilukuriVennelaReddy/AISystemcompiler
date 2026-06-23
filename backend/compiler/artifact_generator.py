import os
from typing import Dict, Any

class ArtifactGenerator:
    @staticmethod
    def generate(ast: Dict[str, Any], output_dir: str) -> Dict[str, str]:
        os.makedirs(output_dir, exist_ok=True)
        
        sql_path = os.path.join(output_dir, "app_sqlite.sql")
        fastapi_path = os.path.join(output_dir, "app_fastapi.py")
        streamlit_path = os.path.join(output_dir, "app_streamlit.py")
        
        # 1. SQL Generator
        sql_content = ArtifactGenerator.generate_sql(ast)
        with open(sql_path, "w") as f:
            f.write(sql_content)
            
        # 2. FastAPI Generator
        fastapi_content = ArtifactGenerator.generate_fastapi(ast)
        with open(fastapi_path, "w") as f:
            f.write(fastapi_content)
            
        # 3. Streamlit Generator
        streamlit_content = ArtifactGenerator.generate_streamlit(ast)
        with open(streamlit_path, "w") as f:
            f.write(streamlit_content)
            
        return {
            "sql_path": sql_path,
            "fastapi_path": fastapi_path,
            "streamlit_path": streamlit_path
        }
        
    @staticmethod
    def generate_sql(ast: Dict[str, Any]) -> str:
        tables = ast.get("database", {}).get("tables", {})
        sql_stmts = []
        
        for table_name, table_spec in tables.items():
            col_definitions = []
            fk_definitions = []
            
            for col_name, col_spec in table_spec.get("columns", {}).items():
                col_type = col_spec.get("type", "TEXT")
                # Map complex types to SQLite compat types
                sqlite_type = "TEXT"
                if "int" in col_type.lower():
                    sqlite_type = "INTEGER"
                elif "float" in col_type.lower() or "decimal" in col_type.lower() or "numeric" in col_type.lower():
                    sqlite_type = "REAL"
                
                parts = [f'"{col_name}"', sqlite_type]
                if col_spec.get("primary_key"):
                    parts.append("PRIMARY KEY")
                if not col_spec.get("nullable", True):
                    parts.append("NOT NULL")
                if col_spec.get("unique"):
                    parts.append("UNIQUE")
                    
                col_definitions.append(" ".join(parts))
                
                if "references" in col_spec:
                    ref_table = col_spec["references"].get("table")
                    ref_col = col_spec["references"].get("column")
                    fk_definitions.append(
                        f'FOREIGN KEY ("{col_name}") REFERENCES "{ref_table}" ("{ref_col}")'
                    )
            
            all_defs = col_definitions + fk_definitions
            defs_str = ",\n  ".join(all_defs)
            stmt = f'CREATE TABLE IF NOT EXISTS "{table_name}" (\n  {defs_str}\n);'
            sql_stmts.append(stmt)
            
        return "\n\n".join(sql_stmts)

    @staticmethod
    def generate_fastapi(ast: Dict[str, Any]) -> str:
        api = ast.get("api", {})
        endpoints = api.get("endpoints", [])
        auth = ast.get("authentication", {})
        permissions = auth.get("endpoint_permissions", [])
        
        # Build paths and endpoints
        endpoints_code = []
        
        for ep in endpoints:
            ep_id = ep.get("id")
            method = ep.get("method", "GET").lower()
            path = ep.get("path", "")
            # Convert paths format from /api/v1/projects/{projectId}/tasks to FastAPI format
            fastapi_path = path.replace("{", "").replace("}", "")
            # Find in-path parameters
            params = ep.get("parameters", [])
            path_params = [p.get("name") for p in params if p.get("in") == "path"]
            
            # Fetch RBAC roles
            allowed_roles = []
            for perm in permissions:
                if perm.get("endpoint_id") == ep_id:
                    allowed_roles = perm.get("allowed_roles", [])
                    break
            
            func_args = ["role: str = Header('Guest')"]
            for p in params:
                p_name = p.get("name")
                p_type = p.get("type", "string")
                py_type = "int" if "int" in p_type.lower() else "str"
                if p.get("in") == "path":
                    func_args.append(f"{p_name}: {py_type}")
                else:
                    func_args.append(f"{p_name}: Optional[{py_type}] = None")
            
            # Request body Pydantic model
            req_body = ep.get("request_body", {})
            body_model_name = f"{ep_id}Request"
            body_model_code = ""
            if req_body:
                body_fields = []
                for b_name, b_spec in req_body.items():
                    b_type = b_spec.get("type", "string")
                    py_b_type = "int" if "int" in b_type.lower() else "str"
                    req_flag = b_spec.get("required", False)
                    if req_flag:
                        body_fields.append(f"{b_name}: {py_b_type}")
                    else:
                        body_fields.append(f"{b_name}: Optional[{py_b_type}] = None")
                
                body_fields_str = "\n    ".join(body_fields)
                body_model_code = f"""
class {body_model_name}(BaseModel):
    {body_fields_str}
"""
                func_args.append(f"body: {body_model_name}")
            
            # DB operation helper
            db_op = ep.get("db_operation", {})
            db_table = db_op.get("table", "")
            db_type = db_op.get("type", "")
            
            db_code = ""
            if db_type == "select":
                db_code = f"""
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM "{db_table}"')
        rows = cursor.fetchall()
        cols = [c[0] for c in cursor.description]
        results = [dict(zip(cols, r)) for r in rows]
        return {{"data": results}}
"""
            elif db_type == "insert":
                # get fields from body
                body_fields_access = ", ".join([f"body.{f}" for f in req_body.keys()])
                body_fields_names = ", ".join([f'"{f}"' for f in req_body.keys()])
                body_fields_placeholders = ", ".join(["?" for _ in req_body.keys()])
                db_code = f"""
        cursor = conn.cursor()
        cursor.execute('INSERT INTO "{db_table}" ({body_fields_names}) VALUES ({body_fields_placeholders})', ({body_fields_access},))
        conn.commit()
        return {{"status": "Success", "id": cursor.lastrowid}}
"""
            elif db_type == "update":
                body_fields_sets = ", ".join([f'"{f}" = ?' for f in req_body.keys()])
                body_fields_values = ", ".join([f"body.{f}" for f in req_body.keys()])
                # Find path param
                id_param = path_params[0] if path_params else "id"
                db_code = f"""
        cursor = conn.cursor()
        cursor.execute('UPDATE "{db_table}" SET {body_fields_sets} WHERE id = ?', ({body_fields_values}, {id_param}))
        conn.commit()
        return {{"status": "Updated"}}
"""
            else:
                db_code = """
        return {"status": "Success"}
"""

            # Auth rules
            auth_check = ""
            if allowed_roles:
                allowed_roles_str = ", ".join([f"'{r}'" for r in allowed_roles])
                auth_check = f"""
    if role not in [{allowed_roles_str}]:
        raise HTTPException(status_code=403, detail="Role not authorized to perform action.")
"""

            ep_code = f"""{body_model_code}
@app.{method}("{fastapi_path}")
def {ep_id.lower()}({", ".join(func_args)}):{auth_check}
    with sqlite3.connect("app.db") as conn:{db_code}
"""
            endpoints_code.append(ep_code)

        full_code = f"""import os
import sqlite3
from fastapi import FastAPI, Header, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional, List, Dict, Any

app = FastAPI(title="Compiled Application API Server")

# Startup database initialization
@app.on_event("startup")
def startup():
    if os.path.exists("app_sqlite.sql"):
        with open("app_sqlite.sql", "r") as f:
            schema = f.read()
        with sqlite3.connect("app.db") as conn:
            conn.executescript(schema)
            conn.commit()
            print("Database schemas initialized.")
""" + "\n\n".join(endpoints_code)
        
        return full_code

    @staticmethod
    def generate_streamlit(ast: Dict[str, Any]) -> str:
        domain = ast.get("intent_ir", {}).get("domain", "General App")
        roles = ast.get("intent_ir", {}).get("roles", ["Admin", "Member", "Guest"])
        components = ast.get("ui", {}).get("components", [])
        endpoints = ast.get("api", {}).get("endpoints", [])
        
        # Construct Streamlit UI components code
        ui_elements_code = []
        
        for comp in components:
            comp_id = comp.get("id")
            comp_type = comp.get("type")
            data_source = comp.get("data_source")
            actions = comp.get("actions", {})
            
            element_code = f"\n    st.subheader('{comp_id} ({comp_type})')"
            
            if comp_type in ["KanbanBoard", "TableList", "List"]:
                if data_source:
                    ep_id = data_source.get("endpoint_id")
                    # Find endpoint schema
                    ep = next((e for e in endpoints if e.get("id") == ep_id), None)
                    if ep:
                        path = ep.get("path", "")
                        # Convert path params to placeholders or defaults
                        clean_path = path.replace("{projectId}", "1").replace("{taskId}", "1")
                        element_code += f"""
    # Fetching from backend
    try:
        res = requests.get(f"http://127.0.0.1:8001{clean_path}", headers={{"role": user_role}})
        if res.status_code == 200:
            data = res.json().get("data", [])
            if data:
                st.dataframe(data, use_container_width=True)
            else:
                st.info("No records found in database table.")
        else:
            st.error(f"API Error ({{res.status_code}}): {{res.json().get('detail', res.text)}}")
    except Exception as e:
        st.warning(f"Could not connect to live API backend on port 8001: {{str(e)}}. Showing mock sample data:")
        st.write([
            {{"id": "1", "title": "Setup database tables", "status": "In Progress"}},
            {{"id": "2", "title": "Configure payments and auth", "status": "Todo"}}
        ])
"""
            elif comp_type == "Form":
                onSubmit = actions.get("onSubmit") or actions.get("Submit")
                if onSubmit:
                    ep_id = onSubmit.get("endpoint_id")
                    ep = next((e for e in endpoints if e.get("id") == ep_id), None)
                    if ep:
                        path = ep.get("path", "")
                        clean_path = path.replace("{projectId}", "1").replace("{taskId}", "1")
                        req_body = ep.get("request_body", {})
                        
                        # Generate form input fields dynamically
                        form_inputs = []
                        payload_fields = []
                        for field_name, field_spec in req_body.items():
                            form_inputs.append(f"{field_name} = st.text_input('{field_name.capitalize()}')")
                            payload_fields.append(f"'{field_name}': {field_name}")
                            
                        form_inputs_str = "\n        ".join(form_inputs)
                        payload_str = ", ".join(payload_fields)
                        
                        element_code += f"""
    with st.form('{comp_id}_form'):
        {form_inputs_str}
        submitted = st.form_submit_button('Submit Form')
        if submitted:
            payload = {{{payload_str}}}
            try:
                res = requests.post(f"http://127.0.0.1:8001{clean_path}", json=payload, headers={{"role": user_role}})
                if res.status_code == 200:
                    st.success("Record created successfully in database!")
                    st.json(res.json())
                else:
                    st.error(f"Submission failed ({{res.status_code}}): {{res.json().get('detail', res.text)}}")
            except Exception as e:
                st.error(f"Could not connect to live API server on port 8001: {{str(e)}}")
"""
            ui_elements_code.append(element_code)
            
        full_code = f"""import streamlit as st
import requests

st.set_page_config(layout="wide")

st.title("Compiled App Runtime UI - {domain}")

st.sidebar.title("App Authentication Context")
user_role = st.sidebar.selectbox("Simulated User Role", {roles})

st.info(f"Viewing page as role: **{{user_role}}**")

# Generated views
st.write("---")
def render_main():
{"".join(ui_elements_code)}

render_main()
"""
        return full_code
