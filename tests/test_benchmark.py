import json
from pathlib import Path
import tempfile
import unittest

import numpy as np

from restoration_benchmark.benchmark import evaluate, paired_interval, run, select_parameters
from restoration_benchmark.data import image_hash, make_cases, manifest
from restoration_benchmark.methods import restore
from restoration_benchmark.metrics import edge_mae, psnr, ssim


class MetricTests(unittest.TestCase):
    def test_psnr_has_analytic_reference_value(self):
        reference = np.full((32, 32), 0.5)
        self.assertAlmostEqual(psnr(reference, reference - 0.1), 20.0, places=10)
        self.assertEqual(psnr(reference, reference), float("inf"))

    def test_ssim_matches_constant_image_formula(self):
        reference, estimate = np.full((32, 32), 0.5), np.full((32, 32), 0.4)
        expected = (2 * 0.5 * 0.4 + 0.01 ** 2) / (0.5 ** 2 + 0.4 ** 2 + 0.01 ** 2)
        self.assertAlmostEqual(ssim(reference, estimate), expected, places=10)
        self.assertAlmostEqual(ssim(reference, reference), 1.0, places=10)

    def test_scoring_border_is_applied(self):
        reference = np.full((32, 32), 0.5)
        estimate = reference.copy()
        estimate[:5] = 0
        self.assertEqual(psnr(reference, estimate), float("inf"))
        self.assertTrue(np.isfinite(psnr(reference, estimate, border=0)))

    def test_edge_metric_alone_cannot_detect_brightness_error(self):
        # This is a documented limitation, and why PSNR/SSIM are also reported.
        a, b = np.full((32, 32), 0.5), np.full((32, 32), 0.4)
        self.assertEqual(edge_mae(a, b), 0)
        self.assertLess(ssim(a, b), 1)

    def test_metrics_reject_invalid_input(self):
        good = np.zeros((32, 32))
        for bad in (np.zeros((31, 32)), np.full((32, 32), np.nan), np.full((32, 32), 1.1)):
            for metric in (psnr, ssim, edge_mae):
                with self.subTest(metric=metric.__name__, shape=bad.shape):
                    with self.assertRaises(ValueError):
                        metric(good, bad)


class DataAndProtocolTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.calibration, cls.test = make_cases("calibration"), make_cases("test")

    def test_data_are_reproducible_and_groups_do_not_overlap(self):
        self.assertEqual(manifest(self.test), manifest(make_cases("test")))
        self.assertEqual(len(self.calibration), 12)
        self.assertEqual(len(self.test), 32)
        self.assertFalse({c.group for c in self.calibration} & {c.group for c in self.test})
        self.assertFalse({image_hash(c.reference) for c in self.calibration} &
                         {image_hash(c.reference) for c in self.test})

    def test_noise_levels_share_clean_image_but_not_observation(self):
        a, b = self.test[:2]
        self.assertEqual(a.group, b.group)
        np.testing.assert_array_equal(a.reference, b.reference)
        self.assertNotEqual(image_hash(a.noisy), image_hash(b.noisy))

    def test_test_cases_cannot_be_used_for_tuning(self):
        with self.assertRaises(ValueError):
            select_parameters(self.test)
        with self.assertRaises(ValueError):
            select_parameters(self.calibration + self.test[:1])

    def test_evaluation_rejects_calibration_data(self):
        with self.assertRaises(ValueError):
            evaluate(self.calibration, {"noisy_input": {}})

    def test_frozen_choice_is_repeatable(self):
        first, trials = select_parameters(self.calibration)
        second, _ = select_parameters(list(reversed(self.calibration)))
        self.assertEqual(first, second)
        self.assertEqual(len(trials), 8)

    def test_noisy_baseline_and_paired_interval(self):
        rows, _ = evaluate(self.test[:2], {"noisy_input": {}})
        self.assertAlmostEqual(rows[0]["psnr_db"], psnr(self.test[0].reference, self.test[0].noisy))
        self.assertEqual(paired_interval(rows, "noisy_input"), [0.0, 0.0])

    def test_modified_manifest_fails_before_writing(self):
        with tempfile.TemporaryDirectory() as tmp:
            expected = manifest(self.calibration + self.test)
            expected["cases"][0]["noisy_sha256"] = "modified"
            manifest_path = Path(tmp) / "expected.json"
            manifest_path.write_text(json.dumps(expected))
            destination = Path(tmp) / "results"
            with self.assertRaisesRegex(ValueError, "manifest mismatch"):
                run(destination, manifest_path)
            self.assertFalse(destination.exists())


class RestorationTests(unittest.TestCase):
    def test_filters_preserve_constant_image_and_do_not_mutate_input(self):
        image = np.full((32, 32), 0.5)
        original = image.copy()
        for method, parameters in (("noisy_input", {}), ("gaussian", {"sigma": 0.7}),
                                   ("median", {"size": 3}), ("wiener", {"size": 3})):
            with self.subTest(method=method):
                restored = restore(image, method, parameters)
                np.testing.assert_allclose(restored, original, atol=1e-12)
                np.testing.assert_array_equal(image, original)

    def test_unknown_method_and_invalid_windows_are_rejected(self):
        image = np.zeros((32, 32))
        for method, parameters in (("missing", {}), ("gaussian", {"sigma": 0}),
                                   ("median", {"size": 4}), ("wiener", {"size": 1})):
            with self.assertRaises(ValueError):
                restore(image, method, parameters)

    def test_smoothing_can_erase_thin_feature_contrast(self):
        image = np.zeros((32, 32))
        image[:, 16] = 1
        estimate = restore(image, "gaussian", {"sigma": 1.0})
        self.assertLess(float(estimate[:, 16].mean()), 0.5)
        self.assertGreater(edge_mae(image, estimate), 0)


if __name__ == "__main__":
    unittest.main()
