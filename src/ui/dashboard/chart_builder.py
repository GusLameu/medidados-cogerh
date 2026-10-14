"""
Componente responsável pela criação do gráfico temporal principal.
"""
from typing import Any

import matplotlib.dates as mdates
import pandas as pd
from matplotlib.axes import Axes
from matplotlib.figure import Figure
from matplotlib.ticker import FuncFormatter

from src.core.config import COR_VAZAO, COR_VELOCIDADE
from src.ui.dashboard.types import MainChartResult


class MainChartBuilder:
    """
    Cria o gráfico temporal principal do dashboard.

    Há dois modos:
    - Completo: vazão, velocidade e linha de média.
    - Simplificado: vazão, volume opcional e linha de média para MV145.
    """

    @staticmethod
    def build_simplified(
        figure: Figure,
        data_frame: pd.DataFrame,
        medidor_model: str,
        medidor_type: str,
        unit: str,
    ) -> MainChartResult:
        """
        Cria o gráfico de vazão e volume do modelo MV145.

        Args:
            figure: Figura Matplotlib que receberá o gráfico.
            data_frame: Dados já processados do medidor.
            medidor_model: Modelo do medidor.
            medidor_type: Tipo do medidor.
            unit: Unidade de exibição da vazão.

        Returns:
            Referências aos elementos criados no gráfico.
        """
        figure.subplots_adjust(
            top=0.82,
            bottom=0.10,
            left=0.07,
            right=0.93,
        )

        flow_axis: Axes = figure.add_subplot(111)

        flow_line, = flow_axis.plot(
            data_frame["Data"],
            data_frame["Vazao"],
            label="VAZÃO",
            color=COR_VAZAO,
            lw=1.5,
        )

        flow_axis.fill_between(
            data_frame["Data"],
            data_frame["Vazao"],
            color=COR_VAZAO,
            alpha=0.08,
        )

        flow_axis.set_ylabel(
            f"Vazão ({unit})",
            color=COR_VAZAO,
            fontsize=12,
            fontweight="bold",
        )

        flow_axis.set_title(
            (
                "MONITORAMENTO DE VAZÃO E VOLUME - "
                f"{medidor_type} ({medidor_model})"
            ),
            fontsize=18,
            fontweight="bold",
            pad=70,
        )

        flow_axis.xaxis.set_major_formatter(
            mdates.DateFormatter("%d/%m/%Y")
        )

        flow_axis.set_xlim(
            data_frame["Data"].min(),
            data_frame["Data"].max(),
        )

        max_flow: float = (
            float(data_frame["Vazao"].max())
            if not data_frame["Vazao"].empty
            else 1.0
        )

        flow_axis.set_ylim(
            -max_flow * 0.05,
            max_flow * 1.3,
        )

        flow_axis.grid(
            True,
            axis="y",
            linestyle=":",
            alpha=0.3,
        )

        flow_values: pd.Series = data_frame["Vazao"].dropna()
        mean_flow: float = (
            float(flow_values.mean())
            if not flow_values.empty
            else 0.0
        )

        flow_axis.axhline(
            y=mean_flow,
            color="green",
            linestyle=":",
            lw=1.5,
            alpha=0.7,
            label=f"MÉDIA ({mean_flow:,.2f})",
        )

        secondary_axis: Axes | None = None
        secondary_line = None

        if (
            "Volume" in data_frame.columns
            and not data_frame["Volume"].isna().all()
        ):
            secondary_axis = flow_axis.twinx()

            secondary_line, = secondary_axis.plot(
                data_frame["Data"],
                data_frame["Volume"],
                label="VOLUME",
                color="#2E7D32",
                lw=1.5,
                linestyle="--",
            )

            secondary_axis.set_ylabel(
                "Volume (m³)",
                color="#2E7D32",
                fontsize=12,
                fontweight="bold",
            )

            flow_lines, flow_labels = flow_axis.get_legend_handles_labels()
            secondary_lines, secondary_labels = (
                secondary_axis.get_legend_handles_labels()
            )

            legend = flow_axis.legend(
                flow_lines + secondary_lines,
                flow_labels + secondary_labels,
                loc="upper center",
                bbox_to_anchor=(0.5, 1.08),
                ncol=3,
                frameon=False,
                fontsize=10,
            )

        else:
            legend = flow_axis.legend(
                loc="upper center",
                bbox_to_anchor=(0.5, 1.08),
                ncol=2,
                frameon=False,
                fontsize=10,
            )

        return MainChartResult(
            flow_axis=flow_axis,
            secondary_axis=secondary_axis,
            flow_line=flow_line,
            secondary_line=secondary_line,
            legend=legend,
            mean_flow=mean_flow,
        )

    @staticmethod
    def build_complete(
        figure: Figure,
        grid_spec: Any,
        data_frame: pd.DataFrame,
        medidor_model: str,
        medidor_type: str,
        unit: str,
    ) -> MainChartResult:
        """
        Cria o gráfico de vazão e velocidade dos modelos completos.

        Args:
            figure: Figura Matplotlib que receberá o gráfico.
            grid_spec: GridSpec já configurado pelo layout principal.
            data_frame: Dados já processados do medidor.
            medidor_model: Modelo do medidor.
            medidor_type: Tipo do medidor.
            unit: Unidade de exibição da vazão.

        Returns:
            Referências aos elementos criados no gráfico.
        """
        flow_axis: Axes = figure.add_subplot(grid_spec[0, :])
        secondary_axis: Axes = flow_axis.twinx()

        flow_axis.set_zorder(secondary_axis.get_zorder() + 1)
        flow_axis.set_frame_on(False)

        for spine in flow_axis.spines.values():
            spine.set_zorder(0)

        def format_mil(value: float, _position: float) -> str:
            """
            Formata valores maiores que mil para o eixo de vazão.
            """
            if value >= 1000:
                return f"{value / 1000:,.1f}mil".replace(".", ",")

            return str(int(value))

        flow_axis.yaxis.set_major_formatter(
            FuncFormatter(format_mil)
        )

        flow_axis.set_ylabel(
            f"Vazão ({unit})",
            color=COR_VAZAO,
            fontsize=12,
            fontweight="bold",
        )

        secondary_axis.set_ylabel(
            "Velocidade (m/s)",
            color=COR_VELOCIDADE,
            fontsize=12,
            fontweight="bold",
        )

        flow_axis.set_title(
            (
                "MONITORAMENTO DE VAZÃO E VELOCIDADE - "
                f"{medidor_type} ({medidor_model})"
            ),
            fontsize=18,
            fontweight="bold",
            pad=55,
        )

        flow_axis.xaxis.set_major_formatter(
            mdates.DateFormatter("%d/%m/%Y")
        )

        flow_axis.set_xlim(
            data_frame["Data"].min(),
            data_frame["Data"].max(),
        )

        max_flow: float = (
            float(data_frame["Vazao"].max())
            if not data_frame["Vazao"].empty
            else 1.0
        )

        max_speed: float = (
            float(data_frame["Velocidade"].max())
            if (
                "Velocidade" in data_frame.columns
                and not data_frame["Velocidade"].empty
            )
            else 1.0
        )

        flow_axis.set_ylim(0, max_flow * 1.3)
        secondary_axis.set_ylim(0, max_speed * 2.8)

        flow_line, = flow_axis.plot(
            data_frame["Data"],
            data_frame["Vazao"],
            label="VAZÃO",
            color=COR_VAZAO,
            lw=1.0,
        )

        flow_axis.fill_between(
            data_frame["Data"],
            data_frame["Vazao"],
            color=COR_VAZAO,
            alpha=0.08,
        )

        secondary_line, = secondary_axis.plot(
            data_frame["Data"],
            data_frame["Velocidade"],
            label="VELOCIDADE",
            color=COR_VELOCIDADE,
            lw=0.8,
            linestyle="--",
        )

        flow_values: pd.Series = data_frame["Vazao"].dropna()
        mean_flow: float = (
            float(flow_values.mean())
            if not flow_values.empty
            else 0.0
        )

        flow_axis.axhline(
            y=mean_flow,
            color="green",
            linestyle=":",
            lw=1.5,
            alpha=0.7,
            label=f"MÉDIA ({mean_flow:,.2f})",
        )

        flow_lines, flow_labels = flow_axis.get_legend_handles_labels()
        secondary_lines, secondary_labels = (
            secondary_axis.get_legend_handles_labels()
        )

        legend = flow_axis.legend(
            flow_lines + secondary_lines,
            flow_labels + secondary_labels,
            loc="upper center",
            bbox_to_anchor=(0.5, 1.18),
            ncol=3,
            frameon=False,
            fontsize=10,
        )

        flow_axis.grid(
            True,
            axis="y",
            linestyle=":",
            alpha=0.3,
        )

        return MainChartResult(
            flow_axis=flow_axis,
            secondary_axis=secondary_axis,
            flow_line=flow_line,
            secondary_line=secondary_line,
            legend=legend,
            mean_flow=mean_flow,
        )