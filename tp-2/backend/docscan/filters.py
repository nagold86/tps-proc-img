from abc import ABC, abstractmethod
from typing import Sequence
import cv2
import numpy as np

class Filter(ABC):
    """Interfaz base para todas las transformaciones de imagen."""

    @abstractmethod
    def apply(self, image: np.ndarray) -> np.ndarray:
        """Aplica la mejora sobre una imagen (en formato BGR o escala de grises de OpenCV).
        
        Retorna la imagen transformada.
        """
        pass

class ColorCorrectionFilter(Filter):
    """Corrige la dominante de color estirando cada canal hacia el blanco."""

    def __init__(self, percentile: float = 99.0):
        self.percentile = percentile

    def apply(self, image: np.ndarray) -> np.ndarray:
        # Si la imagen ya es monocromática (1 canal), no hay canales de color que balancear
        if image.ndim == 2:
            return image

        result = np.empty_like(image, dtype=np.float32)

        # Se procesa cada canal (B, G, R) de forma independiente
        for c in range(3):
            channel = image[:, :, c].astype(np.float32)
            high_val = np.percentile(channel, self.percentile)
            
            # Evitar división por cero si la imagen es completamente negra
            if high_val > 0:
                scale = 255.0 / high_val
                result[:, :, c] = np.clip(channel * scale, 0, 255)
            else:
                result[:, :, c] = channel

        return result.astype(np.uint8)

class SoftenColorsFilter(Filter):
    """Aclara colores altamente saturados y brillantes (resaltadores, sellos) hacia el blanco."""

    def __init__(self, factor: float = 0.0):
        self.factor = float(np.clip(factor, 0.0, 1.0))

    def apply(self, image: np.ndarray) -> np.ndarray:
        if self.factor <= 0.0 or image.ndim == 2:
            return image

        # Convertir a HSV para evaluar saturación y brillo
        hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV).astype(np.float32)
        s = hsv[:, :, 1] / 255.0  # [0, 1]
        v = hsv[:, :, 2] / 255.0  # [0, 1]

        # Usar v**3 para suprimir fuertemente tintas oscuras (v < 0.5)
        # conservando el efecto en resaltadores luminosos (v cerca de 1.0)
        weight = (s * (v ** 3) * self.factor)[:, :, np.newaxis]

        # Interpolación hacia el blanco puro (255)
        img_float = image.astype(np.float32)
        softened = img_float * (1.0 - weight) + 255.0 * weight

        return np.clip(softened, 0, 255).astype(np.uint8)

class GrayscaleFilter(Filter):
    """Convierte la imagen a escala de grises (1 solo canal)."""

    def apply(self, image: np.ndarray) -> np.ndarray:
        if image.ndim == 2:
            return image
        return cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)


class BlackAndWhiteFilter(Filter):
    """Convierte a blanco y negro puro (valores 0 y 255) mediante umbral adaptativo."""

    def __init__(self, block_size: int = 21, c: int = 10):
        # block_size debe ser impar y mayor a 1 para adaptiveThreshold
        self.block_size = block_size if block_size % 2 != 0 else block_size + 1
        self.c = c

    def apply(self, image: np.ndarray) -> np.ndarray:
        # Si viene en BGR, primero la pasamos a escala de grises
        gray = image if image.ndim == 2 else cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

        # Umbral adaptativo: calcula el umbral localmente para cada píxel
        bw = cv2.adaptiveThreshold(
            gray,
            maxValue=255,
            adaptiveMethod=cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            thresholdType=cv2.THRESH_BINARY,
            blockSize=self.block_size,
            C=self.c,
        )
        return bw



class FilterPipeline:
    """Aplica una secuencia de filtros de manera secuencial y polimórfica."""

    def __init__(self, filters: Sequence[Filter]):
        self._filters = list(filters)

    def apply(self, image: np.ndarray) -> np.ndarray:
        result = image
        for f in self._filters:
            result = f.apply(result)
        return result


def build_filters(
    color_mode: str = "color",
    color_correction: bool = True,
    soften_colors: float = 0.0,
) -> FilterPipeline:
    """Construye el pipeline de mejoras en el orden exacto especificado por el enunciado."""
    pipeline_filters = []

    # 1. Corrección de color
    if color_correction:
        pipeline_filters.append(ColorCorrectionFilter())

    # 2. Aclarado de colores fuertes
    if soften_colors > 0.0:
        pipeline_filters.append(SoftenColorsFilter(factor=soften_colors))

    # 3. Modo de color final
    if color_mode == "grayscale":
        pipeline_filters.append(GrayscaleFilter())
    elif color_mode == "bw":
        pipeline_filters.append(BlackAndWhiteFilter())

    return FilterPipeline(pipeline_filters)

