import os
from datetime import date
from garminconnect import Garmin
from dotenv import load_dotenv
from database.db import get_db_connection

# Cargar las variables del archivo .env
load_dotenv()

# Carpeta donde se guardarán los tokens de sesión
SESSION_DIR = ".garmin_session"

def get_garmin_client(email=None, password=None):
    user = email or os.getenv("GARMIN_USERNAME")
    pwd = password or os.getenv("GARMIN_PASSWORD")
    
    if not user or not pwd:
        raise ValueError("No hay credenciales de Garmin configuradas.")
        
    client = Garmin(user, pwd)
    
    try:
        # 1. Intentamos cargar la sesión guardada para no hacer login de cero
        client.login(SESSION_DIR)
        print("✅ Sesión de Garmin cargada desde caché.")
    except Exception:
        # 2. Si no hay sesión o falló, hacemos login tradicional
        print("🔄 Iniciando sesión en Garmin desde cero...")
        client.login()
        # 3. Guardamos los tokens para la próxima vez
        client.garth.dump(SESSION_DIR)
        print("💾 Nueva sesión de Garmin guardada con éxito.")
        
    return client

def obtener_resumen_hoy(fecha_iso=None):
    try:
        # 1. Definimos qué día estamos buscando y cuál es el día de hoy
        hoy_iso = date.today().isoformat()
        fecha_objetivo_str = fecha_iso if fecha_iso else hoy_iso
        fecha_objetivo = date.fromisoformat(fecha_objetivo_str)

        es_pasado = fecha_objetivo_str < hoy_iso

        # 2. Si pedimos un día del PASADO, miramos primero en nuestra caché (SQLite)
        if es_pasado:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute('SELECT calorias_quemadas FROM garmin_cache WHERE fecha = ?', (fecha_objetivo_str,))
            row = cursor.fetchone()
            conn.close()
            
            if row:
                print(f"⚡ [CACHÉ] Calorías de ayer ({fecha_objetivo_str}) cargadas al instante desde SQLite.")
                return {
                    "success": True,
                    "fecha": fecha_objetivo_str,
                    "caloriasTotales": row[0] # Sacamos el número guardado
                }

        # 3. Si es HOY, o es un día pasado que aún no habíamos guardado, llamamos a Garmin
        print(f"📡 [GARMIN API] Conectando a Garmin para descargar datos de {fecha_objetivo_str}...")
        api = get_garmin_client() 
        if not api:
            return {"success": False, "error": "No se pudo autenticar con Garmin"}

        stats = api.get_stats(fecha_objetivo.isoformat())
        calorias_totales = stats.get("totalKilocalories", 0)

        # 4. Si acabamos de descargar un día del PASADO, lo guardamos para no volver a pedirlo nunca
        if es_pasado:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute('''
                INSERT OR IGNORE INTO garmin_cache (fecha, calorias_quemadas) 
                VALUES (?, ?)
            ''', (fecha_objetivo_str, calorias_totales))
            conn.commit()
            conn.close()
            print(f"💾 [CACHÉ] Datos de {fecha_objetivo_str} guardados en el disco duro para siempre.")

        return {
            "success": True,
            "fecha": fecha_objetivo.isoformat(),
            "caloriasTotales": calorias_totales,
            "pasos": stats.get("totalSteps", 0),
            "caloriasActivas": stats.get("activeKilocalories", 0),
            "caloriasReposo": stats.get("bmrKilocalories", 0)
        }
    except Exception as e:
        print(f"Error conectando a Garmin: {e}")
        return {"success": False, "error": str(e)}

