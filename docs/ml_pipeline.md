# ML Pipeline

## 1. Preprocessing (`app/ml/preprocessing.py`)

OpenCV/Pillow-based: EXIF-orientation correction, aspect-preserving resize
with center padding to 224×224 for the model, and a mild bilateral filter to
reduce phone-camera sensor noise without blurring lesion edges. The same
"display" image (denoised, but not resized/normalized for the model) is
reused for segmentation and the overlay image, so what the user sees matches
what was analyzed.

**Both the resize strategy and the denoise step must match what the
training pipeline did**, or validation accuracy silently stops reflecting
real deployed accuracy. This bit us twice during development, both fixed:
- `ml_training/datasets/leaf_dataset.py`'s validation transform originally
  did a plain (aspect-distorting) square resize while inference did
  aspect-preserving padding — different visual input for the "same" image.
  Fixed by giving both the same `AspectPreservingResize` logic.
- Gray-world white-balance normalization was tried here and removed: on
  images with a large non-neutral background (e.g. the dark photography
  backgrounds common in this dataset), it computes a global per-channel
  color correction from the *whole* frame that overcorrects the actual leaf,
  shifting real leaf-green hues out of the classical segmentation step's
  expected range (confirmed on a real photo: correctly-detected leaf
  coverage dropped from ~48% to ~8%). It was also never applied during
  training, so using it only at inference time was a second, independent
  mismatch. `normalize_gray_world()` is kept in the module as a documented
  cautionary tale, not called by the default pipeline.

## 1b. Leaf-validity / out-of-distribution guard (`app/ml/leaf_validity.py`)

A closed-set softmax classifier has no concept of "not one of my classes" —
it always forces its best guess onto one of the 20 trained labels, even for
an image that isn't a leaf at all. Two heuristic signals combine into a
`prediction_warning` surfaced through the API, UI, and PDF:
1. **Leaf coverage** from the classical-CV leaf mask — catches clear
   non-leaf input (a solid color, a mostly-blank frame).
2. **Classifier top-1 confidence** — catches cases where the model itself is
   unsure.

**Honest limitation**: this reliably catches obvious non-leaf input (flat
colors, blank frames) but is *not* a complete defense. Tested against
JPEG-compressed random noise: the compression's block-based quantization
smooths independent per-pixel noise into a spatially-correlated, blurrier
pattern that can survive the leaf-coverage check, and EfficientNet-B0 (like
most deep classifiers) is frequently *overconfident* on out-of-distribution
input rather than uncertain — a well-known, unsolved-in-general problem for
softmax classifiers, not something a confidence threshold alone fixes. A
materially more robust defense would need a dedicated learned "is this a
leaf" detector (e.g. trained with real non-leaf negative examples) or a
proper OOD technique (feature-space distance from training-class centroids,
an energy-based score, etc.) — out of scope for this pass, noted here as the
concrete next step if this matters for your use case.

## 2. Species + disease classification (`app/ml/classifier.py`)

One flat **EfficientNet-B0** transfer-learning classifier predicts a single
combined `crop___disease` label (e.g. `Tomato___Late_blight`), which is split
into a species string and a disease string for display. This is simpler and
more robust than two separate models (a species model + a per-species disease
model), since disease names aren't comparable across crops anyway, and it
matches how public leaf-disease datasets are natively labeled.

**Model status transparency:** if no fine-tuned checkpoint exists at
`MODEL_CHECKPOINT_PATH` (default `models_store/classifier_best.pt`), the app
still runs — it serves predictions from the ImageNet-pretrained backbone with
an **untrained** classification head, and every API response / PDF report
carries `model_status: "pretrained_backbone_untrained_head"` plus a visible
banner in the UI. This is never silently upgraded to look more accurate than
it is. See `docs/setup_dev.md` for how to produce a real checkpoint.

## 3. Segmentation + % infected area (`app/ml/segmentation/`)

See **`docs/segmentation_upgrade.md`** for the full reasoning. Summary: the
default `ClassicalCVSegmenter` uses HSV/Lab color-space thresholding (not a
trained model) to find the leaf, find the lesion within it, and compute
`lesion_pixels / leaf_pixels * 100`. A `UNetSegmenter` implements the same
interface and is used automatically once a checkpoint exists at
`models_store/unet_best.pt` and `SEGMENTATION_BACKEND=unet`.

## 4. Severity classification (`app/ml/severity.py`)

A single tunable table, in the spirit of common agronomic severity scales:

| Severity | % Infected Leaf Area |
|---|---|
| Healthy | 0 – 2% |
| Mild | 2 – 10% |
| Moderate | 10 – 25% |
| Severe | 25 – 50% |
| Critical | > 50% |

## 5. Recommendations (`app/services/recommendation_service.py`)

Looks up `disease_code` in the `diseases_reference` table (seeded from
`app/db/fixtures/diseases_reference_seed.json`) for treatment/prevention
text, and prepends an urgency note when severity is Severe or Critical.

## 6. Composition

All of the above is composed in `app/services/inference_service.py`'s
`InferenceService.run_inference` — the one function the API layer calls
through. See `docs/architecture.md` for the full request flow.

## Training scripts (`backend/ml_training/`)

Written for you to run yourself (not executed automatically):

1. `prepare_dataset.py` — filters your uploaded dataset down to the 6
   supported crops (Apple, Grape, Corn, Tomato, Strawberry, Peach) and
   stratified-samples to ~3000-5000 images; writes the authoritative label
   list to `app/ml/labels_generated.json`.
2. `train_classifier.py` — transfer-learning fine-tune (EfficientNet-B0 or
   MobileNetV3-Small), saves the best checkpoint by validation accuracy to
   `models_store/classifier_best.pt`.
3. `evaluate.py` — per-class precision/recall/F1 + a confusion matrix image.
4. `export_to_onnx.py` — ONNX export for lighter-weight/mobile inference.
5. `train_segmentation.py` + `scripts/label_assist_grabcut.py` — the staged
   U-Net upgrade path once lesion masks exist (see
   `docs/segmentation_upgrade.md`).
