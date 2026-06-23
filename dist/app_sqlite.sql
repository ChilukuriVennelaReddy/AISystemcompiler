CREATE TABLE IF NOT EXISTS "users" (
  "id" TEXT PRIMARY KEY NOT NULL,
  "email" TEXT NOT NULL UNIQUE,
  "full_name" TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS "patients" (
  "id" TEXT PRIMARY KEY NOT NULL,
  "first_name" TEXT NOT NULL,
  "last_name" TEXT NOT NULL,
  "date_of_birth" TEXT,
  "user_id" TEXT NOT NULL,
  FOREIGN KEY ("user_id") REFERENCES "users" ("id")
);

CREATE TABLE IF NOT EXISTS "doctors" (
  "id" TEXT PRIMARY KEY NOT NULL,
  "first_name" TEXT NOT NULL,
  "last_name" TEXT NOT NULL,
  "specialization" TEXT,
  "patient_id" TEXT NOT NULL,
  FOREIGN KEY ("patient_id") REFERENCES "patients" ("id")
);

CREATE TABLE IF NOT EXISTS "appointments" (
  "id" TEXT PRIMARY KEY NOT NULL,
  "date_time" TEXT NOT NULL,
  "reason" TEXT,
  "status" TEXT NOT NULL,
  "doctor_id" TEXT NOT NULL,
  FOREIGN KEY ("doctor_id") REFERENCES "doctors" ("id")
);

CREATE TABLE IF NOT EXISTS "prescriptions" (
  "id" TEXT PRIMARY KEY NOT NULL,
  "medication" TEXT NOT NULL,
  "dosage" TEXT NOT NULL,
  "instructions" TEXT,
  "appointment_id" TEXT NOT NULL,
  FOREIGN KEY ("appointment_id") REFERENCES "appointments" ("id")
);