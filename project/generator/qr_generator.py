from __future__ import annotations

import json

import qrcode
from PIL import Image


class QRGenerator:
    def make(self, payload: dict, size: tuple[int, int]) -> Image.Image:
        qr = qrcode.QRCode(version=1, box_size=10, border=1)
        qr.add_data(json.dumps(payload, ensure_ascii=False))
        qr.make(fit=True)
        image = qr.make_image(fill_color="black", back_color="white").convert("RGB")
        return image.resize(size, Image.Resampling.NEAREST)
