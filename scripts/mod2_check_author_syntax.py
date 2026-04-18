import pandas as pd
from datetime import datetime
from pathlib import Path

UI_BASE_URL = "https://repositorio.dar.org.pe/items"

def auditar_autor(autor):
    """
    Analiza la sintaxis de un autor y devuelve el tipo de error (o 'Correcto').
    Permite apellidos compuestos, iniciales y detecta instituciones.
    """
    if pd.isna(autor) or not str(autor).strip():
        return "Celda vacía"
        
    autor = str(autor).strip()
    
    # 1. Todo en mayúsculas
    if autor.isupper() and len(autor) > 4:
        return "Todo en MAYÚSCULAS"
        
    # 2. Análisis de comas
    comas = autor.count(",")
    
    if comas == 0:
        # Detectar si es una institución para no penalizarlo como un autor humano
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
        
    # 3. Tiene exactamente 1 coma. Verificamos el espacio después de ella.
    if "," in autor and ", " not in autor:
        return "Falta espacio después de la coma"
        
    # Si sobrevive a todas las pruebas, la sintaxis es Correcta
    return "Correcto"

def auditar_autores(df):
    """
    Recibe el DataFrame global de mod0, procesa los autores y exporta a Excel.
    """
    if df.empty:
        print("No hay datos para auditar.")
        return

    print(f"\n[2/3] Auditando {len(df)} registros para validación de autores...")
    registros_autores = []
    
    # Iteramos sobre el DataFrame que nos mandó main.py
    for i, row in df.iterrows():
        uuid = row["UUID"]
        titulo_str = row["Original"]
        autores_str = row["dc.contributor.author"]
        
        # Si no hay autores en este registro, pasamos al siguiente
        if not autores_str or pd.isna(autores_str):
            continue
            
        # Como mod0 unió los autores con " || ", los separamos de nuevo
        lista_autores = str(autores_str).split(" || ")
        
        for nombre_autor in lista_autores:
            nombre_autor = nombre_autor.strip()
            if not nombre_autor:
                continue
                
            resultado_auditoria = auditar_autor(nombre_autor)
            
            # Solo guardamos los que NO están correctos
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
        print("Excelente! Todos los autores tienen una sintaxis perfecta.")
        return

    # Ordenamos por tipo de error para que sea fácil trabajar en bloque
    df_errores = df_errores.sort_values(by=["Observación_en_Autor", "Autor"])

    TIMESTAMP = datetime.now().strftime("%Y%m%d_%H%M")
    OUTPUT_FILE = Path(f"output/reporte_autores_{TIMESTAMP}.xlsx")
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)

    with pd.ExcelWriter(OUTPUT_FILE, engine="openpyxl") as writer:
        df_errores.to_excel(writer, index=False, sheet_name="Revisar")

    print(f"¡Proceso terminado! Se encontraron {len(df_errores)} incidencias para revisión.")
    print(f"Revisa la carpeta 'output': {OUTPUT_FILE.name}")