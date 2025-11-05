# tests/test_basic.py
import numpy as np
from ioumatch import iou_matrix_from_labels

def test_iou_matrix():
    # Test simple IoU calculation
    labels_pred = np.array([[0, 1], [0, 0]], dtype=np.uint8)
    labels_gt = np.array([[0, 1], [0, 2]], dtype=np.uint8)

    iou_matrix = iou_matrix_from_labels(labels_pred, labels_gt)
    assert iou_matrix.shape == (1, 2), f"Expected shape (1, 2), got {iou_matrix.shape}"
    assert iou_matrix[0, 0] == 1.0, f"Expected IoU of 1.0, got {iou_matrix[0, 0]}"
    assert iou_matrix[0, 1] == 0.0, f"Expected IoU of 0.0, got {iou_matrix[0, 1]}"
