# Extractor-Contable-Automatizado---Facturas

Desarrollé esta aplicación para automatizar el cargado de facturas: perder horas tipeando datos de facturas en planillas. AutoFactura lee lotes de comprobantes en PDF, extrae la información fiscal clave y genera inteligencia de negocios al instante.

## 🚀 ¿Qué resuelve este proyecto?
En lugar de cargar datos a mano, el usuario simplemente arrastra sus facturas. El sistema extrae: **Fecha, CUIT, Razón Social, Monto Neto, IVA, Percepciones y Total**.

### Características Principales:
- **Procesamiento Híbrido:** Extrae texto nativo de PDFs de forma instantánea.
- **Validación :** Interfaz de revisión manual que garantiza el cuadre aritmético exacto antes de cualquier guardado (evitando errores en los sistemas contables).
- **Exportación Local:** Opción para descargar consolidado en CSV con formato regionalizado para Argentina (separador por punto y coma, decimales con coma).

## 🛠️ Stack Tecnológico
- **Generacion con google ai studios**
- **Frontend:** Streamlit (Python)
- **Extracción Local:** PyPDF2 y Tesseract OCR
- **Manipulación de Datos:** Pandas y Regex (Expresiones Regulares blindadas para CUITs y montos)

## ⚙️ Cómo usarlo localmente

1. Cloná este repositorio.
2. Asegurate de tener instalado [Tesseract OCR](https://github.com/UB-Mannheim/tesseract/wiki) en tu computadora (Windows).
3. Instalá las dependencias en un entorno virtual:
   ```bash
   pip install -r requirements.txt
