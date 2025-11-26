import os
import time
import mysql.connector
from fastapi import FastAPI, HTTPException, Request, Form
from fastapi.responses import RedirectResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from dotenv import load_dotenv
from concurrent.futures import ProcessPoolExecutor

load_dotenv()

app = FastAPI(
    title="API series y películas de Netflix",
    description="API para gestionar películas y series.",
    version="1.0.0"
)

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

def get_connection():
    return mysql.connector.connect(
        host=os.getenv("DB_HOST"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASS"),
        database=os.getenv("DB_NAME")
    )

@app.get("/health")
def health():
    return {
        "status": "healthy",
        "message": "Server running successfully"
    }

@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/series", response_class=HTMLResponse)
def listar_series(request: Request):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM series ORDER BY serie_id DESC")
    series = cursor.fetchall()
    cursor.close()
    conn.close()

    return templates.TemplateResponse("series_list.html", {"request": request, "series": series})

@app.get("/series/search", response_class=HTMLResponse)
def buscar_serie(request: Request, titulo: str = ""):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM series WHERE titulo LIKE %s", (f"%{titulo}%",))
    results = cursor.fetchall()
    cursor.close()
    conn.close()

    return templates.TemplateResponse("series_search.html", {
        "request": request,
        "titulo": titulo,
        "results": results
    })

@app.get("/series/create", response_class=HTMLResponse)
def form_crear(request: Request):
    return templates.TemplateResponse("series_create.html", {"request": request})

@app.post("/series/create")
def crear_serie(
    titulo: str = Form(...),
    descripcion: str = Form(""),
    anio_lanzamiento: int = Form(...),
    genero: str = Form(...)
):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO series (titulo, descripcion, anio_lanzamiento, genero)
        VALUES (%s, %s, %s, %s)
    """, (titulo, descripcion, anio_lanzamiento, genero))

    conn.commit()
    cursor.close()
    conn.close()

    return RedirectResponse(url="/series", status_code=303)

@app.get("/series/update/{serie_id}", response_class=HTMLResponse)
def form_actualizar(request: Request, serie_id: int):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM series WHERE serie_id = %s", (serie_id,))
    serie = cursor.fetchone()
    cursor.close()
    conn.close()

    if not serie:
        raise HTTPException(status_code=404, detail="Serie not found")

    return templates.TemplateResponse("series_update.html", {
        "request": request,
        "serie": serie
    })

@app.post("/series/update/{serie_id}")
def actualizar_serie(
    serie_id: int,
    titulo: str = Form(...),
    descripcion: str = Form(""),
    anio_lanzamiento: int = Form(...),
    genero: str = Form(...)
):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE series
        SET titulo=%s, descripcion=%s, anio_lanzamiento=%s, genero=%s
        WHERE serie_id=%s
    """, (titulo, descripcion, anio_lanzamiento, genero, serie_id))

    conn.commit()
    cursor.close()
    conn.close()

    return RedirectResponse(url="/series", status_code=303)

@app.get("/series/delete/{serie_id}")
def borrar_serie(serie_id: int):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM series WHERE serie_id = %s", (serie_id,))
    conn.commit()
    cursor.close()
    conn.close()

    return RedirectResponse(url="/series", status_code=303)

def busy_loop(duration: int):
    end_time = time.time() + duration
    x = 0
    while time.time() < end_time:
        x += 1
    return x

@app.get("/load/cpu")
def load_cpu(seconds: int = 10):
    if seconds < 1 or seconds > 60:
        return {"error": "Seconds must be between 1 and 60"}

    # Detecta cantidad de cores
    import multiprocessing
    cores = multiprocessing.cpu_count()

    # Ejecuta un proceso por core
    with ProcessPoolExecutor(max_workers=cores) as executor:
        results = list(executor.map(busy_loop, [seconds] * cores))

    return {
        "message": "CPU Load Completed",
        "cores_used": cores,
        "seconds": seconds,
        "ops_total": sum(results)
    }
