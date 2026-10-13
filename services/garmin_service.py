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

# Ejecutamos esto al arrancar
inicializar_cache_multiusuario()

def leer_cache_garmin(fecha_iso, usuario):
    """Lee de la caché diferenciando por usuario"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT calorias_quemadas FROM garmin_cache_v2 WHERE fecha = ? AND usuario = ?', (fecha_iso, usuario))
    row = cursor.fetchone()
    conn.close()
    return row[0] if row else 0

def sincronizar_garmin_background(fecha_iso, usuario):
    """El minion ahora busca la contraseña de ESE usuario concreto en la BDD"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 1. Buscamos las credenciales del usuario
    cursor.execute('SELECT garmin_user, garmin_password FROM usuarios WHERE username = ?', (usuario,))
    row = cursor.fetchone()
    
    if not row or not row[0] or not row[1]:
        print(f"❌ [BACKGROUND] El usuario {usuario} no tiene credenciales de Garmin vinculadas.")
        conn.close()
        return

    g_user, g_pass = row[0], row[1]
    
    try:
        print(f"📡 [BACKGROUND] Descargando Garmin para {usuario}...")
        client = Garmin(g_user, g_pass)
        
        # 2. Carpeta de sesión única por usuario
        session_dir = f".garmin_session_{usuario}"
        
        try:
            client.login(session_dir)
        except Exception:
            client.login()
            client.garth.dump(session_dir)
            
        # 3. Descargamos y guardamos en la nueva caché multi-usuario
        stats = client.get_stats(fecha_iso)
        calorias = stats.get("totalKilocalories", 0)
        
        cursor.execute('DELETE FROM garmin_cache_v2 WHERE fecha = ? AND usuario = ?', (fecha_iso, usuario))
        cursor.execute('INSERT INTO garmin_cache_v2 (usuario, fecha, calorias_quemadas) VALUES (?, ?, ?)', (usuario, fecha_iso, calorias))
        conn.commit()
        print(f"💾 [BACKGROUND] Garmin actualizado para {usuario}: {calorias} kcal.")
    except Exception as e:
        print(f"❌ [BACKGROUND] Error conectando a Garmin para {usuario}: {e}")
    finally:
        conn.close()