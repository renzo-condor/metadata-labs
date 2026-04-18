import pandas as pd
import requests
import re
import time
from datetime import datetime
from pathlib import Path

UI_BASE_URL = "https://repositorio.dar.org.pe/items"
SLEEP_SEC = 0.2
TIMEOUT_SEC = 10

ORCID_PATTERN = re.compile(r"\b(\d{4}-\d{4}-\d{4}-\d{3}[\dX])\b", re.IGNORECASE)

def extract_orcid_id(text: str) -> str:
    if not text or pd.isna(text):
        return None
    m = ORCID_PATTERN.search(str(text).strip())
    return m.group(1) if m else None

def fetch_orcid_record(orcid_id: str):
    url = f"https://pub.orcid.org/v3.0/{orcid_id}"
    headers = {"Accept": "application/json"}
    try:
        resp = requests.get(url, headers=headers, timeout=TIMEOUT_SEC)
        if resp.status_code == 200:
            return 200, resp.json()
        return resp.status_code, None
    except requests.RequestException:
        return None, None

def parse_names(record: dict):
    if not record:
        return None, None, None
    person = record.get("person", {})
    name = person.get("name", {}) if isinstance(person, dict) else {}
    
    display = name.get("credit-name", {}).get("value") if isinstance(name.get("credit-name"), dict) else None
    given = name.get("given-names", {}).get("value") if isinstance(name.get("given-names"), dict) else None
    family = name.get("family-name", {}).get("value") if isinstance(name.get("family-name"), dict) else None

    return display, given, family

def validar_orcids(df):
    if df.empty or "person.identifier.orcid" not in df.columns:
        print("No hay datos de ORCID para procesar.")
        return

    print(f"\n[1/3] Analizando y validando ORCIDs en {len(df)} registros...")
    
    registros_resultados = []
    memoria_cache = {} # Aquí guardaremos los ORCIDs ya consultados para no repetir
    
    for i, row in df.iterrows():
        uuid = row["UUID"]
        titulo_str = row["Original"]
        orcid_raw = row.get("person.identifier.orcid", "")
        
        # Ignorar si el documento no tiene asesor/ORCID
        if not orcid_raw or pd.isna(orcid_raw):
            continue

        # Separar por si hay múltiples asesores en el mismo documento
        lista_orcids = str(orcid_raw).split(" || ")
        
        for orcid_text in lista_orcids:
            orcid_id = extract_orcid_id(orcid_text)
            
            # Caso 1: El texto no tiene formato de ORCID válido
            if not orcid_id:
                registros_resultados.append({
                    "UUID": uuid,
                    "Título_Documento": titulo_str[:80] + "...",
                    "ORCID_Ingresado": orcid_text,
                    "Estado": "Formato Inválido",
                    "Nombre_en_ORCID": None,
                    "Link_Revisión": f"{UI_BASE_URL}/{uuid}"
                })
                continue
                
            # Caso 2: Es válido, vamos a consultarlo (o sacarlo de la memoria)
            if orcid_id not in memoria_cache:
                status, data = fetch_orcid_record(orcid_id)
                display, given, family = parse_names(data)
                
                memoria_cache[orcid_id] = {
                    "status": status,
                    "nombre": display or f"{given or ''} {family or ''}".strip() or "Sin nombre público"
                }
                time.sleep(SLEEP_SEC) # Pausa de cortesía solo si es una consulta nueva
                
            # Recuperamos los datos de la memoria
            datos_orcid = memoria_cache[orcid_id]
            
            estado_final = "Activo" if datos_orcid["status"] == 200 else f"Error API ({datos_orcid['status']})"
            
            registros_resultados.append({
                "UUID": uuid,
                "Título_Documento": titulo_str[:80] + "...",
                "ORCID_Ingresado": orcid_id,
                "Estado": estado_final,
                "Nombre_en_ORCID": datos_orcid["nombre"] if datos_orcid["status"] == 200 else None,
                "Link_Revisión": f"{UI_BASE_URL}/{uuid}"
            })

    print("[2/3] Generando reporte de validación...")
    df_resultados = pd.DataFrame(registros_resultados)
    
    if df_resultados.empty:
        print("No se encontraron ORCIDs en la colección seleccionada.")
        return

    # Ordenar por estado (para ver los errores arriba)
    df_resultados = df_resultados.sort_values(by=["Estado", "ORCID_Ingresado"])

    print("[3/3] Exportando a Excel...")
    TIMESTAMP = datetime.now().strftime("%Y%m%d_%H%M")
    OUTPUT_FILE = Path(f"output/reporte_orcids_{TIMESTAMP}.xlsx")
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)

    with pd.ExcelWriter(OUTPUT_FILE, engine="openpyxl") as writer:
        df_resultados.to_excel(writer, index=False, sheet_name="Auditoria_ORCID")

    print(f"¡Proceso terminado! Se auditaron {len(df_resultados)} identificadores.")
    print(f"Revisa la carpeta 'output': {OUTPUT_FILE.name}")