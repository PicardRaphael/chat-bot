"""Entry point for the chatbot application."""

import argparse
from utils.logger import logger
from ui.gradio_interface import get_gradio_interface


def main():
    """Main entry point for the chatbot application."""
    parser = argparse.ArgumentParser(description="Raphaël PICARD AI Assistant")
    parser.add_argument(
        "--advanced",
        action="store_true",
        help="Launch advanced interface with configuration and metrics",
    )
    parser.add_argument(
        "--share", action="store_true", help="Create a public link for the interface"
    )
    parser.add_argument(
        "--port",
        type=int,
        default=7860,
        help="Port for the web interface (default: 7860)",
    )
    parser.add_argument(
        "--host",
        type=str,
        default="127.0.0.1",
        help="Host for the web interface (default: 127.0.0.1)",
    )

    args = parser.parse_args()

    # Configure the interface
    interface = get_gradio_interface()
    interface.update_settings(
        share=args.share, server_name=args.host, server_port=args.port
    )

    # Log startup information
    logger.info("🚀 Starting Raphaël PICARD AI Assistant")
    logger.info(f"Interface mode: {'Advanced' if args.advanced else 'Simple'}")
    logger.info(f"Server: {args.host}:{args.port}")
    logger.info(f"Public sharing: {'Enabled' if args.share else 'Disabled'}")

    try:
        # Launch the appropriate interface
        interface.launch(advanced=args.advanced)
    except KeyboardInterrupt:
        logger.info("👋 Application stopped by user")
    except Exception as e:
        logger.error(f"💥 Application error: {e}")
        raise


if __name__ == "__main__":
    main()
