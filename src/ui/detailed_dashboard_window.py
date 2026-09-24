"""
Módulo responsável pela janela de dashboard detalhado do medidor NF750.
Exibe gráficos de Vazão, Velocidade, Nível e Área.
"""
from typing import Any, Optional, TypeAlias

import customtkinter as ctk
import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.axes import Axes
from matplotlib.backend_bases import DrawEvent, MouseEvent
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
from matplotlib.lines import Line2D
from matplotlib.text import Annotation
from tkinter import filedialog

from src.core.config import COR_AREA, COR_NIVEL, COR_VAZAO, COR_VELOCIDADE
from src.utils.helpers import resource_path


CanvasBackground: TypeAlias = Any


class DetailedDashboardWindow(ctk.CTkToplevel):
    """
    Janela de dashboard detalhado para o medidor NF750.

    Exibe gráficos de Vazão, Velocidade, Nível e Área com interação de hover.
    """

    parent: ctk.CTkToplevel
    medidor_model: str
    data_frame: pd.DataFrame
    unit: str

    fig: Figure
    canvas: FigureCanvasTkAgg
    container_frame: ctk.CTkFrame

    ax_vazao: Axes
    ax_velocidade: Axes
    ax_nivel: Axes
    ax_area: Axes

    line_vazao: Line2D
    line_velocidade: Optional[Line2D]
    line_nivel: Optional[Line2D]
    line_area: Optional[Line2D]

    mean_flow_value: float
    _last_hover_idx: Optional[int]
    _background_cache: Optional[CanvasBackground]
    _vert_lines: dict[Axes, Line2D]
    _annotations: dict[Axes, Annotation]

    def __init__(
        self,
        parent: ctk.CTkToplevel,
        data_frame: pd.DataFrame,
        medidor_model: str,
        medidor_type: str,
        unit: str = "m³/h",
    ) -> None:
        """
        Inicializa a janela de dashboard detalhado.

        Args:
            parent: A janela pai (DashboardWindow).
            data_frame: O DataFrame pandas com os dados processados do medidor.
            medidor_model: O modelo do medidor.
            medidor_type: O tipo do medidor.
            unit: Unidade de medida da vazão.
        """
        super().__init__(parent)

        self.parent = parent
        self.medidor_model = medidor_model
        self.data_frame = data_frame
        self.unit = unit
        self._last_hover_idx = None
        self._background_cache = None

        self.title(f"Medidados - Detalhes: {medidor_type} ({medidor_model})")
        self.state("zoomed")
        self.configure(fg_color="white")
        self.attributes("-topmost", True)
        self.after(200, lambda: self.attributes("-topmost", False))

        try:
            self.after(200, lambda: self.iconbitmap(resource_path("logo.ico")))
        except Exception:
            pass

        self.protocol("WM_DELETE_WINDOW", self._on_closing)

        plt.rcParams["axes.facecolor"] = "#ffffff"
        plt.rcParams["figure.facecolor"] = "#ffffff"

        self._setup_detailed_layout(data_frame, medidor_type)

    def _setup_detailed_layout(
        self,
        data_frame: pd.DataFrame,
        medidor_type: str,
    ) -> None:
        """Configura o layout detalhado com quatro gráficos."""
        self.fig = plt.figure(figsize=(20, 12), dpi=100)
        self.fig.subplots_adjust(
            top=0.90,
            bottom=0.08,
            left=0.06,
            right=0.96,
            hspace=0.4,
            wspace=0.3,
        )

        self.ax_vazao = self.fig.add_subplot(2, 2, 1)
        self.ax_velocidade = self.fig.add_subplot(2, 2, 2)
        self.ax_nivel = self.fig.add_subplot(2, 2, 3)
        self.ax_area = self.fig.add_subplot(2, 2, 4)

        self._plot_vazao(data_frame)
        self._plot_velocidade(data_frame)
        self._plot_nivel(data_frame)
        self._plot_area(data_frame)
        self._setup_hover_elements(data_frame)

        self.container_frame = ctk.CTkFrame(self, fg_color="white")
        self.container_frame.pack(fill="both", expand=True, padx=10, pady=5)

        top_bar: ctk.CTkFrame = ctk.CTkFrame(
            self.container_frame,
            fg_color="white",
            height=45,
        )
        top_bar.pack(fill="x", pady=(0, 5))
        top_bar.pack_propagate(False)

        ctk.CTkButton(
            top_bar,
            text="← Fechar",
            command=self._return_to_dashboard,
            fg_color="#6c757d",
            height=35,
            width=100,
        ).pack(side="left", padx=5)

        ctk.CTkButton(
            top_bar,
            text="Exportar Relatório",
            command=self._export_report,
            fg_color=COR_VAZAO,
            height=35,
        ).pack(side="right", padx=5)

        self.canvas = FigureCanvasTkAgg(self.fig, master=self.container_frame)
        self.canvas.get_tk_widget().pack(fill="both", expand=True)
        self.canvas.mpl_connect("motion_notify_event", self._on_hover)
        self.canvas.mpl_connect("draw_event", self._on_draw)

        self._add_info_panel(data_frame, medidor_type)

    def _plot_vazao(self, data_frame: pd.DataFrame) -> None:
        """Plota o gráfico de vazão em azul e sua linha de média."""
        self.line_vazao, = self.ax_vazao.plot(
            data_frame["Data"],
            data_frame["Vazao"],
            label="VAZÃO",
            color=COR_VAZAO,
            lw=1.2,
        )
        self.ax_vazao.fill_between(
            data_frame["Data"],
            data_frame["Vazao"],
            color=COR_VAZAO,
            alpha=0.1,
        )
        self.ax_vazao.set_title(
            "VAZÃO",
            fontsize=14,
            fontweight="bold",
            color=COR_VAZAO,
            pad=30,
        )
        self.ax_vazao.set_ylabel(
            f"Vazão ({self.unit})",
            color=COR_VAZAO,
            fontsize=11,
        )
        self.ax_vazao.xaxis.set_major_formatter(mdates.DateFormatter("%d/%m/%Y"))
        self.ax_vazao.set_xlim(data_frame["Data"].min(), data_frame["Data"].max())
        self.ax_vazao.set_ylim(bottom=data_frame["Vazao"].min())
        self.ax_vazao.grid(True, axis="y", linestyle=":", alpha=0.3)

        vazao_col: pd.Series = data_frame["Vazao"].dropna()
        self.mean_flow_value = float(vazao_col.mean()) if not vazao_col.empty else 0.0

        self.ax_vazao.axhline(
            y=self.mean_flow_value,
            color="green",
            linestyle=":",
            lw=1.2,
            alpha=0.7,
            label=f"Média ({self.mean_flow_value:,.2f})",
        )

        lines_v, labels_v = self.ax_vazao.get_legend_handles_labels()
        self.ax_vazao.legend(
            lines_v,
            labels_v,
            loc="lower center",
            bbox_to_anchor=(0.5, 1.02),
            ncol=2,
            frameon=False,
            fontsize=9,
        )

    def _plot_velocidade(self, data_frame: pd.DataFrame) -> None:
        """Plota o gráfico de velocidade ou exibe aviso de indisponibilidade."""
        self.line_velocidade = None

        if "Velocidade" not in data_frame.columns or data_frame["Velocidade"].isna().all():
            self.ax_velocidade.text(
                0.5,
                0.5,
                "Dados de Velocidade\nNão Disponíveis",
                ha="center",
                va="center",
                fontsize=12,
                color="gray",
                transform=self.ax_velocidade.transAxes,
            )
            self.ax_velocidade.set_title(
                "VELOCIDADE",
                fontsize=14,
                fontweight="bold",
                color=COR_VELOCIDADE,
                pad=30,
            )
            return

        self.line_velocidade, = self.ax_velocidade.plot(
            data_frame["Data"],
            data_frame["Velocidade"],
            label="VELOCIDADE",
            color=COR_VELOCIDADE,
            lw=1.2,
            linestyle="--",
        )
        self.ax_velocidade.set_title(
            "VELOCIDADE",
            fontsize=14,
            fontweight="bold",
            color=COR_VELOCIDADE,
            pad=30,
        )
        self.ax_velocidade.set_ylabel("Velocidade (m/s)", color=COR_VELOCIDADE, fontsize=11)
        self.ax_velocidade.xaxis.set_major_formatter(mdates.DateFormatter("%d/%m/%Y"))
        self.ax_velocidade.set_xlim(data_frame["Data"].min(), data_frame["Data"].max())
        self.ax_velocidade.set_ylim(bottom=data_frame["Velocidade"].min())
        self.ax_velocidade.grid(True, axis="y", linestyle=":", alpha=0.3)
        self.ax_velocidade.legend(
            loc="lower center",
            bbox_to_anchor=(0.5, 1.02),
            ncol=1,
            frameon=False,
            fontsize=9,
        )

    def _plot_nivel(self, data_frame: pd.DataFrame) -> None:
        """Plota o gráfico de nível ou exibe aviso de indisponibilidade."""
        self.line_nivel = None

        if "Nivel" not in data_frame.columns or data_frame["Nivel"].isna().all():
            self.ax_nivel.text(
                0.5,
                0.5,
                "Dados de Nível\nNão Disponíveis",
                ha="center",
                va="center",
                fontsize=12,
                color="gray",
                transform=self.ax_nivel.transAxes,
            )
            self.ax_nivel.set_title(
                "NÍVEL",
                fontsize=14,
                fontweight="bold",
                color=COR_NIVEL,
                pad=30,
            )
            return

        self.line_nivel, = self.ax_nivel.plot(
            data_frame["Data"],
            data_frame["Nivel"],
            label="NÍVEL",
            color=COR_NIVEL,
            lw=1.2,
        )
        self.ax_nivel.fill_between(
            data_frame["Data"],
            data_frame["Nivel"],
            color=COR_NIVEL,
            alpha=0.1,
        )
        self.ax_nivel.set_title(
            "NÍVEL",
            fontsize=14,
            fontweight="bold",
            color=COR_NIVEL,
            pad=30,
        )
        self.ax_nivel.set_ylabel("Nível (m)", color=COR_NIVEL, fontsize=11)
        self.ax_nivel.xaxis.set_major_formatter(mdates.DateFormatter("%d/%m/%Y"))
        self.ax_nivel.set_xlim(data_frame["Data"].min(), data_frame["Data"].max())
        self.ax_nivel.set_ylim(bottom=data_frame["Nivel"].min())
        self.ax_nivel.grid(True, axis="y", linestyle=":", alpha=0.3)
        self.ax_nivel.legend(
            loc="lower center",
            bbox_to_anchor=(0.5, 1.02),
            ncol=1,
            frameon=False,
            fontsize=9,
        )

    def _plot_area(self, data_frame: pd.DataFrame) -> None:
        """Plota o gráfico de área ou exibe aviso de indisponibilidade."""
        self.line_area = None

        if "Area" not in data_frame.columns or data_frame["Area"].isna().all():
            self.ax_area.text(
                0.5,
                0.5,
                "Dados de Área\nNão Disponíveis",
                ha="center",
                va="center",
                fontsize=12,
                color="gray",
                transform=self.ax_area.transAxes,
            )
            self.ax_area.set_title(
                "ÁREA",
                fontsize=14,
                fontweight="bold",
                color=COR_AREA,
                pad=30,
            )
            return

        self.line_area, = self.ax_area.plot(
            data_frame["Data"],
            data_frame["Area"],
            label="ÁREA",
            color=COR_AREA,
            lw=1.2,
        )
        self.ax_area.fill_between(
            data_frame["Data"],
            data_frame["Area"],
            color=COR_AREA,
            alpha=0.1,
        )
        self.ax_area.set_title(
            "ÁREA",
            fontsize=14,
            fontweight="bold",
            color=COR_AREA,
            pad=30,
        )
        self.ax_area.set_ylabel("Área (m²)", color=COR_AREA, fontsize=11)
        self.ax_area.xaxis.set_major_formatter(mdates.DateFormatter("%d/%m/%Y"))
        self.ax_area.set_xlim(data_frame["Data"].min(), data_frame["Data"].max())
        self.ax_area.set_ylim(bottom=data_frame["Area"].min())
        self.ax_area.grid(True, axis="y", linestyle=":", alpha=0.3)
        self.ax_area.legend(
            loc="lower center",
            bbox_to_anchor=(0.5, 1.02),
            ncol=1,
            frameon=False,
            fontsize=9,
        )

    def _export_report(self) -> None:
        """Exporta o dashboard detalhado como imagem PNG."""
        file_path: str = filedialog.asksaveasfilename(
            defaultextension=".png",
            filetypes=[("Imagem PNG", "*.png")],
        )
        if file_path:
            self.fig.savefig(file_path, dpi=300, bbox_inches="tight")

    def _add_info_panel(self, data_frame: pd.DataFrame, medidor_type: str) -> None:
        """Adiciona painel inferior com dados do medidor e período analisado."""
        info_frame: ctk.CTkFrame = ctk.CTkFrame(
            self.container_frame,
            fg_color="#f0f0f0",
            corner_radius=10,
            height=70,
        )
        info_frame.pack(side="bottom", fill="x", padx=10, pady=(5, 10))
        info_frame.pack_propagate(False)

        info_text: str = (
            f"Medidor: {medidor_type} ({self.medidor_model}) | "
            f"Período: {data_frame['Data'].min().strftime('%d/%m/%Y %H:%M')} até "
            f"{data_frame['Data'].max().strftime('%d/%m/%Y %H:%M')} | "
            f"Total de registros: {len(data_frame)}"
        )

        label: ctk.CTkLabel = ctk.CTkLabel(
            info_frame,
            text=info_text,
            font=("Arial", 12, "bold"),
            text_color="#333333",
        )
        label.pack(expand=True)
        info_frame.bind("<Configure>", lambda event: label.configure(wraplength=event.width - 40))

    def _setup_hover_elements(self, data_frame: pd.DataFrame) -> None:
        """Cria linhas verticais e anotações usadas no hover dos subgráficos."""
        ax_config: list[tuple[Axes, str, str]] = [
            (self.ax_vazao, "Vazao", COR_VAZAO),
            (self.ax_velocidade, "Velocidade", COR_VELOCIDADE),
            (self.ax_nivel, "Nivel", COR_NIVEL),
            (self.ax_area, "Area", COR_AREA),
        ]

        self._vert_lines = {}
        self._annotations = {}

        for ax, _column, _color in ax_config:
            vertical_line: Line2D = ax.axvline(
                x=data_frame["Data"].iloc[0],
                color="#333333",
                alpha=0.3,
                lw=0.8,
                visible=False,
                zorder=5,
            )
            annotation: Annotation = ax.annotate(
                "",
                xy=(0, 0),
                xytext=(15, 25),
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
            self._vert_lines[ax] = vertical_line
            self._annotations[ax] = annotation

    def _on_hover(self, event: MouseEvent) -> None:
        """Atualiza linha vertical e tooltip conforme a posição do mouse."""
        if event.inaxes is None or event.xdata is None:
            any_visible: bool = False

            for vertical_line in self._vert_lines.values():
                if vertical_line.get_visible():
                    any_visible = True
                    vertical_line.set_visible(False)

            for annotation in self._annotations.values():
                annotation.set_visible(False)

            if any_visible and self._background_cache is not None:
                self.canvas.restore_region(self._background_cache)
                self.canvas.blit(self.fig.bbox)

            self._last_hover_idx = None
            return

        ax_map: dict[Axes, tuple[str, str, str]] = {
            self.ax_vazao: ("Vazao", "VAZÃO", self.unit),
            self.ax_velocidade: ("Velocidade", "VELOCIDADE", "m/s"),
            self.ax_nivel: ("Nivel", "NÍVEL", "m"),
            self.ax_area: ("Area", "ÁREA", "m²"),
        }

        current_ax: Axes = event.inaxes
        if current_ax not in ax_map:
            return

        col_name, label, unit = ax_map[current_ax]
        if col_name not in self.data_frame.columns or self.data_frame[col_name].isna().all():
            return

        x_data: pd.Series = self.data_frame["Data"]
        y_data: pd.Series = self.data_frame[col_name]
        x_num: np.ndarray[Any, Any] = mdates.date2num(x_data)
        index: int = int(np.abs(x_num - event.xdata).argmin())

        if index == self._last_hover_idx:
            return

        self._last_hover_idx = index
        date_at: Any = x_data.iloc[index]
        value: Any = y_data.iloc[index]

        for vertical_line in self._vert_lines.values():
            vertical_line.set_visible(False)
        for annotation in self._annotations.values():
            annotation.set_visible(False)

        vertical_line = self._vert_lines[current_ax]
        annotation = self._annotations[current_ax]

        vertical_line.set_xdata([date_at, date_at])
        vertical_line.set_visible(True)
        annotation.xy = (date_at, value)

        mean_text: str = (
            f"\nMÉDIA: {self.mean_flow_value:,.2f} {unit}"
            if current_ax == self.ax_vazao
            else ""
        )
        annotation.set_text(
            f"DATA: {date_at.strftime('%d/%m/%Y %H:%M')}\n"
            f"{label}: {value:,.2f} {unit}{mean_text}"
        )
        annotation.set_visible(True)

        if self._background_cache is not None:
            self.canvas.restore_region(self._background_cache)

        current_ax.draw_artist(vertical_line)
        current_ax.draw_artist(annotation)
        self.canvas.blit(self.fig.bbox)

    def _on_draw(self, event: DrawEvent) -> None:
        """Atualiza o cache do canvas após redesenhar os gráficos."""
        del event

        for vertical_line in self._vert_lines.values():
            vertical_line.set_visible(False)
        for annotation in self._annotations.values():
            annotation.set_visible(False)

        self._background_cache = self.canvas.copy_from_bbox(self.fig.bbox)

    def _return_to_dashboard(self) -> None:
        """Fecha a janela detalhada e retorna ao dashboard principal."""
        plt.close(self.fig)
        self.destroy()

    def _on_closing(self) -> None:
        """Fecha corretamente a figura e a janela detalhada."""
        plt.close(self.fig)
        self.destroy()