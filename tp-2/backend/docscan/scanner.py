import numpy as np
from docscan.filters import build_filters


class Scanner:
    """Orquestador temporal/base del core docscan."""

    def scan(
        self,
        image: np.ndarray,
        color_mode: str = "color",
        color_correction: bool = True,
        soften_colors: float = 0.0,
    ) -> tuple[np.ndarray, list[list[float]]]:
        # Por ahora aplica el pipeline de filtros directamente sobre la imagen
        pipeline = build_filters(
            color_mode=color_mode,
            color_correction=color_correction,
            soften_colors=soften_colors,
        )
        final_image = pipeline.apply(image)

        h, w = image.shape[:2]
        # Esquinas por defecto (las 4 esquinas de la foto)
        corners = [[0.0, 0.0], [float(w), 0.0], [float(w), float(h)], [0.0, float(h)]]

        return final_image, corners