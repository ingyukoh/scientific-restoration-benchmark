"""Full-reference metrics for normalized grayscale images."""

import numpy as np
from scipy.ndimage import gaussian_filter, sobel

DEFAULT_BORDER = 5


def _pair(reference, estimate, border):
    a, b = np.asarray(reference, dtype=float), np.asarray(estimate, dtype=float)
    if a.ndim != 2 or a.shape != b.shape:
        raise ValueError("Images must have the same two-dimensional shape.")
    if border < 0 or min(a.shape) <= 2 * border:
        raise ValueError("Invalid scoring border.")
    if not all(np.isfinite(x).all() and x.min() >= 0 and x.max() <= 1 for x in (a, b)):
        raise ValueError("Images must contain finite intensities in [0, 1].")
    return a, b


def _crop(a, border):
    return a[border:-border, border:-border] if border else a


def psnr(reference, estimate, border=DEFAULT_BORDER):
    a, b = _pair(reference, estimate, border)
    mse = float(np.mean(_crop(a - b, border) ** 2))
    return float("inf") if mse == 0 else -10 * np.log10(mse)


def ssim(reference, estimate, border=DEFAULT_BORDER):
    """Gaussian local SSIM, 11x11 window, sigma=1.5, population covariance."""
    a, b = _pair(reference, estimate, border)
    smooth = lambda x: gaussian_filter(x, sigma=1.5, radius=5, mode="reflect")
    ma, mb = smooth(a), smooth(b)
    va = np.maximum(smooth(a * a) - ma * ma, 0)
    vb = np.maximum(smooth(b * b) - mb * mb, 0)
    cov = smooth(a * b) - ma * mb
    c1, c2 = 0.01 ** 2, 0.03 ** 2
    score = ((2 * ma * mb + c1) * (2 * cov + c2)) / (
        (ma * ma + mb * mb + c1) * (va + vb + c2)
    )
    return float(np.mean(_crop(score, border)))


def edge_mae(reference, estimate, border=DEFAULT_BORDER):
    """Mean absolute difference of Sobel gradient magnitudes, kernel divided by 8."""
    a, b = _pair(reference, estimate, border)
    def magnitude(image):
        return np.hypot(sobel(image, 0, mode="reflect") / 8,
                        sobel(image, 1, mode="reflect") / 8)
    return float(np.mean(_crop(np.abs(magnitude(a) - magnitude(b)), border)))


def score(reference, estimate):
    return {"psnr_db": float(psnr(reference, estimate)),
            "ssim": ssim(reference, estimate), "edge_mae": edge_mae(reference, estimate)}
