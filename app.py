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
# GOOGLE CREDENTIALS (CORRECTO)
# --------------------------------------------------
# Streamlit YA entrega el private_key bien formado.
# NO hay que tocarlo.

if "google" in st.secrets:
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "/tmp/gcp_key.json"
    with open("/tmp/gcp_key.json", "w") as f:
        json.dump(dict(st.secrets["google"]), f)

# --------------------------------------------------
# SESSION STATE
# --------------------------------------------------
if "selected_ads" not in st.session_state:
    st.session_state.selected_ads = []

# --------------------------------------------------
# INPUTS
# --------------------------------------------------
project_id = st.text_input("Project ID de Google Cloud", value="")
marca = st.text_input("Marca", value="John Deere")
modelo = st.text_input("Modelo", value="6175R")

# --------------------------------------------------
# HELPERS
# --------------------------------------------------
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

# --------------------------------------------------
# ACTION
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

        st.markdown("## Resultado del barrido")
        st.markdown(resultado_md)

        rows = parse_markdown_table(resultado_md)

        if not rows:
            st.warning("No se pudo extraer una tabla estructurada.")
        else:
            st.markdown("## Filtrar anuncios (selecciona / desmarca)")
            selected = []

            for r in rows:
                col1, col2 = st.columns([1, 12])

                with col1:
                    use = st.checkbox(
                        "",
                        value=True,
                        key=f"chk_{r.get('ID','')}"
                    )

                with col2:
                    url = extract_url(r.get("Enlace", ""))
                    st.markdown(
                        f"**{r.get('ID','')}** | {r.get('Portal','')} | "
                        f"Año: {r.get('Año','')} | Horas: {r.get('Horas','')} | "
                        f"Precio: {r.get('Precio','')} | País: {r.get('País','')}"
                        + (f" | [Ver anuncio]({url})" if url else "")
                    )

                if use:
                    selected.append(r)

            st.session_state.selected_ads = selected
            st.markdown(f"### Anuncios seleccionados: {len(selected)}")

# --------------------------------------------------
# PERSISTENTE
# --------------------------------------------------
st.markdown("---")
st.markdown("## Selección actual (persistente)")

if st.session_state.selected_ads:
    st.json(st.session_state.selected_ads)
else:
    st.info("Aún no hay anuncios seleccionados.")
