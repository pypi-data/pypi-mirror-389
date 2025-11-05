import numpy as np

try:
    import cv2  # optional
    _HAS_CV2 = True
except Exception:
    _HAS_CV2 = False
    try:
        import imageio.v2 as imageio  # lightweight fallback if OpenCV is not available
    except Exception:
        imageio = None

def is_binaryish(arr: np.ndarray) -> bool:
    """
    # Overview
    Checks if the given mask is binary-like, meaning it contains only 0 and 1, or 0 and 255 values.
    This function is used to identify whether an input mask is binary (either 0/1 or 0/255).

    # Parameters:
    - `arr` (np.ndarray): A 2D array representing the mask. It can be a binary mask (0/1 or 0/255).

    # Returns:
    - `bool`: `True` if the mask contains only 0 and 1 (or 0 and 255), otherwise `False`.

    # Example:
    ```python
    mask = np.array([[0, 1, 1], [0, 0, 1], [0, 0, 0]])
    is_binary = is_binaryish(mask)
    print(is_binary)  # Output: True
    ```

    # Notes:
    - The function checks if the set of unique values in the array is a subset of {0, 1} or {0, 255}.
    """
    vals = set(np.unique(arr).tolist())
    return vals.issubset({0, 1}) or vals.issubset({0, 255}) or vals.issubset({0, 1, 255})

def to_instance_labels(arr: np.ndarray) -> np.ndarray:
    """
    # Overview
    Converts a binary mask into instance labels (0 for background, 1..K for objects).
    If the input is a binary mask (0/1 or 0/255), it will be converted to labeled instances using connected components.
    If the input is already labeled, it returns the array unchanged.

    # Parameters:
    - `arr` (np.ndarray): A 2D array representing the mask. It can be binary (0/1) or already labeled (integer values).
      The array should have the shape `(H, W)`.

    # Returns:
    - `np.ndarray`: A labeled instance mask (0 for background, 1..K for each object).

    # Example:
    ```python
    binary_mask = np.array([[0, 1, 1], [0, 0, 1], [0, 0, 0]])
    labeled_mask = to_instance_labels(binary_mask)
    print(labeled_mask)
    ```

    # Notes:
    - If the mask is binary, OpenCV's `connectedComponents` is used to assign unique labels to each object.
    - If the mask is already labeled, it simply returns the input array as an integer mask.
    - If OpenCV is not available, an exception will be raised when trying to label binary masks.
    """
    arr = np.asarray(arr)
    if arr.ndim != 2:
        raise ValueError("The mask must be 2D (H, W).")

    if is_binaryish(arr):
        bin_arr = (arr > 0).astype(np.uint8)
        if bin_arr.sum() == 0:
            # No objects detected
            return np.zeros_like(bin_arr, dtype=np.int32)
        if not _HAS_CV2:
            raise RuntimeError("OpenCV is required for component labeling on a binary mask.")
        _, lab = cv2.connectedComponents(bin_arr)
        return lab.astype(np.int32)

    # Already instance-labeled
    return arr.astype(np.int32)

def read_gray(path: str) -> np.ndarray:
    """
    # Overview
    Reads an image as grayscale (uint8). The function first tries to use OpenCV, then falls back to `imageio` or `Pillow`.
    It reads the image from the given file path and converts it to a 2D NumPy array.

    # Parameters:
    - `path` (str): The path to the image file to be read. It should be a valid image file path (e.g., PNG, TIFF).

    # Returns:
    - `np.ndarray`: A 2D NumPy array representing the grayscale image (with pixel values in the range [0, 255]).

    # Example:
    ```python
    img = read_gray("path_to_image.png")
    print(img)
    ```

    # Notes:
    - The image is read in grayscale mode (single channel).
    - If the image is RGB(A), only the first channel is retained.
    - If neither OpenCV nor `imageio` is available, the function will raise an error.
    """
    if _HAS_CV2:
        arr = cv2.imread(path, cv2.IMREAD_GRAYSCALE)
        if arr is None:
            raise FileNotFoundError(f"Unable to read the image: {path}")
        return arr
    if imageio is None:
        raise RuntimeError("Neither OpenCV nor imageio are available to read images.")
    arr = imageio.imread(path)
    if arr.ndim == 3:
        # Take the first channel if RGB(A)
        arr = arr[..., 0]
    # Force scaling to 0..255
    arr = np.asarray(arr)
    if arr.dtype != np.uint8:
        arr = (arr / arr.max() * 255.0).astype(np.uint8) if arr.max() > 1 else (arr * 255).astype(np.uint8)
    return arr

def get_ids(arr: np.ndarray):
    """
    # Overview
    Returns the list of unique object IDs from the given mask, excluding the background (label `0`).
    The function identifies all unique non-background labels in the mask and returns them as a list.

    # Parameters:
    - `arr` (np.ndarray): The input label mask, which should be a 2D array of integer labels.

    # Returns:
    - `list`: A list of unique non-background object IDs (excluding `0`).

    # Example:
    ```python
    mask = np.array([[0, 1, 1], [0, 2, 2], [0, 0, 0]])
    ids = get_ids(mask)
    print(ids)  # Output: [1, 2]
    ```

    # Notes:
    - The function assumes that the background label is `0`, and it returns only the non-background labels.
    """
    u = np.unique(arr)
    return [int(x) for x in u if x != 0]
