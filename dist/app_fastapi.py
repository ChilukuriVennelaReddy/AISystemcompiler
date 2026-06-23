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

@app.get("/api/v1/users")
def ep_get_users(role: str = Header('Guest')):
    if role not in ['Admin', 'Member']:
        raise HTTPException(status_code=403, detail="Role not authorized to perform action.")

    with sqlite3.connect("app.db") as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM "users"')
        rows = cursor.fetchall()
        cols = [c[0] for c in cursor.description]
        results = [dict(zip(cols, r)) for r in rows]
        return {"data": results}




class EP_CREATE_USERRequest(BaseModel):
    email: str
    full_name: str

@app.post("/api/v1/users")
def ep_create_user(role: str = Header('Guest'), body: EP_CREATE_USERRequest):
    if role not in ['Admin', 'Member']:
        raise HTTPException(status_code=403, detail="Role not authorized to perform action.")

    with sqlite3.connect("app.db") as conn:
        cursor = conn.cursor()
        cursor.execute('INSERT INTO "users" ("email", "full_name") VALUES (?, ?)', (body.email, body.full_name,))
        conn.commit()
        return {"status": "Success", "id": cursor.lastrowid}




@app.get("/api/v1/users/userId/orders")
def ep_get_orders(role: str = Header('Guest'), userId: str):
    if role not in ['Admin', 'Member']:
        raise HTTPException(status_code=403, detail="Role not authorized to perform action.")

    with sqlite3.connect("app.db") as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM "orders"')
        rows = cursor.fetchall()
        cols = [c[0] for c in cursor.description]
        results = [dict(zip(cols, r)) for r in rows]
        return {"data": results}




class EP_CREATE_ORDERRequest(BaseModel):
    order_number: str
    total: str
    status: str

@app.post("/api/v1/users/userId/orders")
def ep_create_order(role: str = Header('Guest'), userId: str, body: EP_CREATE_ORDERRequest):
    if role not in ['Admin', 'Member']:
        raise HTTPException(status_code=403, detail="Role not authorized to perform action.")

    with sqlite3.connect("app.db") as conn:
        cursor = conn.cursor()
        cursor.execute('INSERT INTO "orders" ("order_number", "total", "status") VALUES (?, ?, ?)', (body.order_number, body.total, body.status,))
        conn.commit()
        return {"status": "Success", "id": cursor.lastrowid}

