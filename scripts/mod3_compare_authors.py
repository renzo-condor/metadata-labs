import pandas as pd
import numpy as np
from datetime import datetime
from pathlib import Path
from rapidfuzz import fuzz, process

# === CONFIGURACIÓN ===
# Umbral de similitud
THRESHOLD = 80

def comparar_autores_masivo(df):
    """
    Realiza un control de autoridades fuzzy sobre el DataFrame global.
    Detecta variantes de nombres basándose en similitud de tokens.
    """
    if df.empty:
        print("No hay datos para procesar.")
        return

    print(f"\n[1/3] Extrayendo y contando frecuencias de autores únicos...")
    
    # 1. Expandir autores y contar frecuencias
    # Separamos los autores que mod0 unió con " || "
    all_authors = []
    for val in df["dc.contributor.author"].dropna():
        all_authors.extend([a.strip() for a in str(val).split(" || ") if a.strip()])
    
    if not all_authors:
        print("No se encontraron autores para comparar.")
        return

    # Creamos un conteo de frecuencia (¿Cuántas veces aparece cada autor escrito así?)
    df_counts = pd.Series(all_authors).value_counts().reset_index()
    df_counts.columns = ["Autor", "Frecuencia"]
    
    unique_authors = df_counts["Autor"].tolist()
    n = len(unique_authors)
    print(f"      -> Se encontraron {n} autores únicos en la colección.")

    if n < 2:
        print("No hay suficientes autores distintos para realizar una comparación.")
        return

    print(f"[2/3] Calculando matriz de similitud (RapidFuzz cdist)...")
    
    # 2. Calcular Similitud N x N
    # Usamos token_sort_ratio porque ignora el orden (útil para nombres: Juan Pérez vs Pérez, Juan)
    # score_cutoff ayuda a que el proceso sea más rápido al ignorar coincidencias bajas
    matrix = process.cdist(unique_authors, unique_authors, scorer=fuzz.token_sort_ratio, score_cutoff=THRESHOLD)

    # 3. Extraer los pares sospechosos
    pares_sospechosos = []
    
    # Solo recorremos la mitad superior de la matriz (encima de la diagonal) 
    # para evitar duplicar comparaciones (A vs B y B vs A)
    for i in range(n):
        for j in range(i + 1, n):
            score = matrix[i, j]
            if score >= THRESHOLD:
                autor_a = unique_authors[i]
                autor_b = unique_authors[j]
                
                # Obtener frecuencias
                freq_a = df_counts.loc[df_counts["Autor"] == autor_a, "Frecuencia"].values[0]
                freq_b = df_counts.loc[df_counts["Autor"] == autor_b, "Frecuencia"].values[0]
                
                pares_sospechosos.append({
                    "Autor_A": autor_a,
                    "Freq_A": freq_a,
                    "Autor_B": autor_b,
                    "Freq_B": freq_b,
                    "Similitud_%": round(score, 1)
                })

    print(f"[3/3] Exportando reporte de autoridades...")
    df_final = pd.DataFrame(pares_sospechosos)
    
    if df_final.empty:
        print("No se encontraron variantes sospechosas con el umbral actual.")
        return

    # Ordenar por similitud (lo más parecido arriba)
    df_final = df_final.sort_values(by="Similitud_%", ascending=False)

    TIMESTAMP = datetime.now().strftime("%Y%m%d_%H%M")
    OUTPUT_FILE = Path(f"output/reporte_autoridades_{TIMESTAMP}.xlsx")
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)

    with pd.ExcelWriter(OUTPUT_FILE, engine="openpyxl") as writer:
        df_final.to_excel(writer, index=False, sheet_name="Revisar_Variantes")

    print(f"¡Proceso terminado! Se detectaron {len(df_final)} pares de posibles variantes.")
    print(f"Revisa el reporte en: {OUTPUT_FILE.name}")