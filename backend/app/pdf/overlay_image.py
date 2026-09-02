"""Builds the disease-highlighted overlay image, reused by both the API's
overlay_image_url response field and the PDF report.
"""
import cv2
import numpy as np

_CONTOUR_COLOR_BGR = (35, 55, 226)  # a strong red-orange, drawn in BGR for OpenCV
_FILL_ALPHA = 0.35


def build_overlay(rgb_image: np.ndarray, lesion_mask: np.ndarray) -> np.ndarray:
    """Returns an RGB image with lesion regions outlined and translucently filled."""
    bgr = cv2.cvtColor(rgb_image, cv2.COLOR_RGB2BGR).copy()
    mask_u8 = lesion_mask.astype(np.uint8) * 255

    fill_layer = bgr.copy()
    fill_layer[lesion_mask] = _CONTOUR_COLOR_BGR
    blended = cv2.addWeighted(fill_layer, _FILL_ALPHA, bgr, 1 - _FILL_ALPHA, 0)

    contours, _ = cv2.findContours(mask_u8, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    cv2.drawContours(blended, contours, -1, _CONTOUR_COLOR_BGR, thickness=2)

    return cv2.cvtColor(blended, cv2.COLOR_BGR2RGB)
