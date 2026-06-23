import os
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

@app.get("/api/v1/contacts")
def ep_get_contacts(role: str = Header('Guest')):
    if role not in ['Admin', 'Member']:
        raise HTTPException(status_code=403, detail="Role not authorized to perform action.")

    with sqlite3.connect("app.db") as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM "contacts"')
        rows = cursor.fetchall()
        cols = [c[0] for c in cursor.description]
        results = [dict(zip(cols, r)) for r in rows]
        return {"data": results}




class EP_CREATE_CONTACTRequest(BaseModel):
    first_name: str
    last_name: str
    phone: Optional[str] = None

@app.post("/api/v1/contacts")
def ep_create_contact(role: str = Header('Guest'), body: EP_CREATE_CONTACTRequest):
    if role not in ['Admin', 'Member']:
        raise HTTPException(status_code=403, detail="Role not authorized to perform action.")

    with sqlite3.connect("app.db") as conn:
        cursor = conn.cursor()
        cursor.execute('INSERT INTO "contacts" ("first_name", "last_name", "phone") VALUES (?, ?, ?)', (body.first_name, body.last_name, body.phone,))
        conn.commit()
        return {"status": "Success", "id": cursor.lastrowid}

