"""
BaseController.py

RÔLE :
- Classe de base héritée par tous les contrôleurs.
- Fournit un accès centralisé à :
  * la configuration (.env via config.py)
  * le chemin racine du projet
  * le dossier de stockage des fichiers ("assets/files")
  * des utilitaires (ex: génération de chaînes aléatoires)

RELATIONS :
- Utilise : helpers/config.py → pour charger les paramètres depuis .env
- Hérité par : DataController, ProjectController, ProcessController
"""

from helpers.config import get_settings, Settings
import os
import random
import string


class BaseController:
    
    def __init__(self):
        """
        Initialise les attributs communs à tous les contrôleurs.
        """
        # Charge la configuration centralisée (APP_NAME, FILE_MAX_SIZE, etc.)
        self.app_settings = get_settings()
        
        # Chemin absolu vers la racine du projet (ex: /.../rag-project)
        # __file__ = chemin de ce fichier → on remonte de 2 niveaux
        self.base_dir = os.path.dirname(os.path.dirname(__file__))
        
        # Dossier racine pour stocker TOUS les fichiers uploadés
        # Ex: rag-project/assets/files
        self.files_dir = os.path.join(
            self.base_dir,
            "assets/files"
        )
        
    def generate_random_string(self, length: int = 12):
        """
        Génère une chaîne aléatoire (lettres minuscules + chiffres).
        Utilisé pour créer des noms de fichiers uniques.
        Ex: "a3k9m2n8p1q4"
        """
        return ''.join(random.choices(string.ascii_lowercase + string.digits, k=length))