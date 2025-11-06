import os
import requests
from tqdm import tqdm

MODEL_URL = "https://github.com/ultralytics/assets/releases/download/v0.0.0/sam2.1_l.pt"
MODEL_PATH = os.path.join(os.path.expanduser("~"), ".seglab", "sam2.1_l.pt")

def download_model():
    os.makedirs(os.path.dirname(MODEL_PATH), exist_ok=True)
    if os.path.exists(MODEL_PATH):
        print("✅ Model already exists.")
        return MODEL_PATH

    print("⬇️ Downloading SAM model weights (~1.3GB)...")

    response = requests.get(MODEL_URL, stream=True)
    total_size = int(response.headers.get('content-length', 0))

    with open(MODEL_PATH, "wb") as f, tqdm(
        desc="Downloading sam2.1_l.pt",
        total=total_size,
        unit='B',
        unit_scale=True,
        unit_divisor=1024
    ) as bar:
        for data in response.iter_content(chunk_size=1024):
            size = f.write(data)
            bar.update(size)
    
    print("✅ Download complete:", MODEL_PATH)
    return MODEL_PATH
