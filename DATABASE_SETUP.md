# 🌿 Hamro Baari (हाम्रो बारी) - Supabase Database Setup Guide

This guide explains how to connect **Hamro Baari** with your **Supabase PostgreSQL Database** and run the backend API.

---

## 🚀 Quick Setup (3 Steps)

### Step 1: Run SQL Migration in Supabase (1-Click)
1. Go to your [Supabase Dashboard](https://supabase.com/dashboard).
2. Open your project (or create a new free project).
3. In the left navigation, click **SQL Editor**.
4. Open the [schema.sql](file:///c:/Users/LENOVO/Downloads/Deliver/schema.sql) file from this repository, copy its entire content, paste it into the Supabase SQL Editor, and click **RUN**.
   - This creates all necessary tables (`produce`, `orders`, `order_items`, `farmer_batches`, `dispatch_trucks`, `sms_logs`).
   - Automatically sets up Row Level Security (RLS) policies.
   - Populates initial authentic Nepali produce items (गोलभेंडा, रायोको साग, मुडेको आलु, etc.).

---

### Step 2: Configure your `.env` File
Open your [.env](file:///c:/Users/LENOVO/Downloads/Deliver/.env) file and add your Supabase credentials:

1. **Database Connection URI**:
   - In Supabase Dashboard, go to: **Project Settings** (gear icon) ➔ **Database** ➔ **Connection string** ➔ **URI**.
   - Choose **Transaction pooler (Port 6543)** or Session (Port 5432).
   - Paste it into `DATABASE_URL` in [.env](file:///c:/Users/LENOVO/Downloads/Deliver/.env), replacing `[YOUR-PASSWORD]` with your actual database password:
     ```env
     DATABASE_URL=postgresql://postgres.yourprojectref:yourpassword@aws-0-ap-southeast-1.pooler.supabase.com:6543/postgres?sslmode=require
     ```

2. **Supabase Project URL & Anon Key**:
   - In Supabase Dashboard, go to: **Project Settings** ➔ **API**.
   - Copy **Project URL** and **anon public key** into [.env](file:///c:/Users/LENOVO/Downloads/Deliver/.env):
     ```env
     SUPABASE_URL=https://yourprojectref.supabase.co
     SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
     ```

---

### Step 3: Run the Python FastAPI Backend

Open your terminal or PowerShell in this directory:

```powershell
# 1. Install dependencies
pip install -r requirements.txt

# 2. (Optional) Run the database seeder script
python server/seed.py

# 3. Start the FastAPI development server
python -m uvicorn server.main:app --reload --port 8000
```

Once running:
- **API Base URL**: `http://localhost:8000`
- **Interactive Swagger Documentation**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **Health Check**: [http://localhost:8000/api/health](http://localhost:8000/api/health)

---

## 📁 Backend File Architecture

```
Deliver/
├── .env                    # Active environment credentials (PostgreSQL URI & Supabase keys)
├── .env.example            # Safe template for version control
├── schema.sql              # Supabase PostgreSQL tables, RLS policies & seed data
├── requirements.txt        # Python FastAPI, SQLAlchemy, Psycopg2 dependencies
├── supabase_client.js      # Frontend JS client for connecting to FastAPI & Supabase
├── server/
│   ├── __init__.py         # Python package marker
│   ├── config.py           # Settings loader from .env
│   ├── database.py         # SQLAlchemy engine, session maker, get_db dependency
│   ├── models.py           # Database models (Produce, Order, FarmerBatch, DispatchTruck)
│   ├── schemas.py          # Pydantic request/response validation schemas
│   ├── main.py             # FastAPI app with CORS and REST routes
│   └── seed.py             # Script to seed database items
└── DATABASE_SETUP.md       # This guide
```

---

## 🔌 API Endpoints Reference

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/health` | Verifies live connection to Supabase PostgreSQL |
| `GET` | `/api/produce` | Filter catalog by category, district, search, max price |
| `POST` | `/api/orders` | Create customer pre-order (calculates totals, jute deposit) |
| `GET` | `/api/orders` | Retrieve recent order ledger |
| `GET` | `/api/farmer/batches` | Retrieve voice-registered harvest batches |
| `POST` | `/api/farmer/batches` | Record a farmer voice harvest batch |
| `GET` | `/api/admin/metrics` | Retrieve real-time KPIs (orders, weights, active farmers) |
| `POST` | `/api/admin/sms-broadcast` | Broadcast SMS alert to drivers & farmers |
