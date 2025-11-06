import numpy as np

def generate_pastel_colors(num_colors):
    """Generate bright pastel-like colors."""
    return np.random.randint(100, 255, size=(num_colors, 3), dtype=np.uint8)
