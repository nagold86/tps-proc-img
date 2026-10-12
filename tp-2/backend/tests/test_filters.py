import numpy as np
import pytest
from docscan.filters import (
    BlackAndWhiteFilter,
    ColorCorrectionFilter,
    GrayscaleFilter,
    SoftenColorsFilter,
    build_filters,
)


def test_grayscale_filter_dimensions():
    # Imagen de 10x10 en BGR (3 canales)
    img_bgr = np.full((10, 10, 3), 128, dtype=np.uint8)
    gray = GrayscaleFilter().apply(img_bgr)

    assert gray.ndim == 2
    assert gray.shape == (10, 10)


def test_black_and_white_only_zeros_and_255():
    # Imagen con degradé de grises
    img = np.tile(np.linspace(0, 255, 100, dtype=np.uint8), (100, 1))
    bw = BlackAndWhiteFilter(block_size=15, c=5).apply(img)

    assert bw.ndim == 2
    unique_vals = np.unique(bw)
    # Solo deben existir los valores 0 y 255
    assert set(unique_vals).issubset({0, 255})


def test_soften_colors_preserves_black_white_and_dark_ink():
    # Imagen de 1x4 píxeles: Negro, Blanco, Gris neutro, Azul oscuro (tinta de lapicera)
    pixels = np.array([
        [[0, 0, 0], [255, 255, 255], [128, 128, 128], [120, 20, 20]]
    ], dtype=np.uint8)

    filt = SoftenColorsFilter(factor=0.8)
    res = filt.apply(pixels)

    # Negro, blanco y gris neutro no deben cambiar
    np.testing.assert_array_equal(res[0, 0], [0, 0, 0])
    np.testing.assert_array_equal(res[0, 1], [255, 255, 255])
    np.testing.assert_array_equal(res[0, 2], [128, 128, 128])
    # Tinta azul oscura (V bajo) apenas debe sufrir cambios
    assert res[0, 3, 0] <= 135


def test_soften_colors_softens_bright_saturated_color():
    # Parche amarillo muy saturado y brillante (B=0, G=255, R=255)
    yellow = np.array([[[0, 255, 255]]], dtype=np.uint8)
    softened = SoftenColorsFilter(factor=1.0).apply(yellow)

    # El canal azul (B) debió elevarse significativamente hacia el blanco
    assert softened[0, 0, 0] > 180
    assert softened[0, 0, 1] == 255
    assert softened[0, 0, 2] == 255


def test_color_correction_removes_yellow_tint():
    # Fondo con tinte cálido/amarillento: azul deprimido (B=180, G=230, R=240)
    tinted = np.full((50, 50, 3), [180, 230, 240], dtype=np.uint8)
    corrected = ColorCorrectionFilter().apply(tinted)

    # Todos los canales deben aproximarse al blanco neutro (~255)
    assert corrected[:, :, 0].mean() >= 250
    assert corrected[:, :, 1].mean() >= 250
    assert corrected[:, :, 2].mean() >= 250


def test_filter_pipeline_execution():
    img = np.full((20, 20, 3), 200, dtype=np.uint8)
    pipeline = build_filters(color_mode="bw", color_correction=True, soften_colors=0.5)
    output = pipeline.apply(img)

    assert output.ndim == 2
    assert set(np.unique(output)).issubset({0, 255})