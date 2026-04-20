import os
from google import genai
from dotenv import load_dotenv

load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

client = genai.Client(api_key=GEMINI_API_KEY)

print("🔍 Buscando modelos disponibles para tu API Key...\n")

try:
    # Simplemente listamos e imprimimos el nombre de cada modelo que exista
    for model in client.models.list():
        print(f"✅ {model.name}")
except Exception as e:
    print(f"Error al consultar la API: {e}")