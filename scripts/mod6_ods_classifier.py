import os
import json
import time
import pandas as pd
from pathlib import Path
from datetime import datetime
from google import genai
from google.genai import types
from google.genai.errors import APIError
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not GEMINI_API_KEY:
    print("[!] No se encontró GEMINI_API_KEY en el archivo .env")

# Iniciar el cliente con la nueva SDK de Google
client = genai.Client(api_key=GEMINI_API_KEY)

# Envía título y resumen a Gemini y devuelve los ODS sugeridos. Reintenta si hay error 429.
def clasificar_con_ia(titulo, resumen, reintentos=3):
    prompt = f"""
    Eres un catalogador experto en repositorios académicos. 
    Tu tarea es analizar el título y el resumen de un documento académico y asignarle EXACTAMENTE tres (3) Objetivos de Desarrollo Sostenible (ODS) de la ONU que sean los más pertinentes.

    Reglas estrictas:
    1. Debes devolver ÚNICAMENTE un objeto JSON válido.
    2. La estructura del JSON debe ser exactamente esta: {{"ods": ["ODS X: Nombre", "ODS Y: Nombre", "ODS Z: Nombre"]}}
    3. Usa la nomenclatura oficial en español.
    
    Documento a analizar:
    Título: {titulo}
    Resumen: {resumen}
    """
    
    for intento in range(reintentos):
        try:
            # gemini-3.1-flash-lite-preview: modelo ligero con mayor cuota gratuita
            response = client.models.generate_content(
                model='gemini-3.1-flash-lite-preview',
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                ),
            )
            
            datos = json.loads(response.text)
            return " || ".join(datos.get("ods", []))
            
        except APIError as e:
            # Si el error es 429 (Cuota excedida), esperamos y reintentamos
            if e.code == 429:
                print(f"      [!] La IA necesita respirar (Límite de velocidad). Esperando 20 segundos... (Intento {intento + 1}/{reintentos})")
                time.sleep(35)
            else:
                print(f"      [Error de API]: {e.message}")
                return "Error en clasificación"
        except Exception as e:
            print(f"      [Error Desconocido]: {e}")
            return "Error en clasificación"
            
    return "Error: Límite de cuota excedido repetidamente"

# FASE 1: Lee los ítems, consulta a Gemini uno por uno, y exporta propuestas a Excel.
def fase1_generar_propuestas_ods(df):

    if not GEMINI_API_KEY:
        print("[ERROR] No se puede continuar sin la llave de API.")
        return
        
    print(f"\n[1/3] Iniciando clasificación IA para {len(df)} ítems usando Gemini 1.5 Flash...")
    
    resultados = []
    
    for i, row in df.iterrows():
        uuid = row["UUID"]
        titulo = row["Original"]
        resumen = row.get("Abstract", "Sin resumen")
        
        if resumen == "Sin resumen" and len(titulo) < 10:
            continue

        print(f"   [...] Clasificando: {titulo[:50]}...")
        
        ods_sugeridos = clasificar_con_ia(titulo, resumen)
        
        resultados.append({
            "UUID": uuid,
            "Título": titulo,
            "Resumen": resumen[:100] + "..." if len(resumen) > 100 else resumen,
            "dc.description.ods (Propuesta IA)": ods_sugeridos
        })
        
        # Pausa de cortesía conservadora para evitar el error 429
        time.sleep(10) 

    print("\n[2/3] Generando Excel para revisión humana...")
    df_resultados = pd.DataFrame(resultados)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M")
    output_path = Path(f"output/mod6_ods_classifier_{timestamp}.xlsx")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with pd.ExcelWriter(output_path, engine="openpyxl") as writer:
        df_resultados.to_excel(writer, index=False, sheet_name="Revisión_ODS")
        
    print(f"[OK] Proceso terminado. Revisa y edita el archivo antes de la Fase 2: {output_path.resolve()}")


# FASE 2: ACTUALIZADOR DSPACE
def fase2_actualizar_dspace(session, base_url, archivo_excel):
    # PATCH desactivado: descomentar para ejecución real (actualmente en modo simulación)
    print(f"\nLeyendo archivo revisado: {archivo_excel}...")
    try:
        df_revisado = pd.read_excel(archivo_excel)
    except Exception as e:        
        print(f"[ERROR] No se pudo leer el archivo: {e}")
        return

    print("Iniciando inyección de metadatos vía PATCH...")
    
    for i, row in df_revisado.iterrows():
        uuid = row["UUID"]
        ods_string = str(row["dc.description.ods (Propuesta IA)"])
        
        if ods_string == "nan" or "Error" in ods_string:
            continue
            
        lista_ods = ods_string.split(" || ")
        
        operaciones_patch = []
        for ods in lista_ods:
            operaciones_patch.append({
                "op": "add",
                "path": "/metadata/dc.description.ods",
                "value": ods.strip()
            })
            
        endpoint = f"{base_url}/api/core/items/{uuid}"
        headers = {"Content-Type": "application/json"}
        
        # EJECUCIÓN 
        # r = session.patch(endpoint, json=operaciones_patch, headers=headers)
        # if r.status_code == 200:
        #     print(f"[OK] ODS inyectados en {uuid}")        
        # else:
        #     print(f"[ERROR] {r.status_code} en {uuid}")
            
        print(f"[SIMULACIÓN] Se inyectarían {len(lista_ods)} ODS en UUID {uuid[:8]}")