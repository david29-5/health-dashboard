import os
from datetime import date
from garminconnect import Garmin
from database.db import get_db_connection

def inicializar_cache_multiusuario():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS garmin_cache_v2 (
            usuario TEXT, 
            fecha TEXT, 
            calorias_quemadas INTEGER
        )
    ''')
    conn.commit()
    conn.close()

inicializar_cache_multiusuario()

def leer_cache_garmin(fecha_iso, usuario):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT calorias_quemadas FROM garmin_cache_v2 WHERE fecha = ? AND usuario = ?', (fecha_iso, usuario))
    row = cursor.fetchone()
    conn.close()
    return row[0] if row else 0

def sincronizar_garmin_background(fecha_iso, usuario):
    """Sincronización en segundo plano protegida contra el error 429"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('SELECT garmin_user, garmin_password FROM usuarios WHERE username = ?', (usuario,))
    row = cursor.fetchone()
    
    if not row or not row[0] or not row[1]:
        print(f"❌ [BACKGROUND] El usuario {usuario} no tiene credenciales de Garmin vinculadas.")
        conn.close()
        return

    g_user, g_pass = row[0], row[1]
    conn.close()
    
    try:
        # Carpeta de sesión única por usuario en el disco del servidor
        session_dir = f".garmin_session_{usuario}"
        client = Garmin(g_user, g_pass)
        
        # Intentamos cargar la sesión existente SIN forzar un login nuevo que active el bloqueador 429
        try:
            client.login(session_dir)
            print(f"✅ [GARMIN] Sesión reutilizada desde caché para {usuario}.")
        except Exception:
            print(f"🔄 [GARMIN] Generando nuevo token de sesión para {usuario}...")
            client.login()
            client.garth.dump(session_dir)
            
        # Descargamos los datos del día
        stats = client.get_stats(fecha_iso)
        calorias = stats.get("totalKilocalories", 0)
        
        # Guardamos en la caché local
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('DELETE FROM garmin_cache_v2 WHERE fecha = ? AND usuario = ?', (fecha_iso, usuario))
        cursor.execute('INSERT INTO garmin_cache_v2 (usuario, fecha, calorias_quemadas) VALUES (?, ?, ?)', (usuario, fecha_iso, calorias))
        conn.commit()
        conn.close()
        
        print(f"💾 [BACKGROUND] Garmin actualizado con éxito para {usuario}: {calorias} kcal.")
    except Exception as e:
        print(f"❌ [BACKGROUND] Error de conexión con Garmin (posible bloque temporal 429): {e}")