from groq import Groq
from dotenv import load_dotenv

# Carga tu API Key
load_dotenv()
client = Groq()

print("🔍 Preguntando a Groq qué modelos tienes disponibles...")
modelos = client.models.list()

for m in modelos.data:
    print(f"✅ {m.id}")