"""
Componente responsável pela barra lateral do dashboard.
"""
from collections.abc import Callable
from typing import Any, Optional

import customtkinter as ctk
import pandas as pd

from src.core.config import COR_VAZAO
from src.ui.dashboard.types import GeneralIndicators


class DashboardSidebar:
    """
    Monta e gerencia a barra lateral do dashboard.

    A classe recebe callbacks em vez de depender diretamente de DashboardWindow.
    Dessa forma, ela exibe os botões, enquanto a janela principal continua sendo
    responsável pelas ações: abrir detalhes, exportar ou iniciar nova importação.
    """

    def __init__(
        self,
        master: ctk.CTkFrame,
        data_frame: pd.DataFrame,
        medidor_model: str,
        unit: str,
        general_indicators: Optional[GeneralIndicators],
        on_open_details: Callable[[], None],
        on_export: Callable[[], None],
        on_new_import: Callable[[], None],
    ) -> None:
        """
        Inicializa e renderiza a barra lateral.

        Args:
            master: Frame que conterá a barra lateral.
            data_frame: Dados processados usados como fallback para o período.
            medidor_model: Modelo atual do medidor.
            unit: Unidade selecionada para a vazão.
            general_indicators: Indicadores gerais calculados no serviço.
            on_open_details: Callback para abrir dashboard detalhado.
            on_export: Callback para exportar o gráfico.
            on_new_import: Callback para retornar à importação.
        """
        self.master: ctk.CTkFrame = master
        self.data_frame: pd.DataFrame = data_frame
        self.medidor_model: str = medidor_model
        self.unit: str = unit
        self.general_indicators: Optional[GeneralIndicators] = general_indicators

        self.on_open_details: Callable[[], None] = on_open_details
        self.on_export: Callable[[], None] = on_export
        self.on_new_import: Callable[[], None] = on_new_import

        self.total_label: Optional[ctk.CTkLabel] = None
        self.frame: ctk.CTkFrame = self._build()

    def _build(self) -> ctk.CTkFrame:
        """
        Cria e retorna o frame completo da barra lateral.
        """
        sidebar_frame = ctk.CTkFrame(
            self.master,
            width=320,
            fg_color="#f0f0f0",
            corner_radius=15,
        )
        sidebar_frame.pack(side="right", fill="y", padx=10, pady=20)

        if self.general_indicators:
            self._build_indicators(sidebar_frame)
        else:
            self._build_fallback_period(sidebar_frame)

        self._build_action_buttons(sidebar_frame)

        return sidebar_frame

    def _build_indicators(self, sidebar_frame: ctk.CTkFrame) -> None:
        """
        Exibe número de série, período e total positivo.
        """
        if self.general_indicators is None:
            return

        self._add_info_label(
            sidebar_frame,
            "Nº DE SÉRIE",
            self.general_indicators.get("serial_number", "N/A"),
        )

        ctk.CTkLabel(
            sidebar_frame,
            text="PERÍODO",
            font=("Arial", 11, "bold"),
            text_color="#666666",
        ).pack(pady=(30, 0))

        if (
            "start_date" in self.general_indicators
            and "end_date" in self.general_indicators
        ):
            start_date: Any = self.general_indicators["start_date"]
            end_date: Any = self.general_indicators["end_date"]

            ctk.CTkLabel(
                sidebar_frame,
                text=(
                    f"{start_date.strftime('%d/%m/%Y %H:%M')}\n"
                    "até\n"
                    f"{end_date.strftime('%d/%m/%Y %H:%M')}"
                ),
                font=("Arial", 12, "bold"),
                text_color="#000000",
            ).pack(pady=5)

        # MV145 não tem o mesmo totalizado acumulado dos outros modelos.
        if self.medidor_model.strip().upper() == "MV145":
            return

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

        self._update_total_label()

    def _build_fallback_period(self, sidebar_frame: ctk.CTkFrame) -> None:
        """
        Exibe somente o período usando diretamente o DataFrame.

        Este fallback preserva o comportamento existente caso os indicadores
        gerais não estejam disponíveis.
        """
        ctk.CTkLabel(
            sidebar_frame,
            text="PERÍODO",
            font=("Arial", 11, "bold"),
            text_color="#666666",
        ).pack(pady=(30, 0))

        if self.data_frame.empty:
            return

        ctk.CTkLabel(
            sidebar_frame,
            text=(
                f"{self.data_frame['Data'].min().strftime('%d/%m/%Y %H:%M')}\n"
                "até\n"
                f"{self.data_frame['Data'].max().strftime('%d/%m/%Y %H:%M')}"
            ),
            font=("Arial", 12, "bold"),
            text_color="#000000",
        ).pack(pady=5)

    def _build_action_buttons(self, sidebar_frame: ctk.CTkFrame) -> None:
        """
        Cria os botões de ação da barra lateral.
        """
        has_detailed_view: bool = (
            self.medidor_model.strip().upper() == "NF750"
            and "Area" in self.data_frame.columns
            and "Nivel" in self.data_frame.columns
        )

        if has_detailed_view:
            ctk.CTkButton(
                sidebar_frame,
                text="Detalhar",
                command=self.on_open_details,
                fg_color=COR_VAZAO,
                height=45,
            ).pack(pady=(10, 10), padx=30, fill="x")

        ctk.CTkButton(
            sidebar_frame,
            text="Exportar Relatório",
            command=self.on_export,
            fg_color=COR_VAZAO,
            height=45,
        ).pack(pady=(10, 10), padx=30, fill="x")

        ctk.CTkButton(
            sidebar_frame,
            text="Nova Importação",
            command=self.on_new_import,
            fg_color="#6c757d",
            height=45,
        ).pack(pady=10, padx=30, fill="x")

    @staticmethod
    def _add_info_label(
        master_frame: ctk.CTkFrame,
        title: str,
        value: Any,
    ) -> None:
        """
        Adiciona um título e seu valor na barra lateral.
        """
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
        """
        Atualiza o texto do total positivo.

        O comportamento é igual ao atual: não converte o valor; apenas mostra
        L para unidade l/s e m³ nas demais unidades.
        """
        if self.total_label is None or self.general_indicators is None:
            return

        total_value: Any = self.general_indicators.get(
            "total_positive_accumulated",
            0,
        )

        unit_display: str = "L" if self.unit == "l/s" else "m³"

        self.total_label.configure(
            text=f"{float(total_value):,.0f} {unit_display}".replace(",", ".")
        )