"""
Visualização das ocorrências suspeitas identificadas no totalizado.
"""
from tkinter import ttk

import customtkinter as ctk
import pandas as pd

from src.services.anomaly_detection import AnomalyConfig


class AnomaliesWindow(ctk.CTkToplevel):
    """Exibe o resultado da detecção sem modificar os dados originais."""

    def __init__(
        self,
        parent: ctk.CTkToplevel,
        anomalies_df: pd.DataFrame,
        medidor_model: str,
        config: AnomalyConfig,
    ) -> None:
        super().__init__(parent)

        self.anomalies_df: pd.DataFrame = anomalies_df.copy()
        self.config: AnomalyConfig = config

        self.title(f"Medidados - Anomalias ({medidor_model})")
        self.geometry("1200x650")
        self.minsize(850, 450)
        self.configure(fg_color="white")
        self.transient(parent)

        self._build_layout()
        self._populate_table()

    def _build_layout(self) -> None:
        """Cria cabeçalho, tabela e botão de fechamento."""
        ctk.CTkLabel(
            self,
            text="ANOMALIAS NO TOTALIZADO",
            font=("Arial", 22, "bold"),
            text_color="#B71C1C",
        ).pack(pady=(20, 8))

        positive_count = int(
            self.anomalies_df["TipoAnomalia"]
            .eq("Aumento atípico no totalizado")
            .sum()
        )
        negative_count = int(
            self.anomalies_df["TipoAnomalia"]
            .eq("Possível reset/redução")
            .sum()
        )

        ctk.CTkLabel(
            self,
            text=(
                f"{len(self.anomalies_df)} ocorrências | "
                f"Aumentos atípicos: {positive_count} | "
                f"Possíveis resets/reduções: {negative_count}"
            ),
            font=("Arial", 13),
            text_color="#333333",
        ).pack(pady=(0, 8))

        interval_text = (
            "sem limite de intervalo"
            if self.config.max_interval_minutes is None
            else f"intervalo máximo de {self.config.max_interval_minutes:g} min"
        )

        ctk.CTkLabel(
            self,
            text=(
                f"Salto positivo > {self.config.positive_jump_threshold:,.2f}; "
                f"{interval_text}.\n"
                "Valores na unidade original do totalizado. "
                "Ocorrências exigem análise; não confirmam falha ou zeragem."
            ),
            font=("Arial", 12),
            text_color="#555555",
            wraplength=1000,
        ).pack(padx=20, pady=(0, 15))

        table_frame = ctk.CTkFrame(self, fg_color="white")
        table_frame.pack(
            fill="both",
            expand=True,
            padx=20,
            pady=(0, 15),
        )
        table_frame.grid_rowconfigure(0, weight=1)
        table_frame.grid_columnconfigure(0, weight=1)

        columns: tuple[str, ...] = (
            "previous_date",
            "date",
            "type",
            "previous_total",
            "total",
            "variation",
            "interval",
        )

        self.tree: ttk.Treeview = ttk.Treeview(
            table_frame,
            columns=columns,
            show="headings",
            selectmode="browse",
        )

        headings: dict[str, str] = {
            "previous_date": "Data anterior",
            "date": "Data atual",
            "type": "Ocorrência",
            "previous_total": "Total anterior",
            "total": "Total atual",
            "variation": "Variação",
            "interval": "Intervalo (min)",
        }

        for column in columns:
            self.tree.heading(column, text=headings[column])
            self.tree.column(
                column,
                width=240 if column == "type" else 150,
                minwidth=110,
                anchor="w" if column == "type" else "center",
                stretch=False,
            )

        self.tree.tag_configure(
            "positive",
            background="#FDECEA",
            foreground="#8B1A1A",
        )
        self.tree.tag_configure(
            "negative",
            background="#FFF8E1",
            foreground="#705000",
        )

        vertical_scroll = ttk.Scrollbar(
            table_frame,
            orient="vertical",
            command=self.tree.yview,
        )
        horizontal_scroll = ttk.Scrollbar(
            table_frame,
            orient="horizontal",
            command=self.tree.xview,
        )

        self.tree.configure(
            yscrollcommand=vertical_scroll.set,
            xscrollcommand=horizontal_scroll.set,
        )

        self.tree.grid(row=0, column=0, sticky="nsew")
        vertical_scroll.grid(row=0, column=1, sticky="ns")
        horizontal_scroll.grid(row=1, column=0, sticky="ew")

        ctk.CTkButton(
            self,
            text="Fechar",
            command=self.destroy,
            fg_color="#6c757d",
            height=40,
            width=150,
        ).pack(pady=(0, 20))

    def _populate_table(self) -> None:
        """Preenche a tabela com as ocorrências já calculadas."""
        for _, row in self.anomalies_df.iterrows():
            variation = float(row["Variacao"])

            self.tree.insert(
                "",
                "end",
                values=(
                    pd.Timestamp(row["DataAnterior"]).strftime(
                        "%d/%m/%Y %H:%M:%S"
                    ),
                    pd.Timestamp(row["Data"]).strftime(
                        "%d/%m/%Y %H:%M:%S"
                    ),
                    str(row["TipoAnomalia"]),
                    f"{float(row['TotalAnterior']):,.2f}",
                    f"{float(row['Total']):,.2f}",
                    f"{variation:+,.2f}",
                    f"{float(row['IntervaloMinutos']):,.2f}",
                ),
                tags=("negative" if variation < 0 else "positive",),
            )