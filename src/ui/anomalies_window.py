"""
Janela de visualização das anomalias identificadas no totalizado.
"""
from typing import Optional

import customtkinter as ctk
import pandas as pd
from tkinter import ttk


class AnomaliesWindow(ctk.CTkToplevel):
    """
    Exibe anomalias identificadas em saltos do totalizado do medidor.
    """

    def __init__(
        self,
        parent: ctk.CTkToplevel,
        anomalies_df: pd.DataFrame,
        medidor_model: str,
        unit: str,
    ) -> None:
        super().__init__(parent)

        self.anomalies_df: pd.DataFrame = anomalies_df.copy()
        self.medidor_model: str = medidor_model
        self.unit: str = unit

        self.title(f"Medidados - Anomalias ({medidor_model})")
        self.geometry("1100x600")
        self.configure(fg_color="white")
        self.transient(parent)
        self.grab_set()

        self._setup_layout()

    def _setup_layout(self) -> None:
        """Monta título, resumo e tabela de anomalias."""
        ctk.CTkLabel(
            self,
            text="ANOMALIAS NO TOTALIZADO",
            font=("Arial", 22, "bold"),
            text_color="#D32F2F",
        ).pack(pady=(20, 5))

        ctk.CTkLabel(
            self,
            text=(
                f"Foram encontradas {len(self.anomalies_df)} ocorrências. "
                "Aumentos atípicos e reduções no totalizado exigem validação."
            ),
            font=("Arial", 13),
            text_color="#444444",
        ).pack(pady=(0, 20))

        table_frame = ctk.CTkFrame(self, fg_color="white")
        table_frame.pack(fill="both", expand=True, padx=20, pady=(0, 15))

        columns: tuple[str, ...] = (
            "data",
            "tipo",
            "anterior",
            "atual",
            "variacao",
            "limite",
            "severidade",
        )

        self.tree = ttk.Treeview(
            table_frame,
            columns=columns,
            show="headings",
            height=18,
        )

        headings: dict[str, str] = {
            "data": "Data",
            "tipo": "Tipo",
            "anterior": "Total anterior",
            "atual": "Total atual",
            "variacao": "Variação",
            "limite": "Limite de salto",
            "severidade": "Severidade",
        }

        widths: dict[str, int] = {
            "data": 150,
            "tipo": 250,
            "anterior": 125,
            "atual": 125,
            "variacao": 125,
            "limite": 125,
            "severidade": 100,
        }

        for column in columns:
            self.tree.heading(column, text=headings[column])
            self.tree.column(
                column,
                width=widths[column],
                anchor="center",
            )

        self.tree.tag_configure(
            "alta",
            background="#FDECEA",
            foreground="#B71C1C",
        )
        self.tree.tag_configure(
            "media",
            background="#FFF8E1",
            foreground="#8A6200",
        )

        for _, row in self.anomalies_df.iterrows():
            date_value = pd.Timestamp(row["Data"]).strftime("%d/%m/%Y %H:%M")

            severity = str(row["Severidade"])
            tag = "alta" if severity == "Alta" else "media"

            self.tree.insert(
                "",
                "end",
                values=(
                    date_value,
                    str(row["TipoAnomalia"]),
                    f"{float(row['TotalAnterior']):,.2f}",
                    f"{float(row['Total']):,.2f}",
                    f"{float(row['Variacao']):,.2f}",
                    f"{float(row['LimiteAnomalia']):,.2f}",
                    severity,
                ),
                tags=(tag,),
            )

        scrollbar = ttk.Scrollbar(
            table_frame,
            orient="vertical",
            command=self.tree.yview,
        )
        self.tree.configure(yscrollcommand=scrollbar.set)

        self.tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        ctk.CTkButton(
            self,
            text="Fechar",
            command=self.destroy,
            fg_color="#6C757D",
            height=40,
            width=150,
        ).pack(pady=(0, 20))