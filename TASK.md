# Task: Make a defensible scientific image-denoising comparison

## Problem

A scientist wants to reduce image noise while preserving small structures. A smoother
image may look better while erasing the feature the scientist needs to measure.
Build an evaluation that makes this trade-off visible and can be repeated by another person.

This exercise uses generated particle and line phantoms. They are not SEM acquisitions,
physical instrument simulations, or observations of a material. No laboratory instrument
operation is part of this task.

## Named software

Python 3.11 or 3.12, NumPy 2.2.6, SciPy 1.15.3, Matplotlib 3.10.3,
the standard-library `unittest` runner, Git and GitHub Actions.
The baseline implementation runs on a CPU without a GPU or API key.

## Inputs

- `src/restoration_benchmark/data.py` defines two pattern families and independent splits.
- Six calibration images and sixteen held-out images each receive two noise levels.
- Additive Gaussian noise is clipped to [0,1] and quantized to 16-bit intensity.
- `reports/input_manifest.json` records every generated input's hash.

## Assignment

1. Reproduce the committed results and explain the parameter-selection protocol.
2. Add one restoration method, or improve an existing one, with a clearly stated hypothesis.
   Tune settings on calibration data only. Keep the existing test seeds and scoring border fixed.
3. Compare against noisy input, Gaussian filtering, median filtering and the local Wiener baseline.
   Use the same held-out observations for every method.
4. Report PSNR, SSIM, edge error, paired differences and a suitable uncertainty summary.
   Explain what your uncertainty estimate does and does not cover.
5. Show a fixed-intensity-scale comparison panel, including a case where smoothing harms a thin feature.
6. Measure restoration time separately from scoring and plotting. State the CPU, software
   environment, image size, warm-up and repetition policy.
7. Explain one failure, one assumption and what real microscopy data would be needed next.

If you inspect test results while iterating, label that set a development set and create a
new untouched final set. A public test set cannot remain a hidden final exam indefinitely.

## Deliverables

- Runnable code with a single reproduction command.
- Per-case measurements, aggregate results and the image panel.
- Frozen parameter choices with the calibration search recorded.
- Tests for split integrity, metrics and at least one meaningful failure case.
- A short technical note describing the decision, evidence and limitations.

## Review rubric

| Area | Weight | What a reviewer should check |
|---|---:|---|
| Experimental design | 30 | Calibration/test separation, paired observations, consistent range and crop |
| Numerical correctness | 25 | Independently checked metrics, finite outputs, valid uncertainty calculation |
| Scientific interpretation | 20 | Feature loss, failure analysis, careful statement of generalization |
| Reproducibility | 15 | Input hashes, dependency versions, commands and generated results |
| Engineering clarity | 10 | Understandable interfaces, appropriate tests and documented runtime |

Estimated scope: half a day for the extension and technical note, depending on the method.
This is an independent portfolio exercise created in November 2026 with AI assistance.
It is not a record of a previous paid engagement. If an application requires a task derived
from paid professional work, document an actual qualifying engagement separately.
