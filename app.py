import streamlit as st
import re
import os
import json

from backend.market_scan import run_market_scan

# --------------------------------------------------
# CONFIG STREAMLIT
# --------------------------------------------------
st.set_page_config(page_title="Tasación 2.0", layout="wide")
st.title("Tasación 2.0 – Barrido de mercado")

# --------------------------------------------------
# GOOGLE CREDENTIALS (ADC via Service Account)
# --------------------------------------------------
# Streamlit Secrets ya entrega el JSON correcto
# NO tocamos la clave

if "google" in st.secrets:
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "/tmp/gcp_key.json"
    with open("/tmp/gcp_key.json", "w") as f:
        json.dump(dict(st.secrets["google"]), f)

# --------------------------------------------------
# SESSION STATE INIT
# --------------------------------------------------
if "selected_ads" not in st.session_state:
    st.session_state.selected_ads = []

if "ad_selection" not in st.session_state:
    st.session_state.ad_selection = {}

if "last_rows" not in st.session_state:
    st.session_state.last_rows = []

# --------------------------------------------------
# INPUTS
# --------------------------------------------------
project_id = st.text_input("Project ID de Google Cloud", value="")
marca = st.text_input("Marca", value="John Deere")
modelo = st.text_input("Modelo", value="6175R")

horas_objetivo = st.number_input(
    "Horas del tractor a tasar",
    min_value=0,
    step=100,
    value=0,
    help="Introduce las horas del tractor objetivo. Si es 0, no se filtra por horas."
)

# --------------------------------------------------
# HELPERS
# --------------------------------------------------
def parse_markdown_table(md_text):
    """
    Parsea una tabla Markdown simple a lista de dicts.
    Columnas esperadas:
    ID | Portal | Año | Horas | Precio | País | Enlace
    """
    rows = []
    lines = [l.strip() for l in md_text.splitlines() if l.strip()]
    table_lines = [l for l in lines if l.startswith("|")]

    if len(table_lines) < 3:
        return rows

    headers = [h.strip() for h in table_lines[0].strip("|").split("|")]

    for line in table_lines[2:]:
        cols = [c.strip() for c in line.strip("|").split("|")]
        if len(cols) == len(headers):
            rows.append(dict(zip(headers, cols)))

    return rows


def extract_url(cell):
    if not cell:
        return ""
    m = re.search(r"\((https?://[^)]+)\)", cell)
    if m:
        return m.group(1)
    m = re.search(r"(https?://\S+)", cell)
    return m.group(1) if m else ""


def has_valid_price(price: str) -> bool:
    """
    Devuelve True solo si el precio parece real (numérico).
    """
    if not price:
        return False

    p = price.lower()

    invalid_keywords = [
        "consultar",
        "a consultar",
        "a convenir",
        "consult",
        "precio a",
        "-"
    ]

    if any(k in p for k in invalid_keywords):
        return False

    return any(char.isdigit() for char in price)


def parse_hours(hours_str: str):
    """
    Extrae horas como entero desde texto.
    Devuelve int o None si no es válido.
    """
    if not hours_str:
        return None

    cleaned = re.sub(r"[^\d]", "", hours_str)
    if not cleaned:
        return None

    return int(cleaned)

# --------------------------------------------------
# ACTION: MARKET SCAN
# --------------------------------------------------
if st.button("Buscar mercado"):
    if not project_id:
        st.error("Introduce el Project ID de Google Cloud")
    else:
        with st.spinner("Buscando anuncios reales en mercado..."):
            resultado_md = run_market_scan(
                project_id=project_id,
                marca=marca,
                modelo=modelo
            )

        # DEBUG opcional
        with st.expander("Ver salida completa del modelo (debug)", expanded=False):
            st.markdown(resultado_md)

        rows = parse_markdown_table(resultado_md)

        # ---- FILTROS AUTOMÁTICOS ----
        rows_filtradas = []

        for r in rows:
            # 1) Precio válido
            if not has_valid_price(r.get("Precio", "")):
                continue

            # 2) Horas válidas
            horas_anuncio = parse_hours(r.get("Horas", ""))
            if horas_anuncio is None:
                continue

            # 3) Filtro ±1000 horas si hay horas objetivo
            if horas_objetivo > 0:
                if abs(horas_anuncio - horas_objetivo) > 1000:
                    continue

            rows_filtradas.append(r)

        st.session_state.last_rows = rows_filtradas

        # Inicializar selección
        st.session_state.ad_selection = {
            r.get("ID", ""): True for r in rows_filtradas
        }

# --------------------------------------------------
# RENDER RESULTADOS (ESTABLE)
# --------------------------------------------------
if st.session_state.last_rows:
    st.markdown("## Filtrar anuncios (selecciona / desmarca)")

    for r in st.session_state.last_rows:
        rid = r.get("ID", "")

        col1, col2 = st.columns([1, 12])

        with col1:
            use = st.checkbox(
                "",
                key=f"chk_{rid}",
                value=st.session_state.ad_selection.get(rid, True)
            )

        st.session_state.ad_selection[rid] = use

        with col2:
            url = extract_url(r.get("Enlace", ""))
            st.markdown(
                f"**{rid}** | {r.get('Portal','')} | "
                f"Año: {r.get('Año','')} | Horas: {r.get('Horas','')} | "
                f"Precio: {r.get('Precio','')} | País: {r.get('País','')}"
                + (f" | [Ver anuncio]({url})" if url else "")
            )

    # Selección final
    st.session_state.selected_ads = [
        r for r in st.session_state.last_rows
        if st.session_state.ad_selection.get(r.get("ID",""), False)
    ]

    st.markdown(f"### Anuncios seleccionados: {len(st.session_state.selected_ads)}")

# --------------------------------------------------
# SELECCIÓN PERSISTENTE
# --------------------------------------------------
st.markdown("---")
st.markdown("## Selección actual (persistente)")

if st.session_state.selected_ads:
    st.json(st.session_state.selected_ads)
else:
    st.info("Aún no hay anuncios seleccionados.")
