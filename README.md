# Metadata Labs || Control de Calidad de Metadatos

Metadata Labs es una suite de herramientas desarrollada en Python diseñada para automatizar la extracción, auditoría y corrección de metadatos en repositorios institucionales basados en DSpace. Mediante el uso de la API de DSpace, algoritmos de similitud (RapidFuzz) y modelos de Inteligencia Artificial (Google Gemini), este proyecto facilita el control de calidad masivo de colecciones digitales.

## Características Principales

El script principal (`main.py`) opera mediante un menú interactivo que permite ejecutar 6 módulos independientes:

* **Módulo 1: Búsqueda de Títulos Duplicados**
  Normaliza los títulos y utiliza `rapidfuzz` para detectar posibles documentos duplicados dentro de una colección basándose en umbrales de similitud estrictos y flexibles.
* **Módulo 2: Auditoría de Sintaxis de Autores**
  Evalúa reglas de formato en los nombres de los autores, detectando el uso excesivo de mayúsculas, la falta de comas separadoras o la presencia de autores corporativos.
* **Módulo 3: Comparación de Variantes de Autores**
  Extrae autores únicos y calcula una matriz de similitud para identificar distintas formas de escritura de un mismo autor, exportando los pares sospechosos a Excel.
* **Módulo 4: Validación de Identificadores ORCID**
  Extrae los IDs mediante expresiones regulares y los valida en tiempo real contra la API pública de ORCID, recuperando el estado y el nombre oficial registrado.
* **Módulo 5: Descarga Masiva de PDFs**
  Navega por los *bundles* "ORIGINAL" de los ítems en DSpace y descarga los archivos PDF de manera automatizada y segura.
* **Módulo 6: Clasificación ODS con Inteligencia Artificial**
  Utiliza el modelo **Gemini 3.1 Flash Lite** para analizar el título y resumen de los documentos y proponer automáticamente 3 Objetivos de Desarrollo Sostenible (ODS) de la ONU más pertinentes. Permite procesar colecciones enteras o ítems individuales.

## Requisitos Previos

Asegúrate de tener instalado Python 3.8+ y las siguientes librerías:

```bash
pip install pandas numpy rapidfuzz requests openpyxl python-dotenv google-genai
```

## Configuración y Variables de Entorno

El proyecto requiere un archivo `.env` en el directorio raíz para gestionar de forma segura las credenciales y URLs de los servicios. 

Crea tu archivo `.env` guiándote con el archivo `.env.example` incluido en el repositorio, el cual tiene la siguiente estructura:

```env
DSPACE_USER="correo_admin@institucion.org"
DSPACE_PASSWORD="tu_contraseña_segura"
UI_BASE_URL="[https://repositorio.institucion.org/items](https://repositorio.institucion.org/items)"
DSPACE_URL="[https://repositorio.institucion.org/server](https://repositorio.institucion.org/server)"
GEMINI_API_KEY="tu_api_key_de_gemini"
```

## Uso

1. Clona este repositorio en tu máquina local.
2. Configura tu archivo `.env` con tus credenciales reales.
3. Ejecuta el script principal desde tu terminal:

```bash
python main.py
```

El sistema te autenticará en DSpace y te presentará el menú principal interactivo. Podrás elegir escanear todo el repositorio o seleccionar una colección en específico para extraer sus metadatos e iniciar el proceso.

## Salida de Datos

Todos los módulos generan reportes detallados en formato `.xlsx` (Excel). Estos reportes se guardan automáticamente en la carpeta local `output/`, generada con la fecha y hora de ejecución para evitar sobrescribir auditorías anteriores.

## Licencia

Este proyecto está liberado bajo la [GNU General Public License v3.0 (GPLv3)](LICENSE).
Consulta el archivo `LICENSE` para más detalles sobre las libertades y condiciones de uso.