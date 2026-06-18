"""
Módulo principal da interface gráfica do usuário (GUI) para o aplicativo Medidados.
"""
import pandas as pd
import customtkinter as ctk
from tkinter import filedialog, messagebox
from tkinterdnd2 import TkinterDnD, DND_FILES
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt
import numpy as np
import threading
from typing import Optional, Dict, Any, Tuple

from src.services.data_processing import DataProcessingService
from src.services.medidor_lookup import MedidorLookupService
from src.utils.helpers import resource_path
from src.ui.dashboard_window import DashboardWindow
from src.core.config import COR_VAZAO, COR_FUNDO_DROP

class AppAnalise(ctk.CTk, TkinterDnD.DnDWrapper): # Renamed from AppAnalise to App
    """
    Classe principal da aplicação GUI Medidados.
    Gerencia a tela inicial, seleção/arrasto de arquivos e inicia o dashboard.
    """
    def __init__(self):
        """
        Inicializa a aplicação, configura a janela principal e os widgets.
        """
        super().__init__()
        self.TkdndVersion = TkinterDnD._require(self)
        self.title("Medidados")
        l, a = 600, 750
        x, y = (self.winfo_screenwidth()//2 - l//2), (self.winfo_screenheight()//2 - a//2)
        self.geometry(f"{l}x{a}+{x}+{y}")
        self.configure(fg_color="white")
        
        try: self.iconbitmap(resource_path("logo.ico"))
        except: pass

        self.drop_target_register(DND_FILES)
        self.dnd_bind('<<Drop>>', self.soltar_arquivo)

        ctk.CTkLabel(self, text="Medidados", font=("Arial", 32, "bold"), text_color=COR_VAZAO).pack(pady=(50, 5))
        ctk.CTkLabel(self, text="Sistema de Análise Técnica", font=("Arial", 14), text_color="gray").pack(pady=(0, 40))

        self.btn_manual = ctk.CTkButton(self, text="BUSCAR ARQUIVO MANUALMENTE", command=self.run_manual, 
                                      height=55, width=380, font=("Arial", 14, "bold"), fg_color=COR_VAZAO)
        self.btn_manual.pack(pady=30)

        self.frame_drop = ctk.CTkFrame(self, width=450, height=160, fg_color=COR_FUNDO_DROP, border_width=2, border_color=COR_VAZAO, corner_radius=20)
        self.frame_drop.pack(pady=10); self.frame_drop.pack_propagate(False)
        ctk.CTkLabel(self.frame_drop, text="ARRASTE O ARQUIVO AQUI\n(Excel ou CSV)", font=("Arial", 15, "bold"), text_color=COR_VAZAO).pack(expand=True)

        ctk.CTkLabel(self, text="v6.0 | Medidados\nGustavo Lopes Lameu\nGEMED", font=("Arial", 10), text_color="gray").pack(side="bottom", pady=15)

        self.medidor_lookup_service = MedidorLookupService()
        self.data_processing_service = DataProcessingService()

    def _set_processing_state(self, is_processing: bool) -> None:
        """
        Define o estado visual do botão de busca manual durante o processamento.

        Args:
            is_processing: True para estado de processamento, False para estado normal.
        """
        self.btn_manual.configure(state="disabled" if is_processing else "normal",
                                  text="PROCESSANDO DADOS..." if is_processing else "BUSCAR ARQUIVO MANUALMENTE")

    def soltar_arquivo(self, event):
        filepath = event.data.strip('{}')
        self.processar_caminho(filepath)

    def run_manual(self):
        p = filedialog.askopenfilename(filetypes=[("Arquivos de Dados", "*.csv *.xlsx *.xls")])
        if p: self.processar_caminho(p)

    def processar_caminho(self, path):
        """
        Inicia o processamento do arquivo em uma thread separada.

        Args:
            path: Caminho completo para o arquivo de dados.
        """
        self._set_processing_state(True)
        def tarefa_background():
            try:
                # 1. Tentar extrair o número de série
                serial_number = self.data_processing_service.peek_serial_number(path)
                if not serial_number:
                    raise ValueError("Não foi possível extrair o número de série do arquivo. Verifique o formato.")

                # 2. Buscar informações do medidor (tipo e modelo)
                medidor_info = self.medidor_lookup_service.get_medidor_info(serial_number)
                if not medidor_info:
                    raise ValueError(f"Número de série '{serial_number}' não encontrado na base de medidores. Verifique o arquivo 'Medidores - 2026.xlsx'.")
                
                medidor_type, medidor_model = medidor_info

                # 3. Processar os dados completos com o modelo identificado
                processed_df = self.data_processing_service.process_medidor_data(path, medidor_model)
                
                self.after(0, lambda: self._finalizar_carregamento(processed_df, medidor_model, medidor_type))
            except Exception as e:
                self.after(0, lambda: messagebox.showerror("Erro", str(e)))
                self.after(0, self._reset_interface)
        threading.Thread(target=tarefa_background, daemon=True).start()

    def _finalizar_carregamento(self, data_frame: pd.DataFrame, medidor_model: str, medidor_type: str) -> None:
        """
        Finaliza o carregamento dos dados e abre a janela do dashboard.

        Args:
            data_frame: O DataFrame pandas processado.
            medidor_model: O modelo do medidor.
            medidor_type: O tipo do medidor.
        """
        self.withdraw()
        DashboardWindow(self, data_frame, medidor_model, medidor_type)
        self._reset_interface()

    def _reset_interface(self) -> None:
        """
        Reseta a interface do usuário para o estado inicial após o processamento.
        """
        self._set_processing_state(False)