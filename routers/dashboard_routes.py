# --- SUSTITUYE TODO EL CONTENIDO DE routers/dashboard_routes.py ---

from fastapi import APIRouter
from datetime import date
import sqlite3
from database.db import get_db_connection
from services.garmin_service import obtener_resumen_hoy
from datetime import date, timedelta
from pydantic import BaseModel

router = APIRouter(prefix="/api/dashboard", tags=["Dashboard"])

@router.get("/balance/{usuario}")
def obtener_balance_diario(usuario: str, fecha: str = None):
    from datetime import date
    if not fecha:
        fecha_objetivo = date.today().isoformat()
    else:
        fecha_limpia = fecha.strip()[:10]
        fecha_objetivo = fecha_limpia
        
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 1. Búsqueda de comidas (índices: 0=calorias, 1=proteinas, 2=carbos, 3=grasas)
    cursor.execute('''
        SELECT SUM(calorias), SUM(proteinas), SUM(carbohidratos), SUM(grasas)
        FROM registro_comidas WHERE usuario = ? AND fecha = ?
    ''', (usuario, fecha_objetivo))
    row = cursor.fetchone()
    
    consumidas = row[0] if row and row[0] else 0
    macros = {
        "proteinas": row[1] if row and row[1] else 0,
        "carbohidratos": row[2] if row and row[2] else 0,
        "grasas": row[3] if row and row[3] else 0,
    }

    # Lista de comidas (índices: 0=id, 1=desc, 2=cal, 3=prot, 4=carb, 5=grasas)
    cursor.execute('''
        SELECT id, descripcion, calorias, proteinas, carbohidratos, grasas 
        FROM registro_comidas WHERE usuario = ? AND fecha = ?
    ''', (usuario, fecha_objetivo))
    lista_comidas = [
        {
            "id": c[0], "descripcion": c[1], "calorias": c[2], 
            "proteinas": c[3], "carbohidratos": c[4], "grasas": c[5]
        } 
        for c in cursor.fetchall()
    ]

    # 2. Búsqueda de entrenamientos manuales (Boxeo)
    cursor.execute('SELECT SUM(calorias) FROM registro_entrenamientos WHERE usuario = ? AND fecha = ?', (usuario, fecha_objetivo))
    row_entrenos = cursor.fetchone()
    calorias_extra = row_entrenos[0] if row_entrenos and row_entrenos[0] else 0
    
    # Lista de entrenamientos (índices: 0=id, 1=desc, 2=cal)
    cursor.execute('SELECT id, descripcion, calorias FROM registro_entrenamientos WHERE usuario = ? AND fecha = ?', (usuario, fecha_objetivo))
    lista_entrenamientos = [
        {"id": e[0], "descripcion": e[1], "calorias": e[2]} 
        for e in cursor.fetchall()
    ]
    
    conn.close()
   
    # 3. Llamada a Garmin
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
        "entrenamientos_registrados": lista_entrenamientos,
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
from fastapi import APIRouter
from pydantic import BaseModel
from database.db import get_db_connection

# Modelo para recibir los datos del frontend
class CaloriasManuales(BaseModel):
    calorias: int
    fecha: str

@router.post("/calorias-manuales/{usuario}")
def añadir_calorias_manuales(usuario: str, datos: CaloriasManuales):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Lo insertamos como si fuera un entrenamiento genérico
    cursor.execute('''
        INSERT INTO registro_entrenamientos (usuario, fecha, descripcion, calorias)
        VALUES (?, ?, ?, ?)
    ''', (usuario, datos.fecha, "Gasto Diario (Manual)", datos.calorias))
    
    conn.commit()
    conn.close()
    
    return {"success": True, "mensaje": "Calorías manuales añadidas correctamente"}

# 1. Creamos el "molde" de los datos que enviará la web
class GastoManual(BaseModel):
    calorias: int
    fecha: str

# 2. Creamos la ruta para guardarlo
@router.post("/gasto-manual/{usuario}")
def añadir_gasto_manual(usuario: str, datos: GastoManual):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Lo insertamos directo en la tabla de entrenamientos
    # Como es un INSERT, no nos afecta el problema de los índices (row[0]) de Turso
    cursor.execute('''
        INSERT INTO registro_entrenamientos (usuario, fecha, descripcion, calorias)
        VALUES (?, ?, ?, ?)
    ''', (usuario, datos.fecha, "Gasto Diario (Manual)", datos.calorias))
    
    conn.commit()
    conn.close()
    
    return {"success": True, "mensaje": "Gasto manual añadido correctamente"}