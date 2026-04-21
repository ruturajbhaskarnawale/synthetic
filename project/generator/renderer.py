from __future__ import annotations

from dataclasses import dataclass

from PIL import Image, ImageDraw, ImageFont

from .identity_generator import IdentityRecord
from .qr_generator import QRGenerator
from .template_loader import CardTemplate


@dataclass
class RenderedCard:
    image: Image.Image
    bboxes: dict[str, list[int]]


class CardRenderer:
    def __init__(self, font_path: str | None = None):
        self.font_path = font_path or "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
        self.qr = QRGenerator()

    def _font(self, size: int) -> ImageFont.ImageFont:
        try:
            return ImageFont.truetype(self.font_path, size)
        except Exception:
            return ImageFont.load_default()

    def render(
        self,
        template: CardTemplate,
        identity: IdentityRecord,
        face_image: Image.Image,
        signature_image: Image.Image | None = None,
    ) -> RenderedCard:
        canvas = template.image.copy().convert("RGB")
        draw = ImageDraw.Draw(canvas)
        layout = template.layout

        self._paste_face(canvas, face_image, layout["photo"])
        self._draw_text_in_box(draw, identity.name, layout["name"], self._font(32))
        self._draw_text_in_box(draw, identity.dob, layout["dob"], self._font(26))
        self._draw_text_in_box(draw, identity.id_number, layout["id_number"], self._font(34))

        if "gender" in layout:
            self._draw_text_in_box(draw, identity.gender, layout["gender"], self._font(24))

        if template.doc_type == "pan" and identity.father_name and "father_name" in layout:
            self._draw_text_in_box(draw, identity.father_name, layout["father_name"], self._font(24))

        qr_payload = {"id": identity.id_number, "name": identity.name, "dob": identity.dob}
        qr_box = layout["qr"]
        qr_image = self.qr.make(qr_payload, size=(qr_box[2] - qr_box[0], qr_box[3] - qr_box[1]))
        canvas.paste(qr_image, (qr_box[0], qr_box[1]))

        if template.doc_type == "pan" and "signature" in layout:
            sign = signature_image if signature_image else self._default_signature(layout["signature"])
            self._paste_signature(canvas, sign, layout["signature"])

        return RenderedCard(image=canvas, bboxes=layout)

    def _draw_text_in_box(self, draw: ImageDraw.ImageDraw, text: str, box: list[int], font: ImageFont.ImageFont) -> None:
        x1, y1, x2, y2 = box
        max_w = x2 - x1
        max_h = y2 - y1

        for size in [getattr(font, "size", 24), 30, 26, 24, 22, 20, 18, 16, 14]:
            candidate = self._font(size)
            bbox = draw.textbbox((0, 0), text, font=candidate)
            text_w, text_h = bbox[2] - bbox[0], bbox[3] - bbox[1]
            if text_w <= max_w and text_h <= max_h:
                draw.text((x1, y1 + (max_h - text_h) // 2), text, fill=(10, 10, 10), font=candidate)
                return
        clipped = text[: max(1, int(len(text) * 0.85))]
        draw.text((x1, y1 + 2), clipped, fill=(10, 10, 10), font=self._font(14))

    @staticmethod
    def _paste_face(canvas: Image.Image, face: Image.Image, box: list[int]) -> None:
        x1, y1, x2, y2 = box
        canvas.paste(face.resize((x2 - x1, y2 - y1), Image.Resampling.LANCZOS), (x1, y1))

    @staticmethod
    def _default_signature(box: list[int]) -> Image.Image:
        w, h = box[2] - box[0], box[3] - box[1]
        sign = Image.new("RGB", (w, h), "white")
        d = ImageDraw.Draw(sign)
        d.arc((5, 5, w - 5, h - 5), 180, 360, fill=(10, 10, 140), width=2)
        d.text((w // 6, h // 4), "A. Sign", fill=(10, 10, 140))
        return sign

    @staticmethod
    def _paste_signature(canvas: Image.Image, signature: Image.Image, box: list[int]) -> None:
        x1, y1, x2, y2 = box
        canvas.paste(signature.resize((x2 - x1, y2 - y1)), (x1, y1))
