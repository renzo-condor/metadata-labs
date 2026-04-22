import os
import pandas as pd
from datetime import datetime
from pathlib import Path

UI_BASE_URL = os.getenv("UI_BASE_URL")

# Evalúa la sintaxis de un autor individual y devuelve una observación o "Correcto".
def auditar_autor(autor):
    if pd.isna(autor) or not str(autor).strip():
        return "Celda vacía"
        
    autor = str(autor).strip()
    
    if autor.isupper() and len(autor) > 4:
        return "Todo en MAYÚSCULAS"
        
    comas = autor.count(",")
    
    if comas == 0:
        palabras_corporativas = ["asociación", "centro", "fundación", "ministerio", 
                                 "instituto", "red", "coordinadora", "derecho", 
                                 "acción", "programa", "foro", "plataforma", "sociedad",
                                 "observatorio", "movimiento", "equipo", "capítulo"]
                                 
        if any(palabra in autor.lower() for palabra in palabras_corporativas) or len(autor.split()) >= 4:
            return "Posible Autor Corporativo (Sin coma)"
        else:
            return "Falta coma separadora"
            
    if comas > 1:
        return "Exceso de comas (Más de 1)"
        
    if "," in autor and ", " not in autor:
        return "Falta espacio después de la coma"
        
    return "Correcto"

# Itera sobre todos los autores del DataFrame, audita su sintaxis y exporta las incidencias a Excel.
def auditar_autores(df):
    if df.empty:
        print("[!] No hay datos para auditar.")
        return

    print(f"\n[2/3] Auditando {len(df)} registros para validación de autores...")
    registros_autores = []
    
    for i, row in df.iterrows():
        uuid = row["UUID"]
        titulo_str = row["Original"]
        autores_str = row["dc.contributor.author"]
        
        if not autores_str or pd.isna(autores_str):
            continue

        # Los autores vienen concatenados con " || " desde el módulo de extracción    
        lista_autores = str(autores_str).split(" || ")
        
        for nombre_autor in lista_autores:
            nombre_autor = nombre_autor.strip()
            if not nombre_autor:
                continue
                
            resultado_auditoria = auditar_autor(nombre_autor)
            
            if resultado_auditoria != "Correcto":
                registros_autores.append({
                    "UUID": uuid,
                    "Título": titulo_str[:80] + "..." if len(titulo_str) > 80 else titulo_str,
                    "Autor": nombre_autor,
                    "Observación_en_Autor": resultado_auditoria,
                    "Link_Revisión": f"{UI_BASE_URL}/{uuid}"
                })

    print("[3/3] Generando reporte de auditoría...")
    df_errores = pd.DataFrame(registros_autores)
    
    if df_errores.empty:
        print("[OK] Todos los autores tienen una sintaxis correcta.")
        return

    df_errores = df_errores.sort_values(by=["Observación_en_Autor", "Autor"])

    TIMESTAMP = datetime.now().strftime("%Y%m%d_%H%M")
    OUTPUT_FILE = Path(f"output/mod2_check_author_syntax_{TIMESTAMP}.xlsx")
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)

    with pd.ExcelWriter(OUTPUT_FILE, engine="openpyxl") as writer:
        df_errores.to_excel(writer, index=False, sheet_name="Revisar")

    print(f"[OK] Proceso terminado. {len(df_errores)} incidencias encontradas. Reporte: {OUTPUT_FILE.name}")