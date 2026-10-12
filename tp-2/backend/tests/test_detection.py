import numpy as np
import pytest

from docscan import ContourDetector, DocumentNotFound, order_corners
from test_contract import document, no_document, photo

TOLERANCE_PX = 10


@pytest.fixture
def detector() -> ContourDetector:
    return ContourDetector()


def test_order_corners_from_shuffled_points():
    expected = np.float32([[10, 10], [100, 12], [98, 200], [8, 195]])
    shuffled = expected[[2, 0, 3, 1]]
    np.testing.assert_allclose(order_corners(shuffled), expected)