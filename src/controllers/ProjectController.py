"""
ProjectController.py

RÔLE :
- Gère la création et l'accès aux dossiers de projets individuels.
- Permet d'isoler les fichiers par projet (ex: assets/files/proj_abc123/)

RELATIONS :
- Hérite de BaseController → accès à self.files_dir
- Utilisé par : DataController (pour sauvegarder), ProcessController (pour charger)
"""

from .BaseController import BaseController
import os


class ProjectController(BaseController):
    
    def __init__(self):
        """
        Appelle le constructeur de BaseController pour initialiser app_settings, files_dir, etc.
        """
        super().__init__()

    def get_project_path(self, project_id: str):
        """
        Retourne le chemin absolu du dossier d'un projet.
        Crée le dossier s'il n'existe pas.
        
        Exemple :
          project_id = "my_rag_project"
          → retourne "/.../rag-project/assets/files/my_rag_project/"
        """
        # Construit le chemin complet du projet
        project_dir = os.path.join(
            self.files_dir,   # ← depuis BaseController (ex: assets/files)
            project_id        # identifiant fourni par l'utilisateur
        )

        # Crée le dossier si nécessaire (évite les erreurs de lecture/écriture)
        if not os.path.exists(project_dir):
            os.makedirs(project_dir)

        return project_dir