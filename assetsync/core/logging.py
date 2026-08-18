import logging


def get_logger(name: str = "assetsync") -> logging.Logger:
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter("[AssetSync] %(message)s"))
        logger.addHandler(handler)
    logger.propagate = False
    return logger


def configure_logging(level: str) -> None:
    get_logger().setLevel(getattr(logging, str(level).upper(), logging.INFO))

