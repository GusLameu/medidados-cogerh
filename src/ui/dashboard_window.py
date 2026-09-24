"""
Módulo responsável pela janela do dashboard que exibe os gráficos e métricas dos medidores.
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
from matplotlib.gridspec import GridSpec
from matplotlib.legend import Legend
from matplotlib.lines import Line2D
from matplotlib.patches import Wedge
from matplotlib.text import Annotation, Text
from matplotlib.ticker import FuncFormatter
from tkinter import filedialog, messagebox

from src.core.config import COR_VAZAO, COR_VELOCIDADE, CORES_ROSCA, MODELO_CONFIG, PIE_COLORS
from src.services.data_processing import DataProcessingService
from src.ui.detailed_dashboard_window import DetailedDashboardWindow
from src.utils.helpers import resource_path
from src.utils.logger import get_logger


logger = get_logger(__name__)

MetricCounts: TypeAlias = dict[str, int]
GeneralIndicators: TypeAlias = dict[str, Any]
PieChartConfig: TypeAlias = tuple[MetricCounts, str, tuple[int, int], str]
WedgeInfo: TypeAlias = dict[str, Any]
CanvasBackground: TypeAlias = Any


class DashboardWindow(ctk.CTkToplevel):
    """
    Janela do dashboard que exibe gráficos de vazão, velocidade e métricas de qualidade.

    O layout varia conforme o modelo do medidor: o MV145 usa um layout simplificado
    com vazão e volume, enquanto os demais modelos usam gráfico principal e roscas.
    """

    parent: ctk.CTk
    medidor_model: str
    data_frame: pd.DataFrame
    unit: str
    model_config: dict[str, Any]

    main_container: ctk.CTkFrame
    container_frame: ctk.CTkFrame
    total_label: ctk.CTkLabel
    general_indicators: GeneralIndicators

    fig: Figure
    canvas: FigureCanvasTkAgg
    ax_flow_speed: Axes
    ax_speed_twin: Optional[Axes]

    line_flow: Line2D
    line_speed: Optional[Line2D]
    main_legend: Legend
    vertical_line: Line2D
    annotation_line: Annotation
    annotation_pie: Text

    mean_flow_value: float
    wedges_info_map: dict[Wedge, WedgeInfo]
    pie_chart_legends: list[Legend]
    _last_hover_idx: Optional[int]
    _background_cache: Optional[CanvasBackground]

    def __init__(
        self,
        parent: ctk.CTk,
        data_frame: pd.DataFrame,
        medidor_model: str,
        medidor_type: str,
        unit: str = "m³/h",
    ) -> None:
        """
        Inicializa a janela do dashboard.

        Args:
            parent: Janela principal da aplicação.
            data_frame: DataFrame pandas com os dados já processados do medidor.
            medidor_model: Modelo do medidor.
            medidor_type: Tipo do medidor.
            unit: Unidade escolhida para exibir a vazão.
        """
        super().__init__(parent)

        self.unit = unit
        self.parent = parent
        self.medidor_model = medidor_model
        self.data_frame = data_frame
        self._last_hover_idx = None
        self._background_cache = None
        self.pie_chart_legends = []

        self.title(f"Medidados - Dashboard: {medidor_type} ({medidor_model})")
        self.state("zoomed")
        self.configure(fg_color="white")

        try:
            self.after(200, lambda: self.iconbitmap(resource_path("logo.ico")))
        except Exception:
            pass

        self.protocol("WM_DELETE_WINDOW", self._on_closing)

        self.model_config = MODELO_CONFIG.get(
            medidor_model.strip().upper(),
            MODELO_CONFIG["MV110"],
        )

        flow_ranges_raw, data_quality_raw, general_indicators = (
            DataProcessingService.calculate_dashboard_metrics(data_frame)
        )

        if medidor_model.strip().upper() == "MV145":
            flow_ranges_filtered: MetricCounts = {}
            data_quality_filtered: MetricCounts = {}
            hydraulic_status_filtered: MetricCounts = {}
            trigger_quality_filtered: MetricCounts = {}
            process_status_filtered: MetricCounts = {}
        else:
            flow_ranges_filtered = {key: value for key, value in flow_ranges_raw.items() if value > 0}
            data_quality_filtered = {key: value for key, value in data_quality_raw.items() if value > 0}

            hydraulic_status_raw: MetricCounts = (
                DataProcessingService.calculate_hydraulic_status(data_frame)
                if "status_hidraulico" in self.model_config["pie_charts"]
                else {}
            )
            hydraulic_status_filtered = {
                key: value for key, value in hydraulic_status_raw.items() if value > 0
            }

            trigger_quality_raw: MetricCounts = (
                DataProcessingService.calculate_trigger_quality_status(data_frame)
                if "qualidade_trigger" in self.model_config["pie_charts"]
                else {}
            )
            trigger_quality_filtered = {
                key: value for key, value in trigger_quality_raw.items() if value > 0
            }

            process_status_raw: MetricCounts = (
                DataProcessingService.calculate_process_status(data_frame)
                if "status_process" in self.model_config["pie_charts"]
                else {}
            )
            process_status_filtered = {
                key: value for key, value in process_status_raw.items() if value > 0
            }

        self.main_container = ctk.CTkFrame(self, fg_color="white")
        self.main_container.pack(fill="both", expand=True, padx=20, pady=20)

        self.container_frame = ctk.CTkFrame(self.main_container, fg_color="white")
        self.container_frame.pack(side="left", fill="both", expand=True)

        if medidor_model.strip().upper() == "MV145":
            self._setup_simplified_layout(data_frame, medidor_type, general_indicators)
        else:
            self._setup_complete_layout(
                data_frame,
                medidor_type,
                flow_ranges_filtered,
                data_quality_filtered,
                hydraulic_status_filtered,
                trigger_quality_filtered,
                process_status_filtered,
                general_indicators,
            )

    def _setup_simplified_layout(
        self,
        data_frame: pd.DataFrame,
        medidor_type: str,
        general_indicators: GeneralIndicators,
    ) -> None:
        """Configura o layout simplificado de vazão e volume do MV145."""
        self.fig = plt.figure(figsize=(16, 8), dpi=100)
        self.fig.subplots_adjust(top=0.82, bottom=0.10, left=0.07, right=0.93)

        self.ax_flow_speed = self.fig.add_subplot(111)

        self.line_flow, = self.ax_flow_speed.plot(
            data_frame["Data"],
            data_frame["Vazao"],
            label="VAZÃO",
            color=COR_VAZAO,
            lw=1.5,
        )
        self.ax_flow_speed.fill_between(
            data_frame["Data"],
            data_frame["Vazao"],
            color=COR_VAZAO,
            alpha=0.08,
        )
        self.ax_flow_speed.set_ylabel(
            f"Vazão ({self.unit})",
            color=COR_VAZAO,
            fontsize=12,
            fontweight="bold",
        )
        self.ax_flow_speed.set_title(
            f"MONITORAMENTO DE VAZÃO E VOLUME - {medidor_type} ({self.medidor_model})",
            fontsize=18,
            fontweight="bold",
            pad=70,
        )
        self.ax_flow_speed.xaxis.set_major_formatter(mdates.DateFormatter("%d/%m/%Y"))
        self.ax_flow_speed.set_xlim(data_frame["Data"].min(), data_frame["Data"].max())

        max_flow: float = float(data_frame["Vazao"].max()) if not data_frame["Vazao"].empty else 1.0
        self.ax_flow_speed.set_ylim(-max_flow * 0.05, max_flow * 1.3)
        self.ax_flow_speed.grid(True, axis="y", linestyle=":", alpha=0.3)

        flow_values: pd.Series = data_frame["Vazao"].dropna()
        self.mean_flow_value = float(flow_values.mean()) if not flow_values.empty else 0.0
        self.ax_flow_speed.axhline(
            y=self.mean_flow_value,
            color="green",
            linestyle=":",
            lw=1.5,
            alpha=0.7,
            label=f"MÉDIA ({self.mean_flow_value:,.2f})",
        )

        self.ax_speed_twin = None
        self.line_speed = None

        if "Volume" in data_frame.columns and not data_frame["Volume"].isna().all():
            self.ax_speed_twin = self.ax_flow_speed.twinx()
            self.line_speed, = self.ax_speed_twin.plot(
                data_frame["Data"],
                data_frame["Volume"],
                label="VOLUME",
                color="#2E7D32",
                lw=1.5,
                linestyle="--",
            )
            self.ax_speed_twin.set_ylabel(
                "Volume (m³)",
                color="#2E7D32",
                fontsize=12,
                fontweight="bold",
            )
            lines1, labels1 = self.ax_flow_speed.get_legend_handles_labels()
            lines2, labels2 = self.ax_speed_twin.get_legend_handles_labels()
            self.main_legend = self.ax_flow_speed.legend(
                lines1 + lines2,
                labels1 + labels2,
                loc="upper center",
                bbox_to_anchor=(0.5, 1.08),
                ncol=3,
                frameon=False,
                fontsize=10,
            )
        else:
            self.main_legend = self.ax_flow_speed.legend(
                loc="upper center",
                bbox_to_anchor=(0.5, 1.08),
                ncol=2,
                frameon=False,
                fontsize=10,
            )

        if "Volume" not in data_frame.columns:
            logger.warning(
                "Aviso: Coluna 'Volume' não encontrada nos dados. "
                "Gráfico de volume não será exibido."
            )

        self.vertical_line = self.ax_flow_speed.axvline(
            x=data_frame["Data"].iloc[0],
            color="#333333",
            alpha=0.3,
            lw=0.8,
            visible=False,
            zorder=5,
        )
        self.annotation_line = self.ax_flow_speed.annotate(
            "",
            xy=(0, 0),
            xytext=(20, 0),
            textcoords="offset points",
            bbox=dict(boxstyle="round,pad=0.5", fc="white", ec="black", lw=1, alpha=0.98),
            zorder=100,
            visible=False,
            clip_on=False,
        )
        self.annotation_pie = self.fig.text(
            0,
            0,
            "",
            bbox=dict(boxstyle="round,pad=0.5", fc="white", ec="black", lw=1, alpha=0.98),
            visible=False,
            zorder=101,
        )

        self.canvas = FigureCanvasTkAgg(self.fig, master=self.container_frame)
        self.canvas.get_tk_widget().pack(side="left", fill="both", expand=True)
        self.canvas.mpl_connect("motion_notify_event", self._on_hover)
        self.canvas.mpl_connect("draw_event", self._on_draw)

        self._add_sidebar(data_frame, general_indicators)

    def _setup_complete_layout(
        self,
        data_frame: pd.DataFrame,
        medidor_type: str,
        flow_ranges: MetricCounts,
        data_quality: MetricCounts,
        hydraulic_status: MetricCounts,
        trigger_quality: MetricCounts,
        process_status: MetricCounts,
        general_indicators: GeneralIndicators,
    ) -> None:
        """Configura o layout completo com gráfico principal e gráficos de rosca."""
        self.fig = plt.figure(figsize=(16, 10), dpi=100)

        num_pie_charts: int = len(self.model_config["pie_charts"])
        gs: GridSpec

        if num_pie_charts == 2:
            gs = self.fig.add_gridspec(
                2,
                2,
                height_ratios=[1.5, 1],
                hspace=0.6,
                wspace=0.3,
                top=0.82,
                bottom=0.15,
            )
        elif num_pie_charts == 3:
            gs = self.fig.add_gridspec(
                2,
                3,
                height_ratios=[1.5, 1],
                hspace=0.6,
                wspace=0.4,
                top=0.82,
                bottom=0.15,
            )
        elif num_pie_charts == 4:
            gs = self.fig.add_gridspec(
                2,
                4,
                height_ratios=[1.5, 1],
                hspace=0.6,
                wspace=0.4,
                top=0.82,
                bottom=0.15,
            )
        else:
            gs = self.fig.add_gridspec(1, 1, top=0.82, bottom=0.15)

        self.ax_flow_speed = self.fig.add_subplot(gs[0, :])
        self.ax_speed_twin = self.ax_flow_speed.twinx()

        self.ax_flow_speed.set_zorder(self.ax_speed_twin.get_zorder() + 1)
        self.ax_flow_speed.set_frame_on(False)
        for spine in self.ax_flow_speed.spines.values():
            spine.set_zorder(0)

        def format_mil(value: float, _position: Any) -> str:
            """Formata valores de vazão acima de mil para o eixo Y."""
            return f"{value / 1000:,.1f}mil".replace(".", ",") if value >= 1000 else str(int(value))

        self.ax_flow_speed.yaxis.set_major_formatter(FuncFormatter(format_mil))
        self.ax_flow_speed.set_ylabel(
            f"Vazão ({self.unit})",
            color=COR_VAZAO,
            fontsize=12,
            fontweight="bold",
        )
        self.ax_speed_twin.set_ylabel(
            "Velocidade (m/s)",
            color=COR_VELOCIDADE,
            fontsize=12,
            fontweight="bold",
        )
        self.ax_flow_speed.set_title(
            f"MONITORAMENTO DE VAZÃO E VELOCIDADE - {medidor_type} ({self.medidor_model})",
            fontsize=18,
            fontweight="bold",
            pad=55,
        )
        self.ax_flow_speed.xaxis.set_major_formatter(mdates.DateFormatter("%d/%m/%Y"))
        self.ax_flow_speed.set_xlim(data_frame["Data"].min(), data_frame["Data"].max())

        max_flow: float = float(data_frame["Vazao"].max()) if not data_frame["Vazao"].empty else 1.0
        max_speed: float = (
            float(data_frame["Velocidade"].max())
            if "Velocidade" in data_frame.columns and not data_frame["Velocidade"].empty
            else 1.0
        )
        self.ax_flow_speed.set_ylim(0, max_flow * 1.3)
        self.ax_speed_twin.set_ylim(0, max_speed * 2.8)

        self.line_flow, = self.ax_flow_speed.plot(
            data_frame["Data"],
            data_frame["Vazao"],
            label="VAZÃO",
            color=COR_VAZAO,
            lw=1.0,
        )
        self.ax_flow_speed.fill_between(
            data_frame["Data"],
            data_frame["Vazao"],
            color=COR_VAZAO,
            alpha=0.08,
        )
        self.line_speed, = self.ax_speed_twin.plot(
            data_frame["Data"],
            data_frame["Velocidade"],
            label="VELOCIDADE",
            color=COR_VELOCIDADE,
            lw=0.8,
            linestyle="--",
        )

        flow_values: pd.Series = data_frame["Vazao"].dropna()
        self.mean_flow_value = float(flow_values.mean()) if not flow_values.empty else 0.0
        self.ax_flow_speed.axhline(
            y=self.mean_flow_value,
            color="green",
            linestyle=":",
            lw=1.5,
            alpha=0.7,
            label=f"MÉDIA ({self.mean_flow_value:,.2f})",
        )

        lines1, labels1 = self.ax_flow_speed.get_legend_handles_labels()
        lines2, labels2 = self.ax_speed_twin.get_legend_handles_labels()
        self.main_legend = self.ax_flow_speed.legend(
            lines1 + lines2,
            labels1 + labels2,
            loc="upper center",
            bbox_to_anchor=(0.5, 1.18),
            ncol=3,
            frameon=False,
            fontsize=10,
        )

        self.ax_flow_speed.grid(True, axis="y", linestyle=":", alpha=0.3)

        self.vertical_line = self.ax_flow_speed.axvline(
            x=data_frame["Data"].iloc[0],
            color="#333333",
            alpha=0.3,
            lw=0.8,
            visible=False,
            zorder=5,
        )
        self.annotation_line = self.ax_flow_speed.annotate(
            "",
            xy=(0, 0),
            xytext=(20, 35),
            textcoords="offset points",
            bbox=dict(boxstyle="round,pad=0.5", fc="white", ec="black", lw=1, alpha=0.98),
            zorder=100,
            visible=False,
            clip_on=False,
        )
        self.annotation_pie = self.fig.text(
            0,
            0,
            "",
            bbox=dict(boxstyle="round,pad=0.5", fc="white", ec="black", lw=1, alpha=0.98),
            visible=False,
            zorder=101,
        )
        self.wedges_info_map = {}

        pie_configs: list[PieChartConfig] = []
        col_idx: int = 0

        if "vazao" in self.model_config["pie_charts"]:
            pie_configs.append((flow_ranges, "Faixa de Vazão", (1, col_idx), "vazao"))
            col_idx += 1

        if "qualidade" in self.model_config["pie_charts"]:
            pie_configs.append((data_quality, "Qualidade Telemetria", (1, col_idx), "qualidade"))
            col_idx += 1

        if "status_process" in self.model_config["pie_charts"]:
            pie_configs.append((process_status, "Status de Processo", (1, col_idx), "status_process"))
            col_idx += 1

        if "status_hidraulico" in self.model_config["pie_charts"]:
            pie_configs.append(
                (hydraulic_status, "Qualidade Hidráulica", (1, col_idx), "status_hidraulico")
            )
            col_idx += 1

        if "qualidade_trigger" in self.model_config["pie_charts"]:
            pie_configs.append((trigger_quality, "Qualidade Trigger", (1, col_idx), "qualidade_trigger"))

        for data_dict, title, grid_pos, chart_type in pie_configs:
            self._create_pie_chart(self.fig, gs, data_dict, title, grid_pos, chart_type)

        self.canvas = FigureCanvasTkAgg(self.fig, master=self.container_frame)
        self.canvas.get_tk_widget().pack(side="left", fill="both", expand=True)
        self.canvas.mpl_connect("motion_notify_event", self._on_hover)
        self.canvas.mpl_connect("draw_event", self._on_draw)

        self._add_sidebar(data_frame, general_indicators)

    def _create_pie_chart(
        self,
        fig: Figure,
        gs: GridSpec,
        data_dict: MetricCounts,
        title: str,
        grid_pos: tuple[int, int],
        chart_type: str,
    ) -> None:
        """Cria um gráfico de rosca com cores, legendas e percentuais."""
        ax: Axes = fig.add_subplot(gs[grid_pos[0], grid_pos[1]])
        values: list[int] = list(data_dict.values())
        labels: list[str] = list(data_dict.keys())
        total_sum: int = sum(values) if sum(values) > 0 else 1

        color_config: dict[str, Any] = PIE_COLORS.get(chart_type, {})
        patterns: dict[str, str] = color_config.get("patterns", {})
        default_colors: list[str] = color_config.get("default", CORES_ROSCA)

        current_colors: list[str] = []
        for label in labels:
            color_assigned: bool = False
            normalized_label: str = str(label).replace(" ", "").lower()

            for pattern, color in patterns.items():
                normalized_pattern: str = str(pattern).replace(" ", "").lower()
                if normalized_pattern in normalized_label:
                    current_colors.append(color)
                    color_assigned = True
                    break

            if not color_assigned:
                current_colors.append(default_colors[len(current_colors) % len(default_colors)])

        wedges: list[Wedge]
        wedges, _texts = ax.pie(
            values,
            startangle=90,
            colors=current_colors,
            wedgeprops={"width": 0.35, "edgecolor": "white"},
        )
        ax.set_title(title, fontsize=14, fontweight="bold", pad=25)

        legend: Legend = ax.legend(
            wedges,
            labels,
            title="Categorias",
            loc="upper center",
            bbox_to_anchor=(0.5, -0.1),
            ncol=2,
            frameon=False,
            fontsize=9,
        )
        self.pie_chart_legends.append(legend)

        annotations_data: list[dict[str, Any]] = []
        for index, wedge in enumerate(wedges):
            percentage: float = values[index] / total_sum * 100
            if percentage < 0.1:
                continue

            angle_rad: float = (
                (wedge.theta2 - wedge.theta1) / 2.0 * np.pi / 180.0
                + wedge.theta1 * np.pi / 180.0
            )
            y_coord: float = float(np.sin(angle_rad))
            x_coord: float = float(np.cos(angle_rad))
            annotations_data.append(
                {
                    "x": x_coord,
                    "y": y_coord,
                    "pct": percentage,
                    "angle": angle_rad,
                    "wedge": wedge,
                    "label": labels[index],
                    "value": values[index],
                }
            )

        annotations_data.sort(key=lambda item: float(item["y"]), reverse=True)

        occupied_y_left: list[float] = []
        occupied_y_right: list[float] = []
        min_vertical_dist: float = 0.18

        for annotation_data in annotations_data:
            is_right_side: bool = float(annotation_data["x"]) > 0
            reference_list: list[float] = occupied_y_right if is_right_side else occupied_y_left

            horizontal_alignment: str = "left" if is_right_side else "right"
            x_position: float = 1.35 if is_right_side else -1.35
            y_position: float = 1.3 * float(annotation_data["y"])

            if reference_list:
                last_y: float = reference_list[-1]
                if abs(y_position - last_y) < min_vertical_dist:
                    y_position = last_y - min_vertical_dist

            ax.annotate(
                f"{float(annotation_data['pct']):.1f}%",
                xy=(float(annotation_data["x"]), float(annotation_data["y"])),
                xytext=(x_position, y_position),
                textcoords="data",
                ha=horizontal_alignment,
                fontsize=8,
                fontweight="bold",
                bbox=dict(boxstyle="round,pad=0.3", fc="white", ec="white", alpha=0.7),
                arrowprops=dict(arrowstyle="-", color="black", lw=0.5),
            )
            reference_list.append(y_position)

            wedge = annotation_data["wedge"]
            if isinstance(wedge, Wedge):
                self.wedges_info_map[wedge] = {
                    "label": annotation_data["label"],
                    "value": annotation_data["value"],
                    "total": total_sum,
                }

    def _add_sidebar(
        self,
        data_frame: pd.DataFrame,
        general_indicators: Optional[GeneralIndicators] = None,
    ) -> None:
        """Adiciona a barra lateral com informações gerais e ações do dashboard."""
        sidebar_frame: ctk.CTkFrame = ctk.CTkFrame(
            self.container_frame,
            width=320,
            fg_color="#f0f0f0",
            corner_radius=15,
        )
        sidebar_frame.pack(side="right", fill="y", padx=10, pady=20)

        if general_indicators:
            self._add_info_label(
                sidebar_frame,
                "Nº DE SÉRIE",
                general_indicators.get("serial_number", "N/A"),
            )

            ctk.CTkLabel(
                sidebar_frame,
                text="PERÍODO",
                font=("Arial", 11, "bold"),
                text_color="#666666",
            ).pack(pady=(30, 0))

            if "start_date" in general_indicators and "end_date" in general_indicators:
                ctk.CTkLabel(
                    sidebar_frame,
                    text=(
                        f"{general_indicators['start_date'].strftime('%d/%m/%Y %H:%M')}\n"
                        "até\n"
                        f"{general_indicators['end_date'].strftime('%d/%m/%Y %H:%M')}"
                    ),
                    font=("Arial", 12, "bold"),
                    text_color="#000000",
                ).pack(pady=5)

            if self.medidor_model.strip().upper() != "MV145":
                ctk.CTkLabel(
                    sidebar_frame,
                    text="TOTAL POSITIVO ≈",
                    font=("Arial", 11, "bold"),
                    text_color="#666666",
                ).pack(pady=(30, 0))

                self.total_label = ctk.CTkLabel(
                    sidebar_frame,
                    text="",
                    font=("Arial", 22, "bold"),
                    text_color="#000000",
                )
                self.total_label.pack(pady=(0, 5))
                self.general_indicators = general_indicators
                self._update_total_label()
        else:
            ctk.CTkLabel(
                sidebar_frame,
                text="PERÍODO",
                font=("Arial", 11, "bold"),
                text_color="#666666",
            ).pack(pady=(30, 0))

            if not data_frame.empty:
                ctk.CTkLabel(
                    sidebar_frame,
                    text=(
                        f"{data_frame['Data'].min().strftime('%d/%m/%Y %H:%M')}\n"
                        "até\n"
                        f"{data_frame['Data'].max().strftime('%d/%m/%Y %H:%M')}"
                    ),
                    font=("Arial", 12, "bold"),
                    text_color="#000000",
                ).pack(pady=5)

        if (
            self.medidor_model.strip().upper() == "NF750"
            and "Area" in data_frame.columns
            and "Nivel" in data_frame.columns
        ):
            ctk.CTkButton(
                sidebar_frame,
                text="Detalhar",
                command=self._open_detailed_dashboard,
                fg_color=COR_VAZAO,
                height=45,
            ).pack(pady=(10, 10), padx=30, fill="x")

        ctk.CTkButton(
            sidebar_frame,
            text="Exportar Relatório",
            command=self._export_report,
            fg_color=COR_VAZAO,
            height=45,
        ).pack(pady=(10, 10), padx=30, fill="x")

        ctk.CTkButton(
            sidebar_frame,
            text="Nova Importação",
            command=self._return_to_import,
            fg_color="#6c757d",
            height=45,
        ).pack(pady=10, padx=30, fill="x")

    def _add_info_label(self, master_frame: ctk.CTkFrame, title: str, value: Any) -> None:
        """Adiciona um par de labels de título e valor ao frame informado."""
        ctk.CTkLabel(
            master_frame,
            text=title,
            font=("Arial", 11, "bold"),
            text_color="#666666",
        ).pack(pady=(30, 0))
        ctk.CTkLabel(
            master_frame,
            text=str(value),
            font=("Arial", 22, "bold"),
            text_color="#000000",
        ).pack(pady=(0, 5))

    def _update_total_label(self) -> None:
        """Atualiza o label do total positivo conforme a unidade selecionada."""
        if not hasattr(self, "total_label") or not hasattr(self, "general_indicators"):
            return

        total_value: Any = self.general_indicators.get("total_positive_accumulated", 0)
        unit_display: str = "L" if self.unit == "l/s" else "m³"

        self.total_label.configure(
            text=f"{float(total_value):,.0f} {unit_display}".replace(",", ".")
        )

    def _redraw_static_elements(self) -> None:
        """Redesenha legendas estáticas após restaurar o cache do canvas."""
        if hasattr(self, "main_legend"):
            self.ax_flow_speed.draw_artist(self.main_legend)

        for legend in self.pie_chart_legends:
            self.fig.draw_artist(legend)

    def _on_draw(self, event: DrawEvent) -> None:
        """Armazena o fundo do canvas após o redesenho dos gráficos."""
        del event

        if hasattr(self, "vertical_line"):
            self.vertical_line.set_visible(False)
            self.annotation_line.set_visible(False)
            self.annotation_pie.set_visible(False)

        self._redraw_static_elements()
        self._background_cache = self.canvas.copy_from_bbox(self.fig.bbox)

    def _on_hover(self, event: MouseEvent) -> None:
        """Atualiza tooltips para gráfico principal e gráficos de rosca."""
        if event.inaxes is None or event.xdata is None:
            if (
                hasattr(self, "vertical_line")
                and (
                    self.vertical_line.get_visible()
                    or self.annotation_line.get_visible()
                    or self.annotation_pie.get_visible()
                )
            ):
                if self._background_cache is not None:
                    self.canvas.restore_region(self._background_cache)
                self._redraw_static_elements()
                self.canvas.blit(self.fig.bbox)

            if hasattr(self, "vertical_line"):
                self.vertical_line.set_visible(False)
                self.annotation_line.set_visible(False)
                self.annotation_pie.set_visible(False)

            self._last_hover_idx = None
            return

        if (
            hasattr(self, "ax_flow_speed")
            and event.inaxes in [self.ax_flow_speed, self.ax_speed_twin]
        ):
            x_data, y_flow = self.line_flow.get_data()
            x_num: np.ndarray[Any, Any] = mdates.date2num(x_data)
            index: int = int(np.abs(x_num - event.xdata).argmin())

            if index == self._last_hover_idx:
                return

            self._last_hover_idx = index
            date_at: Any = x_data[index]
            flow_val: float = float(y_flow[index])
            xlim: tuple[float, float] = self.ax_flow_speed.get_xlim()
            ylim: tuple[float, float] = self.ax_flow_speed.get_ylim()

            offset_x: int = (
                -175
                if event.xdata > (xlim[0] + (xlim[1] - xlim[0]) * 0.7)
                else 25
            )
            offset_y: int = 35 if flow_val < (ylim[1] * 0.6) else -110

            self.vertical_line.set_xdata([date_at, date_at])
            self.vertical_line.set_visible(True)
            self.annotation_line.xy = (date_at, flow_val)
            self.annotation_line.set_position((offset_x, offset_y))

            if self.line_speed is not None:
                extra_val: float = float(self.line_speed.get_data()[1][index])
                extra_label: str = "VOLUME" if self.medidor_model == "MV145" else "VELOCIDADE"
                extra_unit: str = "m³" if self.medidor_model == "MV145" else "m/s"
                tooltip_text: str = (
                    f"DATA: {pd.Timestamp(date_at).strftime('%d/%m/%Y %H:%M')}\n"
                    f"VAZÃO: {flow_val:,.2f} {self.unit}\n"
                    f"MÉDIA: {self.mean_flow_value:,.2f} {self.unit}\n"
                    f"{extra_label}: {extra_val:,.2f} {extra_unit}"
                )
            else:
                tooltip_text = (
                    f"DATA: {pd.Timestamp(date_at).strftime('%d/%m/%Y %H:%M')}\n"
                    f"VAZÃO: {flow_val:,.2f} {self.unit}\n"
                    f"MÉDIA: {self.mean_flow_value:,.2f} {self.unit}"
                )

            self.annotation_line.set_text(tooltip_text)
            self.annotation_line.set_visible(True)
            self.annotation_pie.set_visible(False)

            if self._background_cache is not None:
                self.canvas.restore_region(self._background_cache)

            self._redraw_static_elements()
            self.ax_flow_speed.draw_artist(self.vertical_line)
            self.ax_flow_speed.draw_artist(self.annotation_line)
            self.canvas.blit(self.fig.bbox)
            return

        if not hasattr(self, "wedges_info_map"):
            return

        found_pie_wedge: bool = False
        for wedge, info in self.wedges_info_map.items():
            if wedge.contains_point([event.x, event.y]):
                total: float = float(info["total"]) if info["total"] > 0 else 1.0
                percentage: float = float(info["value"]) / total * 100
                self.annotation_pie.set_text(
                    f"CATEGORIA: {info['label']}\nPERCENTUAL: {percentage:.1f}%"
                )
                self.annotation_pie.set_position(
                    (
                        event.x / self.fig.bbox.width + 0.01,
                        event.y / self.fig.bbox.height + 0.01,
                    )
                )
                self.annotation_pie.set_visible(True)
                self.vertical_line.set_visible(False)
                self.annotation_line.set_visible(False)

                if self._background_cache is not None:
                    self.canvas.restore_region(self._background_cache)

                self._redraw_static_elements()
                self.fig.draw_artist(self.annotation_pie)
                self.canvas.blit(self.fig.bbox)
                self._last_hover_idx = None
                found_pie_wedge = True
                break

        if not found_pie_wedge and self.annotation_pie.get_visible():
            self.annotation_pie.set_visible(False)
            if self._background_cache is not None:
                self.canvas.restore_region(self._background_cache)
            self._redraw_static_elements()
            self.canvas.blit(self.fig.bbox)

    def _open_detailed_dashboard(self) -> None:
        """Abre o dashboard detalhado com vazão, velocidade, nível e área."""
        window_title: str = self.title()
        medidor_type: str = (
            window_title.replace("Medidados - Dashboard: ", "").split(" (")[0]
            if "Dashboard: " in window_title
            else self.medidor_model
        )
        DetailedDashboardWindow(
            parent=self,
            data_frame=self.data_frame,
            medidor_model=self.medidor_model,
            medidor_type=medidor_type,
            unit=self.unit,
        )

    def _return_to_import(self) -> None:
        """Fecha o dashboard e retorna para a janela principal de importação."""
        plt.close(self.fig)
        self.parent.deiconify()
        self.destroy()

    def _on_closing(self) -> None:
        """Confirma o encerramento e fecha corretamente todas as janelas."""
        if not messagebox.askokcancel("Sair", "Deseja realmente fechar o programa?"):
            return

        try:
            plt.close("all")
            self.destroy()
            self.parent.destroy()
        except Exception as error:
            logger.error(f"Erro ao fechar dashboard: {error}")
            try:
                self.destroy()
                self.parent.destroy()
            except Exception:
                pass

    def _export_report(self) -> None:
        """Exporta o gráfico do dashboard como uma imagem PNG."""
        file_path: str = filedialog.asksaveasfilename(
            defaultextension=".png",
            filetypes=[("Imagem PNG", "*.png")],
        )
        if file_path:
            self.fig.savefig(file_path, dpi=300, bbox_inches="tight")