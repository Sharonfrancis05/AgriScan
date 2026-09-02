"""Semi-manual lesion-mask labeling tool using OpenCV GrabCut.

Much faster than pixel-painting: for each image you draw one rectangle
around the lesion region(s), optionally scribble a couple of corrections,
and GrabCut refines the rest. Output masks land in the layout
train_segmentation.py expects (masks_dir/images/, masks_dir/masks/).

This is an INTERACTIVE, windowed tool — run it on your own desktop (it opens
an OpenCV window), not in a headless/CI environment.

Usage:
    python ml_training/scripts/label_assist_grabcut.py \
        --input-dir ml_training/data_prepared/Tomato___Late_blight \
        --output-dir ml_training/data_masks

Controls (per image):
  - Left-click + drag: draw a rectangle around the diseased region(s) —
    GrabCut treats everything outside it as definite background.
  - Left-click + drag while holding 'f': mark additional pixels as
    DEFINITE foreground (lesion) to correct GrabCut's guess.
  - Left-click + drag while holding 'b': mark additional pixels as
    DEFINITE background (healthy tissue) to correct GrabCut's guess.
  - 'g': (re)run GrabCut with the current rectangle/scribbles.
  - 's': save the current mask and move to the next image.
  - 'n': skip this image without saving.
  - 'q': quit the tool entirely.
"""
import argparse
from pathlib import Path

import cv2
import numpy as np

_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp"}
_WINDOW = "label_assist_grabcut — draw rect, f/b to correct, g=run, s=save, n=skip, q=quit"


class _GrabCutSession:
    def __init__(self, image: np.ndarray):
        self.image = image
        self.display = image.copy()
        self.mask = np.zeros(image.shape[:2], dtype=np.uint8)  # cv2.GC_* labels
        self.rect = None
        self.drawing = False
        self.mode = "rect"  # "rect" | "fgd" | "bgd"
        self.start_point = None

    def on_mouse(self, event, x, y, flags, _param):
        if event == cv2.EVENT_LBUTTONDOWN:
            self.drawing = True
            self.start_point = (x, y)
        elif event == cv2.EVENT_MOUSEMOVE and self.drawing:
            self.display = self.image.copy()
            if self.mode == "rect":
                cv2.rectangle(self.display, self.start_point, (x, y), (0, 255, 0), 2)
            else:
                color = (0, 255, 0) if self.mode == "fgd" else (0, 0, 255)
                cv2.circle(self.display, (x, y), 4, color, -1)
                label = cv2.GC_FGD if self.mode == "fgd" else cv2.GC_BGD
                cv2.circle(self.mask, (x, y), 4, label, -1)
        elif event == cv2.EVENT_LBUTTONUP:
            self.drawing = False
            if self.mode == "rect":
                x0, y0 = self.start_point
                self.rect = (min(x0, x), min(y0, y), abs(x - x0), abs(y - y0))


def _process_one(image_path: Path, output_dir: Path) -> bool:
    """Returns True if a mask was saved, False if skipped."""
    image = cv2.imread(str(image_path))
    if image is None:
        print(f"Could not read {image_path}, skipping.")
        return False

    session = _GrabCutSession(image)
    cv2.namedWindow(_WINDOW)
    cv2.setMouseCallback(_WINDOW, session.on_mouse)

    while True:
        cv2.imshow(_WINDOW, session.display)
        key = cv2.waitKey(20) & 0xFF

        if key == ord("f"):
            session.mode = "fgd"
        elif key == ord("b"):
            session.mode = "bgd"
        elif key == ord("g"):
            if session.rect is None:
                print("Draw a rectangle around the lesion first.")
                continue
            bgd_model = np.zeros((1, 65), np.float64)
            fgd_model = np.zeros((1, 65), np.float64)
            grabcut_mask = session.mask.copy()
            grabcut_mask[grabcut_mask == 0] = cv2.GC_PR_BGD
            cv2.grabCut(
                image, grabcut_mask, session.rect, bgd_model, fgd_model, 5, cv2.GC_INIT_WITH_RECT
            )
            binary = np.where((grabcut_mask == cv2.GC_FGD) | (grabcut_mask == cv2.GC_PR_FGD), 255, 0).astype(
                np.uint8
            )
            overlay = image.copy()
            overlay[binary > 0] = (0, 0, 255)
            session.display = cv2.addWeighted(overlay, 0.4, image, 0.6, 0)
            session._last_binary = binary
        elif key == ord("s"):
            binary = getattr(session, "_last_binary", None)
            if binary is None:
                print("Run GrabCut with 'g' before saving.")
                continue
            (output_dir / "images").mkdir(parents=True, exist_ok=True)
            (output_dir / "masks").mkdir(parents=True, exist_ok=True)
            cv2.imwrite(str(output_dir / "images" / image_path.name), image)
            cv2.imwrite(str(output_dir / "masks" / f"{image_path.stem}.png"), binary)
            cv2.destroyWindow(_WINDOW)
            return True
        elif key == ord("n"):
            cv2.destroyWindow(_WINDOW)
            return False
        elif key == ord("q"):
            cv2.destroyAllWindows()
            raise SystemExit(0)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-dir", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, default=Path("ml_training/data_masks"))
    args = parser.parse_args()

    image_paths = sorted(p for p in args.input_dir.iterdir() if p.suffix.lower() in _IMAGE_EXTENSIONS)
    print(f"{len(image_paths)} images to label. See this script's docstring for controls.")

    saved_count = 0
    for image_path in image_paths:
        if _process_one(image_path, args.output_dir):
            saved_count += 1

    cv2.destroyAllWindows()
    print(f"Saved {saved_count}/{len(image_paths)} masks to {args.output_dir}")


if __name__ == "__main__":
    main()
