import os
import time
import mysql.connector
from fastapi import FastAPI
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()

def get_connection():
    return mysql.connector.connect(
        host=os.getenv("DB_HOST"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASS"),
        database=os.getenv("DB_NAME")
    )

@app.get("/")
def home():
    return {"message": "API funcionando proyecto final computación en la nube grupo 05"}

@app.get("/loadtest/cpu")
def cpu_stress(seconds: int = 5):
    end_time = time.time() + seconds
    x = 0
    
    while time.time() < end_time:
        x += 1

    return {
        "message": f"CPU Stress test completed",
        "duration_seconds": seconds,
        "operations": x
    }

@app.get("/series")
def get_series():
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT * FROM series")
    result = cursor.fetchall()

    cursor.close()
    conn.close()

    return result

@app.get("/series/{id}")
def get_serie_by_id(id: int):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT * FROM series WHERE serie_id = %s", (id,))
    result = cursor.fetchone()

    cursor.close()
    conn.close()

    if not result:
        raise HTTPException(status_code=404, detail="Serie not found")

    return result