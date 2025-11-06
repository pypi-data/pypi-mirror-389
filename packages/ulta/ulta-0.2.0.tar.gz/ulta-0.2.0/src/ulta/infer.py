from pathlib import Path
from PIL import Image
from typing import Optional, Union
import torch

from .manager import ModelManager
from .model import get_orientation_model
from .utils import get_device, get_data_transforms, predict_single_image
from .enum import Orientation


# Configuration for your model
MODEL_URL = "https://github.com/duartebarbosadev/deep-image-orientation-detection/releases/download/v2/orientation_model_v2_0.9882.pth"
MODEL_HASH = (
    "cc6bd460ef23b7213265e92753d0f2f13185031b0e646b86c31335fe35fcd2a2"  # SHA256 hash
)
MODEL_FILENAME = "orientation_model_v7.pth"

class OrientationDetection:
    """Main inference engine that uses the downloaded model."""

    def __init__(self, cache_dir: Optional[Path] = None):
        """
        Initialize the inference engine.

        Args:
            cache_dir: Optional custom cache directory for models
        """
        self.manager = ModelManager(cache_dir)
        self._model_path = self.manager.download_model(
            url=MODEL_URL,
            filename=MODEL_FILENAME,
            expected_hash=MODEL_HASH,
            force_download=False,
        )

        self.device = get_device()
        self.all_transforms = get_data_transforms()
        self.transforms = self.all_transforms["val"]

        self._model = get_orientation_model(
            pretrained=False
        )  # No need to download weights

        state_dict = torch.load(self._model_path, map_location=self.device)
        self._model.load_state_dict(state_dict)
        self._model.to(self.device)
        self._model.eval()

    def detect_orientation(self, image: Union[Image.Image, str]) -> Orientation:
        """
        Detect the orientation of an image.

        Args:
            image: Path to the input image or a PIL Image

        Returns:
            Prediction result
        """
        return predict_single_image(self._model, image, self.device, self.transforms)
