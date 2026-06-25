import logging


def _configure_logger() -> logging.Logger:
    logging.basicConfig(
        level=logging.WARNING,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            # logging.FileHandler("app.log"),  # Log to a file
            logging.StreamHandler(),  # Log to the console
        ],
    )
    return logging.getLogger(__name__)


logger = _configure_logger()
