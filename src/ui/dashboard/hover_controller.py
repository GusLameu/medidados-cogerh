"""
Controlador de interações de hover dos gráficos do dashboard.
"""
from typing import Any, Optional

import matplotlib.dates as mdates
import numpy as np
import pandas as pd
from matplotlib.axes import Axes
from matplotlib.backend_bases import DrawEvent, MouseEvent
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
from matplotlib.legend import Legend
from matplotlib.lines import Line2D
from matplotlib.text import Annotation, Text

from src.ui.dashboard.types import (
    CanvasBackground,
    PieChartLegends,
    WedgeInfoMap,
)


class DashboardHoverController:
    """
    Controla os tooltips do gráfico temporal e das roscas.

    Mantém o cache de fundo do canvas para evitar redraw completo do Matplotlib
    a cada movimento do mouse.
    """

    def __init__(
        self,
        canvas: FigureCanvasTkAgg,
        figure: Figure,
        flow_axis: Axes,
        secondary_axis: Optional[Axes],
        flow_line: Line2D,
        secondary_line: Optional[Line2D],
        main_legend: Legend,
        pie_legends: PieChartLegends,
        wedge_info_map: WedgeInfoMap,
        unit: str,
        medidor_model: str,
        mean_flow: float,
    ) -> None:
        """
        Inicializa o controlador e cria os elementos visuais do hover.

        Args:
            canvas: Canvas Matplotlib ligado à interface Tkinter.
            figure: Figura Matplotlib do dashboard.
            flow_axis: Eixo principal de vazão.
            secondary_axis: Eixo secundário de velocidade ou volume.
            flow_line: Linha de vazão.
            secondary_line: Linha de velocidade ou volume, se existir.
            main_legend: Legenda principal do gráfico temporal.
            pie_legends: Legendas dos gráficos de rosca.
            wedge_info_map: Dados de cada fatia de rosca para tooltip.
            unit: Unidade escolhida para vazão.
            medidor_model: Modelo atual do medidor.
            mean_flow: Média de vazão calculada.
        """
        self.canvas: FigureCanvasTkAgg = canvas
        self.figure: Figure = figure
        self.flow_axis: Axes = flow_axis
        self.secondary_axis: Optional[Axes] = secondary_axis
        self.flow_line: Line2D = flow_line
        self.secondary_line: Optional[Line2D] = secondary_line
        self.main_legend: Legend = main_legend
        self.pie_legends: PieChartLegends = pie_legends
        self.wedge_info_map: WedgeInfoMap = wedge_info_map
        self.unit: str = unit
        self.medidor_model: str = medidor_model
        self.mean_flow: float = mean_flow

        self._last_hover_idx: Optional[int] = None
        self._background_cache: Optional[CanvasBackground] = None

        self.vertical_line: Line2D = self.flow_axis.axvline(
            x=self.flow_line.get_data()[0][0],
            color="#333333",
            alpha=0.3,
            lw=0.8,
            visible=False,
            zorder=5,
        )

        self.annotation_line: Annotation = self.flow_axis.annotate(
            "",
            xy=(0, 0),
            xytext=(20, 35),
            textcoords="offset points",
            bbox=dict(
                boxstyle="round,pad=0.5",
                fc="white",
                ec="black",
                lw=1,
                alpha=0.98,
            ),
            zorder=100,
            visible=False,
            clip_on=False,
        )

        self.annotation_pie: Text = self.figure.text(
            0,
            0,
            "",
            bbox=dict(
                boxstyle="round,pad=0.5",
                fc="white",
                ec="black",
                lw=1,
                alpha=0.98,
            ),
            visible=False,
            zorder=101,
        )

    def _redraw_static_elements(self) -> None:
        """
        Redesenha as legendas após a restauração do cache do canvas.
        """
        self.flow_axis.draw_artist(self.main_legend)

        for legend in self.pie_legends:
            self.figure.draw_artist(legend)

    def on_draw(self, event: DrawEvent) -> None:
        """
        Atualiza o cache do fundo do canvas após um redraw do Matplotlib.
        """
        del event

        self.vertical_line.set_visible(False)
        self.annotation_line.set_visible(False)
        self.annotation_pie.set_visible(False)

        self._redraw_static_elements()

        self._background_cache = self.canvas.copy_from_bbox(
            self.figure.bbox
        )

    def on_hover(self, event: MouseEvent) -> None:
        """
        Atualiza o tooltip do gráfico de linha ou de uma fatia de rosca.
        """
        if event.inaxes is None or event.xdata is None:
            self._hide_annotations()
            return

        chart_axes: list[Axes] = [self.flow_axis]

        if self.secondary_axis is not None:
            chart_axes.append(self.secondary_axis)

        if event.inaxes in chart_axes:
            self._handle_line_hover(event)
            return

        self._handle_pie_hover(event)

    def _handle_line_hover(self, event: MouseEvent) -> None:
        """
        Atualiza o tooltip da série temporal de vazão.
        """
        if event.xdata is None:
            return

        x_data, y_flow = self.flow_line.get_data()
        x_num: np.ndarray[Any, Any] = mdates.date2num(x_data)
        index: int = int(np.abs(x_num - event.xdata).argmin())

        if index == self._last_hover_idx:
            return

        self._last_hover_idx = index

        date_at: Any = x_data[index]
        flow_value: float = float(y_flow[index])

        xlim: tuple[float, float] = self.flow_axis.get_xlim()
        ylim: tuple[float, float] = self.flow_axis.get_ylim()

        offset_x: int = (
            -175
            if event.xdata > (xlim[0] + (xlim[1] - xlim[0]) * 0.7)
            else 25
        )

        offset_y: int = (
            35
            if flow_value < (ylim[1] * 0.6)
            else -110
        )

        self.vertical_line.set_xdata([date_at, date_at])
        self.vertical_line.set_visible(True)

        self.annotation_line.xy = (date_at, flow_value)
        self.annotation_line.set_position((offset_x, offset_y))

        tooltip_text: str = self._build_line_tooltip(
            date_at=date_at,
            flow_value=flow_value,
            index=index,
        )

        self.annotation_line.set_text(tooltip_text)
        self.annotation_line.set_visible(True)
        self.annotation_pie.set_visible(False)

        self._restore_and_draw_line_hover()

    def _build_line_tooltip(
        self,
        date_at: Any,
        flow_value: float,
        index: int,
    ) -> str:
        """
        Monta o texto do tooltip para vazão, média e velocidade/volume.
        """
        base_text: str = (
            f"DATA: {pd.Timestamp(date_at).strftime('%d/%m/%Y %H:%M')}\n"
            f"VAZÃO: {flow_value:,.2f} {self.unit}\n"
            f"MÉDIA: {self.mean_flow:,.2f} {self.unit}"
        )

        if self.secondary_line is None:
            return base_text

        secondary_data = self.secondary_line.get_data()[1]
        secondary_value: float = float(secondary_data[index])

        is_mv145: bool = self.medidor_model.strip().upper() == "MV145"

        extra_label: str = "VOLUME" if is_mv145 else "VELOCIDADE"
        extra_unit: str = "m³" if is_mv145 else "m/s"

        return (
            f"{base_text}\n"
            f"{extra_label}: {secondary_value:,.2f} {extra_unit}"
        )

    def _restore_and_draw_line_hover(self) -> None:
        """
        Restaura o fundo e redesenha apenas os elementos de hover da linha.
        """
        if self._background_cache is not None:
            self.canvas.restore_region(self._background_cache)

        self._redraw_static_elements()

        self.flow_axis.draw_artist(self.vertical_line)
        self.flow_axis.draw_artist(self.annotation_line)

        self.canvas.blit(self.figure.bbox)

    def _handle_pie_hover(self, event: MouseEvent) -> None:
        """
        Localiza a fatia de rosca sob o mouse e exibe seu tooltip.
        """
        found_wedge: bool = False

        for wedge, info in self.wedge_info_map.items():
            if not wedge.contains_point([event.x, event.y]):
                continue

            total: float = float(info["total"])

            if total <= 0:
                total = 1.0

            percentage: float = float(info["value"]) / total * 100

            self.annotation_pie.set_text(
                f"CATEGORIA: {info['label']}\n"
                f"PERCENTUAL: {percentage:.1f}%"
            )

            self.annotation_pie.set_position(
                (
                    event.x / self.figure.bbox.width + 0.01,
                    event.y / self.figure.bbox.height + 0.01,
                )
            )

            self.annotation_pie.set_visible(True)
            self.vertical_line.set_visible(False)
            self.annotation_line.set_visible(False)

            if self._background_cache is not None:
                self.canvas.restore_region(self._background_cache)

            self._redraw_static_elements()
            self.figure.draw_artist(self.annotation_pie)
            self.canvas.blit(self.figure.bbox)

            self._last_hover_idx = None
            found_wedge = True
            break

        if not found_wedge and self.annotation_pie.get_visible():
            self.annotation_pie.set_visible(False)

            if self._background_cache is not None:
                self.canvas.restore_region(self._background_cache)

            self._redraw_static_elements()
            self.canvas.blit(self.figure.bbox)

    def _hide_annotations(self) -> None:
        """
        Oculta os tooltips quando o mouse sai dos gráficos.
        """
        has_visible_annotation: bool = (
            self.vertical_line.get_visible()
            or self.annotation_line.get_visible()
            or self.annotation_pie.get_visible()
        )

        if has_visible_annotation and self._background_cache is not None:
            self.canvas.restore_region(self._background_cache)

        self.vertical_line.set_visible(False)
        self.annotation_line.set_visible(False)
        self.annotation_pie.set_visible(False)

        if has_visible_annotation:
            self._redraw_static_elements()
            self.canvas.blit(self.figure.bbox)

        self._last_hover_idx = None