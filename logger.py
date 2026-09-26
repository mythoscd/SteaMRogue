# %% [markdown]
# # Logger Module
# Configures logging for console output and file logging.

# %%
import os
import logging
from datetime import datetime

# %%
def setup_logger(log_dir: str = "logs") -> logging.Logger:
    """Configures and returns a logger instance writing to a file and console."""
    logger = logging.getLogger("SteamToolsAuto")
    logger.setLevel(logging.DEBUG)
    
    # Avoid duplicate handlers if logger is reinitialized
    if logger.handlers:
        return logger
        
    # Console Handler - Basic logging
    console_handler = logging.StreamHandler()
    console_formatter = logging.Formatter("%(message)s")
    console_handler.setFormatter(console_formatter)
    console_handler.setLevel(logging.INFO)
    logger.addHandler(console_handler)

    # Determine safe log directory
    safe_dir = None
    target_dirs = [
        log_dir,
        os.path.join(os.environ.get("LOCALAPPDATA", ""), "SteaMRogue", "logs"),
        os.path.join(os.environ.get("APPDATA", ""), "SteaMRogue", "logs"),
        os.path.join(os.path.expanduser("~"), ".steamrogue", "logs"),
        os.path.join(os.environ.get("TEMP", ""), "steamrogue_logs")
    ]

    for d in target_dirs:
        if not d:
            continue
        try:
            os.makedirs(d, exist_ok=True)
            test_file = os.path.join(d, ".perm_test")
            with open(test_file, "w") as f:
                f.write("ok")
            os.remove(test_file)
            safe_dir = d
            break
        except Exception:
            continue

    if safe_dir:
        try:
            log_file = os.path.join(safe_dir, "steamtools_auto.log")
            file_handler = logging.FileHandler(log_file, encoding="utf-8")
            file_formatter = logging.Formatter(
                "[%(asctime)s] [%(levelname)s] [%(filename)s:%(lineno)d]: %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S"
            )
            file_handler.setFormatter(file_formatter)
            file_handler.setLevel(logging.DEBUG)
            logger.addHandler(file_handler)
        except Exception as e:
            logger.warning(f"Could not attach file logger: {e}")

    return logger

# %%
# Instantiate a default logger for imported modules
logger = setup_logger()
