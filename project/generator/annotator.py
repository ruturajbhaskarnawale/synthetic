from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path


@dataclass
class Annotation:
    sample_id: str
    doc_type: str
    tamper_type: str
    fields_modified: list[str]
    bboxes: dict[str, list[int]]

    def save(self, path: Path) -> None:
        payload = {
            "sample_id": self.sample_id,
            "doc_type": self.doc_type,
            "tamper_type": self.tamper_type,
            "fields_modified": self.fields_modified,
            "bboxes": self.bboxes,
        }
        path.write_text(json.dumps(payload, indent=2))


class QualityController:
    @staticmethod
    def validate(identity_dict: dict, bboxes: dict[str, list[int]], image_size: tuple[int, int]) -> None:
        if any(v is None or str(v).strip() == "" for v in identity_dict.values()):
            raise ValueError("Identity includes empty values")

        width, height = image_size
        for key, box in bboxes.items():
            x1, y1, x2, y2 = box
            if not (0 <= x1 < x2 <= width and 0 <= y1 < y2 <= height):
                raise ValueError(f"Invalid bbox for field '{key}': {box}")
