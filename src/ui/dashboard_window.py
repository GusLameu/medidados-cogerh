"""
Módulo responsável pela janela do dashboard que exibe os gráficos e métricas dos medidores.
"""
import pandas as pd
import customtkinter as ctk
from tkinter import filedialog, messagebox
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.ticker import FuncFormatter
import numpy as np
import sys
from typing import Optional, Dict, Any, Tuple, List

from src.services.data_processing import DataProcessingService
from src.utils.helpers import resource_path
from src.core.config import (
    COR_VAZAO, COR_VELOCIDADE, COR_TEXTO, CORES_ROSCA, 
    MODELO_CONFIG, COR_STATUS_RUIM, COR_STATUS_MEDIO, COR_STATUS_BOM,
    PIE_COLORS
)

class DashboardWindow(ctk.CTkToplevel):
    """
    Janela do dashboard que exibe gráficos de vazão/velocidade e métricas de qualidade.
    O layout varia conforme o modelo do medidor.
    """
    def __init__(self, parent: ctk.CTk, data_frame: pd.DataFrame, medidor_model: str, medidor_type: str):
        """
        Inicializa a janela do dashboard.

        Args:
            parent: A janela pai (AppAnalise).
            data_frame: O DataFrame pandas com os dados processados do medidor.
            medidor_model: O modelo do medidor.
            medidor_type: O tipo do medidor.
        """
        super().__init__(parent)
        self.parent = parent
        self.medidor_model = medidor_model
        self.data_frame = data_frame
        self.title(f"Medidados - Dashboard: {medidor_type} ({medidor_model})")
        self._last_hover_idx: Optional[int] = None 
        self._background_cache: Optional[Any] = None 
        self.pie_chart_legends: List[Any] = [] 
        self.state('zoomed')
        self.configure(fg_color="white")

        try: self.after(200, lambda: self.iconbitmap(resource_path("logo.ico")))
        except: pass

        self.protocol("WM_DELETE_WINDOW", self._on_closing)

        # Obter configuração do modelo
        self.model_config = MODELO_CONFIG.get(medidor_model, MODELO_CONFIG["MV110"])

        # Calcular métricas apenas uma vez para evitar duplicação
        if self.model_config["show_pie_charts"] or not self.model_config["show_pie_charts"]:
            flow_ranges_raw, data_quality_raw, general_indicators = DataProcessingService.calculate_dashboard_metrics(data_frame)

            # Filtrar métricas apenas para layouts que precisam
            if medidor_model == "MV145":
                flow_ranges_filtered = {}
                data_quality_filtered = {}
                hydraulic_status_filtered = {}
            else:
                flow_ranges_filtered = {k: v for k, v in flow_ranges_raw.items() if v > 0}
                data_quality_filtered = {k: v for k, v in data_quality_raw.items() if v > 0}
                hydraulic_status_raw = DataProcessingService.calculate_hydraulic_status(data_frame) if self.model_config["show_status_process"] else {}
                hydraulic_status_filtered = {k: v for k, v in hydraulic_status_raw.items() if v > 0}

        plt.rcParams['axes.facecolor'] = '#ffffff'
        plt.rcParams['figure.facecolor'] = '#ffffff'

        # Renderizar layout conforme modelo
        if medidor_model == "MV145":
            self._setup_simplified_layout(data_frame, medidor_type, general_indicators)
        else:
            self._setup_complete_layout(
                data_frame, medidor_type, flow_ranges_filtered, 
                data_quality_filtered, hydraulic_status_filtered, general_indicators
            )

    def _setup_simplified_layout(self, data_frame: pd.DataFrame, medidor_type: str, general_indicators: Dict[str, Any]) -> None:
        """Layout simplificado apenas com gráfico de vazão e volume (MV145)."""
        self.fig = plt.figure(figsize=(16, 8), dpi=100)
        # top=0.82 abre espaço entre o topo da figura e o eixo para título + legenda não se sobreporem
        self.fig.subplots_adjust(top=0.82, bottom=0.10, left=0.07, right=0.93)

        self.ax_flow_speed = self.fig.add_subplot(111)

        self.line_flow, = self.ax_flow_speed.plot(data_frame['Data'], data_frame['Vazao'], label='VAZÃO', color=COR_VAZAO, lw=1.5)
        self.ax_flow_speed.fill_between(data_frame['Data'], data_frame['Vazao'], color=COR_VAZAO, alpha=0.08)
        self.ax_flow_speed.set_ylabel("Vazão (m³/h)", color=COR_VAZAO, fontsize=12, fontweight='bold')
        # pad=70 garante que o título fique acima da legenda (bbox_to_anchor=1.08)
        self.ax_flow_speed.set_title(f"MONITORAMENTO DE VAZÃO E VOLUME - {medidor_type} ({self.medidor_model})",
                                     fontsize=18, fontweight='bold', pad=70)
        self.ax_flow_speed.xaxis.set_major_formatter(mdates.DateFormatter('%d/%m/%Y'))
        self.ax_flow_speed.set_xlim(data_frame['Data'].min(), data_frame['Data'].max())

        # Margem inferior para o ponto mínimo não tocar na borda
        max_flow = data_frame['Vazao'].max() if not data_frame['Vazao'].empty else 1.0
        self.ax_flow_speed.set_ylim(-max_flow * 0.05, max_flow * 1.3)
        self.ax_flow_speed.grid(True, axis='y', linestyle=':', alpha=0.3)

        # Volume como eixo secundário, se disponível
        self.ax_speed_twin = None
        self.line_speed = None
        if 'Volume' in data_frame.columns and not data_frame['Volume'].isna().all():
            self.ax_speed_twin = self.ax_flow_speed.twinx()
            self.line_speed, = self.ax_speed_twin.plot(data_frame['Data'], data_frame['Volume'], label='VOLUME',
                                                       color='#2E7D32', lw=1.5, linestyle='--')
            self.ax_speed_twin.set_ylabel("Volume (m³)", color='#2E7D32', fontsize=12, fontweight='bold')
            lines1, labels1 = self.ax_flow_speed.get_legend_handles_labels()
            lines2, labels2 = self.ax_speed_twin.get_legend_handles_labels()
            self.main_legend = self.ax_flow_speed.legend(lines1 + lines2, labels1 + labels2,
                                                         loc='upper center', bbox_to_anchor=(0.5, 1.08),
                                                         ncol=2, frameon=False, fontsize=10)
        else:
            self.main_legend = self.ax_flow_speed.legend(loc='upper center', bbox_to_anchor=(0.5, 1.08),
                                                         ncol=1, frameon=False, fontsize=10)
        if 'Volume' not in data_frame.columns:
            print("Aviso: Coluna 'Volume' não encontrada nos dados. Gráfico de volume não será exibido.")

        # Elementos de hover
        self.vertical_line = self.ax_flow_speed.axvline(x=data_frame['Data'].iloc[0],
                                                        color='#333333', alpha=0.3, lw=0.8, visible=False, zorder=5)
        self.annotation_line = self.ax_flow_speed.annotate("", xy=(0, 0), xytext=(20, 0),
                                                            textcoords="offset points",
                                                            bbox=dict(boxstyle="round,pad=0.5", fc="white", ec="black", lw=1, alpha=0.98),
                                                            zorder=100, visible=False, clip_on=False)
        self.annotation_pie = self.fig.text(0, 0, "",
                                            bbox=dict(boxstyle="round,pad=0.5", fc="white", ec="black", lw=1, alpha=0.98),
                                            visible=False, zorder=101)

        self.container_frame = ctk.CTkFrame(self, fg_color="white")
        self.container_frame.pack(fill="both", expand=True, padx=20)
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.container_frame)
        self.canvas.get_tk_widget().pack(side="left", fill="both", expand=True)

        self.canvas.mpl_connect("motion_notify_event", self._on_hover)
        self.canvas.mpl_connect("draw_event", self._on_draw)

        self._add_sidebar(data_frame, general_indicators)

    def _setup_complete_layout(self, data_frame: pd.DataFrame, medidor_type: str, 
                               flow_ranges: Dict[str, int], data_quality: Dict[str, int],
                               hydraulic_status: Dict[str, int], general_indicators: Dict[str, Any]) -> None:
        """Layout completo com gráfico principal e roscas conforme configuração."""
        self.fig = plt.figure(figsize=(16, 10), dpi=100)

        # Determinar layout do gridspec baseado no modelo
        num_pie_charts = len(self.model_config["pie_charts"])
        if num_pie_charts == 2:
            gs = self.fig.add_gridspec(2, 2, height_ratios=[1.5, 1], hspace=0.6, wspace=0.3, 
                                       top=0.82, bottom=0.15)
        elif num_pie_charts == 3:
            gs = self.fig.add_gridspec(2, 3, height_ratios=[1.5, 1], hspace=0.6, wspace=0.4, 
                                       top=0.82, bottom=0.15)
        else:
            gs = self.fig.add_gridspec(1, 1, top=0.82, bottom=0.15)

        # Gráfico principal (Vazão e Velocidade)
        self.ax_flow_speed = self.fig.add_subplot(gs[0, :])
        self.ax_speed_twin = self.ax_flow_speed.twinx()

        self.ax_flow_speed.set_zorder(self.ax_speed_twin.get_zorder() + 1)
        self.ax_flow_speed.set_frame_on(False) 
        for spine in self.ax_flow_speed.spines.values():
            spine.set_zorder(0)

        def format_mil(x: float, pos: Any) -> str:
            return f'{x/1000:,.1f}mil'.replace('.', ',') if x >= 1000 else str(int(x))

        self.ax_flow_speed.yaxis.set_major_formatter(FuncFormatter(format_mil))
        self.ax_flow_speed.set_ylabel("Vazão (m³/h)", color=COR_VAZAO, fontsize=12, fontweight='bold')
        self.ax_speed_twin.set_ylabel("Velocidade (m/s)", color=COR_VELOCIDADE, fontsize=12, fontweight='bold')
        self.ax_flow_speed.set_title(f"MONITORAMENTO DE VAZÃO E VELOCIDADE - {medidor_type} ({self.medidor_model})", 
                                     fontsize=18, fontweight='bold', pad=55)
        self.ax_flow_speed.xaxis.set_major_formatter(mdates.DateFormatter('%d/%m/%Y'))

        self.ax_flow_speed.set_xlim(data_frame['Data'].min(), data_frame['Data'].max())
        max_flow = data_frame['Vazao'].max() if not data_frame['Vazao'].empty else 1.0
        max_speed = data_frame['Velocidade'].max() if 'Velocidade' in data_frame.columns and not data_frame['Velocidade'].empty else 1.0
        self.ax_flow_speed.set_ylim(0, max_flow * 1.3) 
        self.ax_speed_twin.set_ylim(0, max_speed * 2.8) 

        self.line_flow, = self.ax_flow_speed.plot(data_frame['Data'], data_frame['Vazao'], 
                                                   label='VAZÃO', color=COR_VAZAO, lw=1.0)
        self.ax_flow_speed.fill_between(data_frame['Data'], data_frame['Vazao'], color=COR_VAZAO, alpha=0.08)
        self.line_speed, = self.ax_speed_twin.plot(data_frame['Data'], data_frame['Velocidade'], 
                                                    label='VELOCIDADE', color=COR_VELOCIDADE, lw=0.8, linestyle='--')

        mean_flow_value = data_frame['Vazao'].mean()
        self.ax_flow_speed.axhline(y=mean_flow_value, color='green', linestyle=':',lw=1.5,alpha=0.7,
                                   label=f'MÉDIA({mean_flow_value:,.2f})')

        lines1, labels1 = self.ax_flow_speed.get_legend_handles_labels()
        lines2, labels2 = self.ax_speed_twin.get_legend_handles_labels()
        self.main_legend = self.ax_flow_speed.legend(lines1 + lines2, labels1 + labels2, 
                                                     loc='upper center', bbox_to_anchor=(0.5, 1.18), 
                                                     ncol=3, frameon=False, fontsize=10)

        self.ax_flow_speed.grid(True, axis='y', linestyle=':', alpha=0.3)

        self.vertical_line = self.ax_flow_speed.axvline(x=data_frame['Data'].iloc[0], 
                                                        color='#333333', alpha=0.3, lw=0.8, visible=False, zorder=5)
        self.annotation_line = self.ax_flow_speed.annotate("", xy=(0,0), xytext=(20,35), 
                                                            textcoords="offset points",
                                                            bbox=dict(boxstyle="round,pad=0.5", fc="white", ec="black", lw=1, alpha=0.98),
                                                            zorder=100, visible=False, clip_on=False)

        self.annotation_pie = self.fig.text(0, 0, "", 
                                            bbox=dict(boxstyle="round,pad=0.5", fc="white", ec="black", lw=1, alpha=0.98), 
                                            visible=False, zorder=101)

        self.wedges_info_map: Dict[Any, Dict[str, Any]] = {}

        # Criar roscas conforme configuração do modelo
        pie_configs = []
        col_idx = 0

        if "vazao" in self.model_config["pie_charts"]:
            pie_configs.append((flow_ranges, "Percentual por Faixa de Vazão", (1, col_idx), "vazao"))
            col_idx += 1

        if "qualidade" in self.model_config["pie_charts"]:
            pie_configs.append((data_quality, "Qualidade da Integridade dos Dados", (1, col_idx), "qualidade"))
            col_idx += 1

        if "status_hidraulico" in self.model_config["pie_charts"]:
            pie_configs.append((hydraulic_status, "Status de Processo", (1, col_idx), "status_hidraulico"))

        for data_dict, title, grid_pos, chart_type in pie_configs:
            self._create_pie_chart(self.fig, gs, data_dict, title, grid_pos, chart_type)

        self.container_frame = ctk.CTkFrame(self, fg_color="white")
        self.container_frame.pack(fill="both", expand=True, padx=20)
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.container_frame)
        self.canvas.get_tk_widget().pack(side="left", fill="both", expand=True)

        self.canvas.mpl_connect("motion_notify_event", self._on_hover)
        self.canvas.mpl_connect("draw_event", self._on_draw)

        self._add_sidebar(data_frame, general_indicators)

    def _create_pie_chart(self, fig, gs, data_dict: Dict[str, int], title: str, grid_pos: Tuple[int, int], chart_type: str) -> None:
        """Cria um gráfico de rosca com as cores e legendas apropriadas."""
        ax = fig.add_subplot(gs[grid_pos[0], grid_pos[1]])
        values, labels = list(data_dict.values()), list(data_dict.keys())
        total_sum = sum(values) if sum(values) > 0 else 1

        # Obtém a configuração de cores para o tipo de gráfico
        color_config = PIE_COLORS.get(chart_type, {})
        patterns = color_config.get("patterns", {})
        default_colors = color_config.get("default", CORES_ROSCA)

        current_colors = []
        for label in labels:
            color_assigned = False
            for pattern, color in patterns.items():
                if pattern in label:
                    current_colors.append(color)
                    color_assigned = True
                    break
            if not color_assigned:
                # Usa uma cor da lista default rotativa baseada no índice atual
                current_colors.append(default_colors[len(current_colors) % len(default_colors)])

        wedges, _ = ax.pie(values, startangle=90, colors=current_colors, 
                           wedgeprops={'width': 0.35, 'edgecolor': 'white'})

        ax.set_title(title, fontsize=14, fontweight='bold', pad=25)

        leg = ax.legend(wedges, labels, title="Categorias", loc='upper center', 
                        bbox_to_anchor=(0.5, -0.1), ncol=2, frameon=False, fontsize=9)
        self.pie_chart_legends.append(leg)

        # Anti-colisão para percentuais
        annotations_data = []
        for j, p in enumerate(wedges):
            pct = values[j] / total_sum * 100
            if pct < 0.1: continue 

            angle_rad = (p.theta2 - p.theta1)/2. * np.pi/180. + p.theta1 * np.pi/180.
            y_coord = np.sin(angle_rad)
            x_coord = np.cos(angle_rad)
            annotations_data.append({'x': x_coord, 'y': y_coord, 'pct': pct, 'angle': angle_rad, 
                                     'wedge': p, 'label': labels[j], 'value': values[j]})

        annotations_data.sort(key=lambda x: x['y'], reverse=True)

        occupied_y_left: List[float] = []
        occupied_y_right: List[float] = []
        MIN_VERTICAL_DIST = 0.18

        for ann in annotations_data:
            is_right_side = ann['x'] > 0
            reference_list = occupied_y_right if is_right_side else occupied_y_left

            horizontal_alignment = "left" if is_right_side else "right"
            x_position = 1.35 if is_right_side else -1.35
            y_position = 1.3 * ann['y']

            if reference_list:
                last_y = reference_list[-1]
                if abs(y_position - last_y) < MIN_VERTICAL_DIST:
                    y_position = last_y - MIN_VERTICAL_DIST

            reference_list.append(y_position)

            ax.annotate(f"{ann['pct']:.1f}%", 
                        xy=(ann['x'], ann['y']), 
                        xytext=(x_position, y_position),
                        horizontalalignment=horizontal_alignment,
                        fontsize=10, fontweight='bold',
                        arrowprops=dict(arrowstyle="-", color="#555555", lw=0.8, 
                                       connectionstyle="angle3,angleA=0,angleB=90"))

            self.wedges_info_map[ann['wedge']] = {'label': ann['label'], 'value': ann['value'], 'total': total_sum}

    def _add_sidebar(self, data_frame: pd.DataFrame, general_indicators: Optional[Dict[str, Any]] = None) -> None:
        """Adiciona a barra lateral com informações gerais."""
        sidebar_frame = ctk.CTkFrame(self.container_frame, width=320, fg_color="#f0f0f0", corner_radius=15)
        sidebar_frame.pack(side="right", fill="y", padx=10, pady=20)

        if general_indicators:
            self._add_info_label(sidebar_frame, "Nº DE SÉRIE", general_indicators.get('serial_number', 'N/A'))
            ctk.CTkLabel(sidebar_frame, text="PERÍODO", font=("Arial", 11, "bold"), text_color="#666666").pack(pady=(30, 0))
            if 'start_date' in general_indicators and 'end_date' in general_indicators:
                ctk.CTkLabel(sidebar_frame, text=f"{general_indicators['start_date'].strftime('%d/%m/%Y %H:%M')}\naté\n{general_indicators['end_date'].strftime('%d/%m/%Y %H:%M')}", 
                             font=("Arial", 12, "bold"), text_color="#000000").pack(pady=5)
            self._add_info_label(sidebar_frame, "TOTAL POSITIVO ≈", 
                                 f"{general_indicators.get('total_positive_accumulated', 0):,.0f} m³/h".replace(',', '.'))
        else:
            # Para MV145, adicionar informações básicas
            ctk.CTkLabel(sidebar_frame, text="PERÍODO", font=("Arial", 11, "bold"), text_color="#666666").pack(pady=(30, 0))
            if not data_frame.empty:
                ctk.CTkLabel(sidebar_frame, text=f"{data_frame['Data'].min().strftime('%d/%m/%Y %H:%M')}\naté\n{data_frame['Data'].max().strftime('%d/%m/%Y %H:%M')}", 
                             font=("Arial", 12, "bold"), text_color="#000000").pack(pady=5)

        ctk.CTkButton(sidebar_frame, text="Exportar Relatório", command=self._export_report, 
                      fg_color=COR_VAZAO, height=45).pack(pady=(50, 10), padx=30, fill="x")
        ctk.CTkButton(sidebar_frame, text="Nova Importação", command=self._return_to_import, 
                      fg_color="#6c757d", height=45).pack(pady=10, padx=30, fill="x")

    def _add_info_label(self, master_frame: ctk.CTkFrame, title: str, value: Any) -> None:
        """Adiciona um par de labels (título e valor) a um frame."""
        ctk.CTkLabel(master_frame, text=title, font=("Arial", 11, "bold"), text_color="#666666").pack(pady=(30,0))
        ctk.CTkLabel(master_frame, text=str(value), font=("Arial", 22, "bold"), text_color="#000000").pack(pady=(0,5))

    def _redraw_static_elements(self) -> None:
        """Redesenha elementos estáticos do gráfico."""
        if hasattr(self, 'main_legend'):
            self.ax_flow_speed.draw_artist(self.main_legend)
        for leg in self.pie_chart_legends:
            self.fig.draw_artist(leg)

    def _on_draw(self, event: Any) -> None:
        """Manipulador para o desenho do canvas."""
        if hasattr(self, 'vertical_line'):
            self.vertical_line.set_visible(False)
            self.annotation_line.set_visible(False)
            self.annotation_pie.set_visible(False)
        self._redraw_static_elements()
        self._background_cache = self.canvas.copy_from_bbox(self.fig.bbox)

    def _on_hover(self, event: Any) -> None:
        """Manipulador para o movimento do mouse sobre o gráfico."""
        if event.inaxes is None:
            if hasattr(self, 'vertical_line') and (self.vertical_line.get_visible() or self.annotation_line.get_visible() or self.annotation_pie.get_visible()):
                if self._background_cache is not None:
                    self.canvas.restore_region(self._background_cache)
                self._redraw_static_elements()
                self.canvas.blit(self.fig.bbox)
            if hasattr(self, 'vertical_line'):
                self.vertical_line.set_visible(False)
                self.annotation_line.set_visible(False)
                self.annotation_pie.set_visible(False)
            self._last_hover_idx = None
            return

        if hasattr(self, 'ax_flow_speed') and event.inaxes in [self.ax_flow_speed, self.ax_speed_twin]:
            x_data, y_flow = self.line_flow.get_data()
            x_num = mdates.date2num(x_data)
            idx = np.abs(x_num - event.xdata).argmin()

            if idx != self._last_hover_idx:
                self._last_hover_idx = idx
                date_at, flow_val = x_data[idx], y_flow[idx]
                xlim = self.ax_flow_speed.get_xlim(); ylim = self.ax_flow_speed.get_ylim()
                offset_x = -175 if event.xdata > (xlim[0] + (xlim[1]-xlim[0])*0.7) else 25
                offset_y = 35 if flow_val < (ylim[1] * 0.6) else -110

                self.vertical_line.set_xdata([date_at, date_at]); self.vertical_line.set_visible(True)
                self.annotation_line.xy = (date_at, flow_val); self.annotation_line.set_position((offset_x, offset_y))

                # Montar texto do balão conforme colunas disponíveis
                if self.line_speed is not None:
                    extra_val = self.line_speed.get_data()[1][idx]
                    extra_label = "VOLUME" if self.medidor_model == "MV145" else "VELOCIDADE"
                    extra_unit = "m³" if self.medidor_model == "MV145" else "m/s"
                    tooltip_text = (f"DATA: {pd.Timestamp(date_at).strftime('%d/%m/%Y %H:%M')}\n"
                                    f"VAZÃO: {flow_val:,.2f} m³/h\n"
                                    f"{extra_label}: {extra_val:,.2f} {extra_unit}")
                else:
                    tooltip_text = (f"DATA: {pd.Timestamp(date_at).strftime('%d/%m/%Y %H:%M')}\n"
                                    f"VAZÃO: {flow_val:,.2f} m³/h")

                self.annotation_line.set_text(tooltip_text)
                self.annotation_line.set_visible(True); self.annotation_pie.set_visible(False)

                if self._background_cache is not None:
                    self.canvas.restore_region(self._background_cache)
                self._redraw_static_elements()
                self.ax_flow_speed.draw_artist(self.vertical_line)
                self.ax_flow_speed.draw_artist(self.annotation_line)
                self.canvas.blit(self.fig.bbox)
        elif hasattr(self, 'wedges_info_map'):
            found_pie_wedge = False
            for wedge, info in self.wedges_info_map.items():
                if wedge.contains_point([event.x, event.y]):
                    pct = info['value'] / (info['total'] if info['total'] > 0 else 1) * 100
                    self.annotation_pie.set_text(f"CATEGORIA: {info['label']}\nPERCENTUAL: {pct:.1f}%")
                    self.annotation_pie.set_position((event.x/self.fig.bbox.width + 0.01, event.y/self.fig.bbox.height + 0.01))
                    self.annotation_pie.set_visible(True)
                    if hasattr(self, 'vertical_line'):
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

    def _return_to_import(self) -> None:
        """Fecha a janela do dashboard e retorna para a janela principal de importação."""
        plt.close(self.fig)
        self.parent.deiconify()
        self.destroy()

    def _on_closing(self) -> None:
        """Manipulador para o evento de fechamento da janela."""
        if messagebox.askokcancel("Sair", "Deseja realmente fechar o programa?"):
            try:
                plt.close('all')
                self.parent.quit()
                if self.parent.winfo_exists():
                    self.parent.destroy()
                sys.exit(0)
            except (RuntimeError, Exception):
                sys.exit(0)

    def _export_report(self) -> None:
        """Exporta o gráfico do dashboard como uma imagem PNG."""
        file_path = filedialog.asksaveasfilename(defaultextension=".png", filetypes=[("Imagem PNG", "*.png")])
        if file_path: self.fig.savefig(file_path, dpi=300, bbox_inches='tight')
