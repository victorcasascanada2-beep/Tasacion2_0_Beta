from google import genai
from google.genai.types import Tool, GoogleSearch


def get_gemini_client(project_id: str, location: str = "global"):
    """
    Devuelve un cliente Gemini configurado para Vertex AI.
    """
    return genai.Client(
        vertexai=True,
        project=project_id,
        location=location
    )


def get_google_search_tool():
    """
    Devuelve la tool de Google Search para grounding / browsing.
    """
    return [Tool(google_search=GoogleSearch())]
