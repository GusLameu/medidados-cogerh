"""
Componente responsável pela criação de gráficos de rosca do dashboard.
"""
from dataclasses import dataclass
from typing import Any

import numpy as np
from matplotlib.axes import Axes
from matplotlib.figure import Figure
from matplotlib.gridspec import GridSpec
from matplotlib.legend import Legend
from matplotlib.patches import Wedge

from src.core.config import CORES_ROSCA, PIE_COLORS
from src.ui.dashboard.types import (
    MetricCounts,
    PieChartPosition,
    WedgeInfoMap,
)


@dataclass
class PieChartResult:
    """
    Elementos criados durante a montagem de um gráfico de rosca.
    """

    axis: Axes
    legend: Legend
    wedge_info_map: WedgeInfoMap


class PieChartBuilder:
    """
    Cria gráficos de rosca, legendas e rótulos percentuais do dashboard.
    """

    @staticmethod
    def build(
        figure: Figure,
        grid_spec: GridSpec,
        data: MetricCounts,
        title: str,
        grid_position: PieChartPosition,
        chart_type: str,
    ) -> PieChartResult:
        """
        Cria um gráfico de rosca com cores, legenda e percentuais.

        Args:
            figure: Figura Matplotlib que conterá o gráfico.
            grid_spec: GridSpec usado para posicionar o gráfico.
            data: Contagens por categoria.
            title: Título do gráfico.
            grid_position: Posição no GridSpec no formato (linha, coluna).
            chart_type: Tipo configurado em PIE_COLORS.

        Returns:
            Objeto contendo eixo, legenda e informações das fatias para hover.
        """
        axis: Axes = figure.add_subplot(
            grid_spec[grid_position[0], grid_position[1]]
        )

        values: list[int] = list(data.values())
        labels: list[str] = list(data.keys())
        total_sum: int = sum(values) if sum(values) > 0 else 1

        color_config: dict[str, Any] = PIE_COLORS.get(chart_type, {})
        patterns: dict[str, str] = color_config.get("patterns", {})
        default_colors: list[str] = color_config.get(
            "default",
            CORES_ROSCA,
        )

        current_colors: list[str] = []

        for label in labels:
            normalized_label: str = str(label).replace(" ", "").lower()
            assigned_color: str | None = None

            for pattern, color in patterns.items():
                normalized_pattern: str = (
                    str(pattern).replace(" ", "").lower()
                )

                if normalized_pattern in normalized_label:
                    assigned_color = color
                    break

            if assigned_color is None:
                assigned_color = default_colors[
                    len(current_colors) % len(default_colors)
                ]

            current_colors.append(assigned_color)

        wedges: list[Wedge]
        wedges, _ = axis.pie(
            values,
            startangle=90,
            colors=current_colors,
            wedgeprops={
                "width": 0.35,
                "edgecolor": "white",
            },
        )

        axis.set_title(
            title,
            fontsize=14,
            fontweight="bold",
            pad=25,
        )

        legend: Legend = axis.legend(
            wedges,
            labels,
            title="Categorias",
            loc="upper center",
            bbox_to_anchor=(0.5, -0.1),
            ncol=2,
            frameon=False,
            fontsize=9,
        )

        wedge_info_map: WedgeInfoMap = {}
        annotations_data: list[dict[str, Any]] = []

        for index, wedge in enumerate(wedges):
            percentage: float = values[index] / total_sum * 100

            if percentage < 0.1:
                continue

            angle_rad: float = (
                (wedge.theta2 - wedge.theta1) / 2.0 * np.pi / 180.0
                + wedge.theta1 * np.pi / 180.0
            )

            x_coord: float = float(np.cos(angle_rad))
            y_coord: float = float(np.sin(angle_rad))

            annotations_data.append(
                {
                    "x": x_coord,
                    "y": y_coord,
                    "percentage": percentage,
                    "wedge": wedge,
                    "label": labels[index],
                    "value": values[index],
                }
            )

        annotations_data.sort(
            key=lambda item: float(item["y"]),
            reverse=True,
        )

        occupied_y_left: list[float] = []
        occupied_y_right: list[float] = []
        min_vertical_distance: float = 0.18

        for annotation in annotations_data:
            is_right_side: bool = float(annotation["x"]) > 0

            occupied_positions: list[float] = (
                occupied_y_right
                if is_right_side
                else occupied_y_left
            )

            horizontal_alignment: str = "left" if is_right_side else "right"
            x_position: float = 1.35 if is_right_side else -1.35
            y_position: float = 1.3 * float(annotation["y"])

            if occupied_positions:
                last_y: float = occupied_positions[-1]

                if abs(y_position - last_y) < min_vertical_distance:
                    y_position = last_y - min_vertical_distance

            axis.annotate(
                f"{float(annotation['percentage']):.1f}%",
                xy=(
                    float(annotation["x"]),
                    float(annotation["y"]),
                ),
                xytext=(x_position, y_position),
                textcoords="data",
                ha=horizontal_alignment,
                fontsize=8,
                fontweight="bold",
                bbox={
                    "boxstyle": "round,pad=0.3",
                    "fc": "white",
                    "ec": "white",
                    "alpha": 0.7,
                },
                arrowprops={
                    "arrowstyle": "-",
                    "color": "black",
                    "lw": 0.5,
                },
            )

            occupied_positions.append(y_position)

            wedge_info_map[wedge] = {
                "label": annotation["label"],
                "value": annotation["value"],
                "total": total_sum,
            }

        return PieChartResult(
            axis=axis,
            legend=legend,
            wedge_info_map=wedge_info_map,
        )