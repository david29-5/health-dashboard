from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

# Importamos todas las rutas y la base de datos de una sola vez
from routers import garmin_routes, nutrition_routes, dashboard_routes, auth_routes
from database.db import init_db, get_db_connection

def inicializar_db():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS usuarios (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT,
                usa_garmin BOOLEAN DEFAULT 0,
                garmin_user TEXT,
                garmin_password TEXT
            )
        ''')
        conn.commit()
        conn.close()
        print("✅ Base de datos de usuarios verificada/creada con éxito.")
    except Exception as e:
        print(f"❌ Error creando la tabla usuarios: {e}")

# Inicializamos las tablas al arrancar el servidor
inicializar_db()
init_db()

app = FastAPI(
    title="Health Dashboard API", 
    description="Backend para análisis de Garmin y Nutrición con IA",
    version="1.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Conectar los routers
app.include_router(garmin_routes.router)
app.include_router(nutrition_routes.router)
app.include_router(dashboard_routes.router)
app.include_router(auth_routes.router)

# Montamos la carpeta frontend bajo la ruta /static
app.mount("/static", StaticFiles(directory="frontend"), name="static")

# Rutas para servir la web, el manifest y el icono de la App
@app.get("/")
def serve_frontend():
    return FileResponse("frontend/index.html")

@app.get("/manifest.json")
def serve_manifest():
    return FileResponse("manifest.json")

@app.get("/icon.png")
def serve_icon():
    return FileResponse("frontend/icon.png")