import os
import requests
from dotenv import load_dotenv
from scripts.mod1_title_duplicates import procesar_duplicados

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

if __name__ == "__main__":
    print("=======================================")
    print("📚 METADATA LABS - DSpace 7 Automator")
    print("=======================================\n")
    
    session = get_session()
    
    if login(session):
        print("\n¿Qué módulo deseas ejecutar?")
        print("1. Buscar Títulos Duplicados (Lectura y Excel)")
        print("2. Salir")
        
        opcion = input("\nElige una opción (1-2): ")
        
        if opcion == "1":
            # Aquí llamamos al nuevo selector de colecciones
            coleccion_uuid = seleccionar_coleccion(session, BASE_URL)
            
            if coleccion_uuid:
                print("\nIniciando módulo de Duplicados...")
                # Le pasamos el UUID de la colección al script de duplicados
                procesar_duplicados(session, BASE_URL, coleccion_uuid)
        else:
            print("Saliendo del programa...")