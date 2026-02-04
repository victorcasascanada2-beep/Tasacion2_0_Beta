import streamlit as st
import re
import os
import json

from backend.market_scan import run_market_scan

# ==================================================
# CONFIG STREAMLIT
# ==================================================
st.set_page_config(page_title="Tasación 2.0", layout="wide")
st.title("Tasación 2.0 – Barrido de mercado")

# ==================================================
# GOOGLE CREDENTIALS (Service Account)
# ==================================================
if "google" in st.secrets:
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "/tmp/gcp_key.json"
    with open("/tmp/gcp_key.json", "w") as f:
        json.dump(dict(st.secrets["google"]), f)

# ==================================================
# SESSION STATE INIT
# ==================================================
defaults = {
    "last_rows": [],
    "ad_selection": {},
    "selected_ads": [],
    "last_raw_md": None,
    "media_result": None,
}

for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ==================================================
# INPUTS
# ==================================================
project_id = st.text_input("Project ID de Google Cloud", value="")
marca = st.text_input("Marca", value="John Deere")
modelo = st.text_input("Modelo", value="6175R")

horas_objetivo = st.number_input(
    "Horas del tractor a tasar",
    min_value=0,
    step=100,
    value=0,
    help="Si es 0 no se filtra. Si se indica, se aplica ±1000 h."
)

# ==================================================
# HELPERS
# ==================================================
def parse_markdown_table(md_text):
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
    if not price:
        return False
    p = price.lower()
    invalid = ["consultar", "a convenir", "consult", "precio a", "-"]
    if any(k in p for k in invalid):
        return False
    return any(c.isdigit() for c in price)


def parse_price(price_str: str):
    if not price_str:
        return None
    cleaned = re.sub(r"[^\d]", "", price_str)
    return int(cleaned) if cleaned else None


def parse_hours(hours_str: str):
    if not hours_str:
        return None
    cleaned = re.sub(r"[^\d]", "", hours_str)
    return int(cleaned) if cleaned else None


def truncated_mean(values: list[int]):
    if len(values) < 3:
        return None
    values = sorted(values)
    trimmed = values[1:-1]
    return sum(trimmed) / len(trimmed)

# ==================================================
# ACTION: MARKET SCAN
# ==================================================
if st.button("🔍 Buscar mercado"):
    if not project_id:
        st.error("Introduce el Project ID de Google Cloud")
    else:
        with st.spinner("Buscando anuncios reales en mercado..."):
            resultado_md = run_market_scan(
                project_id=project_id,
                marca=marca,
                modelo=modelo
            )

        st.session_state.last_raw_md = resultado_md

        rows = parse_markdown_table(resultado_md)

        # -------- FILTROS AUTOMÁTICOS --------
        filtradas = []
        for r in rows:
            # precio
            if not has_valid_price(r.get("Precio", "")):
                continue

            # horas
            horas = parse_hours(r.get("Horas", ""))
            if horas is None:
                continue

            # filtro ±1000 horas
            if horas_objetivo > 0 and abs(horas - horas_objetivo) > 1000:
                continue

            filtradas.append(r)

        st.session_state.last_rows = filtradas

        # inicializar selección SOLO una vez
        st.session_state.ad_selection = {
            r.get("ID", ""): True for r in filtradas
        }

        st.session_state.media_result = None

# ==================================================
# RENDER LISTA + CHECKBOXES (VISIBLE)
# ==================================================
if st.session_state.last_rows:
    st.markdown("## Comparables encontrados")

    for r in st.session_state.last_rows:
        rid = r.get("ID", "")

        col1, col2 = st.columns([2, 10])

        with col1:
            use = st.checkbox(
                "Seleccionar",
                key=f"chk_{rid}",
                value=st.session_state.ad_selection.get(rid, True)
            )
            st.session_state.ad_selection[rid] = use

        with col2:
            url = extract_url(r.get("Enlace", ""))
            st.markdown(
                f"**{rid}** | {r.get('Portal','')} | "
                f"Año: {r.get('Año','')} | "
                f"Horas: {r.get('Horas','')} | "
                f"Precio: {r.get('Precio','')} | "
                f"País: {r.get('País','')}"
                + (f" | [Ver anuncio]({url})" if url else "")
            )

    st.session_state.selected_ads = [
        r for r in st.session_state.last_rows
        if st.session_state.ad_selection.get(r.get("ID", ""), False)
    ]

    st.markdown(f"### Anuncios seleccionados: {len(st.session_state.selected_ads)}")

# ==================================================
# TASACIÓN (BOTÓN CLARO)
# ==================================================
if st.session_state.selected_ads:
    st.markdown("## Tasación")

    if st.button("📊 Calcular media de mercado"):
        prices = []
        for r in st.session_state.selected_ads:
            p = parse_price(r.get("Precio", ""))
            if p:
                prices.append(p)

        if len(prices) < 3:
            st.warning("Se necesitan al menos 3 anuncios para una media truncada.")
        else:
            media = truncated_mean(prices)
            st.session_state.media_result = {
                "media": media,
                "min": min(prices),
                "max": max(prices),
                "n": len(prices),
            }

# ==================================================
# RESULTADO TASACIÓN
# ==================================================
if st.session_state.media_result:
    res = st.session_state.media_result
    st.success("Tasación calculada")
    st.metric("Precio medio de mercado", f"{res['media']:,.0f} €")
    st.write(f"Anuncios usados: {res['n']}")
    st.write(f"Precio mínimo: {res['min']:,.0f} €")
    st.write(f"Precio máximo: {res['max']:,.0f} €")

# ==================================================
# DEBUG (NO MOLESTA)
# ==================================================
if st.session_state.last_raw_md:
    st.markdown("---")
    with st.expander("🛠 Ver salida completa del modelo (debug)", expanded=False):
        st.markdown(st.session_state.last_raw_md)
