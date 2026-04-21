from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from PIL import Image, ImageDraw


@dataclass
class CardTemplate:
    doc_type: str
    image: Image.Image
    layout: dict[str, list[int]]


DEFAULT_LAYOUTS = {
    "aadhaar": {
        "photo": [35, 110, 220, 325],
        "name": [245, 135, 760, 180],
        "dob": [245, 185, 520, 225],
        "gender": [245, 230, 460, 270],
        "id_number": [245, 292, 680, 335],
        "qr": [705, 95, 960, 350],
    },
    "pan": {
        "photo": [45, 105, 245, 320],
        "name": [270, 120, 770, 165],
        "father_name": [270, 165, 770, 210],
        "dob": [270, 210, 560, 255],
        "id_number": [270, 265, 650, 315],
        "signature": [590, 315, 900, 380],
        "qr": [25, 335, 235, 545],
    },
}


class TemplateLoader:
    def __init__(self, templates_dir: Path):
        self.templates_dir = templates_dir

    def load(self, doc_type: str) -> CardTemplate:
        doc_type = doc_type.lower()
        image_path = self.templates_dir / f"{doc_type}.png"
        layout_path = self.templates_dir / f"{doc_type}_layout.json"

        if not image_path.exists():
            image = self._build_default_template(doc_type)
            image.save(image_path)
        else:
            image = Image.open(image_path).convert("RGB")

        if layout_path.exists():
            layout = json.loads(layout_path.read_text())
        else:
            layout = DEFAULT_LAYOUTS[doc_type]
            layout_path.write_text(json.dumps(layout, indent=2))

        return CardTemplate(doc_type=doc_type, image=image, layout=layout)

    @staticmethod
    def _build_default_template(doc_type: str) -> Image.Image:
        size = (1000, 600)
        if doc_type == "aadhaar":
            bg = (250, 245, 238)
            accent = (196, 92, 23)
        elif doc_type == "pan":
            bg = (233, 241, 248)
            accent = (23, 74, 124)
        else:
            raise ValueError(f"Unsupported doc_type: {doc_type}")

        image = Image.new("RGB", size, bg)
        draw = ImageDraw.Draw(image)
        draw.rectangle((0, 0, size[0], 56), fill=accent)
        draw.rectangle((0, size[1] - 12, size[0], size[1]), fill=accent)
        draw.text((20, 18), f"SYNTHETIC {doc_type.upper()} TEMPLATE", fill=(255, 255, 255))

        layout = DEFAULT_LAYOUTS[doc_type]
        for key, box in layout.items():
            draw.rectangle(box, outline=(70, 70, 70), width=2)
            draw.text((box[0] + 4, box[1] + 4), key, fill=(70, 70, 70))
        return image
