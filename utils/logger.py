"""
Configuration centralisée du système de logging
"""

import logging
import sys
from pathlib import Path
from typing import Optional


class ChatbotLogger:
    """Gestionnaire de logs centralisé pour le chatbot"""

    def __init__(self, name: str = "raph_chatbot", level: str = "INFO"):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(getattr(logging, level.upper()))

        # Éviter les doublons si le logger existe déjà
        if not self.logger.handlers:
            self._setup_handlers()

    def _setup_handlers(self):
        """Configure les handlers pour console et fichier"""

        # Format des logs
        formatter = logging.Formatter(
            fmt="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )

        # Handler console (stdout)
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        console_handler.setLevel(logging.INFO)
        self.logger.addHandler(console_handler)

        # Handler fichier (optionnel)
        try:
            log_dir = Path("raph/logs")
            log_dir.mkdir(exist_ok=True)

            file_handler = logging.FileHandler(
                log_dir / "chatbot.log", encoding="utf-8"
            )
            file_handler.setFormatter(formatter)
            file_handler.setLevel(logging.DEBUG)
            self.logger.addHandler(file_handler)
        except Exception:
            # Si impossible de créer le fichier, on continue sans
            pass

    def debug(self, message: str, **kwargs):
        """Log de niveau DEBUG"""
        self.logger.debug(message, **kwargs)

    def info(self, message: str, **kwargs):
        """Log de niveau INFO"""
        self.logger.info(message, **kwargs)

    def warning(self, message: str, **kwargs):
        """Log de niveau WARNING"""
        self.logger.warning(message, **kwargs)

    def error(self, message: str, **kwargs):
        """Log de niveau ERROR"""
        self.logger.error(message, **kwargs)

    def critical(self, message: str, **kwargs):
        """Log de niveau CRITICAL"""
        self.logger.critical(message, **kwargs)

    def exception(self, message: str, **kwargs):
        """Log d'exception avec traceback"""
        self.logger.exception(message, **kwargs)


# Instance globale du logger
_logger_instance: Optional[ChatbotLogger] = None


def get_logger(name: str = "raph_chatbot", level: str = "INFO") -> ChatbotLogger:
    """
    Récupère l'instance singleton du logger

    Args:
        name: Nom du logger
        level: Niveau de log (DEBUG, INFO, WARNING, ERROR, CRITICAL)

    Returns:
        ChatbotLogger: Instance du logger configuré
    """
    global _logger_instance

    if _logger_instance is None:
        _logger_instance = ChatbotLogger(name, level)

    return _logger_instance


# Logger par défaut pour utilisation directe
logger = get_logger()


# Context managers pour des logs de session/opération
class LogContext:
    """Context manager pour logger le début/fin d'opération"""

    def __init__(
        self, operation_name: str, logger_instance: Optional[ChatbotLogger] = None
    ):
        self.operation_name = operation_name
        self.logger = logger_instance or logger

    def __enter__(self):
        self.logger.info(f"🚀 Starting: {self.operation_name}")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is None:
            self.logger.info(f"✅ Completed: {self.operation_name}")
        else:
            self.logger.error(f"❌ Failed: {self.operation_name} - {exc_val}")
        return False  # Ne pas supprimer l'exception


class EvaluationLogContext:
    """Context manager spécialisé pour les logs d'évaluation"""

    def __init__(self, message: str, logger_instance: Optional[ChatbotLogger] = None):
        self.message = message[:50] + "..." if len(message) > 50 else message
        self.logger = logger_instance or logger

    def log_evaluation_start(self):
        """Log le début d'évaluation"""
        self.logger.info(f"🔍 Evaluating response for: '{self.message}'")

    def log_evaluation_passed(self):
        """Log évaluation réussie"""
        self.logger.info(f"✅ Evaluation PASSED - response accepted")

    def log_evaluation_failed(self, feedback: str):
        """Log évaluation échouée"""
        self.logger.warning(f"⚠️  Evaluation FAILED - retrying")
        self.logger.debug(f"Feedback: {feedback}")

    def log_evaluation_error(self, error: str):
        """Log erreur d'évaluation"""
        self.logger.error(f"💥 Evaluation ERROR: {error}")
