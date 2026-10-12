# --- SUSTITUYE TODO EL CONTENIDO DE routers/dashboard_routes.py ---

from fastapi import APIRouter
from datetime import date
import sqlite3
from database.db import get_db_connection
from services.garmin_service import obtener_resumen_hoy
from datetime import date, timedelta

router = APIRouter(prefix="/api/dashboard", tags=["Dashboard"])

@router.get("/balance/{usuario}")
def obtener_balance_diario(usuario: str, fecha: str = None):
    if not fecha:
        fecha_objetivo = date.today().isoformat()
    else:
        fecha_limpia = fecha.strip()[:10]
        fecha_objetivo = fecha_limpia
        
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 1. Búsqueda de comidas
    cursor.execute('''
        SELECT SUM(calorias) as total_calorias, SUM(proteinas) as total_proteinas,
               SUM(carbohidratos) as total_carbos, SUM(grasas) as total_grasas
        FROM registro_comidas WHERE usuario = ? AND fecha = ?
    ''', (usuario, fecha_objetivo))
    row = cursor.fetchone()
    
    consumidas = row["total_calorias"] if row["total_calorias"] else 0
    macros = {
        "proteinas": row["total_proteinas"] if row["total_proteinas"] else 0,
        "carbohidratos": row["total_carbos"] if row["total_carbos"] else 0,
        "grasas": row["total_grasas"] if row["total_grasas"] else 0,
    }

    cursor.execute('''
        SELECT id, descripcion, calorias, proteinas, carbohidratos, grasas 
        FROM registro_comidas WHERE usuario = ? AND fecha = ?
    ''', (usuario, fecha_objetivo))
    lista_comidas = [dict(comida) for comida in cursor.fetchall()]

    # 2. Búsqueda de entrenamientos manuales (Boxeo) - ¡ANTES DE CERRAR!
    cursor.execute('SELECT SUM(calorias) as calorias_entreno FROM registro_entrenamientos WHERE usuario = ? AND fecha = ?', (usuario, fecha_objetivo))
    row_entrenos = cursor.fetchone()
    calorias_extra = row_entrenos["calorias_entreno"] if row_entrenos and row_entrenos["calorias_entreno"] else 0
    
    # EXTRAEMOS LA LISTA PARA LA WEB
    cursor.execute('SELECT id, descripcion, calorias FROM registro_entrenamientos WHERE usuario = ? AND fecha = ?', (usuario, fecha_objetivo))
    lista_entrenamientos = [dict(e) for e in cursor.fetchall()]
    
    # ¡AQUÍ CERRAMOS LA CONEXIÓN!
    conn.close()
   
    # 3. Llamada a Garmin (no necesita la base de datos sqlite aquí)
    garmin_data = obtener_resumen_hoy(fecha_objetivo) 
    quemadas_garmin = garmin_data.get("caloriasTotales", 0) if garmin_data.get("success") else 0
    
    # 4. Cálculo final
    quemadas_totales = quemadas_garmin + calorias_extra
    balance_neto = consumidas - quemadas_totales

    return {
        "success": True,
        "usuario": usuario,
        "fecha": fecha_objetivo,
        "resumen": {
            "calorias_ingeridas": consumidas,
            "calorias_quemadas_garmin": quemadas_totales,
            "balance_neto": balance_neto,
            "estado": "Déficit 📉" if balance_neto < 0 else "Superávit 📈"
        },
        "macros_acumulados": macros,
        "comidas_registradas": lista_comidas,
        "entrenamientos_registrados": lista_entrenamientos,  # <--- AÑADE ESTA LÍNEA
        "garmin_conectado": garmin_data.get("success", False)
    }
@router.get("/historico/{usuario}")
def obtener_historico(usuario: str, dias: int = 7):
    historico = []
    hoy = date.today()
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Viajamos hacia atrás en el tiempo
    for i in range(dias - 1, -1, -1): 
        fecha_objetivo = (hoy - timedelta(days=i)).isoformat()
        
        # 1. Sumamos lo que comiste ese día
        cursor.execute('''
            SELECT SUM(calorias) 
            FROM registro_comidas 
            WHERE usuario = ? AND fecha = ?
        ''', (usuario, fecha_objetivo))
        ingeridas_row = cursor.fetchone()
        ingeridas = ingeridas_row[0] if ingeridas_row and ingeridas_row[0] else 0
        
        # 2. Vemos lo que quemaste (magia de la caché)
        # Importante: Como esta ruta ahora está en dashboard_routes, 
        # asegúrate de que arriba del todo tienes importado:
        # from services.garmin_service import obtener_resumen_hoy
        garmin_data = obtener_resumen_hoy(fecha_objetivo)
        quemadas = garmin_data.get("caloriasTotales", 0) if garmin_data.get("success") else 0
        
        # 3. Lo metemos a la lista
        historico.append({
            "fecha": fecha_objetivo[-5:], # MM-DD
            "ingeridas": ingeridas,
            "quemadas": quemadas,
            "balance": ingeridas - quemadas
        })
        
    conn.close()
    
    return {
        "success": True, 
        "usuario": usuario, 
        "dias": dias, 
        "datos": historico
    }