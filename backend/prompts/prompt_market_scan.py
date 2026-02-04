
def build_market_scan_prompt(marca: str, modelo: str) -> str:
    """
    Prompt para barrido de mercado usando Google Search.
    SOLO búsqueda y listado de resultados.
    """

    return f"""
Eres un asistente especializado en investigación de mercado
de maquinaria agrícola usada.

REGLAS ABSOLUTAS:
- Usa Google Search como herramienta.
- SOLO busca y lista resultados.
- NO analices precios.
- NO hagas medias.
- NO estimes valores.
- NO inventes anuncios ni enlaces.
- Si un dato no aparece, déjalo vacío.

OBJETIVO:
Realizar un barrido de mercado del siguiente tractor:

Marca: {marca}
Modelo: {modelo}

INSTRUCCIONES DE BÚSQUEDA:
1. Busca anuncios ACTIVOS del modelo exacto.
2. Prioriza estas plataformas:
   - Agriaffaires
   - Mascus
   - Tractorpool
   - Milanuncios
   - e-farm
3. Prioriza resultados europeos.
4. Descarta variantes distintas.

DATOS A EXTRAER POR RESULTADO:
- ID (R1, R2, R3…)
- Portal
- Enlace real
- Año
- Horas
- Precio anunciado
- País

CRITERIO DE PARADA:
- Si hay menos de 5 resultados útiles, indícalo claramente.
- NO continúes con análisis ni estimaciones.

FORMATO DE SALIDA OBLIGATORIO:
I. Resumen breve del barrido
II. Tabla Markdown con columnas:
ID | Portal | Año | Horas | Precio | País | Enlace
"""
