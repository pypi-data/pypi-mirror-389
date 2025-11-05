import glob
import numpy as np
from .utils import to_instance_labels, read_gray
from .iou import iou_matrix_from_labels
from .matching import match_greedy, match_hungarian

def evaluate_image(labels_pred: np.ndarray,
                   labels_gt:   np.ndarray,
                   threshold:   float = 0.5,
                   method:      str   = "greedy",
                   inclusive:   bool  = False,
                   normalize:   bool  = True):
    """
    # Overview
    Evaluates an image by comparing predicted labels against ground truth labels using Intersection over Union (IoU).
    This function computes the True Positives (TP), False Positives (FP), False Negatives (FN), and F1-score based
    on IoU matching. It also returns the IoU matrix for detailed analysis of the object-level matching between
    predicted and ground truth labels.

    # Parameters:
    - `labels_pred` (np.ndarray): 2D array of predicted labels (e.g., binary or integer label matrix).
      It represents the predicted objects in the image.
    - `labels_gt` (np.ndarray): 2D array of ground truth labels (e.g., binary or integer label matrix).
      It represents the actual objects in the image.
    - `threshold` (float): The IoU threshold above which a match is considered valid. Default is `0.5`.
    - `method` (str): The matching method used. `"greedy"` uses a simple greedy matching algorithm,
      while `"hungarian"` uses the optimal Hungarian algorithm (if SciPy is installed).
    - `inclusive` (bool): If `True`, considers IoU values equal to the threshold as valid matches.
      If `False`, only values strictly greater than the threshold are considered valid.
    - `normalize` (bool): If `True`, automatically converts binary masks into instance labels (objects with unique IDs).
      If `False`, assumes that labels are already in integer format (instance labels).

    # Returns:
    - A dictionary with:
        - `tp`: The number of true positives (valid matches).
        - `fp`: The number of false positives (predictions without matches).
        - `fn`: The number of false negatives (ground truth objects without matches).
        - `f1`: The F1-score, calculated as `2 * tp / (2 * tp + fp + fn)`.
        - `iou_matrix`: A 2D array representing the IoU matrix for each predicted object vs ground truth object.

    # Example:
    ```python
    import numpy as np
    from ioumatch import evaluate_image

    labels_pred = np.array([[0, 1, 1], [0, 0, 1], [0, 0, 0]], dtype=np.uint8)
    labels_gt = np.array([[0, 1, 2], [0, 0, 0], [0, 0, 2]], dtype=np.uint8)

    res = evaluate_image(labels_pred, labels_gt, threshold=0.5)
    print(res)
    ```

    # Notes:
    - **IoU (Intersection over Union)** is computed for each predicted object and ground truth object.
    - The **F1-score** is computed based on the IoU threshold.
    - **True Positives** are matched using the greedy or Hungarian method depending on the `method` parameter.

    # Limitations:
    - Assumes the background is labeled as `0` in both `labels_pred` and `labels_gt`.
    """
    if normalize:
        labels_pred = to_instance_labels(labels_pred)
        labels_gt = to_instance_labels(labels_gt)
    else:
        labels_pred = labels_pred.astype(np.int32)
        labels_gt = labels_gt.astype(np.int32)

    M = iou_matrix_from_labels(labels_pred, labels_gt)

    nb_pred = max(len(np.unique(labels_pred)) - 1, 0)
    nb_gt = max(len(np.unique(labels_gt)) - 1, 0)

    if method == "hungarian":
        tp = match_hungarian(M, threshold, inclusive)
    else:
        tp = match_greedy(M, threshold, inclusive)

    fp = nb_pred - tp
    fn = nb_gt - tp

    den = 2 * tp + fp + fn
    f1 = (2 * tp / den) if den > 0 else 0.0
    return {"tp": int(tp), "fp": int(fp), "fn": int(fn), "f1": float(f1), "iou_matrix": M}

def evaluate_paths(pred_path: str,
                   gt_path:   str,
                   threshold: float = 0.5,
                   method:    str   = "greedy",
                   inclusive: bool  = False,
                   normalize: bool  = True):
    """
    # Overview
    This function reads two image files (predicted mask and ground truth mask) from the provided paths and
    then calls the `evaluate_image` function to calculate TP, FP, FN, and F1-score.

    # Parameters:
    - `pred_path` (str): The file path to the predicted mask image.
    - `gt_path` (str): The file path to the ground truth mask image.
    - `threshold` (float): The IoU threshold above which a match is considered valid. Default is `0.5`.
    - `method` (str): The matching method used. `"greedy"` uses a simple greedy matching algorithm,
      while `"hungarian"` uses the optimal Hungarian algorithm (if SciPy is installed).
    - `inclusive` (bool): If `True`, considers IoU values equal to the threshold as valid matches.
      If `False`, only values strictly greater than the threshold are considered valid.
    - `normalize` (bool): If `True`, automatically converts binary masks into instance labels (objects with unique IDs).
      If `False`, assumes that labels are already in integer format (instance labels).

    # Returns:
    - The result of the `evaluate_image` function, which includes `tp`, `fp`, `fn`, `f1`, and `iou_matrix`.

    # Example:
    ```python
    result = evaluate_paths("pred_masks/img_01.png", "gt_masks/img_01.png", threshold=0.5)
    print(result)
    ```

    # Notes:
    - The paths to the predicted and ground truth images must exist and be in a compatible format (e.g., PNG, TIFF).
    """
    pred = read_gray(pred_path)
    gt = read_gray(gt_path)
    if pred.shape != gt.shape:
        raise ValueError(f"Different sizes: {pred.shape} vs {gt.shape}")
    return evaluate_image(pred, gt, threshold, method, inclusive, normalize)

def evaluate_pairs(pred_glob: str,
                   gt_glob:   str,
                   threshold: float = 0.5,
                   method:    str   = "greedy",
                   inclusive: bool  = False,
                   normalize: bool  = True):
    """
    # Overview
    This function evaluates a batch of images by matching files based on sorted glob patterns.
    It processes the images in pairs, compares the predicted masks to the ground truth masks, and returns
    aggregated results (TP, FP, FN, F1-score). It also returns a detailed result for each image.

    # Parameters:
    - `pred_glob` (str): The glob pattern for predicted mask images (e.g., 'preds/*.png').
    - `gt_glob` (str): The glob pattern for ground truth mask images (e.g., 'gts/*.png').
    - `threshold` (float): The IoU threshold above which a match is considered valid. Default is `0.5`.
    - `method` (str): The matching method used. `"greedy"` uses a simple greedy matching algorithm,
      while `"hungarian"` uses the optimal Hungarian algorithm (if SciPy is installed).
    - `inclusive` (bool): If `True`, considers IoU values equal to the threshold as valid matches.
      If `False`, only values strictly greater than the threshold are considered valid.
    - `normalize` (bool): If `True`, automatically converts binary masks into instance labels (objects with unique IDs).
      If `False`, assumes that labels are already in integer format (instance labels).

    # Returns:
    - A tuple containing:
        - `aggregated_results`: A dictionary with aggregated TP, FP, FN, F1, and total IoU matrix.
        - `per_image_results`: A list of tuples, where each tuple contains the paths to the predicted and ground truth images,
          along with the evaluation results for that pair.

    # Example:
    ```python
    aggregated, per_image = evaluate_pairs("pred_masks/*.png", "gt_masks/*.png", threshold=0.5)
    print(aggregated)
    ```

    # Notes:
    - The glob patterns should match corresponding predicted and ground truth images in the same order.
    - The evaluation results for each image pair are stored in the `per_image_results`.
    """
    pred_list = sorted(glob.glob(pred_glob))
    gt_list = sorted(glob.glob(gt_glob))
    if not pred_list or not gt_list or len(pred_list) != len(gt_list):
        raise ValueError("Empty or mismatched file lists.")

    agg_tp = agg_fp = agg_fn = 0
    per_image = []
    for p, g in zip(pred_list, gt_list):
        res = evaluate_paths(p, g, threshold, method, inclusive, normalize)
        agg_tp += res["tp"]
        agg_fp += res["fp"]
        agg_fn += res["fn"]
        per_image.append((p, g, res))

    den = 2 * agg_tp + agg_fp + agg_fn
    f1 = (2 * agg_tp / den) if den > 0 else 0.0
    return {"tp": int(agg_tp), "fp": int(agg_fp), "fn": int(agg_fn), "f1": float(f1)}, per_image
