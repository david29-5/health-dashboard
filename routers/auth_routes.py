from fastapi import APIRouter
from pydantic import BaseModel
from database.db import get_db_connection
from security.crypto import obtener_password_hash, verificar_password, crear_token_acceso

router = APIRouter(prefix="/api/auth", tags=["Autenticación"])

# Molde de datos que recibiremos desde la web
class UsuarioAuth(BaseModel):
    username: str
    password: str

@router.post("/registro")
def registrar_usuario(datos: UsuarioAuth):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 1. Comprobar si el usuario ya existe
    cursor.execute("SELECT id FROM usuarios WHERE username = ?", (datos.username,))
    if cursor.fetchone():
        conn.close()
        return {"success": False, "error": "El nombre de usuario ya está en uso."}
        
    # 2. Convertir la contraseña en un texto ilegible (Hashing)
    hashed_pwd = obtener_password_hash(datos.password)
    
    # 3. Guardarlo de forma segura
    cursor.execute('''
        INSERT INTO usuarios (username, password_hash, usa_garmin) 
        VALUES (?, ?, ?)
    ''', (datos.username, hashed_pwd, False)) # Por defecto sin Garmin
    
    conn.commit()
    conn.close()
    
    return {"success": True, "mensaje": "Usuario creado correctamente. ¡Ya puedes iniciar sesión!"}

@router.post("/login")
def iniciar_sesion(datos: UsuarioAuth):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Buscamos la contraseña cifrada de ese usuario
    cursor.execute("SELECT password_hash FROM usuarios WHERE username = ?", (datos.username,))
    row = cursor.fetchone()
    conn.close()
    
    # Si no hay usuario, o si no tiene contraseña, o si la contraseña no cuadra con el Hash
    if not row or not row[0] or not verificar_password(datos.password, row[0]):
        return {"success": False, "error": "Usuario o contraseña incorrectos."}
        
    # Si todo es correcto, le fabricamos un Token de acceso válido por 7 días
    token = crear_token_acceso({"sub": datos.username})
    
    return {
        "success": True, 
        "token": token,
        "username": datos.username
    }

    # Molde para recibir las credenciales de Garmin
class GarminCreds(BaseModel):
    usuario: str
    garmin_user: str
    garmin_password: str

@router.post("/guardar-garmin")
def guardar_credenciales_garmin(datos: GarminCreds):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Guardamos el correo y la contraseña de Garmin para este usuario
    cursor.execute('''
        UPDATE usuarios 
        SET garmin_user = ?, garmin_password = ?, usa_garmin = 1 
        WHERE username = ?
    ''', (datos.garmin_user, datos.garmin_password, datos.usuario))
    
    conn.commit()
    conn.close()
    
    return {"success": True, "mensaje": "Credenciales de Garmin vinculadas a tu cuenta."}