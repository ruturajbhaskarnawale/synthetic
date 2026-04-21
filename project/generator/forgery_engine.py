from __future__ import annotations

import random
from dataclasses import dataclass

from PIL import Image, ImageDraw, ImageFilter

from .identity_generator import IdentityGenerator
from .qr_generator import QRGenerator


TAMPER_CLASS = {
    "face_swap": 1,
    "text_edit": 2,
    "qr_tamper": 3,
    "copy_move": 4,
    "partial_occlusion": 5,
    "mixed": 6,
}


@dataclass
class ForgeryResult:
    image: Image.Image
    binary_mask: Image.Image
    multiclass_mask: Image.Image
    tamper_type: str
    fields_modified: list[str]


class ForgeryEngine:
    def __init__(self, face_provider, seed: int | None = None):
        self.face_provider = face_provider
        self.rng = random.Random(seed)
        self.id_gen = IdentityGenerator(seed=seed)
        self.qr = QRGenerator()

    def apply(self, image: Image.Image, bboxes: dict[str, list[int]], tamper_type: str, doc_type: str) -> ForgeryResult:
        canvas = image.copy()
        binary = Image.new("L", canvas.size, 0)
        multiclass = Image.new("L", canvas.size, 0)

        if tamper_type == "mixed":
            choices = self.rng.sample(["face_swap", "text_edit", "qr_tamper", "copy_move"], k=2)
            fields = []
            for choice in choices:
                fields.extend(self._apply_single(canvas, bboxes, binary, multiclass, choice, doc_type))
        else:
            fields = self._apply_single(canvas, bboxes, binary, multiclass, tamper_type, doc_type)

        return ForgeryResult(canvas, binary, multiclass, tamper_type, sorted(set(fields)))

    def _apply_single(self, canvas, bboxes, binary, multiclass, tamper_type, doc_type):
        if tamper_type == "face_swap":
            return self._face_swap(canvas, bboxes, binary, multiclass)
        if tamper_type == "text_edit":
            return self._text_edit(canvas, bboxes, binary, multiclass, doc_type)
        if tamper_type == "qr_tamper":
            return self._qr_tamper(canvas, bboxes, binary, multiclass)
        if tamper_type == "copy_move":
            return self._copy_move(canvas, bboxes, binary, multiclass)
        if tamper_type == "partial_occlusion":
            return self._partial_occlusion(canvas, bboxes, binary, multiclass)
        return []

    def _paint_mask(self, binary, multiclass, box, cls):
        ImageDraw.Draw(binary).rectangle(box, fill=255)
        ImageDraw.Draw(multiclass).rectangle(box, fill=cls)

    def _face_swap(self, canvas, bboxes, binary, multiclass):
        box = bboxes["photo"]
        face = self.face_provider.get_face((box[2] - box[0], box[3] - box[1]))
        canvas.paste(face, (box[0], box[1]))
        self._paint_mask(binary, multiclass, box, TAMPER_CLASS["face_swap"])
        return ["photo"]

    def _text_edit(self, canvas, bboxes, binary, multiclass, doc_type):
        fields = ["name", "dob", "id_number"]
        target = self.rng.choice(fields)
        identity = self.id_gen.generate(doc_type)
        value = identity.to_dict()[target]

        draw = ImageDraw.Draw(canvas)
        box = bboxes[target]
        draw.rectangle(box, fill=(245, 245, 245))
        draw.text((box[0] + 4, box[1] + 4), value, fill=(15, 15, 15))
        self._paint_mask(binary, multiclass, box, TAMPER_CLASS["text_edit"])
        return [target]

    def _qr_tamper(self, canvas, bboxes, binary, multiclass):
        box = bboxes["qr"]
        fake_data = {"id": "9999 8888 7777", "name": "Tampered Identity", "dob": "01/01/1991"}
        qr = self.qr.make(fake_data, (box[2] - box[0], box[3] - box[1]))
        canvas.paste(qr, (box[0], box[1]))
        self._paint_mask(binary, multiclass, box, TAMPER_CLASS["qr_tamper"])
        return ["qr"]

    def _copy_move(self, canvas, bboxes, binary, multiclass):
        src = bboxes["id_number"]
        crop = canvas.crop((src[0], src[1], src[0] + 90, src[3]))
        dest_box = [src[0] + 130, src[1], src[0] + 220, src[3]]
        canvas.paste(crop, (dest_box[0], dest_box[1]))
        self._paint_mask(binary, multiclass, dest_box, TAMPER_CLASS["copy_move"])
        return ["id_number"]

    def _partial_occlusion(self, canvas, bboxes, binary, multiclass):
        target = self.rng.choice(["name", "id_number", "photo"])
        box = bboxes[target]
        region = canvas.crop(tuple(box)).filter(ImageFilter.GaussianBlur(radius=5.2))
        canvas.paste(region, (box[0], box[1]))
        self._paint_mask(binary, multiclass, box, TAMPER_CLASS["partial_occlusion"])
        return [target]
