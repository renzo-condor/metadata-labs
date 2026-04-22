import os
import pandas as pd
from datetime import datetime
from pathlib import Path
from rapidfuzz import fuzz, process

# === CONFIGURACIÓN ===
UI_BASE_URL = os.getenv("UI_BASE_URL")
THRESH_STRICT = 90
THRESH_LOOSE = 80

# === UTILIDADES DE LIMPIEZA ===

# Normaliza texto: comillas rectas y espacios colapsados.
def normalize_text(s: str) -> str:
    if pd.isna(s): return ""
    s = str(s).strip()
    s = s.replace("“", '"').replace("”", '"').replace("’", "'").replace("‘", "'")
    return " ".join(s.split())

# Pasa a minúsculas y quita puntuación final para comparar.
def normalize_for_compare(s: str) -> str:
    s1 = normalize_text(s).lower()
    return s1.strip(" .,-;:")

# === FUNCIÓN PRINCIPAL DEL MÓDULO ===

# Detecta pares de títulos similares y exporta los resultados a Excel.
def procesar_duplicados(df):
    if df.empty or len(df) < 2:
        print("[!] No hay suficientes ítems para comparar.")
        return

    print(f"\n[2/4] Normalizando {len(df)} títulos...")
    records = []
    
    # Iteramos sobre el DataFrame que nos mandó main.py
    for i, row in df.iterrows():
        t = row["Original"]
        records.append({
            "Idx": i + 1,
            "UUID": row["UUID"],
            "URL_Revisión": f"{UI_BASE_URL}/{row['UUID']}", 
            "Original": t,
            "Normalized": normalize_text(t),
            "CompareKey": normalize_for_compare(t),
        })

    df_norm = pd.DataFrame(records)

    print("[3/4] Ejecutando algoritmo de similitud (RapidFuzz)...")
    compare_list = df_norm["CompareKey"].tolist()
    index_list = df_norm["Idx"].tolist()

    sim_pairs = []
    scores_matrix = process.cdist(
        compare_list, compare_list, scorer=fuzz.token_set_ratio, score_cutoff=THRESH_LOOSE
    )

    n = len(compare_list)
    for i in range(n):
        for j in range(i + 1, n):
            score = scores_matrix[i, j]
            if score >= THRESH_LOOSE:
                row_A = df_norm.loc[df_norm["Idx"] == index_list[i]].iloc[0]
                row_B = df_norm.loc[df_norm["Idx"] == index_list[j]].iloc[0]
                
                sim_pairs.append({
                    "UUID_A": row_A["UUID"],
                    "Title_A": row_A["Original"],
                    "Link_A": row_A["URL_Revisión"],
                    "UUID_B": row_B["UUID"],
                    "Title_B": row_B["Original"],
                    "Link_B": row_B["URL_Revisión"],
                    "Score": int(score)
                })

    df_pairs = pd.DataFrame(sim_pairs)
    if not df_pairs.empty:
        df_pairs = df_pairs.sort_values(["Score"], ascending=[False])
        df_pairs_strict = df_pairs[df_pairs["Score"] >= THRESH_STRICT].copy()
        df_pairs_loose = df_pairs[(df_pairs["Score"] >= THRESH_LOOSE) & (df_pairs["Score"] < THRESH_STRICT)].copy()
    else:
        df_pairs_strict = pd.DataFrame()
        df_pairs_loose = pd.DataFrame()

    print("[4/4] Exportando resultados a Excel...")
    TIMESTAMP = datetime.now().strftime("%Y%m%d_%H%M")
    OUTPUT_FILE = Path(f"output/mod1_title_duplicates_{TIMESTAMP}.xlsx")
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)

    with pd.ExcelWriter(OUTPUT_FILE, engine="openpyxl") as writer:
        if not df_pairs_strict.empty:
            df_pairs_strict.to_excel(writer, index=False, sheet_name=f"Pairs_{THRESH_STRICT}_plus")
        
        if not df_pairs_loose.empty:
            df_pairs_loose.to_excel(writer, index=False, sheet_name=f"Pairs_{THRESH_LOOSE}_{THRESH_STRICT-1}")
            
        df_norm[["UUID", "URL_Revisión", "Original", "Normalized"]].to_excel(writer, index=False, sheet_name="All_titles_normalized")

    print(f"[OK] Proceso terminado. Reporte: {OUTPUT_FILE.name}")