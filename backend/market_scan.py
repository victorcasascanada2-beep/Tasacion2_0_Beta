from backend.gemini_client import get_gemini_client, get_google_search_tool
from backend.prompts.prompt_market_scan import build_market_scan_prompt


def run_market_scan(
    project_id: str,
    marca: str,
    modelo: str,
    location: str = "global"
) -> str:
    """
    Ejecuta un barrido de mercado usando Gemini 2.5 Pro en Vertex AI
    con Google Search como herramienta.
    Devuelve el resultado en texto Markdown.
    """

    # Crear cliente Gemini (VERTEX AI)
    client = get_gemini_client(
        project_id=project_id,
        location=location
    )

    # Herramienta de búsqueda (Google Search)
    tools = get_google_search_tool()

    # Construir prompt
    prompt = build_market_scan_prompt(
        marca=marca,
        modelo=modelo
    )

    # Llamada al modelo (IMPORTANTE: tools dentro de config)
    response = client.models.generate_content(
        model="gemini-2.5-pro",
        contents=prompt,
        config={
            "tools": tools,
            "temperature": 0.2,
            "max_output_tokens": 2048
        }
    )

    # Devolver texto generado
    return response.text
