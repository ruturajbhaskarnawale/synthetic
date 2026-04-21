# Synthetic Indian ID Forgery Dataset Generator

Generates synthetic Aadhaar/PAN cards and forged versions for OCR, fraud detection, and forgery localization training.

## Features
- 100% synthetic identity fields (no real PII)
- AI-generated non-existent faces (cache + online fetch)
- Aadhaar + PAN layout rendering with filled fields
- Pixel-level binary + multiclass tamper masks
- Forgery types:
  - face swap
  - text edit
  - QR tampering
  - copy-move
  - partial occlusion
  - mixed (engine support)
- Realism augmentations with Albumentations
- Multiprocessing batch generation and stats logging

## Project structure

```
project/
  generator/
    template_loader.py
    identity_generator.py
    face_generator.py
    qr_generator.py
    renderer.py
    augmenter.py
    annotator.py
    forgery_engine.py
  templates/
    aadhaar.png
    pan.png
    aadhaar_layout.json
    pan_layout.json
  output/
    images/
    masks/
    annotations/
    logs/
  generate_dataset.py
```

## Install

```bash
cd project
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Run full generation

```bash
python generate_dataset.py \
  --aadhaar-count 5000 \
  --pan-count 5000 \
  --forged-count 5000 \
  --workers 8
```

## Quick smoke run

```bash
python generate_dataset.py --aadhaar-count 4 --pan-count 4 --forged-count 6 --workers 2
```

## Output artifacts per sample
- `output/images/<sample_id>.png`
- `output/masks/<sample_id>_binary.png`
- `output/masks/<sample_id>_multi.png`
- `output/annotations/<sample_id>.json`

Annotation schema:

```json
{
  "sample_id": "aadhaar_forged_00001",
  "doc_type": "aadhaar",
  "tamper_type": "text_edit",
  "fields_modified": ["name"],
  "bboxes": {
    "photo": [35, 110, 220, 325],
    "name": [245, 135, 760, 180]
  }
}
```

## Using your attached layout/template
Replace the auto-generated template files with your attachment-derived assets:
1. Put card images at `templates/aadhaar.png` and `templates/pan.png`.
2. Update `templates/aadhaar_layout.json` and `templates/pan_layout.json` with exact coordinates from your attachment.
3. Re-run generation. The renderer/forgery engine automatically uses updated boxes.

## Notes
- If network is unavailable, preload AI-generated faces in `assets/faces_cache/`.
- All fields are always populated; QC validates empties + bbox sanity.
