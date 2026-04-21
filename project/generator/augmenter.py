from __future__ import annotations

import numpy as np

try:
    import albumentations as A
except Exception:  # pragma: no cover
    A = None

from PIL import Image


class Augmenter:
    def __init__(self):
        if A is None:
            self.pipeline = None
        else:
            self.pipeline = A.Compose(
                [
                    A.OneOf([A.GaussianBlur(blur_limit=3), A.MotionBlur(blur_limit=3)], p=0.3),
                    A.GaussNoise(var_limit=(5.0, 40.0), p=0.4),
                    A.RandomBrightnessContrast(p=0.5),
                    A.Perspective(scale=(0.01, 0.04), p=0.25),
                    A.ImageCompression(quality_range=(45, 95), p=0.6),
                ]
            )

    def apply(self, image: Image.Image, masks: dict[str, Image.Image]) -> tuple[Image.Image, dict[str, Image.Image]]:
        if self.pipeline is None:
            return image, masks

        img = np.array(image)
        mask_stack = [np.array(m, dtype=np.uint8) for m in masks.values()]
        augmented = self.pipeline(image=img, masks=mask_stack)
        out_img = Image.fromarray(augmented["image"])
        out_masks = {
            name: Image.fromarray(mask.astype(np.uint8))
            for name, mask in zip(masks.keys(), augmented["masks"], strict=True)
        }
        return out_img, out_masks
