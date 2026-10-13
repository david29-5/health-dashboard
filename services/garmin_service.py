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
        client.login(SESSION_DIR)
        print("✅ Sesión de Garmin cargada desde caché.")
    except Exception:
        print("🔄 Iniciando sesión en Garmin desde cero...")
        client.login()
        client.garth.dump(SESSION_DIR)
        print("💾 Nueva sesión de Garmin guardada con éxito.")
        
    return client

def leer_cache_garmin(fecha_iso):
    """Lee los datos súper rápido de la base de datos local"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT calorias_quemadas FROM garmin_cache WHERE fecha = ?', (fecha_iso,))
    row = cursor.fetchone()
    conn.close()
    
    # Devuelve las calorías guardadas. Si no hay nada aún, devuelve 0 para no bloquear la web.
    return row[0] if row else 0

def sincronizar_garmin_background(fecha_iso):
    """Esta función se ejecuta 'por la espalda' sin congelar la web"""
    try:
        print(f"📡 [BACKGROUND] Descargando datos de Garmin para {fecha_iso}...")
        api = get_garmin_client() 
        if not api:
            return

        fecha_objetivo = date.fromisoformat(fecha_iso)
        stats = api.get_stats(fecha_objetivo.isoformat())
        calorias_totales = stats.get("totalKilocalories", 0)

        # Guardamos el dato fresco en nuestra base de datos (machacando el anterior si existía)
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('DELETE FROM garmin_cache WHERE fecha = ?', (fecha_iso,))
        cursor.execute('INSERT INTO garmin_cache (fecha, calorias_quemadas) VALUES (?, ?)', (fecha_iso, calorias_totales))
        conn.commit()
        conn.close()
        
        print(f"💾 [BACKGROUND] ¡Garmin actualizado! ({calorias_totales} kcal listas para la próxima recarga)")

    except Exception as e:
        print(f"❌ [BACKGROUND] Error con Garmin: {e}")