from __future__ import annotations

import argparse
import json
import multiprocessing as mp
from collections import Counter
from pathlib import Path

from PIL import Image, ImageDraw

from generator.annotator import Annotation, QualityController
from generator.augmenter import Augmenter
from generator.config import default_config
from generator.face_generator import FaceGenerator
from generator.forgery_engine import ForgeryEngine
from generator.identity_generator import IdentityGenerator
from generator.renderer import CardRenderer
from generator.template_loader import TemplateLoader


FORGERY_DISTRIBUTION = {
    "face_swap": 0.30,
    "text_edit": 0.30,
    "qr_tamper": 0.20,
    "copy_move": 0.20,
}


def build_signature(size: tuple[int, int]) -> Image.Image:
    w, h = size
    sig = Image.new("RGB", size, "white")
    d = ImageDraw.Draw(sig)
    d.line([(10, h // 2), (w // 3, h // 4), (w // 2, h // 2), (w - 10, h // 3)], fill=(12, 20, 140), width=3)
    d.text((w // 3, h // 2), "synthetic", fill=(12, 20, 140))
    return sig


def choose_tamper(i: int, total: int) -> str:
    idx = i / max(1, total)
    if idx < FORGERY_DISTRIBUTION["face_swap"]:
        return "face_swap"
    if idx < FORGERY_DISTRIBUTION["face_swap"] + FORGERY_DISTRIBUTION["text_edit"]:
        return "text_edit"
    if idx < 0.8:
        return "qr_tamper"
    return "copy_move"


def process_one(args: tuple[int, str, bool, str]) -> dict:
    i, doc_type, forged, out_root = args
    root = Path(out_root)
    template = TemplateLoader(root / "templates").load(doc_type)
    id_gen = IdentityGenerator(seed=1000 + i)
    face_gen = FaceGenerator(root / "assets" / "faces_cache", seed=2000 + i)
    renderer = CardRenderer()
    augmenter = Augmenter()
    forgery_engine = ForgeryEngine(face_gen, seed=3000 + i)

    identity = id_gen.generate(doc_type)
    face = face_gen.get_face((template.layout["photo"][2] - template.layout["photo"][0], template.layout["photo"][3] - template.layout["photo"][1]))
    signature = None
    if doc_type == "pan" and "signature" in template.layout:
        sbox = template.layout["signature"]
        signature = build_signature((sbox[2] - sbox[0], sbox[3] - sbox[1]))

    rendered = renderer.render(template, identity, face, signature)
    QualityController.validate(identity.to_dict(), rendered.bboxes, rendered.image.size)

    if forged:
        tamper_type = choose_tamper(i, 5000)
        forged_result = forgery_engine.apply(rendered.image, rendered.bboxes, tamper_type, doc_type)
        masks = {"binary": forged_result.binary_mask, "multiclass": forged_result.multiclass_mask}
        image_aug, masks_aug = augmenter.apply(forged_result.image, masks)
        image = image_aug
        binary, multiclass = masks_aug["binary"], masks_aug["multiclass"]
        fields = forged_result.fields_modified
    else:
        image, binary, multiclass = rendered.image, Image.new("L", rendered.image.size, 0), Image.new("L", rendered.image.size, 0)
        tamper_type = "none"
        fields = []

    sample_id = f"{doc_type}_{'forged' if forged else 'clean'}_{i:05d}"
    (root / "output" / "images" / f"{sample_id}.png").parent.mkdir(parents=True, exist_ok=True)
    image.save(root / "output" / "images" / f"{sample_id}.png")
    binary.save(root / "output" / "masks" / f"{sample_id}_binary.png")
    multiclass.save(root / "output" / "masks" / f"{sample_id}_multi.png")

    ann = Annotation(sample_id, doc_type, tamper_type, fields, rendered.bboxes)
    ann.save(root / "output" / "annotations" / f"{sample_id}.json")

    return {"sample_id": sample_id, "doc_type": doc_type, "tamper": tamper_type}


def run(aadhaar_count: int, pan_count: int, forged_count: int, workers: int) -> None:
    cfg = default_config()
    for p in [cfg.templates_dir, cfg.output_dir / "images", cfg.output_dir / "masks", cfg.output_dir / "annotations", cfg.output_dir / "logs", cfg.faces_cache_dir]:
        p.mkdir(parents=True, exist_ok=True)

    tasks: list[tuple[int, str, bool, str]] = []
    tasks.extend((i, "aadhaar", False, str(cfg.root)) for i in range(aadhaar_count))
    tasks.extend((i, "pan", False, str(cfg.root)) for i in range(pan_count))

    half = forged_count // 2
    tasks.extend((i, "aadhaar", True, str(cfg.root)) for i in range(half))
    tasks.extend((i, "pan", True, str(cfg.root)) for i in range(forged_count - half))

    with mp.Pool(processes=workers) as pool:
        results = list(pool.imap_unordered(process_one, tasks, chunksize=20))

    counts = Counter((r["doc_type"], r["tamper"]) for r in results)
    (cfg.output_dir / "logs" / "dataset_stats.json").write_text(json.dumps({f"{k[0]}::{k[1]}": v for k, v in counts.items()}, indent=2))
    print("Generation complete", len(results))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Synthetic Aadhaar/PAN dataset generator")
    parser.add_argument("--aadhaar-count", type=int, default=5000)
    parser.add_argument("--pan-count", type=int, default=5000)
    parser.add_argument("--forged-count", type=int, default=5000)
    parser.add_argument("--workers", type=int, default=max(1, mp.cpu_count() - 1))
    args = parser.parse_args()
    run(args.aadhaar_count, args.pan_count, args.forged_count, args.workers)
