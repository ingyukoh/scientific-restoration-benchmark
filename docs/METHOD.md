# Method and interpretation

## Data and provenance

`data.py` generates geometric disks or narrow horizontal/vertical lines over a smooth
intensity ramp. Positions, widths and intensities vary by seed. These are mathematical
test patterns. Their appearance does not certify a model of a microscope or material.

Each clean image is perturbed independently at two requested Gaussian noise levels.
Intensity clipping changes the residual distribution near 0 and 1. Both reference and
observation are quantized to 16-bit intensity before scoring; hashes cover those exact
quantized pixels as little-endian unsigned integers in row-major order.

Calibration seeds are 0–2 and test seeds are 100–107 in each of two families. Splits
share a generator but no clean-image seed or reference image. This measures generalization
to different samples from the same generator, not to new acquisition physics.

## Baselines and selection

Every restoration function accepts only the noisy image and frozen parameters.
Neither the clean reference nor the requested noise level is given to the function.

- Noisy input: identity control.
- Gaussian filter: σ in {0.4, 0.7, 1.0}.
- Median filter: square window width in {3, 5}.
- Local Wiener filter: square window width in {3, 5, 7}.

For the Wiener baseline, local mean m and variance v use a reflected-boundary uniform
window. Estimated noise power n is the image-wide average of v. The output is
`m + max(v-n, 0) / max(v, 1e-12) * (x-m)`, clipped to [0,1]. The small denominator floor
handles flat regions. Structure contaminating n is a known limitation of this estimator.

One candidate per method maximizes average calibration PSNR over both families and noise
levels. Ties retain the first declared candidate. Test data cannot be passed into the
selection API. All candidate scores are saved, not just the winner.

## Metrics

All arrays use a fixed data range of 1. Every method is evaluated on the same interior
pixels after excluding five pixels on each side.

- PSNR = -10 log10(MSE). A perfectly identical image has infinite PSNR.
- SSIM uses a normalized Gaussian 11×11 window with σ=1.5, K1=0.01, K2=0.03,
  population variances/covariance and reflected boundaries. This exact convention matters
  when comparing against another library's defaults.
- Edge MAE is mean absolute error between Sobel gradient magnitudes, with each derivative
  kernel divided by eight. It is a supporting diagnostic. A uniform brightness shift can
  evade it, which is why it is not the sole quality measure.

The comparison panel uses one fixed [0,1] display scale for all images. Its examples are
predefined: the first test seed in each family at requested σ=0.10. They are not selected
by which method wins.

## Uncertainty and timing

The PSNR interval is paired against the noisy observation of the same case. Differences
are averaged within each clean-image group across noise levels. Two thousand bootstrap
resamples of the 16 groups give the 5th and 95th percentiles (seed 0).

This interval does not include generator misspecification, uncertainty from method selection,
variation across independent real datasets, or the effect of repeated development on the test set.

Each timed restoration gets one preceding untimed call and three measured calls. The median
of those calls is retained per test case; p50 and p95 summarize the resulting 32 measurements.
Metrics, plotting and input generation are excluded. Hardware and dependency versions are
recorded separately. Single-thread controls are not imposed, so compare machines cautiously.

## Next useful experiment

Add a feature-sensitive method and report whether any PSNR gain survives on line patterns.
Then obtain a permissioned paired microscopy dataset, record its actual acquisition provenance,
and define a new held-out evaluation before drawing conclusions about microscopy performance.

## References

- [SciPy Gaussian filtering](https://docs.scipy.org/doc/scipy/reference/generated/scipy.ndimage.gaussian_filter.html)
- [SciPy median filtering](https://docs.scipy.org/doc/scipy/reference/generated/scipy.ndimage.median_filter.html)
- [SciPy Wiener-filter reference](https://docs.scipy.org/doc/scipy/reference/generated/scipy.signal.wiener.html).
  This repository implements a reflected-boundary local variant; it does not promise bitwise
  equivalence to `scipy.signal.wiener`.
- Wang et al., [Image quality assessment: from error visibility to structural similarity](https://doi.org/10.1109/TIP.2003.819861), IEEE Transactions on Image Processing, 2004.
