import os
import shutil
import time
from pathlib import Path
from config import Config

def full_reset():
    # Kill running processes
    os.system("taskkill /f /im python.exe >nul 2>&1")
    
    paths = [
        Config.KEYWORD_DB,
        Config.QDRANT_LOCATION,
        Config.EMBEDDING_STORAGE,
        Config.VECTOR_DB_DIR / Config.FILE_HASHES_JSON,
        Config.MODEL_CACHE
    ]
    
    for path in paths:
        path = Path(path)
        if path.exists():
            try:
                if path.is_file():
                    os.remove(path)
                else:
                    shutil.rmtree(path, ignore_errors=True)
                print(f"Deleted: {path}")
                time.sleep(0.2)
            except Exception as e:
                print(f"Error deleting {path}: {str(e)}")
    
    # Recreate directories
    for dir_path in [Config.VECTOR_DB_DIR, Config.EMBEDDING_STORAGE,
                    Config.MODEL_CACHE, Config.PDF_DIRECTORY,
                    Config.PUBLIC_DIR, Config.INTERNAL_DIR,
                    Config.CONFIDENTIAL_DIR]:
        dir_path.mkdir(parents=True, exist_ok=True)
    
    print("Reset complete. Ready for new processing.")

if __name__ == "__main__":
    full_reset()