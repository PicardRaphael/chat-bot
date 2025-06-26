"""
Utilitaires pour la lecture de fichiers du profil
"""

import os
from pypdf import PdfReader


class FileReadError(Exception):
    """Exception levée lors d'erreurs de lecture de fichiers"""

    pass


def read_pdf_file(file_path: str) -> str:
    """
    Lit un fichier PDF et retourne son contenu textuel

    Args:
        file_path: Chemin vers le fichier PDF

    Returns:
        str: Contenu textuel du PDF

    Raises:
        FileReadError: Si le fichier n'existe pas ou ne peut pas être lu
    """
    if not os.path.exists(file_path):
        raise FileReadError(f"Le fichier PDF {file_path} n'existe pas")

    try:
        reader = PdfReader(file_path)
        content = ""
        for page in reader.pages:
            text = page.extract_text()
            if text:
                content += text
        return content.strip()
    except Exception as e:
        raise FileReadError(f"Erreur lors de la lecture du PDF {file_path}: {str(e)}")


def read_text_file(file_path: str, encoding: str = "utf-8") -> str:
    """
    Lit un fichier texte et retourne son contenu

    Args:
        file_path: Chemin vers le fichier texte
        encoding: Encodage du fichier (défaut: utf-8)

    Returns:
        str: Contenu du fichier texte

    Raises:
        FileReadError: Si le fichier n'existe pas ou ne peut pas être lu
    """
    if not os.path.exists(file_path):
        raise FileReadError(f"Le fichier texte {file_path} n'existe pas")

    try:
        with open(file_path, "r", encoding=encoding) as f:
            content = f.read()
        return content.strip()
    except Exception as e:
        raise FileReadError(
            f"Erreur lors de la lecture du fichier {file_path}: {str(e)}"
        )


def read_linkedin_profile(profile_dir: str, linkedin_filename: str) -> str:
    """
    Lit le profil LinkedIn depuis un PDF

    Args:
        profile_dir: Répertoire contenant les fichiers de profil
        linkedin_filename: Nom du fichier PDF LinkedIn

    Returns:
        str: Contenu du profil LinkedIn

    Raises:
        FileReadError: Si le fichier ne peut pas être lu
    """
    linkedin_path = os.path.join(profile_dir, linkedin_filename)
    return read_pdf_file(linkedin_path)


def read_summary_file(profile_dir: str, summary_filename: str) -> str:
    """
    Lit le fichier de résumé textuel

    Args:
        profile_dir: Répertoire contenant les fichiers de profil
        summary_filename: Nom du fichier de résumé

    Returns:
        str: Contenu du résumé

    Raises:
        FileReadError: Si le fichier ne peut pas être lu
    """
    summary_path = os.path.join(profile_dir, summary_filename)
    return read_text_file(summary_path)


def validate_profile_files(
    profile_dir: str, linkedin_filename: str, summary_filename: str
) -> dict[str, bool | str]:
    """
    Valide l'existence des fichiers de profil requis

    Args:
        profile_dir: Répertoire contenant les fichiers de profil
        linkedin_filename: Nom du fichier PDF LinkedIn
        summary_filename: Nom du fichier de résumé

    Returns:
        dict: État de validation de chaque fichier
    """
    linkedin_path = os.path.join(profile_dir, linkedin_filename)
    summary_path = os.path.join(profile_dir, summary_filename)

    return {
        "profile_dir_exists": os.path.exists(profile_dir),
        "linkedin_exists": os.path.exists(linkedin_path),
        "summary_exists": os.path.exists(summary_path),
        "linkedin_path": linkedin_path,
        "summary_path": summary_path,
    }
