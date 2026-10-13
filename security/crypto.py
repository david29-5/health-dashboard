# src/security/crypto.py

from passlib.context import CryptContext
import jwt
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv

load_dotenv()

# Configuración del motor de encriptación de contraseñas de la app (Bcrypt)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Clave secreta para firmar los Tokens (¡Asegúrate de poner SECRET_KEY en tu .env de Render!)
SECRET_KEY = os.getenv("SECRET_KEY", "una_clave_secreta_super_segura_y_muy_larga")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7  # Los tokens durarán 7 días

def obtener_password_hash(password: str):
    """Convierte '1234' en un churro ilegible irreversible"""
    return pwd_context.hash(password)

def verificar_password(plain_password: str, hashed_password: str):
    """Comprueba si '1234' coincide con el churro guardado en base de datos"""
    return pwd_context.verify(plain_password, hashed_password)

def crear_token_acceso(data: dict):
    """Crea la 'pulsera de acceso' (JWT) para el usuario"""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt