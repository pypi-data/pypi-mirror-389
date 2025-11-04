# surframe-ucodec-pro (PyPI marker)

Este paquete **no** incluye el plugin PRO. Es sólo un marcador para PyPI.

Para usar el plugin real, configurá un índice privado y un token:

set SURFRAME_PRIVATE_INDEX=https://{TOKEN}@repo.tu-dominio/simple
set SURFRAME_ACCESS_TOKEN=<token>


Luego, desde `surframe`, el loader intentará instalar el plugin real automáticamente.
