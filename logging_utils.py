import logging
import os
from pathlib import Path
from kivy.logger import Logger
# Путь для хранения файлов
PROJECT_ROOT = Path(__file__).parent.parent
LOG_DIRECTORY = str(PROJECT_ROOT / "logs") # os.path.join(os.path.dirname(__file__), "logs") 
os.makedirs(LOG_DIRECTORY, exist_ok=True)
filename = os.path.join(LOG_DIRECTORY, "app.log")

LOG_FORMAT = "%(asctime)s - %(levelname)s - %(message)s"


def init_logging():
    try:
        logger = logging.getLogger('App')
        logger.setLevel(logging.INFO)
        
        formatter = logging.Formatter(LOG_FORMAT)
        
        file_handler = logging.FileHandler(filename, encoding='utf-8')
        
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
        
        #logging.basicConfig(
        ## filename=os.path.join(LOG_DIRECTORY, "app.log"),
        #llevel=logging.INFO,
        #lformat=LOG_FORMAT,
        #lhandlers=[
        #    logging.FileHandler(filename, encoding='utf-8', mode='a')
        #]
        #)
        
    except Exception as e:
        print(f"Ошибка логирования {e}")

def log_message(message):
    logger = logging.getLogger(__name__)
    logger.info(message)
    
    
