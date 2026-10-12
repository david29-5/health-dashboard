import json
from groq import Groq
from dotenv import load_dotenv

# Carga la API Key (GROQ_API_KEY) desde tu archivo .env
load_dotenv()
client = Groq()

def analizar_comida(descripcion: str):
    prompt_sistema = """
    Eres un experto nutricionista. Voy a darte una descripción de una comida.
    Tu trabajo es estimar las calorías y los macronutrientes (proteínas, carbohidratos, grasas).
    DEBES responder ÚNICAMENTE con un objeto JSON válido, sin texto adicional, sin saludos y sin formato markdown.
    El JSON debe tener exactamente esta estructura y los valores deben ser números enteros:
    {
        "calorias": 0,
        "proteinas": 0,
        "carbohidratos": 0,
        "grasas": 0
    }
    """

    # Lista de modelos de respaldo. Si uno falla, pasa al siguiente.
    modelos_a_probar = [
        "qwen/qwen3.8-27b",
        "openai/gpt-oss-120b",
        "openai/gpt-oss-20b",
        "allam-2-7b"
    ]

    ultimo_error = None

    for modelo in modelos_a_probar:
        try:
            print(f"Probando IA con el modelo: {modelo}...")
            chat_completion = client.chat.completions.create(
                messages=[
                    {"role": "system", "content": prompt_sistema},
                    {"role": "user", "content": descripcion}
                ],
                model=modelo,
                temperature=0.1,
            )
            
            # Extraemos la respuesta
            respuesta_texto = chat_completion.choices[0].message.content.strip()
            print(f"¡Éxito con el modelo {modelo}!")
            
            # PARCHE: Limpiamos la basura de Markdown que a veces meten los modelos
            respuesta_texto = respuesta_texto.replace("```json", "").replace("```", "").strip()
            
            # Convertimos a diccionario de Python
            datos_nutricion = json.loads(respuesta_texto)
            return {"success": True, "data": datos_nutricion}

        except json.JSONDecodeError:
            ultimo_error = f"El modelo {modelo} no devolvió un JSON válido."
            print(ultimo_error)
            continue # Pasa al siguiente modelo
            
        except Exception as e:
            ultimo_error = str(e)
            print(f"Fallo con {modelo}: {ultimo_error}")
            continue # Pasa al siguiente modelo

    # Si el bucle termina y todos han fallado, entonces sí devolvemos error
    return {"success": False, "error": f"Todos los modelos fallaron. Último error: {ultimo_error}"}