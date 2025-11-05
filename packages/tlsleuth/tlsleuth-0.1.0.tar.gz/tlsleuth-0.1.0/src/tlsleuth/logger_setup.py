import logging
import logging.config
from os import path, makedirs, getcwd


def setup_logging(default_path='logging.conf'):
    """Setup logging configuration and ensure log directory exists."""
    # Use current working directory for logs to avoid site-packages write issues
    cwd = getcwd()
    log_dir = path.join(cwd, 'logs')
    if not path.exists(log_dir):
        try:
            makedirs(log_dir)
        except Exception:
            # Fallback to basicConfig if not writable
            logging.basicConfig(level=logging.INFO)
            return logging.getLogger()

    # Config file sits next to this module inside the package
    script_dir = path.dirname(path.abspath(__file__))
    config_path = path.join(script_dir, default_path)

    if path.exists(config_path):
        try:
            logging.config.fileConfig(config_path)
        except Exception:
            logging.basicConfig(
                level=logging.INFO,
                format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
    else:
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )

    return logging.getLogger()
