"""
Visualização moderna e detalhada das ocorrências suspeitas identificadas no totalizado.
"""
from typing import Any, Optional
from tkinter import ttk, filedialog, messagebox

import customtkinter as ctk
import pandas as pd

from src.services.anomaly_detection import AnomalyConfig
from src.core.config import COR_VAZAO
from src.utils.helpers import resource_path
from src.utils.logger import get_logger

logger = get_logger(__name__)


class AnomaliesWindow(ctk.CTkToplevel):
    """
    Exibe o resultado da detecção de anomalias no totalizado com interface moderna,
    indicadores chave (KPIs), filtros interativos e opção de exportação.
    """

    def __init__(
        self,
        parent: ctk.CTkToplevel,
        anomalies_df: pd.DataFrame,
        medidor_model: str,
        config: AnomalyConfig,
    ) -> None:
        super().__init__(parent)

        self.parent: ctk.CTkToplevel = parent
        self.anomalies_df: pd.DataFrame = anomalies_df.copy()
        self.medidor_model: str = medidor_model
        self.config: AnomalyConfig = config
        self._sort_reverse: dict[str, bool] = {}
        self._current_filter: str = "Todas"

        self.title(f"Medidados - Anomalias no Totalizado ({medidor_model})")
        self.geometry("1240x720")
        self.minsize(920, 500)
        self.configure(fg_color="#F8FAFC")
        self.transient(parent)

        try:
            self.after(100, lambda: self.iconbitmap(resource_path("logo.ico")))
        except Exception:
            pass

        self._setup_treeview_style()
        self._build_layout()
        self._populate_table()
        self._center_window(1240, 720)

    def _center_window(self, width: int, height: int) -> None:
        """Posiciona a janela suavemente centralizada sobre a janela pai."""
        self.update_idletasks()
        try:
            parent_x = self.parent.winfo_rootx()
            parent_y = self.parent.winfo_rooty()
            parent_w = self.parent.winfo_width()
            parent_h = self.parent.winfo_height()
            x = parent_x + (parent_w // 2) - (width // 2)
            y = parent_y + (parent_h // 2) - (height // 2)
        except Exception:
            screen_w = self.winfo_screenwidth()
            screen_h = self.winfo_screenheight()
            x = (screen_w // 2) - (width // 2)
            y = (screen_h // 2) - (height // 2)

        x = max(10, x)
        y = max(10, y)
        self.geometry(f"{width}x{height}+{x}+{y}")

    def _setup_treeview_style(self) -> None:
        """Aplica estilo moderno e limpo ao ttk.Treeview."""
        style = ttk.Style()
        try:
            style.theme_use("clam")
        except Exception:
            pass

        style.configure(
            "Anomalies.Treeview",
            background="#FFFFFF",
            foreground="#1E293B",
            rowheight=32,
            fieldbackground="#FFFFFF",
            font=("Segoe UI", 10),
            borderwidth=0,
        )
        style.configure(
            "Anomalies.Treeview.Heading",
            background="#F1F5F9",
            foreground="#334155",
            font=("Segoe UI", 10, "bold"),
            relief="flat",
            padding=[10, 8],
            borderwidth=0,
        )
        style.map(
            "Anomalies.Treeview.Heading",
            background=[("active", "#E2E8F0")],
            foreground=[("active", "#0F172A")],
        )
        style.map(
            "Anomalies.Treeview",
            background=[("selected", "#E0E7FF")],
            foreground=[("selected", "#1E3A8A")],
        )

    def _build_layout(self) -> None:
        """Constrói todos os componentes visuais organizados da janela."""
        # Container principal com scroll caso a resolução seja pequena
        main_container = ctk.CTkFrame(self, fg_color="transparent")
        main_container.pack(fill="both", expand=True, padx=24, pady=20)

        # 1. Cabeçalho Superior
        self._build_header(main_container)

        # 2. Cards de Métricas (KPIs)
        self._build_metric_cards(main_container)

        # 3. Barra de Controles e Filtros
        self._build_control_bar(main_container)

        # 4. Tabela de Ocorrências
        self._build_table(main_container)

        # 5. Rodapé Informativo e Ações
        self._build_footer(main_container)

    def _build_header(self, container: ctk.CTkFrame) -> None:
        """Cabeçalho elegante com identidade visual e resumo de critérios."""
        header_card = ctk.CTkFrame(
            container,
            fg_color="#FFFFFF",
            corner_radius=12,
            border_width=1,
            border_color="#E2E8F0",
        )
        header_card.pack(fill="x", pady=(0, 16))

        inner = ctk.CTkFrame(header_card, fg_color="transparent")
        inner.pack(fill="x", padx=20, pady=16)

        # Lado esquerdo: Título e Identificação
        left_box = ctk.CTkFrame(inner, fg_color="transparent")
        left_box.pack(side="left", fill="both", expand=True)

        badge_row = ctk.CTkFrame(left_box, fg_color="transparent")
        badge_row.pack(anchor="w", pady=(0, 4))

        model_badge = ctk.CTkLabel(
            badge_row,
            text=f" MODELO {self.medidor_model.upper()} ",
            font=("Segoe UI", 11, "bold"),
            fg_color="#EFF6FF",
            text_color="#1D4ED8",
            corner_radius=6,
            height=22,
        )
        model_badge.pack(side="left", padx=(0, 8))

        ctk.CTkLabel(
            badge_row,
            text="ANÁLISE DE INTEGRIDADE",
            font=("Segoe UI", 10, "bold"),
            text_color="#64748B",
        ).pack(side="left")

        ctk.CTkLabel(
            left_box,
            text="Detecção de Anomalias no Totalizado",
            font=("Segoe UI", 20, "bold"),
            text_color="#0F172A",
        ).pack(anchor="w")

        ctk.CTkLabel(
            left_box,
            text="Identificação de variações atípicas, saltos e reduções suspeitas nos acumuladores de vazão.",
            font=("Segoe UI", 12),
            text_color="#64748B",
        ).pack(anchor="w", pady=(2, 0))

        # Lado direito: Parâmetros aplicados
        right_box = ctk.CTkFrame(
            inner,
            fg_color="#F8FAFC",
            corner_radius=8,
            border_width=1,
            border_color="#E2E8F0",
        )
        right_box.pack(side="right", padx=(12, 0), pady=2)

        right_inner = ctk.CTkFrame(right_box, fg_color="transparent")
        right_inner.pack(padx=14, pady=8)

        interval_text = (
            "Ilimitado"
            if self.config.max_interval_minutes is None
            else f"≤ {self.config.max_interval_minutes:g} min"
        )

        ctk.CTkLabel(
            right_inner,
            text="CRITÉRIOS DE FILTRAGEM",
            font=("Segoe UI", 9, "bold"),
            text_color="#64748B",
        ).pack(anchor="w")

        ctk.CTkLabel(
            right_inner,
            text=f"Salto Positivo: > {self.config.positive_jump_threshold:,.2f}\n"
                 f"Intervalo Máx.: {interval_text}\n"
                 f"Tolerância Neg.: {self.config.negative_tolerance:,.2f}",
            font=("Segoe UI", 11),
            text_color="#334155",
            justify="left",
        ).pack(anchor="w", pady=(2, 0))

    def _build_metric_cards(self, container: ctk.CTkFrame) -> None:
        """Cria 3 cartões informativos (KPIs) no topo."""
        cards_row = ctk.CTkFrame(container, fg_color="transparent")
        cards_row.pack(fill="x", pady=(0, 16))
        cards_row.grid_columnconfigure((0, 1, 2), weight=1, uniform="kpi")

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
        total_count = len(self.anomalies_df)

        # Card 1: Total
        self._create_card(
            parent=cards_row,
            column=0,
            title="TOTAL IDENTIFICADO",
            value=str(total_count),
            subtext="Ocorrências sob análise",
            accent_color="#0047AB",
            badge_bg="#EFF6FF",
            badge_fg="#1D4ED8",
            icon="📊",
        )

        # Card 2: Aumentos Atípicos
        self._create_card(
            parent=cards_row,
            column=1,
            title="AUMENTOS ATÍPICOS",
            value=str(positive_count),
            subtext="▲ Saltos acima do limiar configurado",
            accent_color="#DC2626",
            badge_bg="#FEF2F2",
            badge_fg="#991B1B",
            icon="▲",
        )

        # Card 3: Resets / Reduções
        self._create_card(
            parent=cards_row,
            column=2,
            title="POSSÍVEIS RESETS / REDUÇÕES",
            value=str(negative_count),
            subtext="▼ Reduções negativas no acumulado",
            accent_color="#D97706",
            badge_bg="#FFFBEB",
            badge_fg="#92400E",
            icon="▼",
        )

    def _create_card(
        self,
        parent: ctk.CTkFrame,
        column: int,
        title: str,
        value: str,
        subtext: str,
        accent_color: str,
        badge_bg: str,
        badge_fg: str,
        icon: str,
    ) -> None:
        """Cria um card métrico individual moderno."""
        card = ctk.CTkFrame(
            parent,
            fg_color="#FFFFFF",
            corner_radius=10,
            border_width=1,
            border_color="#E2E8F0",
        )
        card.grid(row=0, column=column, sticky="nsew", padx=6 if column == 1 else (0, 6) if column == 0 else (6, 0))

        content = ctk.CTkFrame(card, fg_color="transparent")
        content.pack(fill="both", expand=True, padx=16, pady=14)

        top_row = ctk.CTkFrame(content, fg_color="transparent")
        top_row.pack(fill="x")

        ctk.CTkLabel(
            top_row,
            text=title,
            font=("Segoe UI", 10, "bold"),
            text_color="#64748B",
        ).pack(side="left")

        ctk.CTkLabel(
            top_row,
            text=f" {icon} ",
            font=("Segoe UI", 11, "bold"),
            fg_color=badge_bg,
            text_color=badge_fg,
            corner_radius=4,
            height=20,
        ).pack(side="right")

        ctk.CTkLabel(
            content,
            text=value,
            font=("Segoe UI", 26, "bold"),
            text_color="#0F172A",
        ).pack(anchor="w", pady=(6, 2))

        ctk.CTkLabel(
            content,
            text=subtext,
            font=("Segoe UI", 11),
            text_color=accent_color,
        ).pack(anchor="w")

    def _build_control_bar(self, container: ctk.CTkFrame) -> None:
        """Barra com seletor de visualização (abas em cápsula cinza) e botão de exportação."""
        bar = ctk.CTkFrame(container, fg_color="transparent")
        bar.pack(fill="x", pady=(0, 10))

        # Cápsula de fundo cinza unificada, sem divisórias escuras
        self.filter_container = ctk.CTkFrame(
            bar,
            fg_color="#E2E8F0",
            corner_radius=8,
            border_width=0,
        )
        self.filter_container.pack(side="left")

        self.filter_buttons: dict[str, ctk.CTkButton] = {}
        filters: list[str] = [
            "Todas",
            "Aumentos Atípicos",
            "Possíveis Resets / Reduções",
        ]

        for filter_name in filters:
            btn = ctk.CTkButton(
                self.filter_container,
                text=filter_name,
                font=("Segoe UI", 11, "bold"),
                height=32,
                corner_radius=6,
                border_width=0,
                command=lambda name=filter_name: self._on_filter_changed(name),
            )
            btn.pack(side="left", padx=3, pady=3)
            self.filter_buttons[filter_name] = btn

        self._update_filter_button_styles()

        # Botão de Exportação CSV
        ctk.CTkButton(
            bar,
            text="📥 Exportar Relatório (CSV)",
            command=self._export_csv,
            fg_color=COR_VAZAO,
            hover_color="#003580",
            font=("Segoe UI", 11, "bold"),
            height=34,
            corner_radius=8,
        ).pack(side="right")

    def _update_filter_button_styles(self) -> None:
        """Atualiza a aparência dos botões: o selecionado em azul mais claro e sem divisões cinza escuro."""
        for name, btn in self.filter_buttons.items():
            if name == self._current_filter:
                btn.configure(
                    fg_color="#2563EB",
                    hover_color="#1D4ED8",
                    text_color="#FFFFFF",
                )
            else:
                btn.configure(
                    fg_color="transparent",
                    hover_color="#CBD5E1",
                    text_color="#475569",
                )

    def _build_table(self, container: ctk.CTkFrame) -> None:
        """Monta o container estilizado da tabela com scrollbars."""
        table_card = ctk.CTkFrame(
            container,
            fg_color="#FFFFFF",
            corner_radius=10,
            border_width=1,
            border_color="#E2E8F0",
        )
        table_card.pack(fill="both", expand=True, pady=(0, 14))

        table_card.grid_rowconfigure(0, weight=1)
        table_card.grid_columnconfigure(0, weight=1)

        columns: tuple[str, ...] = (
            "previous_date",
            "date",
            "type",
            "previous_total",
            "total",
            "variation",
            "interval",
        )

        self.tree = ttk.Treeview(
            table_card,
            columns=columns,
            show="headings",
            selectmode="browse",
            style="Anomalies.Treeview",
        )

        headings: dict[str, str] = {
            "previous_date": "Data Anterior",
            "date": "Data Atual",
            "type": "Classificação da Ocorrência",
            "previous_total": "Total Anterior",
            "total": "Total Atual",
            "variation": "Variação",
            "interval": "Intervalo (min)",
        }

        for column in columns:
            self.tree.heading(
                column,
                text=headings[column],
                command=lambda c=column: self._sort_column(c),
            )
            is_type = column == "type"
            is_date = column in ("previous_date", "date")

            self.tree.column(
                column,
                width=260 if is_type else 160 if is_date else 135,
                minwidth=110,
                anchor="w" if is_type else "center" if is_date else "e",
                stretch=True,
            )

        # Tags suaves para linhas
        self.tree.tag_configure(
            "positive",
            background="#FEF2F2",
            foreground="#991B1B",
        )
        self.tree.tag_configure(
            "negative",
            background="#FFFBEB",
            foreground="#92400E",
        )

        # Scrollbars modernas do CustomTkinter
        vertical_scroll = ctk.CTkScrollbar(
            table_card,
            orientation="vertical",
            command=self.tree.yview,
        )
        horizontal_scroll = ctk.CTkScrollbar(
            table_card,
            orientation="horizontal",
            command=self.tree.xview,
        )

        self.tree.configure(
            yscrollcommand=vertical_scroll.set,
            xscrollcommand=horizontal_scroll.set,
        )

        self.tree.grid(row=0, column=0, sticky="nsew", padx=(10, 0), pady=(10, 0))
        vertical_scroll.grid(row=0, column=1, sticky="ns", padx=(4, 8), pady=(10, 0))
        horizontal_scroll.grid(row=1, column=0, sticky="ew", padx=(10, 0), pady=(0, 8))

    def _build_footer(self, container: ctk.CTkFrame) -> None:
        """Rodapé informativo com contador e botão de fechamento."""
        footer = ctk.CTkFrame(container, fg_color="transparent")
        footer.pack(fill="x")

        # Texto informativo à esquerda
        info_label = ctk.CTkLabel(
            footer,
            text=(
                "ℹ️ Valores na unidade original do totalizado. "
                "Ocorrências exigem análise técnica especializada e não confirmam necessariamente falha do equipamento."
            ),
            font=("Segoe UI", 11),
            text_color="#64748B",
            justify="left",
            wraplength=750,
        )
        info_label.pack(side="left")

        # Botão Fechar e Contador à direita
        right_footer = ctk.CTkFrame(footer, fg_color="transparent")
        right_footer.pack(side="right")

        self.counter_label = ctk.CTkLabel(
            right_footer,
            text="",
            font=("Segoe UI", 11, "bold"),
            text_color="#64748B",
        )
        self.counter_label.pack(side="left", padx=(0, 16))

        ctk.CTkButton(
            right_footer,
            text="Fechar",
            command=self.destroy,
            fg_color="#64748B",
            hover_color="#475569",
            font=("Segoe UI", 11, "bold"),
            height=36,
            width=110,
            corner_radius=8,
        ).pack(side="right")

    def _on_filter_changed(self, selected_filter: str) -> None:
        """Callback acionado ao alternar o filtro de ocorrências."""
        self._current_filter = selected_filter
        self._update_filter_button_styles()
        self._populate_table()

    def _populate_table(self) -> None:
        """Preenche ou atualiza os dados da tabela respeitando os filtros ativos."""
        for item in self.tree.get_children():
            self.tree.delete(item)

        df = self.anomalies_df
        if self._current_filter == "Aumentos Atípicos":
            df = df[df["TipoAnomalia"] == "Aumento atípico no totalizado"]
        elif self._current_filter == "Possíveis Resets / Reduções":
            df = df[df["TipoAnomalia"] == "Possível reset/redução"]

        for _, row in df.iterrows():
            variation = float(row["Variacao"])
            is_negative = variation < 0

            # Formatação amigável com separador brasileiro
            tipo = str(row["TipoAnomalia"])
            prefix = "▼ " if is_negative else "▲ "

            self.tree.insert(
                "",
                "end",
                values=(
                    pd.Timestamp(row["DataAnterior"]).strftime("%d/%m/%Y %H:%M:%S"),
                    pd.Timestamp(row["Data"]).strftime("%d/%m/%Y %H:%M:%S"),
                    f"{prefix}{tipo}",
                    self._format_number(float(row["TotalAnterior"])),
                    self._format_number(float(row["Total"])),
                    self._format_number(variation, signed=True),
                    self._format_number(float(row["IntervaloMinutos"])),
                ),
                tags=("negative" if is_negative else "positive",),
            )

        self.counter_label.configure(
            text=f"Exibindo {len(df)} de {len(self.anomalies_df)} registros"
        )

    @staticmethod
    def _format_number(val: float, signed: bool = False) -> str:
        """Formata valores numéricos para o padrão pt-BR (1.234,56)."""
        sign_str = ""
        if signed and val > 0:
            sign_str = "+"
        elif val < 0:
            sign_str = "-"

        abs_str = f"{abs(val):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        return f"{sign_str}{abs_str}"

    def _sort_column(self, col: str) -> None:
        """Ordena as linhas da tabela de forma natural ao clicar no cabeçalho."""
        reverse = self._sort_reverse.get(col, False)
        self._sort_reverse[col] = not reverse

        items = [(self.tree.set(k, col), k) for k in self.tree.get_children("")]

        def parse_key(item: tuple[str, str]) -> Any:
            val = item[0]
            # Tenta limpar formatação numérica brasileira e ordenar como float
            cleaned = (
                val.replace(".", "")
                .replace(",", ".")
                .replace("+", "")
                .replace("▲", "")
                .replace("▼", "")
                .strip()
            )
            try:
                return (0, float(cleaned))
            except ValueError:
                pass

            # Tenta converter para datetime se for data
            try:
                return (1, pd.to_datetime(val, format="%d/%m/%Y %H:%M:%S"))
            except Exception:
                pass

            return (2, val.lower())

        items.sort(key=parse_key, reverse=reverse)
        for index, (_, k) in enumerate(items):
            self.tree.move(k, "", index)

    def _export_csv(self) -> None:
        """Exporta os registros de anomalias para um arquivo CSV formatado para Excel."""
        if self.anomalies_df.empty:
            messagebox.showinfo(
                "Exportação",
                "Não existem registros de anomalias para exportar.",
                parent=self,
            )
            return

        file_path = filedialog.asksaveasfilename(
            parent=self,
            title="Exportar Relatório de Anomalias",
            defaultextension=".csv",
            filetypes=[("Planilha CSV (*.csv)", "*.csv"), ("Todos os arquivos", "*.*")],
            initialfile=f"anomalias_{self.medidor_model.lower()}.csv",
        )
        if not file_path:
            return

        try:
            # Exporta com delimitador ';' e decimal ',' para compatibilidade nativa com Excel pt-BR
            export_df = self.anomalies_df.copy()
            export_df.to_csv(
                file_path,
                index=False,
                sep=";",
                encoding="utf-8-sig",
                decimal=",",
            )
            messagebox.showinfo(
                "Exportação Concluída",
                f"O arquivo foi salvo com sucesso em:\n{file_path}",
                parent=self,
            )
        except Exception as error:
            logger.error(f"Erro ao exportar anomalias para CSV: {error}")
            messagebox.showerror(
                "Erro na Exportação",
                f"Não foi possível salvar o arquivo:\n{error}",
                parent=self,
            )
