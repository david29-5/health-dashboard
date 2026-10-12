from fastapi import APIRouter
from services.garmin_service import obtener_resumen_hoy

router = APIRouter(prefix="/api/garmin", tags=["Garmin"])

@router.get("/calorias")
def obtener_calorias():
    # De momento tiramos de tus credenciales del .env
    return obtener_resumen_hoy()
