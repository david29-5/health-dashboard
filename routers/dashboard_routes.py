from fastapi import APIRouter, BackgroundTasks
from pydantic import BaseModel
from datetime import date, timedelta
from database.db import get_db_connection
from services.garmin_service import leer_cache_garmin, sincronizar_garmin_background 

router = APIRouter(prefix="/api/dashboard", tags=["Dashboard"])

# Molde para el gasto manual
class GastoManual(BaseModel):
    calorias: int
    fecha: str

@router.get("/balance/{usuario}")
def obtener_balance_diario(usuario: str, background_tasks: BackgroundTasks, fecha: str = None, modo: str = "garmin"):
    if not fecha:
        fecha_objetivo = date.today().isoformat()
    else:
        fecha_limpia = fecha.strip()[:10]
        fecha_objetivo = fecha_limpia
        
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 1. Búsqueda de comidas
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

    cursor.execute('''
        SELECT id, descripcion, calorias, proteinas, carbohidratos, grasas 
        FROM registro_comidas WHERE usuario = ? AND fecha = ?
    ''', (usuario, fecha_objetivo))
    lista_comidas = [{"id": c[0], "descripcion": c[1], "calorias": c[2], "proteinas": c[3], "carbohidratos": c[4], "grasas": c[5]} for c in cursor.fetchall()]

    # 2. Búsqueda de entrenamientos REALES (Excluimos el Gasto Manual)
    cursor.execute('''
        SELECT id, descripcion, calorias 
        FROM registro_entrenamientos 
        WHERE usuario = ? AND fecha = ? AND descripcion != 'Gasto Diario (Manual)'
    ''', (usuario, fecha_objetivo))
    lista_entrenamientos = [{"id": e[0], "descripcion": e[1], "calorias": e[2]} for e in cursor.fetchall()]
    calorias_extra_entrenos = sum(e["calorias"] for e in lista_entrenamientos)

    # 3. Extraer el Gasto Fijo Manual oculto
    cursor.execute('''
        SELECT SUM(calorias) FROM registro_entrenamientos 
        WHERE usuario = ? AND fecha = ? AND descripcion = 'Gasto Diario (Manual)'
    ''', (usuario, fecha_objetivo))
    row_manual = cursor.fetchone()
    calorias_fijas_manuales = row_manual[0] if row_manual and row_manual[0] else 0
    
    conn.close()
   
    # 4. Lógica de Base: Garmin vs Manual (SISTEMA MULTI-USUARIO)
    if modo == "garmin":
        # ¡AQUÍ ESTÁ EL CAMBIO! Le pasamos el 'usuario' para que lea solo su caché
        quemadas_base = leer_cache_garmin(fecha_objetivo, usuario)
        estado_garmin = True
        
        # ¡AQUÍ TAMBIÉN! El minion recibe el usuario para conectarse con su contraseña
        background_tasks.add_task(sincronizar_garmin_background, fecha_objetivo, usuario)
    else:
        quemadas_base = calorias_fijas_manuales
        estado_garmin = False
    
    # 5. Cálculo final
        quemadas_totales = (quemadas_base or 0) + (calorias_extra_entrenos or 0)
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
        "garmin_conectado": estado_garmin
    }

@router.get("/historico/{usuario}")
def obtener_historico(usuario: str, background_tasks: BackgroundTasks, dias: int = 7):
    historico = []
    hoy = date.today()
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    for i in range(dias - 1, -1, -1): 
        fecha_objetivo = (hoy - timedelta(days=i)).isoformat()
        
        cursor.execute('''
            SELECT SUM(calorias) 
            FROM registro_comidas 
            WHERE usuario = ? AND fecha = ?
        ''', (usuario, fecha_objetivo))
        ingeridas_row = cursor.fetchone()
        ingeridas = ingeridas_row[0] if ingeridas_row and ingeridas_row[0] else 0
        
        # ¡AQUÍ ESTÁ EL CAMBIO DEL HISTÓRICO!
        quemadas = leer_cache_garmin(fecha_objetivo, usuario)
        background_tasks.add_task(sincronizar_garmin_background, fecha_objetivo, usuario)
        
        historico.append({
            "fecha": fecha_objetivo[-5:], 
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

@router.post("/gasto-manual/{usuario}")
def añadir_gasto_manual(usuario: str, datos: GastoManual):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        DELETE FROM registro_entrenamientos 
        WHERE usuario = ? AND fecha = ? AND descripcion = 'Gasto Diario (Manual)'
    ''', (usuario, datos.fecha))
    
    cursor.execute('''
        INSERT INTO registro_entrenamientos (usuario, fecha, descripcion, calorias)
        VALUES (?, ?, ?, ?)
    ''', (usuario, datos.fecha, "Gasto Diario (Manual)", datos.calorias))
    
    conn.commit()
    conn.close()
    
    return {"success": True, "mensaje": "Gasto manual actualizado"}