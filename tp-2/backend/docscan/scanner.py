from dataclasses import dataclass
from typing import Iterator
import numpy as np

from docscan.detection import ContourDetector, Detector, order_corners
from docscan.filters import build_filters
from docscan.perspective import PerspectiveCorrector


@dataclass
class ScanResult:
    image: np.ndarray
    corners: list[list[float]]

    # Permite desempaquetar: scanned_image, corners = scanner.scan(...)
    def __iter__(self) -> Iterator:
        yield self.image
        yield self.corners


class Scanner:
    """Orquestador central del core docscan."""

    def __init__(
        self,
        detector: Detector | None = None,
        corrector: PerspectiveCorrector | None = None,
    ) -> None:
        self.detector = detector or ContourDetector()
        self.corrector = corrector or PerspectiveCorrector()

    def scan(
        self,
        image: np.ndarray,
        corners: list[list[float]] | np.ndarray | None = None,
        color_mode: str = "color",
        color_correction: bool = True,
        soften_colors: float = 0.0,
    ) -> ScanResult:
        # 1. Si no hay esquinas, detectar (si no halla doc, lanza DocumentNotFound)
        if corners is None:
            corners_arr = self.detector.detect(image)
        else:
            corners_arr = order_corners(np.asarray(corners, dtype=np.float32))

        # 2. Corrección de perspectiva con la clase del proyecto
        warped_image = self.corrector.correct(image, corners_arr)

        # 3. Pipeline de filtros (Facundo)
        pipeline = build_filters(
            color_mode=color_mode,
            color_correction=color_correction,
            soften_colors=soften_colors,
        )
        scanned_image = pipeline.apply(warped_image)

        return ScanResult(image=scanned_image, corners=corners_arr.tolist())