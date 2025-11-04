# Este es un marcador de PyPI: NO incluye el codec PRO.
__all__ = ["MARKER_ONLY", "__version__"]
__version__ = "0.16.0"
MARKER_ONLY = True

msg = (
    "surframe-ucodec-pro (PyPI marker): este paquete no incluye el plugin PRO.\n"
    "Para instalar el plugin real, configura:\n"
    "  set SURFRAME_PRIVATE_INDEX=https://{TOKEN}@repo.tu-dominio/simple\n"
    "  set SURFRAME_ACCESS_TOKEN=<token>\n"
    "y deja que SURFRAME lo resuelva automáticamente.\n"
)
raise ImportError(msg)
