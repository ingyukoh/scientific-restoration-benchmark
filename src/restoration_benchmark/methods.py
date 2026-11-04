"""All methods consume the noisy image only; no clean reference or noise label."""

import numpy as np
from scipy.ndimage import gaussian_filter, median_filter, uniform_filter

CANDIDATES = {
    "gaussian": [{"sigma": value} for value in (0.4, 0.7, 1.0)],
    "median": [{"size": value} for value in (3, 5)],
    "wiener": [{"size": value} for value in (3, 5, 7)],
}


def restore(image, method, parameters):
    x = np.asarray(image, dtype=float)
    if x.ndim != 2 or not np.isfinite(x).all() or x.min() < 0 or x.max() > 1:
        raise ValueError("Expected a finite grayscale image in [0, 1].")
    if method == "noisy_input":
        result = x.copy()
    elif method == "gaussian":
        sigma = parameters["sigma"]
        if sigma <= 0:
            raise ValueError("sigma must be positive.")
        result = gaussian_filter(x, sigma=sigma, mode="reflect")
    elif method in ("median", "wiener"):
        size = parameters["size"]
        if not isinstance(size, int) or size < 3 or size % 2 == 0:
            raise ValueError("Window size must be an odd integer >= 3.")
        if method == "median":
            result = median_filter(x, size=size, mode="reflect")
        else:
            mean = uniform_filter(x, size=size, mode="reflect")
            variance = np.maximum(uniform_filter(x * x, size=size, mode="reflect") - mean ** 2, 0)
            noise_estimate = float(variance.mean())
            gain = np.maximum(variance - noise_estimate, 0) / np.maximum(variance, 1e-12)
            result = mean + gain * (x - mean)
    else:
        raise ValueError(f"Unknown method: {method}")
    return np.clip(result, 0, 1)
