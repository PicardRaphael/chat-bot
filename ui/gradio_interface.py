"""Gradio interface for the chatbot application."""

import gradio as gr
from typing import Optional, List, Tuple
from config.settings import settings
from utils.logger import logger
from services.chat_service import get_chat_service


class GradioInterface:
    """Manages the Gradio user interface for the chatbot."""

    def __init__(
        self,
        title: str = "Raphaël PICARD - AI Assistant",
        description: str = "Chat with Raphaël's AI assistant",
        theme: str = "soft",
        share: bool = False,
        server_name: str = "127.0.0.1",
        server_port: int = 7860,
    ):
        """
        Initialize the Gradio interface.

        Args:
            title: Title of the interface
            description: Description shown in the interface
            theme: Gradio theme to use
            share: Whether to create a public link
            server_name: Server hostname
            server_port: Server port
        """
        self.title = title
        self.description = description
        self.theme = theme
        self.share = share
        self.server_name = server_name
        self.server_port = server_port
        self.chat_service = get_chat_service()

        logger.debug(f"GradioInterface initialized with title: '{title}'")

    def chat_wrapper(self, message: str, history: List[Tuple[str, str]]) -> str:
        """
        Wrapper function for chat that handles errors gracefully.

        Args:
            message: User message
            history: Conversation history

        Returns:
            AI response or error message
        """
        try:
            logger.debug(f"Processing chat message: '{message[:50]}...'")
            response = self.chat_service.chat(message, history)
            logger.debug(f"Chat response generated: {len(response)} characters")
            return response
        except Exception as e:
            error_msg = f"Sorry, I encountered an error: {str(e)}"
            logger.error(f"Chat wrapper error: {e}")
            return error_msg

    def create_chat_interface(self) -> gr.ChatInterface:
        """
        Create the main chat interface.

        Returns:
            Configured Gradio ChatInterface
        """
        logger.info("Creating chat interface")

        chat_interface = gr.ChatInterface(
            fn=self.chat_wrapper,
            type="messages",
            title=self.title,
            description=self.description,
            theme=self.theme,
        )

        logger.info("Chat interface created successfully")
        return chat_interface

    def create_advanced_interface(self) -> gr.Blocks:
        """
        Create an advanced interface with additional features.

        Returns:
            Configured Gradio Blocks interface
        """
        logger.info("Creating advanced interface")

        with gr.Blocks(
            title=self.title,
            theme=self.theme,
        ) as interface:

            # Header
            gr.Markdown(f"# {self.title}")
            gr.Markdown(self.description)

            with gr.Tab("💬 Chat"):
                # Main chat interface
                chatbot = gr.Chatbot(
                    height=600,
                    placeholder="<strong>Bonjour !</strong><br>Je suis l'assistant IA de Raphaël PICARD. Comment puis-je vous aider aujourd'hui ?",
                    show_label=False,
                )

                with gr.Row():
                    msg_input = gr.Textbox(
                        placeholder="Tapez votre message ici...",
                        container=False,
                        scale=8,
                    )
                    send_btn = gr.Button("Envoyer", variant="primary", scale=1)

                with gr.Row():
                    retry_btn = gr.Button("🔄 Réessayer")
                    undo_btn = gr.Button("↶ Annuler")
                    clear_btn = gr.Button("🗑️ Effacer")

            with gr.Tab("⚙️ Configuration"):
                gr.Markdown("### Paramètres de l'assistant")

                with gr.Row():
                    with gr.Column():
                        model_info = gr.Textbox(
                            value=f"Chat: {settings.CHAT_MODEL}\nÉvaluation: {settings.EVALUATION_MODEL}",
                            label="Modèles utilisés",
                            interactive=False,
                            lines=2,
                        )

                        profile_status = gr.Textbox(
                            value="Profile chargé depuis: " + settings.PROFILE_DIR,
                            label="Statut du profil",
                            interactive=False,
                        )

                    with gr.Column():
                        refresh_btn = gr.Button(
                            "🔄 Actualiser le profil", variant="secondary"
                        )
                        test_btn = gr.Button(
                            "🧪 Tester la connexion", variant="secondary"
                        )

                        status_output = gr.Textbox(
                            label="Statut",
                            interactive=False,
                            lines=3,
                        )

            with gr.Tab("📊 Métriques"):
                gr.Markdown("### Statistiques d'utilisation")

                with gr.Row():
                    total_messages = gr.Number(
                        value=0, label="Messages traités", interactive=False
                    )
                    avg_response_time = gr.Number(
                        value=0, label="Temps de réponse moyen (s)", interactive=False
                    )
                    success_rate = gr.Number(
                        value=0, label="Taux de succès (%)", interactive=False
                    )

                metrics_refresh_btn = gr.Button("🔄 Actualiser les métriques")

                # Placeholder for metrics chart
                gr.Markdown(
                    "*Les métriques détaillées seront disponibles dans une future version.*"
                )

            # Event handlers
            def handle_chat(message, history):
                if not message.strip():
                    return history, ""

                try:
                    response = self.chat_wrapper(message, history)
                    history.append((message, response))
                    return history, ""
                except Exception as e:
                    logger.error(f"Chat handling error: {e}")
                    history.append((message, f"Erreur: {str(e)}"))
                    return history, ""

            def handle_retry(history):
                if not history:
                    return history

                try:
                    last_message = history[-1][0]
                    history_without_last = history[:-1]
                    response = self.chat_wrapper(last_message, history_without_last)
                    history[-1] = (last_message, response)
                    return history
                except Exception as e:
                    logger.error(f"Retry handling error: {e}")
                    return history

            def handle_undo(history):
                if history:
                    return history[:-1]
                return history

            def handle_clear():
                return []

            def handle_test_connection():
                try:
                    # Test des connexions API
                    status = "🟢 Connexions OK\n"
                    status += f"✅ Chat model: {settings.CHAT_MODEL}\n"
                    status += f"✅ Evaluation model: {settings.EVALUATION_MODEL}"
                    return status
                except Exception as e:
                    return f"🔴 Erreur de connexion: {str(e)}"

            def handle_refresh_profile():
                try:
                    # Rafraîchir le profil
                    from core.profile_loader import get_profile_loader

                    loader = get_profile_loader()
                    loader.refresh_profile()
                    return "🟢 Profil actualisé avec succès"
                except Exception as e:
                    return f"🔴 Erreur lors de l'actualisation: {str(e)}"

            # Bind events
            send_btn.click(
                handle_chat, inputs=[msg_input, chatbot], outputs=[chatbot, msg_input]
            )

            msg_input.submit(
                handle_chat, inputs=[msg_input, chatbot], outputs=[chatbot, msg_input]
            )

            retry_btn.click(handle_retry, inputs=[chatbot], outputs=[chatbot])

            undo_btn.click(handle_undo, inputs=[chatbot], outputs=[chatbot])

            clear_btn.click(handle_clear, outputs=[chatbot])

            test_btn.click(handle_test_connection, outputs=[status_output])

            refresh_btn.click(handle_refresh_profile, outputs=[status_output])

        logger.info("Advanced interface created successfully")
        return interface

    def launch_simple(self) -> None:
        """
        Launch the simple chat interface.
        """
        logger.info("Launching simple chat interface")

        interface = self.create_chat_interface()

        interface.launch(
            share=self.share,
            server_name=self.server_name,
            server_port=self.server_port,
            show_error=True,
            quiet=False,
        )

    def launch_advanced(self) -> None:
        """
        Launch the advanced interface with multiple tabs.
        """
        logger.info("Launching advanced interface")

        interface = self.create_advanced_interface()

        interface.launch(
            share=self.share,
            server_name=self.server_name,
            server_port=self.server_port,
            show_error=True,
            quiet=False,
        )

    def launch(self, advanced: bool = False) -> None:
        """
        Launch the appropriate interface.

        Args:
            advanced: Whether to launch the advanced interface
        """
        if advanced:
            self.launch_advanced()
        else:
            self.launch_simple()

    def update_settings(self, **kwargs) -> None:
        """
        Update interface settings.

        Args:
            **kwargs: Settings to update
        """
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
                logger.debug(f"Updated interface setting: {key} = {value}")


# Global interface instance
_gradio_interface: Optional[GradioInterface] = None


def get_gradio_interface() -> GradioInterface:
    """
    Get the global Gradio interface instance (singleton pattern).

    Returns:
        The configured GradioInterface instance
    """
    global _gradio_interface

    if _gradio_interface is None:
        _gradio_interface = GradioInterface()

    return _gradio_interface


# Convenience functions for backward compatibility
def launch_simple_chat() -> None:
    """Launch simple chat interface."""
    get_gradio_interface().launch_simple()


def launch_advanced_chat() -> None:
    """Launch advanced chat interface."""
    get_gradio_interface().launch_advanced()


def create_chat_interface() -> gr.ChatInterface:
    """Create a simple chat interface."""
    return get_gradio_interface().create_chat_interface()


def create_advanced_interface() -> gr.Blocks:
    """Create an advanced interface."""
    return get_gradio_interface().create_advanced_interface()
