Backend del parcial 2 de Programacion 4
---------------------------------------
Integrantes:
- Gomez Cristian
- Guerra Martin
---------------------------------------
Comandos para ejecucion (puede variar segun version de python instalada):
- python -m venv .venv
- .venv\Scripts\activate
- pip install -r requirements.txt
- python -m fastapi dev main.py
---------------------------------------
Ejecutar seed
- python -m app.db.seed

video: https://www.youtube.com/watch?v=2V3IXbaUrUI

----------
- Descargarse ngrok https://ngrok.com/download/windows
- Logearse y copiar Access token y ejecutar en consola: 
    ngrok config add-authtoken {token}
- ejecutar y dejar corriendo: ngrok http 8000 
-copiar url y añadir al env(MP_NGROK_URL)
