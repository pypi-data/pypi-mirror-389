import logging
from stiggy.cli import app


def configure_logging() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(name)s - %(message)s"
    )


def main() -> None:
    configure_logging()
    app()


if __name__ == "__main__":
    main()
