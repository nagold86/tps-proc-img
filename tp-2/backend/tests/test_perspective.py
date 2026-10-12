import numpy as np

from docscan.perspective import PerspectiveCorrector


def test_correct_returns_rectangle_with_expected_size():
    image = np.zeros((300, 400, 3), dtype=np.uint8)
    corners = np.array(
        [
            [80, 60],
            [319, 60],
            [319, 239],
            [80, 239],
        ],
        dtype=np.float32,
    )

    result = PerspectiveCorrector().correct(image, corners)

    assert result.shape == (179, 239, 3)