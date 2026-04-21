from __future__ import annotations

import io
import random
import time
from pathlib import Path

import requests
from PIL import Image, ImageFilter, ImageOps


class FaceGenerator:
    """Supplies AI-generated faces using local cache or thispersondoesnotexist.com."""

    def __init__(self, cache_dir: Path, seed: int | None = None):
        self.cache_dir = cache_dir
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.rng = random.Random(seed)

    def get_face(self, size: tuple[int, int]) -> Image.Image:
        source = self._get_source_face()
        face = ImageOps.fit(source.convert("RGB"), size, method=Image.Resampling.LANCZOS)
        face = face.filter(ImageFilter.GaussianBlur(radius=self.rng.uniform(0.1, 0.6)))
        return face

    def _get_source_face(self) -> Image.Image:
        cached = sorted(self.cache_dir.glob("*.jpg"))
        if cached and self.rng.random() < 0.8:
            return Image.open(self.rng.choice(cached)).copy()

        for _ in range(4):
            try:
                response = requests.get(
                    "https://thispersondoesnotexist.com/image",
                    timeout=10,
                    headers={"User-Agent": "synthetic-id-generator/1.0"},
                )
                response.raise_for_status()
                image = Image.open(io.BytesIO(response.content)).convert("RGB")
                output = self.cache_dir / f"face_{int(time.time() * 1000)}_{self.rng.randint(1000, 9999)}.jpg"
                image.save(output, quality=95)
                return image
            except Exception:
                continue

        if cached:
            return Image.open(self.rng.choice(cached)).copy()
        raise RuntimeError("Unable to fetch AI-generated faces and cache is empty.")
