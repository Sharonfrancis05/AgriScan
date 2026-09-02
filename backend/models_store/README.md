# models_store

Drop trained checkpoints here (this directory is a Docker volume mount, so
files placed here on the host are visible inside the running backend
container without a rebuild):

- `classifier_best.pt` — produced by `ml_training/train_classifier.py`.
  Expected format: `torch.save({"state_dict": model.state_dict(), "model_version": "..."}, path)`.
- `unet_best.pt` — produced by `ml_training/train_segmentation.py`, exported
  as TorchScript (`torch.jit.save`) since `app/ml/segmentation/unet_backend.py`
  loads it with `torch.jit.load`.

If `classifier_best.pt` is absent, the API still runs — it serves
predictions from an ImageNet-pretrained EfficientNet-B0 backbone with an
**untrained** classification head, and reports
`model_status: "pretrained_backbone_untrained_head"` in every response so
this is never mistaken for a real result.

If `unet_best.pt` is absent (expected until masks are available — see
`docs/segmentation_upgrade.md`), segmentation falls back to
`ClassicalCVSegmenter` regardless of `SEGMENTATION_BACKEND`.
