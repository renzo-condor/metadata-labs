import pandas as pd
from pathlib import Path
from datetime import datetime

# === CONFIGURACIÓN ===
TIMEOUT_SEC = 30

# Limpia caracteres inválidos para Windows/Mac
def limpiar_nombre_archivo(nombre):
    return "".join(c for c in nombre if c.isalnum() or c in (' ', '.', '_', '-')).strip()

# Descarga físicamente el archivo desde la API de DSpace.
def descargar_pdf(session, url, destino):
    try:
        # stream=True es vital para no saturar la RAM con PDFs gigantes
        with session.get(url, stream=True, timeout=TIMEOUT_SEC) as r:
            r.raise_for_status()
            with open(destino, 'wb') as f:
                for chunk in r.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
        return True
    except Exception as e:
        print(f"      [ERROR] Falló la conexión: {e}")
        return False

# Orquesta el proceso completo de descarga para cada ítem del DataFrame.
def procesar_descargas(session, df, base_url):
    if df.empty:
        print("No hay ítems para procesar.")
        return

    print(f"\n[1/2] Iniciando proceso de descarga para {len(df)} ítems...")
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M")
    folder_path = Path(f"output/descargas_{timestamp}")
    folder_path.mkdir(parents=True, exist_ok=True)
    
    log_descargas = []
    
    for i, row in df.iterrows():
        uuid = row["UUID"]
        titulo = row["Original"][:50] + "..." if len(row["Original"]) > 50 else row["Original"]
        
        # PASO 1: Pedir la lista de "Cajones" (Bundles) del ítem
        url_bundles = f"{base_url}/api/core/items/{uuid}/bundles"
        r_bundles = session.get(url_bundles)
        
        if r_bundles.status_code != 200:
            print(f"   [!] Error HTTP {r_bundles.status_code} al buscar cajones para: {titulo}")
            continue
            
        lista_bundles = r_bundles.json().get("_embedded", {}).get("bundles", [])
        pdfs_encontrados = []
        
        # PASO 2: Buscar el cajón ORIGINAL
        for bundle in lista_bundles:
            if bundle.get("name") == "ORIGINAL":
                
                # PASO 3: Extraer el enlace oficial a los archivos de este cajón
                url_bitstreams = bundle.get("_links", {}).get("bitstreams", {}).get("href")
                
                if url_bitstreams:
                    # PASO 4: Entrar a ese enlace para ver los archivos
                    r_bits = session.get(url_bitstreams)
                    
                    if r_bits.status_code == 200:
                        archivos = r_bits.json().get("_embedded", {}).get("bitstreams", [])
                        
                        # PASO 5: Filtrar los PDFs
                        for bs in archivos:
                            nombre = bs.get("name", "")
                            mimetype = bs.get("mimeType", "").lower()
                            
                            if "application/pdf" in mimetype or nombre.lower().endswith(".pdf"):
                                link_descarga = bs.get("_links", {}).get("content", {}).get("href")
                                if link_descarga:
                                    pdfs_encontrados.append({
                                        "nombre": nombre,
                                        "url": link_descarga
                                    })
                break # Ya revisamos el ORIGINAL, no necesitamos ver más cajones
                
        if not pdfs_encontrados:
            print(f"   [?] Sin PDFs públicos en el bloque ORIGINAL: {titulo}")
            log_descargas.append({
                "UUID": uuid,
                "Título": row["Original"],
                "Archivo": "N/A",
                "Estado": "Sin PDFs en ORIGINAL"
            })
            continue

        print(f"   -> Encontrados {len(pdfs_encontrados)} PDF(s) en: {titulo}")
        
        for pdf in pdfs_encontrados:
            nombre_limpio = limpiar_nombre_archivo(pdf["nombre"])
            filename = f"{uuid[:8]}_{nombre_limpio}" 
            destino = folder_path / filename
            
            exito = descargar_pdf(session, pdf["url"], destino)
            
            log_descargas.append({
                "UUID": uuid,
                "Título": row["Original"],
                "Archivo": pdf["nombre"],
                "Estado": "Descargado" if exito else "Error de descarga"
            })
            
    print(f"\n[2/2] Generando reporte de descargas...")
    df_log = pd.DataFrame(log_descargas)
    reporte_path = folder_path / "resumen_descargas.xlsx"
    
    with pd.ExcelWriter(reporte_path, engine="openpyxl") as writer:
        df_log.to_excel(writer, index=False, sheet_name="Descargas")
        
    print(f"¡Proceso terminado de forma exitosa!")
    print(f"Archivos y reporte guardados en: {folder_path.resolve()}")