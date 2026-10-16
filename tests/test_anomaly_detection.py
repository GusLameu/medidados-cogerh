"""Testes da detecção de anomalias no totalizado."""
import unittest

import pandas as pd

from src.services.anomaly_detection import (
    AnomalyConfig,
    AnomalyDetectionService,
)


class TestAnomalyDetection(unittest.TestCase):
    def setUp(self) -> None:
        self.config = AnomalyConfig(
            positive_jump_threshold=1_000.0,
            negative_tolerance=0.0,
            max_interval_minutes=90.0,
        )

    def test_detects_jump_and_reduction(self) -> None:
        data = pd.DataFrame({
            "Data": pd.date_range("2026-10-01", periods=6, freq="h"),
            "Total": [1_000, 1_100, 1_200, 9_000, 0, 100],
        })

        result = AnomalyDetectionService.detect(data, self.config)

        self.assertEqual(len(result), 2)
        self.assertEqual(
            result["TipoAnomalia"].tolist(),
            [
                "Aumento atípico no totalizado",
                "Possível reset/redução",
            ],
        )
        self.assertEqual(result["Variacao"].tolist(), [7_800, -9_000])

    def test_missing_reading_does_not_become_reset(self) -> None:
        data = pd.DataFrame({
            "Data": pd.date_range("2026-10-01", periods=3, freq="h"),
            "Total": [1_000, None, 5_000],
        })

        result = AnomalyDetectionService.detect(data, self.config)

        self.assertTrue(result.empty)

    def test_negative_recovery_is_not_positive_jump(self) -> None:
        data = pd.DataFrame({
            "Data": pd.date_range("2026-10-01", periods=3, freq="h"),
            "Total": [10_000, -10_000, 0],
        })

        result = AnomalyDetectionService.detect(data, self.config)

        self.assertEqual(len(result), 1)
        self.assertEqual(
            result.iloc[0]["TipoAnomalia"],
            "Possível reset/redução",
        )

    def test_long_interval_is_not_positive_jump(self) -> None:
        data = pd.DataFrame({
            "Data": pd.to_datetime([
                "2026-10-01 00:00",
                "2026-10-02 00:00",
            ]),
            "Total": [1_000, 10_000],
        })

        result = AnomalyDetectionService.detect(data, self.config)

        self.assertTrue(result.empty)

    def test_without_total_returns_empty(self) -> None:
        data = pd.DataFrame({
            "Data": pd.date_range("2026-10-01", periods=2, freq="h"),
            "Vazao": [10, 20],
        })

        result = AnomalyDetectionService.detect(data, self.config)

        self.assertTrue(result.empty)


if __name__ == "__main__":
    unittest.main()