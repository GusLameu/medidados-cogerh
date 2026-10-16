"""
Detecção de ocorrências suspeitas no totalizado de um medidor.

Entrada esperada:
- Data: datas já interpretadas pelo processamento.
- Total: valores numéricos na unidade original do totalizado.
"""
from dataclasses import dataclass
from math import isfinite

import numpy as np
import pandas as pd


@dataclass(frozen=True)
class AnomalyConfig:
    """Parâmetros explícitos para a detecção."""

    positive_jump_threshold: float
    negative_tolerance: float = 0.0
    max_interval_minutes: float | None = None

    def __post_init__(self) -> None:
        if (
            not isfinite(self.positive_jump_threshold)
            or self.positive_jump_threshold <= 0
        ):
            raise ValueError("O limite de salto deve ser finito e positivo.")

        if (
            not isfinite(self.negative_tolerance)
            or self.negative_tolerance < 0
        ):
            raise ValueError("A tolerância negativa deve ser finita e não negativa.")

        if self.max_interval_minutes is not None:
            if (
                not isfinite(self.max_interval_minutes)
                or self.max_interval_minutes <= 0
            ):
                raise ValueError("O intervalo máximo deve ser finito e positivo.")


class AnomalyDetectionService:
    """Detecta saltos positivos e reduções no totalizado."""

    RESULT_COLUMNS: tuple[str, ...] = (
        "DataAnterior",
        "Data",
        "TotalAnterior",
        "Total",
        "Variacao",
        "IntervaloMinutos",
        "LimiteAplicado",
        "TipoAnomalia",
    )

    @classmethod
    def detect(
        cls,
        data_frame: pd.DataFrame,
        config: AnomalyConfig,
    ) -> pd.DataFrame:
        """
        Analisa pares consecutivos em ordem cronológica.

        Não altera o DataFrame original.

        Leituras inválidas interrompem a comparação: não são removidas
        para evitar comparar artificialmente registros separados por falhas.

        Reduções não confirmam zeragem. Uma recuperação após total negativo
        não é classificada como salto positivo nesta primeira versão.
        """
        if not {"Data", "Total"}.issubset(data_frame.columns):
            return cls._empty_result()

        analysis = data_frame.loc[:, ["Data", "Total"]].copy()

        analysis["Data"] = pd.to_datetime(
            analysis["Data"],
            errors="coerce",
        )
        analysis["Total"] = pd.to_numeric(
            analysis["Total"],
            errors="coerce",
        ).replace([np.inf, -np.inf], np.nan)

        # Sem data válida, não é possível posicionar a leitura na campanha.
        # Interrompemos a análise em vez de presumir sua posição.
        if analysis["Data"].isna().any():
            raise ValueError(
                "A detecção exige datas válidas. "
                "Verifique o processamento antes de analisar anomalias."
            )

        analysis = analysis.sort_values(
            "Data",
            kind="stable",
        ).reset_index(drop=True)

        if len(analysis) < 2:
            return cls._empty_result()

        analysis["DataAnterior"] = analysis["Data"].shift(1)
        analysis["TotalAnterior"] = analysis["Total"].shift(1)
        analysis["Variacao"] = analysis["Total"].diff()
        analysis["IntervaloMinutos"] = (
            analysis["Data"].diff().dt.total_seconds() / 60.0
        )

        valid_pair = (
            analysis["Total"].notna()
            & analysis["TotalAnterior"].notna()
            & analysis["IntervaloMinutos"].gt(0)
        )

        positive_pair = valid_pair.copy()

        if config.max_interval_minutes is not None:
            positive_pair &= analysis["IntervaloMinutos"].le(
                config.max_interval_minutes
            )

        positive_jump = (
            positive_pair
            & analysis["TotalAnterior"].ge(0)
            & analysis["Total"].ge(0)
            & analysis["Variacao"].gt(config.positive_jump_threshold)
        )

        negative_change = (
            valid_pair
            & analysis["Variacao"].lt(-config.negative_tolerance)
        )

        selected = positive_jump | negative_change

        if not selected.any():
            return cls._empty_result()

        result = analysis.loc[selected].copy()

        result["LimiteAplicado"] = config.positive_jump_threshold
        result["TipoAnomalia"] = "Aumento atípico no totalizado"

        result.loc[
            result["Variacao"].lt(0),
            "TipoAnomalia",
        ] = "Possível reset/redução"

        return result.loc[:, list(cls.RESULT_COLUMNS)].reset_index(drop=True)

    @classmethod
    def _empty_result(cls) -> pd.DataFrame:
        """Retorna um resultado vazio com as colunas esperadas pela UI."""
        return pd.DataFrame(columns=list(cls.RESULT_COLUMNS))