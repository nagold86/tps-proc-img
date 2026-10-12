import cv2
import numpy as np


class PerspectiveCorrector:
    def correct(
        self,
        image: np.ndarray,
        corners: np.ndarray,
    ) -> np.ndarray:
        top_left, top_right, bottom_right, bottom_left = corners

        width = round(max(
            np.linalg.norm(top_right - top_left),
            np.linalg.norm(bottom_right - bottom_left),
        ))
        height = round(max(
            np.linalg.norm(bottom_left - top_left),
            np.linalg.norm(bottom_right - top_right),
        ))

        destination = np.array(
            [
                [0, 0],
                [width - 1, 0],
                [width - 1, height - 1],
                [0, height - 1],
            ],
            dtype=np.float32,
        )

        transform = cv2.getPerspectiveTransform(
            corners.astype(np.float32),
            destination,
        )

        return cv2.warpPerspective(image, transform, (width, height))