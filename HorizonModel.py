"""
Standalone horizon model for use in other projects. Just the architecture
and a predict function, no training/labeling code.

Copy this file plus your checkpoint (e.g. model_v3.pt) into the new
project. Requires: torch, numpy, pillow.

Usage:
    from horizon_model import HorizonModel

    model = HorizonModel("model_v3.pt")
    row_px = model.predict("some_image.jpeg")
"""

import numpy as np
import torch
import torch.nn as nn
from PIL import Image

IMG_H, IMG_W = 256, 512  # must match what the checkpoint was trained with


class HorizonNet(nn.Module):
    def __init__(self, out_dim=1):
        super().__init__()

        def block(cin, cout, stride=2):
            return nn.Sequential(
                nn.Conv2d(cin, cout, 3, stride=stride, padding=1),
                nn.BatchNorm2d(cout),
                nn.ReLU(inplace=True),
            )

        self.features = nn.Sequential(
            block(1, 16), block(16, 32), block(32, 64),
            block(64, 128), block(128, 128),
        )
        self.head = nn.Sequential(
            nn.AdaptiveAvgPool2d(1),
            nn.Flatten(),
            nn.Linear(128, 64),
            nn.ReLU(inplace=True),
            nn.Linear(64, out_dim),
            nn.Sigmoid(),
        )

    def forward(self, x):
        return self.head(self.features(x))


class HorizonModel:
    def __init__(self, checkpoint_path, device=None):
        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")
        self.model = HorizonNet().to(self.device)
        self.model.load_state_dict(torch.load(checkpoint_path, map_location=self.device))
        self.model.eval()

    def predict(self, image_path):
        """Returns the predicted horizon row in pixels, for the original image size."""
        img = Image.open(image_path).convert("L")
        orig_w, orig_h = img.size
        img_resized = img.resize((IMG_W, IMG_H))
        arr = np.array(img_resized, dtype=np.float32) / 255.0
        tensor = torch.from_numpy(arr).unsqueeze(0).unsqueeze(0).float().to(self.device)
        with torch.no_grad():
            row_norm = self.model(tensor).item()
        return row_norm * orig_h


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--image", required=True)
    parser.add_argument("--checkpoint", required=True)
    args = parser.parse_args()

    model = HorizonModel(args.checkpoint)
    row_px = model.predict(args.image)
    print(f"Predicted horizon row: {row_px:.1f}px")
