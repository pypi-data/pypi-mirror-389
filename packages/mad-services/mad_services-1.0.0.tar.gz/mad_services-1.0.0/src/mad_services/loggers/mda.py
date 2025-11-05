import logging
import MDAnalysis
from pathlib import Path


# This is not working
def redirect_mda_logger(file: Path):
    MDAnalysis.start_logging(logfile="MDAnalysis.log", version="1.0.0")
    mda_logger = logging.getLogger("MDAnalysis")

    # Remove all StreamHandlers (which print to console)
    for handler in mda_logger.handlers[:]:
        print(handler)
        if isinstance(handler, logging.StreamHandler):
            print("To remove")
            mda_logger.removeHandler(handler)

    mda_logger.setLevel(logging.ERROR)
