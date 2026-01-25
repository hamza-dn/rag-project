"""
ProcessController.py

RÔLE :
- Cœur du pipeline RAG :
  1. Charger un fichier (PDF ou TXT) → extraire le texte
  2. Découper le texte en "chunks" exploitables
  3. Conserver les métadonnées (source, page, etc.)

RELATIONS :
- Hérite de BaseController → accès à app_settings (non utilisé ici, mais cohérent)
- Utilise ProjectController → pour accéder au fichier dans le bon dossier
- Utilise ProcessingEnum → pour comparer les extensions de façon sécurisée
- Appelé par : routes/data.py (endpoint /process)
- Dépend de : langchain_community (chargement), langchain_text_splitters (découpage)
"""

from .BaseController import BaseController
from .ProjectController import ProjectController
import os
from langchain_community.document_loaders import TextLoader
from langchain_community.document_loaders import PyMuPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from models import ProcessingEnum


class ProcessController(BaseController):

    def __init__(self, project_id: str):
        """
        Initialise le contrôleur avec un ID de projet.
        Récupère le chemin du dossier du projet.
        """
        super().__init__()
        self.project_id = project_id
        # Chemin absolu vers le dossier du projet (ex: assets/files/abc123/)
        self.project_path = ProjectController().get_project_path(project_id=project_id)

    def get_file_extension(self, file_id: str):
        """
        Extrait l'extension d'un fichier.
        Ex: "abc123_rapport.pdf" → ".pdf"
        """
        return os.path.splitext(file_id)[-1]

    def get_file_loader(self, file_id: str):
        """
        Retourne le chargeur LangChain adapté selon l'extension.
        Utilise les valeurs définies dans ProcessingEnum (ex: ".txt", ".pdf").

        Retourne :
          TextLoader ou PyMuPDFLoader si supporté
          None si non supporté
        """
        file_ext = self.get_file_extension(file_id=file_id)
        file_path = os.path.join(self.project_path, file_id)

        # Compare avec les énumérations sécurisées (pas de chaînes en dur)
        if file_ext == ProcessingEnum.TXT.value:
            return TextLoader(file_path, encoding="utf-8")

        if file_ext == ProcessingEnum.PDF.value:
            return PyMuPDFLoader(file_path)
        
        # Extension non supportée
        return None

    def get_file_content(self, file_id: str):
        """
        Charge le contenu réel du fichier.
        Retourne une liste d'objets Document LangChain.
        Chaque Document contient :
          - .page_content : le texte extrait
          - .metadata : infos comme le nom du fichier, numéro de page (PDF), etc.
        """
        loader = self.get_file_loader(file_id=file_id)
        if loader is None:
            raise ValueError(f"Format de fichier non supporté : {file_id}")
        return loader.load()

    def process_file_content(self, file_content: list, file_id: str,
                            chunk_size: int = 100, overlap_size: int = 20):
        """
        Découpe le contenu en morceaux ("chunks") pour le RAG.

        Pourquoi ?
        - Les LLM ont une limite de tokens → on ne peut pas envoyer un livre entier.
        - On découpe → on indexe → on cherche les meilleurs chunks → on les envoie au LLM.

        Paramètres :
          chunk_size : nombre de caractères par chunk (100 = court, bon pour tests)
          overlap_size : chevauchement entre chunks (évite de couper au milieu d'une phrase)

        Retourne :
          Une liste de nouveaux Documents LangChain (plus petits, avec métadonnées conservées).
        """
        # Configure le découpeur de texte
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=overlap_size,
            length_function=len,  # Mesure la taille en caractères
        )

        # Extrait le texte brut de chaque Document
        file_content_texts = [
            rec.page_content
            for rec in file_content
        ]

        # Extrait aussi les métadonnées (source, page, etc.)
        file_content_metadata = [
            rec.metadata
            for rec in file_content
        ]

        # Découpe ET attache les métadonnées à chaque chunk
        chunks = text_splitter.create_documents(
            file_content_texts,
            metadatas=file_content_metadata
        )

        return chunks