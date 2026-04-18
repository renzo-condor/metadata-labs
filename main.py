from scripts.mod0_dspace_api_client import get_session, login, seleccionar_coleccion, extraer_metadatos, BASE_URL
from scripts.mod1_title_duplicates import procesar_duplicados
from scripts.mod2_check_author_syntax import auditar_autores
from scripts.mod3_compare_authors import comparar_autores_masivo
from scripts.mod4_validate_orcid import validar_orcids

if __name__ == "__main__":
    print("=======================================")
    print("📚 METADATA LABS - DSpace 7 Automator")
    print("=======================================\n")
    
    session = get_session()
    
    if login(session):
        print("\n¿Qué módulo deseas ejecutar?")
        print("1. Buscar Títulos Duplicados")
        print("2. Auditar Sintaxis de Autores")
        print("3. Comparar Variantes de Autores (Control de Autoridades)")
        print("4. Validar Identificadores ORCID")
        print("5. Salir")

        opcion = input("\nElige una opción (1-5): ")
        
        if opcion in ["1", "2", "3", "4"]:
            coleccion_uuid = seleccionar_coleccion(session, BASE_URL)
            
            if coleccion_uuid:
                print("\nExtrayendo metadatos...")
                df_global = extraer_metadatos(session, BASE_URL, coleccion_uuid)
                
                if not df_global.empty:
                    if opcion == "1":
                        procesar_duplicados(df_global)
                    elif opcion == "2":
                        auditar_autores(df_global)
                    elif opcion == "3":
                        comparar_autores_masivo(df_global)
                    elif opcion == "4":
                        validar_orcids(df_global)
                else:
                    print("No se encontraron metadatos para procesar.")
        else:
            print("Saliendo del programa...")