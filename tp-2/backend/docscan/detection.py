"""
Document detection: finds the four corners of a sheet of paper in a photo.
"""

from abc import ABC, abstractmethod

import cv2
import numpy as np

from docscan.exceptions import DocumentNotFound


def order_corners(points: np.ndarray) -> np.ndarray:
    """
    Orders 4 points as top-left, top-right, bottom-right, bottom-left.

    Top-left has the smallest x + y, bottom-right the largest;
    y - x separates top-right (smallest) from bottom-left (largest).
    """
    pts = np.asarray(points, dtype=np.float32).reshape(4, 2)
    sums = pts.sum(axis=1)                # x + y of each point
    diffs = np.diff(pts, axis=1).ravel()  # y - x of each point

    return np.array([
        pts[np.argmin(sums)],   # top-left: smallest x + y
        pts[np.argmin(diffs)],  # top-right: smallest y - x
        pts[np.argmax(sums)],   # bottom-right: largest x + y
        pts[np.argmax(diffs)],  # bottom-left: largest y - x
    ], dtype=np.float32)


class Detector(ABC):
    """Common interface: any detection algorithm returns ordered corners."""

    @abstractmethod
    def detect(self, image: np.ndarray) -> np.ndarray:
        """BGR image → (4, 2) float32 corners (TL, TR, BR, BL). Raises DocumentNotFound."""


class ContourDetector(Detector):
    """Edges + contours + polygonal approximation."""

    def __init__(
        self,
        work_size: int = 600,          # longest side of the reduced copy
        min_area_ratio: float = 0.15,  # rule of the assignment
        blur_kernel: int = 5,          # odd
        canny_sigma: float = 0.33,     # auto-Canny (Unidad 5, 2.2)
        morph_kernel: int = 5,         # closing of edge gaps (Unidad 2, 4)
        approx_epsilon: float = 0.02,  # fraction of the perimeter
        max_candidates: int = 5,       # largest contours to try
    ) -> None:
        self.work_size = work_size
        self.min_area_ratio = min_area_ratio
        self.blur_kernel = blur_kernel
        self.canny_sigma = canny_sigma
        self.morph_kernel = morph_kernel
        self.approx_epsilon = approx_epsilon
        self.max_candidates = max_candidates

    # --- public API -------------------------------------------------------
    def detect(self, image: np.ndarray) -> np.ndarray:
        small, scale = self._resize(image)
        gray = self._preprocess(small)
        min_area = self.min_area_ratio * small.shape[0] * small.shape[1]

        for mask in self._candidate_masks(gray):
            quad = self._find_quadrilateral(mask, min_area)
            if quad is not None:
                return order_corners(quad / scale)
        raise DocumentNotFound()

    # --- steps (each one small and testable) ------------------------------
    def _resize(self, image: np.ndarray) -> tuple[np.ndarray, float]:
        height, width = image.shape[:2]
        scale = min(1.0, self.work_size / max(height, width))
        if scale == 1.0:
            return image, scale
        size = (round(width * scale), round(height * scale))
        return cv2.resize(image, size, interpolation=cv2.INTER_AREA), scale

    def _preprocess(self, image: np.ndarray) -> np.ndarray:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        return cv2.GaussianBlur(gray, (self.blur_kernel, self.blur_kernel), 0)

    def _candidate_masks(self, gray: np.ndarray):
        """Yields binary images to look for the document in, best first."""
        yield self._edges(gray)
        # Optional improvement (enunciado): yield an Otsu mask as a 2nd attempt.

    def _edges(self, gray: np.ndarray) -> np.ndarray:
        median = float(np.median(gray))
        low = int(max(0, (1 - self.canny_sigma) * median))
        high = int(min(255, (1 + self.canny_sigma) * median))
        edges = cv2.Canny(gray, low, high)
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (self.morph_kernel, self.morph_kernel))
        return cv2.morphologyEx(edges, cv2.MORPH_CLOSE, kernel)

    def _find_quadrilateral(self, mask: np.ndarray, min_area: float) -> np.ndarray | None:
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        largest = sorted(contours, key=cv2.contourArea, reverse=True)[: self.max_candidates]
        for contour in largest:
            if cv2.contourArea(contour) < min_area:
                return None
            perimeter = cv2.arcLength(contour, True)
            polygon = cv2.approxPolyDP(contour, self.approx_epsilon * perimeter, True)
            if len(polygon) == 4 and cv2.isContourConvex(polygon):
                return polygon.reshape(4, 2).astype(np.float32)
        return None