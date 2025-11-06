import os
import requests
from tqdm import tqdm

# ✅ Correct direct link to Ultralytics SAM 2.1 Large weights
MODEL_URL = "https://github.com/ultralytics/assets/releases/download/v8.2.0/sam2.1_l.pt"
MODEL_DIR = os.path.join(os.path.expanduser("~"), ".segmlab")
MODEL_PATH = os.path.join(MODEL_DIR, "sam2.1_l.pt")


def download_model():
    """Download the SAM 2.1 Large model if not present."""
    os.makedirs(MODEL_DIR, exist_ok=True)

    # ✅ Check if file already exists and is valid (larger than ~1MB)
    if os.path.exists(MODEL_PATH) and os.path.getsize(MODEL_PATH) > 1_000_000:
        print("✅ Model already exists.")
        return MODEL_PATH

    print("⬇️ Downloading SAM model weights (~1.3GB)...")

    response = requests.get(MODEL_URL, stream=True, allow_redirects=True)
    if response.status_code != 200:
        raise Exception(f"❌ Failed to download model. HTTP {response.status_code}")

    total_size = int(response.headers.get("content-length", 0))

    with open(MODEL_PATH, "wb") as f, tqdm(
        desc="Downloading sam2.1_l.pt",
        total=total_size,
        unit="B",
        unit_scale=True,
        unit_divisor=1024,
    ) as bar:
        for data in response.iter_content(chunk_size=1024 * 1024):
            if data:
                size = f.write(data)
                bar.update(size)

    # ✅ Validate file size after download
    if os.path.getsize(MODEL_PATH) < 1_000_000:
        raise Exception("❌ Downloaded file too small — likely an invalid link or HTML file.")

    print("✅ Download complete:", MODEL_PATH)
    return MODEL_PATH
