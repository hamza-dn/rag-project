# ───────────────────────────────────────────────────────
# IMPORTS : d'où viennent ces modules ?
# ───────────────────────────────────────────────────────

from fastapi import FastAPI, APIRouter, Depends
import os
# get_settings & Settings : définis dans `src/helpers/config.py`
# → C'est ici que tu centralises la configuration (APP_NAME, API keys, etc.)
from helpers.config import get_settings, Settings


# ───────────────────────────────────────────────────────
# ROUTEUR DE BASE : point d'entrée de l'API
# ───────────────────────────────────────────────────────

# Crée un routeur pour regrouper les endpoints principaux
# Tous les endpoints ajoutés à ce routeur auront :
#   - le préfixe "/api/v1"
#   - le tag "api_v1" dans la documentation Swagger (/docs)
base_router = APIRouter(
    prefix="/api/v1",
    tags=["api_v1"],
)


# ───────────────────────────────────────────────────────
# ENDPOINT : page d'accueil de l'API
# ───────────────────────────────────────────────────────

@base_router.get("/")
async def welcome(app_settings: Settings = Depends(get_settings)):
    """
    Endpoint racine de l'API.
    
    Relation avec d'autres fichiers :
    ─────────────────────────────────
    1. `Depends(get_settings)` → 
       - Appelle la fonction `get_settings()` définie dans `src/helpers/config.py`
       - Cette fonction retourne une instance de `Settings`
       - `Settings` lit automatiquement les variables depuis `.env` (grâce à Pydantic)

    2. `app_settings.APP_NAME` et `app_settings.APP_VERSION` →
       - Ces valeurs sont définies dans ton fichier `.env` à la racine du projet
         Exemple de `.env` :
           APP_NAME="Mini RAG App"
           APP_VERSION="v1.0"

    3. Ce routeur (`base_router`) est inclus dans `main.py` :
       ```python
       # main.py
       from src.routes import base
       app.include_router(base.base_router)
       ```
       → Donc cet endpoint sera accessible via : GET /api/v1/

    Objectif métier :
    ───────────────
    - Permet de vérifier que l'API est bien lancée
    - Donne des infos de version utiles pour le monitoring ou le frontend
    """

    # Récupère les valeurs depuis la configuration centralisée
    app_name = app_settings.APP_NAME
    app_version = app_settings.APP_VERSION

    # Retourne un JSON simple (FastAPI le convertit automatiquement)
    return {
        "app_name": app_name,
        "app_version": app_version,
    }