"""
Módulo responsável pela janela de dashboard detalhado do medidor NF750.
Exibe gráficos de Vazão, Velocidade, Nível e Área.
"""
import pandas as pd
import customtkinter as ctk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.ticker import FuncFormatter
import numpy as np
from typing import Optional, Any

from src.utils.helpers import resource_path
from src.core.config import COR_VAZAO, COR_VELOCIDADE, COR_NIVEL, COR_AREA


class DetailedDashboardWindow(ctk.CTkToplevel):
    """
    Janela de dashboard detalhado para o medidor NF750.
    Exibe gráficos de Vazão, Velocidade, Nível e Área.
    """
    def __init__(self, parent: ctk.CTk, data_frame: pd.DataFrame, medidor_model: str, medidor_type: str):
        """
        Inicializa a janela de dashboard detalhado.

        Args:
            parent: A janela pai (DashboardWindow).
            data_frame: O DataFrame pandas com os dados processados do medidor.
            medidor_model: O modelo do medidor.
            medidor_type: O tipo do medidor.
        """
        super().__init__(parent)
        self.parent = parent
        self.medidor_model = medidor_model
        self.data_frame = data_frame
        self.title(f"Medidados - Detalhes: {medidor_type} ({medidor_model})")
        self._last_hover_idx: Optional[int] = None
        self._background_cache: Optional[Any] = None
        self.state('zoomed')
        self.configure(fg_color="white")

        try:
            self.after(200, lambda: self.iconbitmap(resource_path("logo.ico")))
        except:
            pass

        self.protocol("WM_DELETE_WINDOW", self._on_closing)

        plt.rcParams['axes.facecolor'] = '#ffffff'
        plt.rcParams['figure.facecolor'] = '#ffffff'

        self._setup_detailed_layout(data_frame, medidor_type)

    def _setup_detailed_layout(self, data_frame: pd.DataFrame, medidor_type: str) -> None:
        """Layout detalhado com 4 gráficos: Vazão, Velocidade, Nível e Área."""
        self.fig = plt.figure(figsize=(20, 12), dpi=100)
        self.fig.subplots_adjust(top=0.92, bottom=0.08, left=0.06, right=0.96, hspace=0.4, wspace=0.3)

        self.ax_vazao = self.fig.add_subplot(2, 2, 1)
        self.ax_velocidade = self.fig.add_subplot(2, 2, 2)
        self.ax_nivel = self.fig.add_subplot(2, 2, 3)
        self.ax_area = self.fig.add_subplot(2, 2, 4)

        self._plot_vazao(data_frame)
        self._plot_velocidade(data_frame)
        self._plot_nivel(data_frame)
        self._plot_area(data_frame)

        self.container_frame = ctk.CTkFrame(self, fg_color="white")
        self.container_frame.pack(fill="both", expand=True, padx=20, pady=10)
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.container_frame)
        self.canvas.get_tk_widget().pack(side="left", fill="both", expand=True)

        self.canvas.mpl_connect("motion_notify_event", self._on_hover)
        self.canvas.mpl_connect("draw_event", self._on_draw)

        self._add_info_panel(data_frame, medidor_type)

    def _plot_vazao(self, data_frame: pd.DataFrame) -> None:
        """Plota o gráfico de Vazão em azul."""
        self.line_vazao, = self.ax_vazao.plot(
            data_frame['Data'], data_frame['Vazao'],
            label='VAZÃO', color=COR_VAZAO, lw=1.2
        )
        self.ax_vazao.fill_between(
            data_frame['Data'], data_frame['Vazao'],
            color=COR_VAZAO, alpha=0.1
        )
        self.ax_vazao.set_title("VAZÃO", fontsize=14, fontweight='bold', color=COR_VAZAO)
        self.ax_vazao.set_ylabel("Vazão (m³/h)", color=COR_VAZAO, fontsize=11)
        self.ax_vazao.xaxis.set_major_formatter(mdates.DateFormatter('%d/%m/%Y'))
        self.ax_vazao.set_xlim(data_frame['Data'].min(), data_frame['Data'].max())
        self.ax_vazao.grid(True, axis='y', linestyle=':', alpha=0.3)
        self.ax_vazao.legend(loc='upper right', frameon=False, fontsize=9)

        mean_val = data_frame['Vazao'].mean()
        self.ax_vazao.axhline(y=mean_val, color='green', linestyle=':', lw=1.2, alpha=0.7,
                             label=f'Média ({mean_val:,.2f})')
        self.ax_vazao.legend(loc='upper right', frameon=False, fontsize=9)

    def _plot_velocidade(self, data_frame: pd.DataFrame) -> None:
        """Plota o gráfico de Velocidade em vermelho pontilhado."""
        if 'Velocidade' in data_frame.columns and not data_frame['Velocidade'].isna().all():
            self.line_velocidade, = self.ax_velocidade.plot(
                data_frame['Data'], data_frame['Velocidade'],
                label='VELOCIDADE', color=COR_VELOCIDADE, lw=1.2, linestyle='--'
            )
            self.ax_velocidade.set_title("VELOCIDADE", fontsize=14, fontweight='bold', color=COR_VELOCIDADE)
            self.ax_velocidade.set_ylabel("Velocidade (m/s)", color=COR_VELOCIDADE, fontsize=11)
            self.ax_velocidade.xaxis.set_major_formatter(mdates.DateFormatter('%d/%m/%Y'))
            self.ax_velocidade.set_xlim(data_frame['Data'].min(), data_frame['Data'].max())
            self.ax_velocidade.grid(True, axis='y', linestyle=':', alpha=0.3)
            self.ax_velocidade.legend(loc='upper right', frameon=False, fontsize=9)
        else:
            self.ax_velocidade.text(0.5, 0.5, 'Dados de Velocidade\nNão Disponíveis',
                                   ha='center', va='center', fontsize=12, color='gray',
                                   transform=self.ax_velocidade.transAxes)
            self.ax_velocidade.set_title("VELOCIDADE", fontsize=14, fontweight='bold', color=COR_VELOCIDADE)
            self.line_velocidade = None

    def _plot_nivel(self, data_frame: pd.DataFrame) -> None:
        """Plota o gráfico de Nível em verde."""
        if 'Nivel' in data_frame.columns and not data_frame['Nivel'].isna().all():
            self.line_nivel, = self.ax_nivel.plot(
                data_frame['Data'], data_frame['Nivel'],
                label='NÍVEL', color=COR_NIVEL, lw=1.2
            )
            self.ax_nivel.fill_between(
                data_frame['Data'], data_frame['Nivel'],
                color=COR_NIVEL, alpha=0.1
            )
            self.ax_nivel.set_title("NÍVEL", fontsize=14, fontweight='bold', color=COR_NIVEL)
            self.ax_nivel.set_ylabel("Nível (m)", color=COR_NIVEL, fontsize=11)
            self.ax_nivel.xaxis.set_major_formatter(mdates.DateFormatter('%d/%m/%Y'))
            self.ax_nivel.set_xlim(data_frame['Data'].min(), data_frame['Data'].max())
            self.ax_nivel.grid(True, axis='y', linestyle=':', alpha=0.3)
            self.ax_nivel.legend(loc='upper right', frameon=False, fontsize=9)
        else:
            self.ax_nivel.text(0.5, 0.5, 'Dados de Nível\nNão Disponíveis',
                              ha='center', va='center', fontsize=12, color='gray',
                              transform=self.ax_nivel.transAxes)
            self.ax_nivel.set_title("NÍVEL", fontsize=14, fontweight='bold', color=COR_NIVEL)
            self.line_nivel = None

    def _plot_area(self, data_frame: pd.DataFrame) -> None:
        """Plota o gráfico de Área em laranja."""
        if 'Area' in data_frame.columns and not data_frame['Area'].isna().all():
            self.line_area, = self.ax_area.plot(
                data_frame['Data'], data_frame['Area'],
                label='ÁREA', color=COR_AREA, lw=1.2
            )
            self.ax_area.fill_between(
                data_frame['Data'], data_frame['Area'],
                color=COR_AREA, alpha=0.1
            )
            self.ax_area.set_title("ÁREA", fontsize=14, fontweight='bold', color=COR_AREA)
            self.ax_area.set_ylabel("Área (m²)", color=COR_AREA, fontsize=11)
            self.ax_area.xaxis.set_major_formatter(mdates.DateFormatter('%d/%m/%Y'))
            self.ax_area.set_xlim(data_frame['Data'].min(), data_frame['Data'].max())
            self.ax_area.grid(True, axis='y', linestyle=':', alpha=0.3)
            self.ax_area.legend(loc='upper right', frameon=False, fontsize=9)
        else:
            self.ax_area.text(0.5, 0.5, 'Dados de Área\nNão Disponíveis',
                             ha='center', va='center', fontsize=12, color='gray',
                             transform=self.ax_area.transAxes)
            self.ax_area.set_title("ÁREA", fontsize=14, fontweight='bold', color=COR_AREA)
            self.line_area = None

    def _add_info_panel(self, data_frame: pd.DataFrame, medidor_type: str) -> None:
        """Adiciona painel de informações na parte inferior."""
        info_frame = ctk.CTkFrame(self.container_frame, fg_color="#f0f0f0", corner_radius=10, height=60)
        info_frame.pack(fill="x", padx=10, pady=(0, 10))
        info_frame.pack_propagate(False)

        info_text = (
            f"Medidor: {medidor_type} ({self.medidor_model}) | "
            f"Período: {data_frame['Data'].min().strftime('%d/%m/%Y %H:%M')} até "
            f"{data_frame['Data'].max().strftime('%d/%m/%Y %H:%M')} | "
            f"Total de registros: {len(data_frame)}"
        )

        ctk.CTkLabel(info_frame, text=info_text, font=("Arial", 12, "bold"), text_color="#333333").pack(expand=True)

    def _on_hover(self, event: Any) -> None:
        """Manipulador para o movimento do mouse sobre os gráficos."""
        if event.inaxes is None:
            if self._background_cache is not None:
                self.canvas.restore_region(self._background_cache)
                self.canvas.blit(self.fig.bbox)
            self._last_hover_idx = None
            return

        ax_map = {
            self.ax_vazao: ('Vazao', 'VAZÃO', 'm³/h', COR_VAZAO),
            self.ax_velocidade: ('Velocidade', 'VELOCIDADE', 'm/s', COR_VELOCIDADE),
            self.ax_nivel: ('Nivel', 'NÍVEL', 'm', COR_NIVEL),
            self.ax_area: ('Area', 'ÁREA', 'm²', COR_AREA)
        }

        if event.inaxes in ax_map:
            col_name, label, unit, color = ax_map[event.inaxes]
            if col_name in self.data_frame.columns and not self.data_frame[col_name].isna().all():
                x_data = self.data_frame['Data']
                y_data = self.data_frame[col_name]
                x_num = mdates.date2num(x_data)
                idx = np.abs(x_num - event.xdata).argmin()

                if idx != self._last_hover_idx:
                    self._last_hover_idx = idx
                    date_at, val = x_data.iloc[idx], y_data.iloc[idx]

                    tooltip_text = f"DATA: {date_at.strftime('%d/%m/%Y %H:%M')}\n{label}: {val:,.2f} {unit}"

                    event.inaxes.set_title(f"{label}", fontsize=14, fontweight='bold', color=color)

    def _on_draw(self, event: Any) -> None:
        """Manipulador para o desenho do canvas."""
        self._background_cache = self.canvas.copy_from_bbox(self.fig.bbox)

    def _return_to_dashboard(self) -> None:
        """Fecha a janela detalhada e retorna ao dashboard principal."""
        plt.close(self.fig)
        self.destroy()

    def _on_closing(self) -> None:
        """Manipulador para o evento de fechamento da janela."""
        plt.close(self.fig)
        self.destroy()
