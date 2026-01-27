"""
main.py

RÔLE :
- Point d'entrée principal de l'application FastAPI.
- Crée l'instance de l'application.
- Enregistre tous les routeurs (endpoints) définis dans `routes/`.

RELATIONS :
- Importe les routeurs depuis `src/routes/base.py` et `src/routes/data.py`
- Ces routeurs contiennent les endpoints :
    * base.base_router → /api/v1/ (health check)
    * data.data_router → /api/v1/data/upload, /api/v1/data/process
- L'application est lancée via : `uvicorn main:app --reload ...`
"""

# Importe la classe principale de FastAPI
from fastapi import FastAPI

# Importe les routeurs définis dans le dossier `routes/`
# Note : ces imports supposent que Python trouve le package `routes`
# → Cela fonctionne si tu lances uvicorn depuis la racine du projet (rag-project/)
from routes import base, data


# Crée l'instance principale de l'application FastAPI
# Tous les endpoints seront attachés à cette instance
app = FastAPI()


# Enregistre le routeur de base (endpoints généraux)
# → Ajoute tous les endpoints définis dans `base.base_router`
# → Préfixe automatique : "/api/v1" (défini dans base.py)
app.include_router(base.base_router)


# Enregistre le routeur de données (upload + traitement)
# → Ajoute les endpoints : POST /api/v1/data/upload, POST /api/v1/data/process
app.include_router(data.data_router)