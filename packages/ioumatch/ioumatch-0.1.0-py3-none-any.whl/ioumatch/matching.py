import numpy as np


def match_greedy(iou: np.ndarray, threshold: float = 0.5, inclusive: bool = False) -> int:
    """
    # Overview
    This function implements a **greedy one-to-one matching** algorithm, where the most significant remaining
    Intersection over Union (IoU) value is selected as the match for a predicted object and a ground truth object.
    It then marks the corresponding row and column to prevent reuse, and repeats this process until no valid matches
    (IoU > threshold) remain.

    The algorithm stops when all predictions are matched or when no valid matches exceed the threshold.

    # Parameters:
    - `iou` (np.ndarray): A 2D IoU matrix (shape: `(num_pred_objects, num_gt_objects)`). The IoU matrix holds the
      pairwise IoU values between predicted and ground truth objects.
    - `threshold` (float): The IoU threshold above which a match is considered valid. Default is `0.5`.
    - `inclusive` (bool): If `True`, it considers IoU values **equal to** the threshold as valid matches.
      If `False`, only values strictly **greater** than the threshold are considered valid.

    # Returns:
    - `tp` (int): The number of true positive matches found during the matching process.

    # Example:
    ```python
    iou_matrix = np.array([[0.9, 0.1], [0.2, 0.7]])
    tp = match_greedy(iou_matrix, threshold=0.5)
    print(tp)  # Output: 2
    ```

    # Notes:
    - The greedy approach prioritizes the largest IoU for each match but does not guarantee optimal global matching.
    - Once an object is matched, it is excluded from further matching by setting the corresponding row and column in the matrix to `-1`.

    # Limitations:
    - The greedy algorithm might not always yield the optimal solution for large numbers of objects, especially when IoU values are close to each other.
    """
    if iou.size == 0:
        return 0
    M = iou.copy().astype(float)
    tp = 0

    def stop(v):
        return (v < threshold) if inclusive else (v <= threshold)

    while True:
        best = -1.0
        bi = -1
        bj = -1
        for i in range(M.shape[0]):
            for j in range(M.shape[1]):
                if M[i, j] > best:
                    best = M[i, j]
                    bi = i
                    bj = j

        if stop(best):
            break
        tp += 1

        # Mark the corresponding row and column as used
        for jj in range(M.shape[1]):
            M[bi, jj] = -1.0
        for ii in range(M.shape[0]):
            M[ii, bj] = -1.0

    return tp


def match_hungarian(iou: np.ndarray, threshold: float = 0.5, inclusive: bool = False) -> int:
    """
    # Overview
    This function implements the **Hungarian algorithm** for optimal one-to-one object matching.
    It solves the assignment problem by minimizing the cost (in this case, maximizing IoU) across all object pairs.
    If **SciPy** is installed, it will use the `linear_sum_assignment` function to find the optimal matching.

    If **SciPy** is not available, the function falls back to the greedy matching algorithm (`match_greedy`).

    # Parameters:
    - `iou` (np.ndarray): A 2D IoU matrix (shape: `(num_pred_objects, num_gt_objects)`) where each element represents
      the IoU between a predicted object and a ground truth object.
    - `threshold` (float): The IoU threshold above which a match is considered valid. Default is `0.5`.
    - `inclusive` (bool): If `True`, it considers IoU values **equal to** the threshold as valid matches.
      If `False`, only values strictly **greater** than the threshold are considered valid.

    # Returns:
    - `tp` (int): The number of true positive matches found by the Hungarian algorithm.

    # Example:
    ```python
    iou_matrix = np.array([[0.9, 0.1], [0.2, 0.7]])
    tp = match_hungarian(iou_matrix, threshold=0.5)
    print(tp)  # Output: 2
    ```

    # Notes:
    - The Hungarian algorithm ensures an **optimal solution**, but it is computationally more expensive than the greedy method.
    - The algorithm uses **SciPy**'s `linear_sum_assignment` if available, otherwise, it falls back to the greedy approach.

    # Limitations:
    - SciPy must be installed for the optimal Hungarian matching to work. If it's not available, the function defaults to greedy matching.
    """
    if iou.size == 0:
        return 0

    try:
        from scipy.optimize import linear_sum_assignment
    except Exception:
        # Fallback to greedy if SciPy is not available
        return match_greedy(iou, threshold, inclusive)

    # Convert IoU matrix into cost matrix (1.0 - IoU)
    cost = 1.0 - iou
    # Mask out the pairs with IoU less than the threshold
    mask = (iou < threshold) if inclusive else (iou <= threshold)

    cost = cost.copy()
    cost[mask] = 1e6  # Assign a high cost to invalid pairs

    # Solve the assignment problem using the Hungarian method
    r, c = linear_sum_assignment(cost)

    # Select the IoU values corresponding to the optimal assignment
    selected = iou[r, c]
    # Check if the selected IoU values are valid (>= threshold)
    ok = (selected >= threshold) if inclusive else (selected > threshold)

    return int(ok.sum())
