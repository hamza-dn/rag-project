"""
DataController.py

RÔLE :
- Valide les fichiers uploadés (type, taille)
- Génère des chemins de fichiers uniques et sécurisés
- Nettoie les noms de fichiers pour éviter les problèmes de sécurité

RELATIONS :
- Hérite de BaseController → accès à app_settings, generate_random_string
- Utilise ProjectController → pour obtenir le dossier du projet
- Retourne des signaux définis dans models/ResponseSignal.py
- Appelé par : routes/data.py (endpoint /upload)
"""

from .BaseController import BaseController
from .ProjectController import ProjectController
from fastapi import UploadFile
from models import ResponseSignal
import re
import os


class DataController(BaseController):
    
    def __init__(self):
        """
        Initialise le contrôleur et définit l'échelle de conversion Mo → octets.
        """
        super().__init__()
        # 1 Mo = 1048576 octets (2^20)
        self.size_scale = 1048576

    def validate_uploaded_file(self, file: UploadFile):
        """
        Valide un fichier uploadé selon deux règles :
        1. Type MIME autorisé (défini dans .env : FILE_ALLOWED_TYPES)
        2. Taille maximale (définie dans .env : FILE_MAX_SIZE en Mo)

        Retourne :
          (True, "FILE_VALIDATED_SUCCESS") si OK
          (False, "SIGNAL_D_ERREUR") sinon
        """
        # Vérifie le type de fichier (ex: "application/pdf", "text/plain")
        if file.content_type not in self.app_settings.FILE_ALLOWED_TYPES:
            return False, ResponseSignal.FILE_TYPE_NOT_SUPPORTED.value

        # Vérifie la taille (file.size est en octets)
        if file.size > self.app_settings.FILE_MAX_SIZE * self.size_scale:
            return False, ResponseSignal.FILE_SIZE_EXCEEDED.value

        return True, ResponseSignal.FILE_VALIDATED_SUCCESS.value

    def generate_unique_filepath(self, orig_file_name: str, project_id: str):
        """
        Génère un chemin de fichier unique pour éviter les conflits.
        Format : <random_key>_<nom_nettoyé>
        Ex: "x7k2m9_rapport_final.pdf"

        Retourne :
          (chemin_absolu, file_id)
        """
        # Génère une clé aléatoire (12 caractères)
        random_key = self.generate_random_string()
        
        # Récupère le dossier du projet (crée si nécessaire)
        project_path = ProjectController().get_project_path(project_id=project_id)

        # Nettoie le nom original du fichier
        cleaned_file_name = self.get_clean_file_name(orig_file_name=orig_file_name)

        # Construit le nouveau chemin
        new_file_path = os.path.join(
            project_path,
            random_key + "_" + cleaned_file_name
        )

        # En cas de collision (très rare), génère une nouvelle clé
        while os.path.exists(new_file_path):
            random_key = self.generate_random_string()
            new_file_path = os.path.join(
                project_path,
                random_key + "_" + cleaned_file_name
            )

        # Le "file_id" est juste le nom du fichier (pas le chemin complet)
        file_id = random_key + "_" + cleaned_file_name
        return new_file_path, file_id

    def get_clean_file_name(self, orig_file_name: str):
        """
        Nettoie le nom de fichier pour plus de sécurité :
        - Supprime tous les caractères non alphanumériques (sauf underscore et point)
        - Remplace les espaces par des underscores

        Exemple :
          "Mon Rapport (Final!).pdf" → "Mon_Rapport_Final.pdf"
        """
        # Garde seulement lettres, chiffres, underscore, point
        cleaned = re.sub(r'[^\w.]', '', orig_file_name.strip())
        # Remplace les espaces restants par underscores
        return cleaned.replace(" ", "_")