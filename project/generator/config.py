from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class ProjectConfig:
    root: Path
    templates_dir: Path
    output_dir: Path
    faces_cache_dir: Path
    font_path: str | None = None


def default_config() -> ProjectConfig:
    root = Path(__file__).resolve().parents[1]
    return ProjectConfig(
        root=root,
        templates_dir=root / "templates",
        output_dir=root / "output",
        faces_cache_dir=root / "assets" / "faces_cache",
    )
