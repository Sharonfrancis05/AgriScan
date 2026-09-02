"""Filters the user's uploaded Kaggle dataset down to the 6 preferred crops
and samples it to a manageable training size (~3000-5000 images), then
writes the authoritative label list that app/ml/labels.py picks up at
runtime.

Usage:
    python prepare_dataset.py \
        --raw-dir data_raw \
        --output-dir data_prepared \
        --max-total-images 4000

The uploaded dataset's exact folder naming is not known in advance, so this
script does not assume a single fixed layout. It recursively finds every
"leaf" directory (a directory containing image files directly, with no
subdirectories) and treats each one as a candidate class, then determines
the crop for that class by checking, in order:
  1. Any ANCESTOR directory name between the leaf and --raw-dir (covers a
     nested "train/<Crop>/<Disease>/" layout — the actual layout of the
     Kaggle dataset this project targets, e.g. "train/Apple/Apple Scab/").
     When matched this way, the disease name is the leaf folder's name
     as-is (normalized to snake_case), since the crop already lives in the
     parent folder and isn't redundantly embedded in the leaf name.
  2. The leaf folder's own name (covers a flat "Crop___Disease"-per-folder
     layout some other datasets use). When matched this way, the crop
     substring is stripped out of the folder name to derive the disease.
Matching is case-insensitive and tolerant of common naming variants (e.g.
"Corn_(maize)" for Corn). Everything not matching the 6 preferred crops
(Potato, Pepper, Cherry, background/other classes, etc.) is skipped and
logged.

Run this once after copying/extracting the Kaggle download into
`data_raw/`. Re-run any time to regenerate `data_prepared/` with a
different sample size or crop list.
"""
import argparse
import json
import logging
import random
import re
import shutil
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(levelname)s | %(message)s")
logger = logging.getLogger(__name__)

_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp"}

# Maps each preferred crop to the name variants seen across public leaf-disease
# datasets, so folder matching is resilient to the uploaded dataset's exact naming.
_CROP_ALIASES = {
    "Apple": ["apple"],
    "Grape": ["grape"],
    "Corn": ["corn", "maize"],
    "Tomato": ["tomato"],
    "Strawberry": ["strawberry"],
    "Peach": ["peach"],
}


def _find_leaf_dirs(root: Path) -> list[Path]:
    """A 'leaf' dir is one that directly contains at least one image file."""
    leaf_dirs = []
    for path in root.rglob("*"):
        if path.is_dir():
            has_images = any(f.suffix.lower() in _IMAGE_EXTENSIONS for f in path.iterdir() if f.is_file())
            if has_images:
                leaf_dirs.append(path)
    return leaf_dirs


def _match_crop(folder_name: str) -> str | None:
    normalized = folder_name.lower()
    for crop, aliases in _CROP_ALIASES.items():
        if any(alias in normalized for alias in aliases):
            return crop
    return None


def _normalize_disease_name(name: str) -> str:
    """snake_case, lowercase — deterministic regardless of the source
    dataset's capitalization (e.g. "Apple Scab" -> "apple_scab"), so the
    same disease always gets the same disease_code no matter how a
    particular dataset happened to capitalize its folder names."""
    normalized = re.sub(r"\s+", " ", name).strip("_- ").strip()
    if not normalized or normalized.lower() in ("healthy", "health"):
        return "healthy"
    return re.sub(r"\s+", "_", normalized).lower()


def _derive_disease_label_flat(folder_name: str, crop: str) -> str:
    """Flat-layout case: the crop is redundantly embedded in the folder name
    itself (e.g. "Apple___Apple_scab"), so strip it out before normalizing."""
    remainder = re.sub(re.escape(crop), "", folder_name, flags=re.IGNORECASE)
    for alias in _CROP_ALIASES[crop]:
        remainder = re.sub(re.escape(alias), "", remainder, flags=re.IGNORECASE)
    return _normalize_disease_name(remainder)


def _extract_label(leaf_dir: Path, raw_dir: Path) -> tuple[str, str] | None:
    """Returns (crop, disease) for a leaf directory, or None if it doesn't
    match any of the 6 preferred crops. See the module docstring for the
    two layouts this handles."""
    for ancestor in leaf_dir.parents:
        if ancestor == raw_dir:
            break
        crop = _match_crop(ancestor.name)
        if crop:
            return crop, _normalize_disease_name(leaf_dir.name)

    crop = _match_crop(leaf_dir.name)
    if crop:
        return crop, _derive_disease_label_flat(leaf_dir.name, crop)

    return None


def prepare_dataset(raw_dir: Path, output_dir: Path, max_total_images: int, val_seed: int = 42) -> None:
    if not raw_dir.exists():
        logger.error(
            "%s does not exist. Extract the Kaggle dataset into this folder first "
            "(e.g. unzip the download so image class folders live directly under it).",
            raw_dir,
        )
        raise SystemExit(1)

    leaf_dirs = _find_leaf_dirs(raw_dir)
    if not leaf_dirs:
        logger.error("No image-containing folders found under %s.", raw_dir)
        raise SystemExit(1)

    matched: dict[str, list[Path]] = {}
    skipped_folders = []

    for leaf_dir in leaf_dirs:
        extracted = _extract_label(leaf_dir, raw_dir)
        if extracted is None:
            skipped_folders.append(leaf_dir.name)
            continue
        crop, disease = extracted
        label = f"{crop}___{disease}"
        images = [f for f in leaf_dir.iterdir() if f.suffix.lower() in _IMAGE_EXTENSIONS]
        matched.setdefault(label, []).extend(images)

    if skipped_folders:
        logger.info(
            "Skipped %d folder(s) not matching the 6 preferred crops (Apple, Grape, Corn, "
            "Tomato, Strawberry, Peach): %s",
            len(skipped_folders),
            ", ".join(sorted(set(skipped_folders))[:20]),
        )

    if not matched:
        logger.error(
            "No folders matched the preferred crops. Check that the raw dataset actually "
            "contains Apple/Grape/Corn/Tomato/Strawberry/Peach classes."
        )
        raise SystemExit(1)

    total_available = sum(len(v) for v in matched.values())
    logger.info(
        "Matched %d classes across %d preferred crops, %d images available.",
        len(matched),
        len({label.split('___')[0] for label in matched}),
        total_available,
    )

    # Stratified cap: sample proportionally to each class's share of the total,
    # so no single class dominates the ~3000-5000 image training set.
    rng = random.Random(val_seed)
    output_dir.mkdir(parents=True, exist_ok=True)
    final_label_counts = {}

    for label, images in sorted(matched.items()):
        share = len(images) / total_available
        target_count = max(1, round(share * max_total_images))
        target_count = min(target_count, len(images))

        rng.shuffle(images)
        selected = images[:target_count]

        class_dir = output_dir / label
        class_dir.mkdir(parents=True, exist_ok=True)
        for src in selected:
            shutil.copy2(src, class_dir / src.name)

        final_label_counts[label] = len(selected)

    total_written = sum(final_label_counts.values())
    logger.info("Wrote %d images across %d classes to %s", total_written, len(final_label_counts), output_dir)
    for label, count in sorted(final_label_counts.items()):
        logger.info("  %-45s %d images", label, count)

    labels_path = Path(__file__).parent.parent / "app" / "ml" / "labels_generated.json"
    labels_path.write_text(json.dumps(sorted(final_label_counts.keys()), indent=2))
    logger.info(
        "Wrote authoritative label list (%d classes) to %s — app/ml/labels.py will pick "
        "this up automatically on next backend restart.",
        len(final_label_counts),
        labels_path,
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--raw-dir", type=Path, default=Path(__file__).parent / "data_raw")
    parser.add_argument("--output-dir", type=Path, default=Path(__file__).parent / "data_prepared")
    parser.add_argument("--max-total-images", type=int, default=4000)
    args = parser.parse_args()

    prepare_dataset(args.raw_dir, args.output_dir, args.max_total_images)


if __name__ == "__main__":
    main()
