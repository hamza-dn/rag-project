# Importe les composants essentiels de FastAPI
from fastapi import FastAPI, APIRouter, Depends, UploadFile, status
from fastapi.responses import JSONResponse  # Pour retourner du JSON personnalisé

# Module standard pour manipuler les chemins de fichiers
import os

# Importe la configuration centralisée (APP_NAME, FILE_DEFAULT_CHUNK_SIZE, etc.)
from helpers.config import get_settings, Settings

# Importe les contrôleurs métier (logique applicative)
from controllers import DataController, ProjectController, ProcessController

# Permet d'écrire des fichiers de manière asynchrone (sans bloquer le serveur)
import aiofiles

# Importe les signaux de réponse prédéfinis (ex: "FILE_UPLOAD_SUCCESS")
from models import ResponseSignal

# Pour logger les erreurs (utile en production)
import logging
logger = logging.getLogger('uvicorn.error')  # Utilise le logger de Uvicorn

# Importe le schéma de validation de la requête POST /process
from .schemes.data import ProcessRequest


# Crée un routeur pour regrouper les endpoints liés aux données
# Tous les endpoints auront le préfixe "/api/v1/data"
# Et seront tagués dans la doc Swagger sous "api_v1" et "data"
data_router = APIRouter(
    prefix="/api/v1/data",
    tags=["api_v1", "data"],
)


# ───────────────────────────────────────────────────────
# Endpoint 1 : Téléverser un fichier
# ───────────────────────────────────────────────────────
@data_router.post("/upload/{project_id}")
async def upload_data(
    project_id: str,           # ID du projet fourni dans l'URL
    file: UploadFile,          # Fichier envoyé par le client
    app_settings: Settings = Depends(get_settings)  # Injecte la config via dépendance
):
    """
    Endpoint pour téléverser un fichier (PDF, TXT, etc.) dans un projet.
    
    Étapes :
    1. Valider le fichier (type, taille, etc.)
    2. Générer un chemin unique pour l'enregistrer
    3. Écrire le fichier sur disque
    4. Retourner un signal de succès ou d'erreur
    """

    # Instancie le contrôleur qui gère la logique de validation/upload
    data_controller = DataController()

    # Vérifie si le fichier est valide (ex: extension autorisée, taille OK)
    is_valid, result_signal = data_controller.validate_uploaded_file(file=file)

    # Si invalide → retourne une erreur 400 avec le signal correspondant
    if not is_valid:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "signal": result_signal  # Ex: "FILE_TYPE_NOT_SUPPORTED"
            }
        )

    # Récupère le chemin du dossier du projet (ex: ./data/projects/abc123)
    project_dir_path = ProjectController().get_project_path(project_id=project_id)

    # Génère un nom de fichier unique (évite les conflits)
    # Ex: "rapport.pdf" → "abc123_1712345678_rapport.pdf"
    file_path, file_id = data_controller.generate_unique_filepath(
        orig_file_name=file.filename,
        project_id=project_id
    )

    # Écrit le fichier sur disque de façon asynchrone (non bloquante)
    try:
        async with aiofiles.open(file_path, "wb") as f:
            # Lit le fichier par morceaux (chunk) pour éviter de saturer la mémoire
            while chunk := await file.read(app_settings.FILE_DEFAULT_CHUNK_SIZE):
                await f.write(chunk)
    except Exception as e:
        # En cas d'erreur, loggue et retourne une erreur
        logger.error(f"Error while uploading file: {e}")
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "signal": ResponseSignal.FILE_UPLOAD_FAILED.value
            }
        )

    # Succès : retourne le signal + l'ID unique du fichier (utile pour le traitement)
    return JSONResponse(
        content={
            "signal": ResponseSignal.FILE_UPLOAD_SUCCESS.value,
            "file_id": file_id  # Ce file_id sera utilisé dans /process
        }
    )


# ───────────────────────────────────────────────────────
# Endpoint 2 : Traiter un fichier déjà uploadé
# ───────────────────────────────────────────────────────
@data_router.post("/process/{project_id}")
async def process_endpoint(
    project_id: str,
    process_request: ProcessRequest  # Corps JSON validé automatiquement
):
    """
    Endpoint pour traiter un fichier (découpage en chunks, extraction de texte, etc.).
    
    Attend un JSON comme :
    {
      "file_id": "abc123_1712345678_rapport.pdf",
      "chunk_size": 500,
      "overlap_size": 50
    }
    
    Retourne la liste des chunks générés (liste de documents LangChain).
    """

    # Extrait les paramètres depuis le corps de la requête
    file_id = process_request.file_id
    chunk_size = process_request.chunk_size
    overlap_size = process_request.overlap_size

    # Instancie le contrôleur de traitement
    process_controller = ProcessController(project_id=project_id)

    # Charge le contenu du fichier (PDF → texte, TXT → texte)
    file_content = process_controller.get_file_content(file_id=file_id)

    # Découpe le contenu en chunks (morceaux exploitables pour le RAG)
    file_chunks = process_controller.process_file_content(
        file_content=file_content,
        file_id=file_id,
        chunk_size=chunk_size,
        overlap_size=overlap_size
    )

    # Vérifie que le traitement a produit des chunks
    if file_chunks is None or len(file_chunks) == 0:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "signal": ResponseSignal.PROCESSING_FAILED.value
            }
        )

    # Retourne directement la liste des chunks
    # FastAPI convertit automatiquement les objets Document en JSON
    return file_chunks