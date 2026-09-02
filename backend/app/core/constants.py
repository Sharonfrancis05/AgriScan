"""Project-wide constants that are cheap facts, not configuration."""

SUPPORTED_CROPS = ["Apple", "Grape", "Corn", "Tomato", "Strawberry", "Peach"]

SEVERITY_LEVELS = ["Healthy", "Mild", "Moderate", "Severe", "Critical"]

MODEL_INPUT_SIZE = 224  # square input, EfficientNet-B0 default
IMAGENET_MEAN = [0.485, 0.456, 0.406]
IMAGENET_STD = [0.229, 0.224, 0.225]
