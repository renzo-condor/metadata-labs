import os
import requests
import pandas as pd
from dotenv import load_dotenv

load_dotenv()

BASE_URL = "https://repositorio.dar.org.pe/server"
USER = os.getenv("DSPACE_USER")
PASSWORD = os.getenv("DSPACE_PASSWORD")

def get_session():
    session = requests.Session()
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (MetadataLabs PoC)",
        "Origin": BASE_URL,
    })
    return session

def refresh_csrf(session):
    r = session.get(f"{BASE_URL}/api/authn/status")
    csrf = r.headers.get("DSPACE-XSRF-TOKEN") or session.cookies.get("DSPACE-XSRF-COOKIE")
    if csrf:
        session.headers.update({"X-XSRF-TOKEN": csrf})
    return csrf

def login(session):
    refresh_csrf(session)
    r = session.post(
        f"{BASE_URL}/api/authn/login",
        data={"user": USER, "password": PASSWORD},
    )
    if r.status_code == 200:
        bearer = r.headers.get("Authorization")
        session.headers.update({"Authorization": bearer})
        print("[OK] Login exitoso.")
        return True
    else:
        print(f"[ERROR] Login falló: {r.status_code} — {r.text}")
        return False

def seleccionar_coleccion(session, base_url):
    print("\nConsultando las colecciones del repositorio...")
    r = session.get(f"{base_url}/api/core/collections?size=100")
    
    if r.status_code != 200:
        print("[ERROR] No se pudo obtener la lista de colecciones.")
        return None
        
    colecciones = r.json().get("_embedded", {}).get("collections", [])
    
    if not colecciones:
        print("No se encontraron colecciones.")
        return None
        
    print("\n=== COLECCIONES DISPONIBLES ===")
    print("0. [Escanear TODO el repositorio - ¡Cuidado!]")
    
    for i, col in enumerate(colecciones, start=1):
        nombre = col.get("name", "Colección sin nombre")
        print(f"{i}. {nombre}")
        
    while True:
        try:
            opcion = int(input("\nElige el número de la colección (0 para todas): "))
            if opcion == 0:
                return "TODO"
            if 1 <= opcion <= len(colecciones):
                coleccion_elegida = colecciones[opcion - 1]
                print(f"-> Has elegido: {coleccion_elegida.get('name')}")
                return coleccion_elegida["uuid"]
            else:
                print("Por favor, elige un número válido de la lista.")
        except ValueError:
            print("Entrada inválida. Ingresa un número.")

def extraer_metadatos(session, base_url, coleccion_uuid):
    if coleccion_uuid == "TODO":
        print("[1/4] Conectando a DSpace y extrayendo TODO el repositorio (Core API)...")
    else:
        print("[1/4] Conectando a DSpace y extrayendo la Colección (Discover API)...")
        
    items_extraidos = []
    page = 0
    size = 100 
    
    while True:
        if coleccion_uuid == "TODO":
            r = session.get(f"{base_url}/api/core/items?size={size}&page={page}")
        else:
            endpoint = f"{base_url}/api/discover/search/objects"
            params = f"?scope={coleccion_uuid}&dsoType=ITEM&embed=indexableObject&size={size}&page={page}"
            r = session.get(endpoint + params)

        if r.status_code != 200:
            print(f"[ERROR] Falló la lectura en la página {page} -> Código HTTP: {r.status_code}")
            break            
            
        data = r.json()
        
        if coleccion_uuid == "TODO":
            page_items = data.get("_embedded", {}).get("items", [])
            total_pages = data.get("page", {}).get("totalPages", 1)
        else:
            search_result = data.get("_embedded", {}).get("searchResult", {})
            objects = search_result.get("_embedded", {}).get("objects", [])
            
            page_items = []
            for obj in objects:
                item = obj.get("_embedded", {}).get("indexableObject")
                if item:
                    page_items.append(item)
            
            total_pages = search_result.get("page", {}).get("totalPages", 1)
            
        if not page_items:
            break
            
        for item in page_items:
            uuid = item.get("uuid")
            metadata = item.get("metadata", {})
            
            # Extraer Título
            titulos = metadata.get("dc.title", [])
            titulo_str = titulos[0].get("value") if titulos else "Sin título"
            
            # Extraer Autores
            autores = metadata.get("dc.contributor.author", [])
            autores_str = " || ".join([a.get("value") for a in autores]) if autores else ""

            # Extraer ORCID
            orcids = metadata.get("person.identifier.orcid", [])
            orcids_str = " || ".join([o.get("value") for o in orcids]) if orcids else ""

            # Extraer Abstract
            abstracts = metadata.get("dc.description.abstract", [])
            abstract_str = abstracts[0].get("value") if abstracts else "Sin resumen"

            items_extraidos.append({
                "UUID": uuid,
                "Original": titulo_str,
                "dc.contributor.author": autores_str,
                "person.identifier.orcid": orcids_str,
                "Abstract": abstract_str
            })
            
        print(f"      -> Página {page + 1} de {total_pages} descargada ({len(items_extraidos)} registros acumulados)")
        
        if page >= total_pages - 1:
            break
        page += 1

    return pd.DataFrame(items_extraidos)

def extraer_metadato_item_individual(session, base_url, uuid):
    """Extrae la información de un solo ítem usando su UUID."""
    print(f"Consultando UUID: {uuid}...")
    url = f"{base_url}/api/core/items/{uuid}"
    
    r = session.get(url)
    if r.status_code != 200:
        print(f"[!] Error: No se encontró el ítem {uuid}")
        return pd.DataFrame()
        
    item_data = r.json()
    metadata = item_data.get("metadata", {})
    
    titulo = metadata.get("dc.title", [{"value": "Sin Título"}])[0].get("value")
    autores = [a.get("value") for a in metadata.get("dc.contributor.author", [])]
    autores_str = " | ".join(autores) if autores else "Sin Autor"
    
    abstract_list = metadata.get("dc.description.abstract", [])
    abstract_str = abstract_list[0].get("value") if abstract_list else "Sin resumen"

    df = pd.DataFrame([{
        "UUID": uuid,
        "Original": titulo,
        "dc.contributor.author": autores_str,
        "Abstract": abstract_str
    }])
    
    return df