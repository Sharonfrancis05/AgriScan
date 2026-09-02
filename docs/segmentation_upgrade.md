# Segmentation: the honest limitation, and the upgrade path

## The problem

"Segment the infected leaf region and compute % infected area" normally
implies a trained segmentation model (U-Net, Mask R-CNN, etc.), which needs
pixel-level ground-truth masks to train on. Public leaf-disease datasets —
including PlantVillage-derived sets like the one this project targets — ship
with **classification labels only** (a folder per crop+disease), not masks.
There is nothing to supervise a U-Net with out of the box.

## What ships today: `ClassicalCVSegmenter`

`app/ml/segmentation/classical_cv.py` is a **classical computer-vision
heuristic**, not a trained model, and it is the default
(`SEGMENTATION_BACKEND=classical_cv`):

1. **Leaf-vs-background mask**: HSV hue thresholding over typical leaf hues
   (green through yellow-brown) unioned with an Otsu threshold on the
   saturation channel, then morphological close/open and largest-connected-
   component selection — isolates the leaf from soil, hands, other leaves,
   etc.
2. **Lesion-vs-healthy-tissue mask**: within the leaf only, Otsu thresholding
   on the Lab color space's `a` (green↔red) channel, unioned with an HSV
   brown/black/yellow lesion-color range, cleaned with morphological
   opening/closing and a minimum-connected-component-area filter.
3. **% infected** = `lesion_pixels / leaf_pixels * 100`, computed only over
   the leaf mask (the biologically meaningful denominator, never counting
   background).

This is genuinely functional today — no training data required — but it is
a heuristic. Accuracy varies with lighting, lesion type (a powdery-mildew
coating segments very differently from rust pustules or a blight patch), and
background clutter. Both the API response and the PDF report disclose the
segmentation backend used, and the PDF footer states plainly when it's the
classical method.

## The upgrade path: training a real `UNetSegmenter`

`app/ml/segmentation/unet_backend.py` implements the exact same
`SegmentationBackend` interface, so switching `SEGMENTATION_BACKEND=unet` in
`.env` is a one-line config change with **no API contract change** — once a
checkpoint exists at `models_store/unet_best.pt` (if it doesn't, `UNetSegmenter`
transparently falls back to the classical pipeline, logging a warning).

`backend/ml_training/train_segmentation.py` trains a small U-Net given a
directory of `images/` + matching `masks/` (0/255 PNGs). Three ways to get
those masks:

1. **Weak/pseudo-masks (free, fastest to start)**: run
   `ClassicalCVSegmenter` over your training images and save its
   `lesion_mask` output as the training target. This is noisy — it inherits
   the heuristic's mistakes — but a CNN trained on it often generalizes
   *better* than the heuristic alone (a form of self-distillation), because
   it learns the underlying visual pattern rather than the exact color
   thresholds.
2. **GrabCut-assisted semi-manual labeling**:
   `ml_training/scripts/label_assist_grabcut.py` is an interactive tool — you
   draw one rectangle around the lesion (and optionally a couple of
   corrective scribbles) per image, and OpenCV's GrabCut algorithm refines
   the rest. Much faster than pixel-painting a mask by hand.
3. **A future labeled dataset**: if you later acquire or hand-label a dataset
   with real lesion masks, point `train_segmentation.py --masks-dir` at it
   directly — no code changes needed.

## Why this isn't hidden

Every layer surfaces the truth: `SegmentationResult.backend_name` is stored
on every `Scan` row (`segmentation_backend` column), returned in the API
response indirectly via the PDF's methodology footnote, and disclosed in the
PDF itself. Nothing about this pipeline claims a trained segmentation model
is running when it isn't.
