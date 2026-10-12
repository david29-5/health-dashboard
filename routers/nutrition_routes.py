from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from datetime import date
from services.ai_service import analizar_comida
from database.db import get_db_connection

router = APIRouter(prefix="/api/nutricion", tags=["Nutrición"])

# Definimos cómo tiene que ser la petición que nos llegue del móvil
class PeticionComida(BaseModel):
    usuario: str
    descripcion: str
    fecha: str = None  # <--- CAMBIO 1: Añadimos la fecha opcional

class PeticionEntrenamiento(BaseModel):
    usuario: str
    fecha: str
    descripcion: str
    calorias: int

@router.post("/registrar")
def registrar_comida(peticion: PeticionComida):
    # <--- CAMBIO 2: Capturamos la fecha que manda la web, o usamos hoy si no manda nada
    fecha_registro = peticion.fecha if peticion.fecha else date.today().isoformat()
    
    # 1. Analizamos la comida con la IA de Groq
    resultado_ia = analizar_comida(peticion.descripcion)
    
    if not resultado_ia["success"]:
        raise HTTPException(status_code=500, detail=resultado_ia["error"])
        
    macros = resultado_ia["data"]
    
    # 2. Lo guardamos en la base de datos
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO registro_comidas 
            (usuario, fecha, descripcion, calorias, proteinas, carbohidratos, grasas)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            peticion.usuario, 
            fecha_registro,  # <--- CAMBIO 3: Guardamos la fecha correcta en la BD
            peticion.descripcion, 
            macros["calorias"], 
            macros["proteinas"], 
            macros["carbohidratos"], 
            macros["grasas"]
        ))
        conn.commit()
        conn.close()
        
        return {
            "success": True, 
            "mensaje": "Comida registrada y guardada con éxito",
            "datos_guardados": macros
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Modelo de datos para cuando editemos el texto de una comida
class EditarComidaRequest(BaseModel):
    descripcion: str

# RUTA 1: Para borrar la comida de la base de datos
@router.delete("/borrar/{comida_id}")
def borrar_comida(comida_id: int):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM registro_comidas WHERE id = ?", (comida_id,))
    conn.commit()
    conn.close()
    return {"success": True, "mensaje": f"Comida {comida_id} eliminada"}

# RUTA 2: Para editar (recalcular con la IA el nuevo texto)
@router.put("/editar/{comida_id}")
def editar_comida(comida_id: int, request: EditarComidaRequest):
    # 1. Mandamos el nuevo texto a la IA para que recalcule
    resultado_ia = analizar_comida(request.descripcion)
    
    if not resultado_ia["success"]:
        return {"success": False, "error": resultado_ia["error"]}
        
    datos = resultado_ia["data"]
    
    # 2. Actualizamos la base de datos con los nuevos valores
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE registro_comidas
        SET descripcion = ?, calorias = ?, proteinas = ?, carbohidratos = ?, grasas = ?
        WHERE id = ?
    ''', (request.descripcion, datos["calorias"], datos["proteinas"], datos["carbohidratos"], datos["grasas"], comida_id))
    conn.commit()
    conn.close()
    
    return {"success": True, "mensaje": "Actualizado", "datos": datos}
@router.post("/entrenamiento")
def registrar_entrenamiento(peticion: PeticionEntrenamiento):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO registro_entrenamientos (usuario, fecha, descripcion, calorias)
        VALUES (?, ?, ?, ?)
    ''', (peticion.usuario, peticion.fecha, peticion.descripcion, peticion.calorias))
    conn.commit()
    conn.close()
    return {"success": True, "mensaje": "Entrenamiento registrado"}
@router.delete("/entrenamiento/{entreno_id}")
def borrar_entrenamiento(entreno_id: int):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM registro_entrenamientos WHERE id = ?", (entreno_id,))
    conn.commit()
    conn.close()
    return {"success": True, "mensaje": "Entrenamiento eliminado"}