"""
Modèles Pydantic pour l'application chatbot
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Literal
from openai.types.chat import ChatCompletionMessageParam


class Evaluation(BaseModel):
    """Modèle pour l'évaluation d'une réponse par l'IA"""

    is_acceptable: bool = Field(description="Si la réponse est acceptable")
    feedback: str = Field(description="Commentaires pour l'amélioration")


class UserProfile(BaseModel):
    """Modèle pour les données du profil utilisateur"""

    name: str = Field(description="Nom complet de l'utilisateur")
    summary: str = Field(description="Résumé professionnel")
    linkedin_content: str = Field(description="Contenu du profil LinkedIn")

    @property
    def profile_info(self) -> tuple[str, str, str]:
        """Retourne les informations du profil dans l'ordre attendu"""
        return self.name, self.summary, self.linkedin_content


class ChatMessage(BaseModel):
    """Modèle pour un message de chat"""

    role: Literal["system", "user", "assistant"] = Field(description="Rôle du message")
    content: str = Field(description="Contenu du message")

    def to_openai_format(self) -> ChatCompletionMessageParam:
        """Convertit en format OpenAI"""
        return {"role": self.role, "content": self.content}  # type: ignore


class ChatHistory(BaseModel):
    """Modèle pour l'historique de conversation"""

    messages: List[ChatMessage] = Field(default_factory=list)

    def add_message(self, role: Literal["system", "user", "assistant"], content: str):
        """Ajoute un message à l'historique"""
        self.messages.append(ChatMessage(role=role, content=content))

    def to_openai_format(self) -> List[ChatCompletionMessageParam]:
        """Convertit en format OpenAI"""
        return [msg.to_openai_format() for msg in self.messages]

    def from_gradio_history(
        self, gradio_history: List[tuple[str, str]]
    ) -> "ChatHistory":
        """Crée un ChatHistory depuis l'historique Gradio"""
        for user_msg, assistant_msg in gradio_history:
            self.add_message("user", user_msg)
            self.add_message("assistant", assistant_msg)
        return self


class ChatRequest(BaseModel):
    """Modèle pour une requête de chat"""

    message: str = Field(description="Message de l'utilisateur")
    history: List[tuple[str, str]] = Field(
        default_factory=list, description="Historique Gradio"
    )

    def get_chat_history(self) -> ChatHistory:
        """Convertit l'historique Gradio en ChatHistory"""
        chat_history = ChatHistory()
        return chat_history.from_gradio_history(self.history)


class ChatResponse(BaseModel):
    """Modèle pour une réponse de chat"""

    content: str = Field(description="Contenu de la réponse")
    evaluation: Optional[Evaluation] = Field(
        default=None, description="Résultat de l'évaluation"
    )
    was_retried: bool = Field(default=False, description="Si la réponse a été retentée")

    @property
    def is_successful(self) -> bool:
        """Vérifie si la réponse est considérée comme réussie"""
        return self.evaluation is None or self.evaluation.is_acceptable


class RetryRequest(BaseModel):
    """Modèle pour une demande de retry"""

    original_reply: str = Field(description="Réponse originale rejetée")
    user_message: str = Field(description="Message utilisateur original")
    history: List[ChatCompletionMessageParam] = Field(
        description="Historique de conversation"
    )
    feedback: str = Field(description="Feedback de l'évaluateur")


class APIClientConfig(BaseModel):
    """Configuration pour les clients API"""

    api_key: str = Field(description="Clé API")
    base_url: Optional[str] = Field(default=None, description="URL de base (optionnel)")
    model: str = Field(description="Nom du modèle à utiliser")

    class Config:
        # Protéger les clés API lors de la sérialisation
        json_encoders = {str: lambda v: "***" if "api_key" in str(v).lower() else v}
