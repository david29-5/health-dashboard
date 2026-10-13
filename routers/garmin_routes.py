from fastapi import APIRouter, BackgroundTasks
from datetime import date
from services.garmin_service import leer_cache_garmin, sincronizar_garmin_background

router = APIRouter(prefix="/api/garmin", tags=["Garmin"])

@router.get("/calorias")
def obtener_calorias(background_tasks: BackgroundTasks):
    hoy = date.today().isoformat()
    
    # Leemos rapidísimo de nuestra caché
    quemadas = leer_cache_garmin(hoy)
    
    # Mandamos al trabajador a que actualice los datos reales por la espalda
    background_tasks.add_task(sincronizar_garmin_background, hoy)
    
    return {
        "success": True, 
        "fecha": hoy, 
        "caloriasTotales": quemadas,
        "nota": "Actualizando Garmin en segundo plano para la próxima recarga"
    }