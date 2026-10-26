import os
import io
import re
import base64
from datetime import datetime
from PIL import Image
import pandas as pd
import streamlit as st
import pypdf
import pytesseract

# -----------------------------------------------------------------------------
# 1. CONFIGURACIÓN LOCAL
# -----------------------------------------------------------------------------
# Ruta de Tesseract OCR instalado en Windows
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

# -----------------------------------------------------------------------------
# 2. FUNCIONES DE EXTRACCIÓN (100% LOCAL SIN IA)
# -----------------------------------------------------------------------------
def limpiar_monto(valor) -> float:
    if isinstance(valor, (int, float)): 
        return float(valor)
    texto = str(valor).replace("$", "").replace(" ", "").strip()
    if texto.count(".") > 1:
        partes = texto.rsplit(".", 1)
        texto = partes[0].replace(".", "") + "." + partes[1]
    if "," in texto and "." in texto:
        texto = texto.replace(",", "")
    elif "," in texto:
        texto = texto.replace(",", ".")
    try:
        return float(texto)
    except ValueError:
        return 0.0

def extraer_datos_local(archivo_bytes: bytes, mime_type: str) -> dict:
    texto_crudo = ""
    
    if "pdf" in mime_type.lower():
        try:
            lector_pdf = pypdf.PdfReader(io.BytesIO(archivo_bytes))
            for pagina in lector_pdf.pages:
                texto_crudo += (pagina.extract_text() or "") + "\n"
        except Exception as e:
            raise Exception(f"Error al leer el archivo PDF: {e}")
    else:
        try:
            imagen_pil = Image.open(io.BytesIO(archivo_bytes))
            texto_crudo = pytesseract.image_to_string(imagen_pil, lang='spa')
        except Exception as e:
            raise Exception(f"Error al procesar la imagen con Tesseract OCR: {e}")

    datos = {
        "fecha": datetime.today().strftime("%Y-%m-%d"),
        "cuit_emisor": "", "razon_social": "",
        "monto_neto": 0.0, "iva": 0.0, "percepciones": 0.0, "total": 0.0
    }
    
    match_cuit = re.search(r'(?:CUIT|C.U.I.T.)[\s:]*([23][0347]-?\d{8}-?\d{1})', texto_crudo, re.IGNORECASE)
    if match_cuit: datos['cuit_emisor'] = match_cuit.group(1).replace('-', '').strip()
        
    match_fecha = re.search(r'(?:Fecha|Emisi[oó]n)[\s:]*(\d{4}-\d{2}-\d{2}|\d{1,2}[/-]\d{1,2}[/-]\d{2,4})', texto_crudo, re.IGNORECASE)
    if match_fecha: datos['fecha'] = match_fecha.group(1)
        
    match_rs = re.search(r'(?:Raz[oó]n Social|Emisor)[\s:]*(.+)', texto_crudo, re.IGNORECASE)
    if match_rs: datos['razon_social'] = match_rs.group(1).strip()
        
    match_neto = re.search(r'(?:Monto Neto|Neto Gravado|Subtotal)[^\d]*([\d\.,]+)', texto_crudo, re.IGNORECASE)
    if match_neto: datos['monto_neto'] = limpiar_monto(match_neto.group(1))
        
    match_iva = re.search(r'\b(?:IVA|1VA|LVA|JVA|I\.V\.A\.)\b(?:.*?%)?[^\d\n]*([\d\.,]+)', texto_crudo, re.IGNORECASE)
    if match_iva: datos['iva'] = limpiar_monto(match_iva.group(1))
        
    match_perc = re.search(r'Percepciones[^\d]*([\d\.,]+)', texto_crudo, re.IGNORECASE)
    if match_perc: datos['percepciones'] = limpiar_monto(match_perc.group(1))
        
    match_total = re.search(r'(?:TOTAL|T0TAL|Importe\s*Total|Total\s*a\s*Pagar|Total\s*Comprobante)[^\d]*([\d\.,]+)', texto_crudo, re.IGNORECASE)
    if match_total: datos['total'] = limpiar_monto(match_total.group(1))
        
    return datos

# -----------------------------------------------------------------------------
# 3. INTERFAZ DE USUARIO STREAMLIT
# -----------------------------------------------------------------------------
st.set_page_config(page_title="Extractor Local + CSV", page_icon="🧾", layout="wide")

# Inicializamos la memoria temporal para guardar el lote de facturas
if "lote_csv" not in st.session_state:
    st.session_state.lote_csv = []
if "datos_factura" not in st.session_state:
    st.session_state.datos_factura = None
if "ultimo_archivo" not in st.session_state:
    st.session_state.ultimo_archivo = None

with st.sidebar:
    st.title("📁 Archivos Contables")
    archivos_subidos = st.file_uploader("Cargar facturas (PDF, PNG, JPG):", type=["pdf", "png", "jpg", "jpeg"], accept_multiple_files=True)
    st.success("✅ Motor: 100% Local (Tesseract/PyPDF)")
    st.success("⬇️ Destino: Archivo CSV")
    
    # Mostrar el lote actual en la barra lateral
    if st.session_state.lote_csv:
        st.markdown("---")
        st.subheader(f"📦 Lote actual: {len(st.session_state.lote_csv)} facturas")
        if st.button("🗑️ Vaciar lote", use_container_width=True):
            st.session_state.lote_csv = []
            st.rerun()

st.title("🧾 Automatización de Data Entry")

if archivos_subidos:
    # Menú para navegar entre los archivos subidos
    nombres_archivos = [a.name for a in archivos_subidos]
    archivo_seleccionado = st.selectbox("📂 Seleccioná la factura a procesar:", nombres_archivos)
    
    archivo_actual = next(a for a in archivos_subidos if a.name == archivo_seleccionado)
    bytes_archivo = archivo_actual.getvalue()
    mime = archivo_actual.type or "application/pdf"
    
    # Extraer solo si cambiamos de archivo
    if st.session_state.ultimo_archivo != archivo_actual.name:
        with st.spinner("🔍 Extrayendo datos localmente..."):
            try:
                st.session_state.datos_factura = extraer_datos_local(bytes_archivo, mime)
                st.session_state.ultimo_archivo = archivo_actual.name
            except Exception as e:
                st.error(f"Error procesando archivo: {e}")
                st.session_state.datos_factura = {"fecha": "", "cuit_emisor": "", "razon_social": "", "monto_neto": 0.0, "iva": 0.0, "percepciones": 0.0, "total": 0.0}

    datos = st.session_state.datos_factura
    col_preview, col_editor = st.columns([1.1, 1], gap="large")

    with col_preview:
        st.subheader("🔍 Vista Previa")
        if "pdf" in mime.lower():
            base64_pdf = base64.b64encode(bytes_archivo).decode('utf-8')
            st.markdown(f'<iframe src="data:application/pdf;base64,{base64_pdf}" width="100%" height="650" style="border: 1px solid #ccc; border-radius: 8px;"></iframe>', unsafe_allow_html=True)
        else:
            st.image(Image.open(io.BytesIO(bytes_archivo)), use_container_width=True)

    with col_editor:
        st.subheader("✍️ Auditado y Revisión Manual")
        val_fecha = st.text_input("Fecha:", value=str(datos.get("fecha", "")))
        val_cuit = st.text_input("CUIT Emisor:", value=str(datos.get("cuit_emisor", "")))
        val_rs = st.text_input("Razón Social:", value=str(datos.get("razon_social", "")))

        m_col1, m_col2, m_col3 = st.columns(3)
        val_neto = m_col1.number_input("Monto Neto ($):", value=float(datos.get("monto_neto", 0.0)), format="%.2f")
        val_iva = m_col2.number_input("IVA ($):", value=float(datos.get("iva", 0.0)), format="%.2f")
        val_perc = m_col3.number_input("Percepciones ($):", value=float(datos.get("percepciones", 0.0)), format="%.2f")
        val_total = st.number_input("Total General ($):", value=float(datos.get("total", 0.0)), format="%.2f")

        suma = round(val_neto + val_iva + val_perc, 2)
        if round(abs(suma - round(val_total, 2)), 2) > 0.05 and val_total > 0:
            st.warning("⚠️ El total no coincide con la suma de Neto + IVA + Percepciones.")
        else:
            st.success("✨ Cuadre aritmético correcto.")

        # Botón para agregar la factura validada al lote temporal
        if st.button("➕ Confirmar y Agregar al CSV", type="primary", use_container_width=True):
            if not val_cuit or len(val_cuit) != 11: 
                st.error("CUIT inválido (11 dígitos).")
            elif val_total <= 0: 
                st.error("El total debe ser mayor a 0.")
            else:
                datos_validados = {
                    "Archivo": archivo_actual.name,
                    "Fecha": val_fecha, 
                    "CUIT": val_cuit, 
                    "Razón Social": val_rs,
                    "Monto Neto": val_neto, 
                    "IVA": val_iva, 
                    "Percepciones": val_perc, 
                    "Total": val_total
                }
                st.session_state.lote_csv.append(datos_validados)
                st.success(f"Factura '{archivo_actual.name}' agregada al lote.")

# -----------------------------------------------------------------------------
# 4. ÁREA DE DESCARGA DEL CSV
# -----------------------------------------------------------------------------
if st.session_state.lote_csv:
    st.markdown("---")
    st.subheader("📥 Lote Listo para Descargar")
    
    # Creamos el DataFrame
    df = pd.DataFrame(st.session_state.lote_csv)
    st.dataframe(df, use_container_width=True)
    
    # Configuramos el CSV para Excel Argentina (separador punto y coma, decimal coma, UTF-8 BOM)
    df_export = df.copy()
    for col in ["Monto Neto", "IVA", "Percepciones", "Total"]:
        df_export[col] = df_export[col].apply(lambda x: str(x).replace(".", ","))
        
    csv = df_export.to_csv(index=False, sep=";", encoding="utf-8-sig")
    
    st.download_button(
        label="⬇️ Descargar Facturas Procesadas (.csv)",
        data=csv,
        file_name=f"lote_facturas_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
        mime="text/csv",
        type="primary",
        use_container_width=True
    )
else:
    if not archivos_subidos:
        st.info("👈 Suba comprobantes desde el panel lateral para iniciar la extracción.")