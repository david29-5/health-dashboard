from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import garmin_routes, nutrition_routes  # <--- AÑADIDO: nutrition_routes # <--- Esta es la línea 1 que faltaba
from database.db import init_db  # <--- NUEVO
from routers import garmin_routes, nutrition_routes, dashboard_routes
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

# Inicializamos la base de datos al arrancar
init_db()  # <--- NUEVO

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

# Conectar las rutas
app.include_router(garmin_routes.router)  # <--- Y esta es la línea 2 que faltaba
app.include_router(nutrition_routes.router) # <--- AÑADIDO: Enganche de nutrición
app.include_router(dashboard_routes.router) # <--- AÑADIDO

# Montamos la carpeta frontend para que sirva los archivos estáticos (JS, CSS, imágenes si hubiera)
app.mount("/static", StaticFiles(directory="frontend"), name="static")

@app.get("/")
def serve_frontend():
    # Cuando entres a localhost:8000, te devolverá el archivo HTML
    return FileResponse("frontend/index.html")