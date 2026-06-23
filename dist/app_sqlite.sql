CREATE TABLE IF NOT EXISTS "users" (
  "id" TEXT PRIMARY KEY NOT NULL,
  "email" TEXT NOT NULL UNIQUE,
  "full_name" TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS "orders" (
  "id" TEXT PRIMARY KEY NOT NULL,
  "order_number" TEXT NOT NULL,
  "total" TEXT NOT NULL,
  "status" TEXT NOT NULL,
  "user_id" TEXT NOT NULL,
  FOREIGN KEY ("user_id") REFERENCES "users" ("id")
);