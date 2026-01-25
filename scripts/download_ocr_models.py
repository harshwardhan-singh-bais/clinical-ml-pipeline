import os
import requests
import zipfile
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def download_file(url, dest_path):
    if dest_path.exists():
        logger.info(f"File {dest_path} already exists, skipping download.")
        return True
    
    logger.info(f"Downloading {url} to {dest_path}...")
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers, stream=True, timeout=30)
        response.raise_for_status()
        
        with open(dest_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
        logger.info(f"Successfully downloaded {dest_path}")
        return True
    except Exception as e:
        logger.error(f"Failed to download {url}: {e}")
        return False

def setup_ocr_models():
    project_root = Path(__file__).parent.parent
    model_dir = project_root / "models" / "ocr_weights"
    model_dir.mkdir(parents=True, exist_ok=True)
    
    models = {
        "craft_mlt_25k.zip": "https://github.com/JaidedAI/EasyOCR/releases/download/pre-v1.1.6/craft_mlt_25k.zip",
        "english_g2.zip": "https://github.com/JaidedAI/EasyOCR/releases/download/v1.3/english_g2.zip"
    }
    
    for filename, url in models.items():
        zip_path = model_dir / filename
        if download_file(url, zip_path):
            # Unzip
            try:
                logger.info(f"Unzipping {zip_path}...")
                with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                    zip_ref.extractall(model_dir)
                logger.info(f"Successfully unzipped {filename}")
                # Optional: remove zip file to save space
                # os.remove(zip_path)
            except Exception as e:
                logger.error(f"Failed to unzip {filename}: {e}")

if __name__ == "__main__":
    setup_ocr_models()
