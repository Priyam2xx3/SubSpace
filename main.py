from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
import sqlite3
import re

# Initialize FastAPI
app = FastAPI(title="SubSpace API")

# Allow the frontend to talk to this API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic models for data validation
class Subscription(BaseModel):
    name: str
    amount: float
    cycle: str
    category: str

class EmailPayload(BaseModel):
    email_text: str

# Database setup
def init_db():
    conn = sqlite3.connect('subspace.db')
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS subscriptions
        (id INTEGER PRIMARY KEY AUTOINCREMENT,
         name TEXT, amount REAL, cycle TEXT, category TEXT)
    ''')
    conn.commit()
    conn.close()

init_db()

@app.get("/api/subscriptions")
def get_subs():
    conn = sqlite3.connect('subspace.db')
    c = conn.cursor()
    c.execute("SELECT id, name, amount, cycle, category FROM subscriptions")
    rows = c.fetchall()
    conn.close()
    
    # Format the data into a list of dictionaries
    return [{"id": r[0], "name": r[1], "amount": r[2], "cycle": r[3], "category": r[4]} for r in rows]

@app.post("/api/subscriptions")
def add_sub(sub: Subscription):
    conn = sqlite3.connect('subspace.db')
    c = conn.cursor()
    c.execute("INSERT INTO subscriptions (name, amount, cycle, category) VALUES (?, ?, ?, ?)",
              (sub.name, sub.amount, sub.cycle, sub.category))
    conn.commit()
    conn.close()
    return {"status": "success", "message": f"{sub.name} added."}

@app.post("/api/parse-email")
def parse_email(payload: EmailPayload):
    text = payload.email_text
    
    # Basic extraction logic (Regex) to find prices like $15.99
    price_match = re.search(r'\$\s*(\d+\.\d{2})', text)
    amount = float(price_match.group(1)) if price_match else 0.0
    
    # A simple keyword scanner to guess the service and category
    name = "Unknown Service"
    category = "other"
    text_lower = text.lower()
    
    if "netflix" in text_lower:
        name, category = "Netflix", "entertainment"
    elif "github" in text_lower or "aws" in text_lower:
        name, category = "Cloud Service", "productivity"
    elif "spotify" in text_lower:
        name, category = "Spotify", "entertainment"

    return {
        "suggested_name": name,
        "suggested_amount": amount,
        "suggested_category": category,
        "cycle": "monthly" # Defaulting to monthly
    }

# Run the app locally (Command: uvicorn main:app --reload)