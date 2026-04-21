import pandas as pd
from scripts.mod0_dspace_api_client import get_session, login, seleccionar_coleccion, extraer_metadatos, BASE_URL
from scripts.mod1_title_duplicates import procesar_duplicados
from scripts.mod2_check_author_syntax import auditar_autores
from scripts.mod3_compare_authors import comparar_autores_masivo
from scripts.mod4_validate_orcid import validar_orcids
from scripts.mod5_download_pdfs import procesar_descargas
from scripts.mod6_ods_classifier import fase1_generar_propuestas_ods

if __name__ == "__main__":
    print("=======================================")
    print("METADATA LABS | Intelligence & Quality Assurance")
    print("=======================================\n")
   
    session = get_session()
    
    if login(session):
        print("\n¿Qué módulo deseas ejecutar?")
        print("1. Buscar Títulos Duplicados")
        print("2. Auditar Sintaxis de Autores")
        print("3. Comparar Variantes de Autores")
        print("4. Validar Identificadores ORCID")
        print("5. Descargar PDFs Masivamente")
        print("6. [IA] Asignar ODS Automáticamente (Gemini)")
        print("7. Salir")

        opcion = input("\nElige una opción (1-7): ")
        
        if opcion in ["1", "2", "3", "4", "5", "6"]:
            df_global = pd.DataFrame() # Creamos un df vacío por defecto
            
            if opcion == "6":
                print("\n¿Qué alcance deseas procesar con la IA?")
                print("1. Una Colección entera (Batch)")
                print("2. Un Ítem específico (Por UUID)")
                alcance = input("Elige 1 o 2: ").strip()
                
                if alcance == "1":
                    coleccion_uuid = seleccionar_coleccion(session, BASE_URL)
                    if coleccion_uuid:
                        print("\nExtrayendo metadatos de la colección...")
                        df_global = extraer_metadatos(session, BASE_URL, coleccion_uuid)
                elif alcance == "2":
                    from scripts.mod0_dspace_api_client import extraer_metadato_item_individual
                    uuid_especifico = input("\nPega el UUID del ítem: ").strip()
                    print("\nExtrayendo metadato individual...")
                    df_global = extraer_metadato_item_individual(session, BASE_URL, uuid_especifico)
                else:
                    print("Opción no válida. Cancelando...")
            
            # --- LÓGICA PARA LOS MÓDULOS 1 AL 5 (Flujo Directo) ---
            else:
                coleccion_uuid = seleccionar_coleccion(session, BASE_URL)
                if coleccion_uuid:
                    print("\nExtrayendo metadatos de la colección...")
                    df_global = extraer_metadatos(session, BASE_URL, coleccion_uuid)

            # --- EL BLOQUE DE EJECUCIÓN ---
            if not df_global.empty:
                if opcion == "1":
                    procesar_duplicados(df_global)
                elif opcion == "2":
                    auditar_autores(df_global)
                elif opcion == "3":
                    comparar_autores_masivo(df_global)
                elif opcion == "4":
                    validar_orcids(df_global)
                elif opcion == "5":
                    procesar_descargas(session, df_global, BASE_URL)
                elif opcion == "6":
                    fase1_generar_propuestas_ods(df_global)
            else:
                # Evitar doble mensaje de error si el usuario se equivocó en el input del alcance
                if opcion != "6" or (opcion == "6" and alcance in ["1", "2"]):
                    print("No se encontraron metadatos para procesar.")
                    
        elif opcion == "7":
            print("Saliendo del programa...")
        else:
            print("Opción no válida.")