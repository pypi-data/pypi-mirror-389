import numpy as np
from .utils import get_ids


def iou_matrix_from_labels(labels_pred: np.ndarray, labels_gt: np.ndarray) -> np.ndarray:
    """
    # Overview
    Computes the Intersection over Union (IoU) matrix between predicted and ground truth labels.
    Each row of the matrix represents a predicted object, and each column represents a ground truth object.

    This function works by comparing predicted labels (`labels_pred`) against the ground truth labels (`labels_gt`),
    calculating the IoU for each pair of predicted and ground truth objects. The resulting IoU matrix has dimensions
    (number of predicted objects x number of ground truth objects), where each element in the matrix represents the
    IoU for a specific predicted object and a specific ground truth object.

    **Note:** This function expects 2D images (arrays) with integer labels, where `0` represents the background.

    # Parameters:
    - `labels_pred` (np.ndarray): 2D array of predicted labels (e.g., binary or integer label matrix).
        The shape of this array must be `(H, W)`, where `H` is the height and `W` is the width of the image.
        Each unique label represents a different predicted object (background should be labeled as 0).
    - `labels_gt` (np.ndarray): 2D array of ground truth labels (e.g., binary or integer label matrix).
        The shape of this array must be `(H, W)`, where `H` is the height and `W` is the width of the image.
        Each unique label represents a different ground truth object (background should be labeled as 0).

    # Returns:
    - `iou_matrix` (np.ndarray): A 2D matrix of IoU values, where each element represents the IoU between a
        predicted object and a ground truth object. The matrix has shape `(num_pred_objects, num_gt_objects)`.
        Each row corresponds to a predicted object, and each column corresponds to a ground truth object.

    # Example:
    ```python
    import numpy as np
    from ioumatch import iou_matrix_from_labels

    # Example predicted and ground truth labels
    labels_pred = np.array([[0, 1, 1], [0, 0, 1], [0, 0, 0]], dtype=np.uint8)
    labels_gt = np.array([[0, 1, 2], [0, 0, 0], [0, 0, 2]], dtype=np.uint8)

    iou_matrix = iou_matrix_from_labels(labels_pred, labels_gt)
    print(iou_matrix)
    ```

    # Notes:
    - The background (`0` label) is ignored when computing IoU.
    - If no object is detected in the predicted or ground truth image, the IoU will be set to `0` for the corresponding pair.

    # Limitations:
    - The function assumes that both `labels_pred` and `labels_gt` have the same shape.
    - Only integer labels are supported. If using binary masks, it is expected that the background is labeled as `0`.
    """

    # Get unique IDs for predicted and ground truth objects (excluding background label 0)
    pred_ids = get_ids(labels_pred)
    gt_ids = get_ids(labels_gt)

    # Initialize an empty matrix to store IoU values
    M = np.zeros((len(pred_ids), len(gt_ids)), dtype=np.float64)

    # Loop over all predicted and ground truth objects to calculate IoU
    for i, pid in enumerate(pred_ids):
        p = (labels_pred == pid)  # Binary mask for the predicted object
        for j, gid in enumerate(gt_ids):
            g = (labels_gt == gid)  # Binary mask for the ground truth object
            inter = np.logical_and(p, g).sum()  # Intersection (number of overlapping pixels)
            uni = np.logical_or(p, g).sum()  # Union (total number of pixels in either object)
            M[i, j] = (inter / uni) if uni > 0 else 0.0  # IoU calculation (intersection over union)

    return M
