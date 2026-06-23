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
    if role not in ['Patient']:
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
    if role not in ['Patient']:
        raise HTTPException(status_code=403, detail="Role not authorized to perform action.")

    with sqlite3.connect("app.db") as conn:
        cursor = conn.cursor()
        cursor.execute('INSERT INTO "users" ("email", "full_name") VALUES (?, ?)', (body.email, body.full_name,))
        conn.commit()
        return {"status": "Success", "id": cursor.lastrowid}




@app.get("/api/v1/users/userId/patients")
def ep_get_patients(role: str = Header('Guest'), userId: str):
    if role not in ['Patient']:
        raise HTTPException(status_code=403, detail="Role not authorized to perform action.")

    with sqlite3.connect("app.db") as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM "patients"')
        rows = cursor.fetchall()
        cols = [c[0] for c in cursor.description]
        results = [dict(zip(cols, r)) for r in rows]
        return {"data": results}




class EP_CREATE_PATIENTRequest(BaseModel):
    first_name: str
    last_name: str
    date_of_birth: Optional[str] = None

@app.post("/api/v1/users/userId/patients")
def ep_create_patient(role: str = Header('Guest'), userId: str, body: EP_CREATE_PATIENTRequest):
    if role not in ['Patient']:
        raise HTTPException(status_code=403, detail="Role not authorized to perform action.")

    with sqlite3.connect("app.db") as conn:
        cursor = conn.cursor()
        cursor.execute('INSERT INTO "patients" ("first_name", "last_name", "date_of_birth") VALUES (?, ?, ?)', (body.first_name, body.last_name, body.date_of_birth,))
        conn.commit()
        return {"status": "Success", "id": cursor.lastrowid}




@app.get("/api/v1/patients/patientId/doctors")
def ep_get_doctors(role: str = Header('Guest'), patientId: str):
    if role not in ['Patient']:
        raise HTTPException(status_code=403, detail="Role not authorized to perform action.")

    with sqlite3.connect("app.db") as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM "doctors"')
        rows = cursor.fetchall()
        cols = [c[0] for c in cursor.description]
        results = [dict(zip(cols, r)) for r in rows]
        return {"data": results}




class EP_CREATE_DOCTORRequest(BaseModel):
    first_name: str
    last_name: str
    specialization: Optional[str] = None

@app.post("/api/v1/patients/patientId/doctors")
def ep_create_doctor(role: str = Header('Guest'), patientId: str, body: EP_CREATE_DOCTORRequest):
    if role not in ['Patient']:
        raise HTTPException(status_code=403, detail="Role not authorized to perform action.")

    with sqlite3.connect("app.db") as conn:
        cursor = conn.cursor()
        cursor.execute('INSERT INTO "doctors" ("first_name", "last_name", "specialization") VALUES (?, ?, ?)', (body.first_name, body.last_name, body.specialization,))
        conn.commit()
        return {"status": "Success", "id": cursor.lastrowid}




@app.get("/api/v1/doctors/doctorId/appointments")
def ep_get_appointments(role: str = Header('Guest'), doctorId: str):
    if role not in ['Patient']:
        raise HTTPException(status_code=403, detail="Role not authorized to perform action.")

    with sqlite3.connect("app.db") as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM "appointments"')
        rows = cursor.fetchall()
        cols = [c[0] for c in cursor.description]
        results = [dict(zip(cols, r)) for r in rows]
        return {"data": results}




class EP_CREATE_APPOINTMENTRequest(BaseModel):
    date_time: str
    reason: Optional[str] = None
    status: str

@app.post("/api/v1/doctors/doctorId/appointments")
def ep_create_appointment(role: str = Header('Guest'), doctorId: str, body: EP_CREATE_APPOINTMENTRequest):
    if role not in ['Patient']:
        raise HTTPException(status_code=403, detail="Role not authorized to perform action.")

    with sqlite3.connect("app.db") as conn:
        cursor = conn.cursor()
        cursor.execute('INSERT INTO "appointments" ("date_time", "reason", "status") VALUES (?, ?, ?)', (body.date_time, body.reason, body.status,))
        conn.commit()
        return {"status": "Success", "id": cursor.lastrowid}




@app.get("/api/v1/appointments/appointmentId/prescriptions")
def ep_get_prescriptions(role: str = Header('Guest'), appointmentId: str):
    if role not in ['Patient']:
        raise HTTPException(status_code=403, detail="Role not authorized to perform action.")

    with sqlite3.connect("app.db") as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM "prescriptions"')
        rows = cursor.fetchall()
        cols = [c[0] for c in cursor.description]
        results = [dict(zip(cols, r)) for r in rows]
        return {"data": results}




class EP_CREATE_PRESCRIPTIONRequest(BaseModel):
    medication: str
    dosage: str
    instructions: Optional[str] = None

@app.post("/api/v1/appointments/appointmentId/prescriptions")
def ep_create_prescription(role: str = Header('Guest'), appointmentId: str, body: EP_CREATE_PRESCRIPTIONRequest):
    if role not in ['Patient']:
        raise HTTPException(status_code=403, detail="Role not authorized to perform action.")

    with sqlite3.connect("app.db") as conn:
        cursor = conn.cursor()
        cursor.execute('INSERT INTO "prescriptions" ("medication", "dosage", "instructions") VALUES (?, ?, ?)', (body.medication, body.dosage, body.instructions,))
        conn.commit()
        return {"status": "Success", "id": cursor.lastrowid}

