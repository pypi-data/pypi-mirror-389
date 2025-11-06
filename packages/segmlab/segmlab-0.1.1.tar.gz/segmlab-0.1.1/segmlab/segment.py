import os
import cv2
import time
import torch
import matplotlib.pyplot as plt
import numpy as np
from ultralytics import SAM

from .utils import generate_pastel_colors
from .model_downloader import download_model

def segment(image_path: str):
    """Run SAM segmentation and display result."""
    if not os.path.exists(image_path):
        raise FileNotFoundError(f"❌ Image not found: {image_path}")

    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"🚀 Using device: {device}")

    model_path = download_model()
    model = SAM(model_path)
    print("✅ Model loaded successfully")

    start_time = time.time()
    results = model(image_path)
    end_time = time.time()

    print(f"🕒 Inference completed in {end_time - start_time:.2f} seconds")

    masks = results[0].masks.data.cpu().numpy()
    num_segments = masks.shape[0]
    print(f"🟩 Total Segments Detected: {num_segments}")

    orig_img = results[0].orig_img.copy()
    overlay = orig_img.copy()
    colors = generate_pastel_colors(num_segments)

    for i, mask in enumerate(masks):
        color = tuple(int(c) for c in colors[i])
        overlay[mask > 0.5] = color

    alpha = 0.7
    blended = cv2.addWeighted(orig_img, 1 - alpha, overlay, alpha, 0)

    plt.figure(figsize=(10, 8))
    plt.imshow(cv2.cvtColor(blended, cv2.COLOR_BGR2RGB))
    plt.axis("off")
    plt.title(f"✨ Segmentation Overlay — {num_segments} segments")
    plt.show()

    return blended
