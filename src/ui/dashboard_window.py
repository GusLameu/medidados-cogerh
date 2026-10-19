"""
Módulo responsável pela janela do dashboard que exibe os gráficos e métricas dos medidores.
"""
from typing import Any, Optional, TypeAlias

import customtkinter as ctk
import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.axes import Axes
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
from matplotlib.gridspec import GridSpec
from matplotlib.legend import Legend
from matplotlib.lines import Line2D
from matplotlib.patches import Wedge
from tkinter import filedialog, messagebox

from src.core.config import MODELO_CONFIG, ANOMALY_CONFIG
from src.services.data_processing import DataProcessingService
from src.services.anomaly_detection import AnomalyConfig, AnomalyDetectionService
from src.ui.detailed_dashboard_window import DetailedDashboardWindow
from src.utils.helpers import resource_path
from src.utils.logger import get_logger
from src.ui.anomalies_window import AnomaliesWindow
from src.ui.dashboard.pie_chart_builder import PieChartBuilder
from src.ui.dashboard.chart_builder import MainChartBuilder
from src.ui.dashboard.sidebar import DashboardSidebar
from src.ui.dashboard.types import WedgeInfoMap, MainChartResult
from src.ui.dashboard.hover_controller import DashboardHoverController


logger = get_logger(__name__)

MetricCounts: TypeAlias = dict[str, int]
GeneralIndicators: TypeAlias = dict[str, Any]
PieChartConfig: TypeAlias = tuple[MetricCounts, str, tuple[int, int], str]
WedgeInfo: TypeAlias = dict[str, Any]


class DashboardWindow(ctk.CTkToplevel):
    """
    Janela do dashboard que exibe gráficos de vazão, velocidade e métricas de qualidade.
    """

    parent: ctk.CTk
    medidor_model: str
    data_frame: pd.DataFrame
    unit: str
    model_config: dict[str, Any]

    main_container: ctk.CTkFrame
    container_frame: ctk.CTkFrame
    general_indicators: GeneralIndicators

    fig: Figure
    canvas: FigureCanvasTkAgg
    ax_flow_speed: Axes
    ax_speed_twin: Optional[Axes]

    line_flow: Line2D
    line_speed: Optional[Line2D]
    main_legend: Legend

    mean_flow_value: float
    wedges_info_map: dict[Wedge, WedgeInfo]
    pie_chart_legends: list[Legend]
    hover_controller: DashboardHoverController
    sidebar: DashboardSidebar

    def __init__(
        self,
        parent: ctk.CTk,
        data_frame: pd.DataFrame,
        medidor_model: str,
        medidor_type: str,
        unit: str = "m³/h",
    ) -> None:
        super().__init__(parent)

        self.unit = unit
        self.parent = parent
        self.medidor_model = medidor_model
        self.data_frame = data_frame
        self.pie_chart_legends = []

        # Configura a detecção de anomalias.
        threshold = ANOMALY_CONFIG["positive_jump_threshold"]
        tolerance = ANOMALY_CONFIG["negative_tolerance"]
        max_interval = ANOMALY_CONFIG["max_interval_minutes"]

        if threshold is None or tolerance is None:
            raise ValueError(
                "O limite de salto e a tolerância negativa "
                "devem estar configurados."
            )

        self.anomaly_config: AnomalyConfig = AnomalyConfig(
            positive_jump_threshold=threshold,
            negative_tolerance=tolerance,
            max_interval_minutes=max_interval,
        )

        # Executa a detecção antes da construção da sidebar.
        self.anomalies_df: pd.DataFrame = AnomalyDetectionService.detect(
            data_frame=self.data_frame,
            config=self.anomaly_config,
        )

        self.anomalies_window: AnomaliesWindow | None = None

        self.title(
            f"Medidados - Dashboard: {medidor_type} ({medidor_model})"
        )
        self.state("zoomed")
        self.configure(fg_color="white")

        try:
            self.after(
                200,
                lambda: self.iconbitmap(resource_path("logo.ico")),
            )
        except Exception:
            pass

        self.protocol("WM_DELETE_WINDOW", self._on_closing)

        normalized_model: str = medidor_model.strip().upper()

        self.model_config = MODELO_CONFIG.get(
            normalized_model,
            MODELO_CONFIG["MV110"],
        )

        # Calcula as métricas gerais do dashboard.
        flow_ranges_raw, data_quality_raw, general_indicators = (
            DataProcessingService.calculate_dashboard_metrics(data_frame)
        )

        if normalized_model == "MV145":
            flow_ranges_filtered: MetricCounts = {}
            data_quality_filtered: MetricCounts = {}
            hydraulic_status_filtered: MetricCounts = {}
            trigger_quality_filtered: MetricCounts = {}
            process_status_filtered: MetricCounts = {}
        else:
            flow_ranges_filtered = {
                key: value
                for key, value in flow_ranges_raw.items()
                if value > 0
            }

            data_quality_filtered = {
                key: value
                for key, value in data_quality_raw.items()
                if value > 0
            }

            hydraulic_status_raw: MetricCounts = (
                DataProcessingService.calculate_hydraulic_status(data_frame)
                if "status_hidraulico" in self.model_config["pie_charts"]
                else {}
            )

            hydraulic_status_filtered = {
                key: value
                for key, value in hydraulic_status_raw.items()
                if value > 0
            }

            trigger_quality_raw: MetricCounts = (
                DataProcessingService.calculate_trigger_quality_status(data_frame)
                if "qualidade_trigger" in self.model_config["pie_charts"]
                else {}
            )

            trigger_quality_filtered = {
                key: value
                for key, value in trigger_quality_raw.items()
                if value > 0
            }

            process_status_raw: MetricCounts = (
                DataProcessingService.calculate_process_status(data_frame)
                if "status_process" in self.model_config["pie_charts"]
                else {}
            )

            process_status_filtered = {
                key: value
                for key, value in process_status_raw.items()
                if value > 0
            }

        # Cria os containers da interface.
        self.main_container = ctk.CTkFrame(
            self,
            fg_color="white",
        )
        self.main_container.pack(
            fill="both",
            expand=True,
            padx=20,
            pady=20,
        )

        self.container_frame = ctk.CTkFrame(
            self.main_container,
            fg_color="white",
        )
        self.container_frame.pack(
            side="left",
            fill="both",
            expand=True,
        )

        # Monta o layout adequado ao modelo.
        if normalized_model == "MV145":
            self._setup_simplified_layout(
                data_frame,
                medidor_type,
                general_indicators,
            )
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
        self.fig = plt.figure(figsize=(16, 8), dpi=100)

        chart_result: MainChartResult = MainChartBuilder.build_simplified(
            figure=self.fig,
            data_frame=data_frame,
            medidor_model=self.medidor_model,
            medidor_type=medidor_type,
            unit=self.unit,
        )

        self.ax_flow_speed = chart_result.flow_axis
        self.ax_speed_twin = chart_result.secondary_axis
        self.line_flow = chart_result.flow_line
        self.line_speed = chart_result.secondary_line
        self.main_legend = chart_result.legend
        self.mean_flow_value = chart_result.mean_flow

        if "Volume" not in data_frame.columns:
            logger.warning(
                "Aviso: Coluna 'Volume' não encontrada nos dados."
            )

        self.canvas = FigureCanvasTkAgg(
            self.fig,
            master=self.container_frame,
        )
        self.canvas.get_tk_widget().pack(
            side="left",
            fill="both",
            expand=True,
        )

        self.hover_controller = DashboardHoverController(
            canvas=self.canvas,
            figure=self.fig,
            flow_axis=self.ax_flow_speed,
            secondary_axis=self.ax_speed_twin,
            flow_line=self.line_flow,
            secondary_line=self.line_speed,
            main_legend=self.main_legend,
            pie_legends=self.pie_chart_legends,
            wedge_info_map=getattr(self, "wedges_info_map", {}),
            unit=self.unit,
            medidor_model=self.medidor_model,
            mean_flow=self.mean_flow_value,
        )

        self.canvas.mpl_connect(
            "motion_notify_event",
            self.hover_controller.on_hover,
        )

        self.canvas.mpl_connect(
            "draw_event",
            self.hover_controller.on_draw,
        )

        self.sidebar = DashboardSidebar(
            master=self.container_frame,
            data_frame=data_frame,
            medidor_model=self.medidor_model,
            unit=self.unit,
            general_indicators=general_indicators,
            on_open_details=self._open_detailed_dashboard,
            on_export=self._export_report,
            on_new_import=self._return_to_import,
            anomaly_count=len(self.anomalies_df),
            on_open_anomalies=self._open_anomalies_window,
        )

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
        self.fig = plt.figure(figsize=(16, 10), dpi=100)

        num_pie_charts: int = len(self.model_config["pie_charts"])
        gs: GridSpec

        if num_pie_charts in (2, 3, 4):
            gs = self.fig.add_gridspec(
                2,
                num_pie_charts,
                height_ratios=[1.5, 1],
                hspace=0.6,
                wspace=0.4 if num_pie_charts > 2 else 0.3,
                top=0.82,
                bottom=0.15,
            )
        else:
            gs = self.fig.add_gridspec(
                1,
                1,
                top=0.82,
                bottom=0.15,
            )

        chart_result: MainChartResult = MainChartBuilder.build_complete(
            figure=self.fig,
            grid_spec=gs,
            data_frame=data_frame,
            medidor_model=self.medidor_model,
            medidor_type=medidor_type,
            unit=self.unit,
        )

        self.ax_flow_speed = chart_result.flow_axis
        self.ax_speed_twin = chart_result.secondary_axis
        self.line_flow = chart_result.flow_line
        self.line_speed = chart_result.secondary_line
        self.main_legend = chart_result.legend
        self.mean_flow_value = chart_result.mean_flow

        self.wedges_info_map: WedgeInfoMap = {}

        pie_definitions = [
            ("vazao", flow_ranges, "Faixa de Vazão"),
            ("qualidade", data_quality, "Qualidade Telemetria"),
            ("status_process", process_status, "Status de Processo"),
            ("status_hidraulico", hydraulic_status, "Qualidade Hidráulica"),
            ("qualidade_trigger", trigger_quality, "Qualidade Trigger"),
        ]

        col_idx: int = 0
        for chart_key, data_dict, title in pie_definitions:
            if chart_key in self.model_config["pie_charts"]:
                pie_result = PieChartBuilder.build(
                    figure=self.fig,
                    grid_spec=gs,
                    data=data_dict,
                    title=title,
                    grid_position=(1, col_idx),
                    chart_type=chart_key,
                )
                self.pie_chart_legends.append(pie_result.legend)
                self.wedges_info_map.update(pie_result.wedge_info_map)
                col_idx += 1

        self.canvas = FigureCanvasTkAgg(
            self.fig,
            master=self.container_frame,
        )
        self.canvas.get_tk_widget().pack(
            side="left",
            fill="both",
            expand=True,
        )

        self.hover_controller = DashboardHoverController(
            canvas=self.canvas,
            figure=self.fig,
            flow_axis=self.ax_flow_speed,
            secondary_axis=self.ax_speed_twin,
            flow_line=self.line_flow,
            secondary_line=self.line_speed,
            main_legend=self.main_legend,
            pie_legends=self.pie_chart_legends,
            wedge_info_map=self.wedges_info_map,
            unit=self.unit,
            medidor_model=self.medidor_model,
            mean_flow=self.mean_flow_value,
        )

        self.canvas.mpl_connect(
            "motion_notify_event",
            self.hover_controller.on_hover,
        )

        self.canvas.mpl_connect(
            "draw_event",
            self.hover_controller.on_draw,
        )

        self.sidebar = DashboardSidebar(
            master=self.container_frame,
            data_frame=data_frame,
            medidor_model=self.medidor_model,
            unit=self.unit,
            general_indicators=general_indicators,
            on_open_details=self._open_detailed_dashboard,
            on_export=self._export_report,
            on_new_import=self._return_to_import,
            anomaly_count=len(self.anomalies_df),
            on_open_anomalies=self._open_anomalies_window,
        )

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

    def _open_anomalies_window(self) -> None:
        """Abre a visualização ou traz uma janela existente para frente."""
        if self.anomalies_df.empty:
            return

        existing_window = self.anomalies_window

        if existing_window is not None and existing_window.winfo_exists():
            existing_window.deiconify()
            existing_window.lift()
            existing_window.focus_set()
            return

        self.anomalies_window = AnomaliesWindow(
            parent=self,
            anomalies_df=self.anomalies_df,
            medidor_model=self.medidor_model,
            config=self.anomaly_config,
        )