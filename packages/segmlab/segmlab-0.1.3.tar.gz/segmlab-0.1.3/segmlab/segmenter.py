import cv2
import numpy as np
import matplotlib.pyplot as plt
from .model_loader import load_model

class Segmenter:
    def __init__(self):
        self.model, self.model_path = load_model()

    def segment(self, image_path, save_path=None):
        image = cv2.imread(image_path)
        if image is None:
            raise FileNotFoundError(f"Image not found: {image_path}")
        image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

        # For now, do a simple segmentation example:
        mask = cv2.Canny(image_rgb, 100, 200)
        color_mask = np.zeros_like(image_rgb)
        color_mask[mask != 0] = [0, 255, 0]

        segmented = cv2.addWeighted(image_rgb, 0.8, color_mask, 0.2, 0)
        plt.imshow(segmented)
        plt.axis('off')
        if save_path:
            plt.savefig(save_path, bbox_inches='tight', pad_inches=0)
        plt.show()
        return segmented
