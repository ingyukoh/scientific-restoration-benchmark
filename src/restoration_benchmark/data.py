"""Deterministic phantoms, not photographs or simulated instrument acquisitions."""

from dataclasses import dataclass
import hashlib

import numpy as np

FAMILIES = ("particles", "lines")
NOISE_LEVELS = (0.05, 0.10)
SPLIT_SEEDS = {"calibration": tuple(range(3)), "test": tuple(range(100, 108))}


@dataclass(frozen=True)
class Case:
    case_id: str
    group: str
    split: str
    family: str
    sigma: float
    reference: np.ndarray
    noisy: np.ndarray


def canonical_image(image):
    """Quantize to 16-bit intensity; this same array is scored and hashed."""
    result = np.rint(np.clip(image, 0, 1) * 65535).astype("<u2")
    return result.astype(np.float64) / 65535.0


def image_hash(image):
    pixels = np.rint(image * 65535).astype("<u2")
    return hashlib.sha256(pixels.tobytes(order="C")).hexdigest()


def phantom(family, seed, size=128):
    if family not in FAMILIES or size < 32:
        raise ValueError("Choose particles or lines, with size >= 32.")
    rng = np.random.default_rng(np.random.SeedSequence([seed, FAMILIES.index(family)]))
    yy, xx = np.mgrid[:size, :size]
    image = 0.08 + 0.08 * xx / size + 0.04 * yy / size
    if family == "particles":
        for _ in range(14):
            cx, cy = rng.uniform(0.12 * size, 0.88 * size, 2)
            radius = rng.uniform(0.025 * size, 0.085 * size)
            disk = (xx - cx) ** 2 + (yy - cy) ** 2 < radius ** 2
            image[disk] = rng.uniform(0.4, 0.9)
    else:
        for _ in range(12):
            position = int(rng.integers(8, size - 8))
            width = int(rng.integers(1, 4))
            intensity = rng.uniform(0.4, 0.9)
            if rng.random() < 0.5:
                image[8:-8, position:position + width] = intensity
            else:
                image[position:position + width, 8:-8] = intensity
    return canonical_image(image)


def make_cases(split):
    if split not in SPLIT_SEEDS:
        raise ValueError("Unknown split.")
    cases = []
    for family_index, family in enumerate(FAMILIES):
        for seed in SPLIT_SEEDS[split]:
            reference = phantom(family, seed)
            for noise_index, sigma in enumerate(NOISE_LEVELS):
                rng = np.random.default_rng(
                    np.random.SeedSequence([seed, family_index, noise_index, 913])
                )
                noisy = canonical_image(reference + rng.normal(0, sigma, reference.shape))
                group = f"{family}/{seed:04d}"
                cases.append(Case(
                    f"{split}/{group}/sigma-{sigma:.2f}", group, split, family,
                    sigma, reference, noisy,
                ))
    return cases


def manifest(cases):
    return {
        "generator": "synthetic-disks-and-lines-v1",
        "intensity_encoding": "uint16 little-endian, row-major, range 0..65535",
        "cases": [
            {"id": c.case_id, "group": c.group, "split": c.split,
             "family": c.family, "sigma_before_clipping": c.sigma,
             "shape": list(c.reference.shape),
             "reference_sha256": image_hash(c.reference),
             "noisy_sha256": image_hash(c.noisy)}
            for c in cases
        ],
    }
