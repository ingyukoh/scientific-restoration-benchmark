"""Compare regenerated measurements to the committed result with numerical tolerance."""

import json
from pathlib import Path
import subprocess

import numpy as np

expected = json.loads(subprocess.check_output(["git", "show", "HEAD:reports/summary.json"], text=True))
actual = json.loads(Path("reports/summary.json").read_text())
assert set(actual) == set(expected), "Method set changed."
for method in expected:
    assert actual[method]["parameters"] == expected[method]["parameters"], "Frozen settings changed."
    assert actual[method]["n_test_cases"] == expected[method]["n_test_cases"], "Population changed."
    for metric in ("psnr_db", "ssim", "edge_mae", "delta_psnr_90pct_interval"):
        np.testing.assert_allclose(actual[method][metric], expected[method][metric], rtol=1e-7, atol=1e-9,
                                   err_msg=f"{method}: {metric}")
print("Committed settings, population and numerical measurements reproduced.")
