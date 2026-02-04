import streamlit as st
import re
from backend.market_scan import run_market_scan

st.set_page_config(page_title="Tasación 2.0", layout="wide")
st.title("Tasación 2.0 – Barrido de mercado")

# ---- Inputs ----
project_id = st.text_input("Project ID de Google Cloud")
marca = st.text_input("Marca", value="John Deere")
modelo = st.text_input("Modelo", value="6175R")

# ---- Helpers ----
def parse_markdown_table(md_text):
    """
    Parsea una tabla Markdown simple a una lista de dicts.
    Espera columnas:
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
        row = dict(zip(headers, cols))
        rows.append(row)
    return rows


def extract_url(cell):
    # Si viene como markdown [text](url) o url directa
    m = re.search(r"\((https?://[^)]+)\)", cell)
    if m:
        return m.group(1)
    m = re.search(r"(https?://\S+)", cell)
    return m.group(1) if m else ""


# ---- Action ----
if st.button("Buscar mercado"):
    if not project_id:
        st.error("Introduce el Project ID de Google Cloud")
    else:
        with st.spinner("Buscando anuncios reales..."):
            resultado_md = run_market_scan(
                project_id=project_id,
                marca=marca,
                modelo=modelo
            )

        st.markdown("## Resultado del barrido")
        st.markdown(resultado_md)

        # ---- Parse table ----
        rows = parse_markdown_table(resultado_md)

        if not rows:
            st.warning("No se pudo extraer una tabla estructurada.")
        else:
            st.markdown("## Filtrar anuncios (selecciona / desmarca)")
            selected = []

            for r in rows:
                col1, col2 = st.columns([1, 12])
                with col1:
                    use = st.checkbox("", value=True, key=r.get("ID", ""))
                with col2:
                    url = extract_url(r.get("Enlace", ""))
                    st.markdown(
                        f"**{r.get('ID','')}** | {r.get('Portal','')} | "
                        f"Año: {r.get('Año','')} | Horas: {r.get('Horas','')} | "
                        f"Precio: {r.get('Precio','')} | País: {r.get('País','')} "
                        + (f"| [Ver anuncio]({url})" if url else "")
                    )
                if use:
                    selected.append(r)

            st.markdown("---")
            st.markdown(f"### Anuncios seleccionados: {len(selected)}")
            st.json(selected)
