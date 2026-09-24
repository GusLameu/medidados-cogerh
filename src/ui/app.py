"""
Modulo principal da interface grafica do usuario (GUI) para o aplicativo Medidados.
"""
from typing import Any, Dict, Optional, Tuple
import pandas as pd
import customtkinter as ctk
from tkinter import filedialog, messagebox
from tkinterdnd2 import TkinterDnD, DND_FILES
import threading
import os

from src.services.data_processing import DataProcessingService
from src.services.medidor_lookup import MedidorLookupService
from src.utils.helpers import resource_path
from src.ui.dashboard_window import DashboardWindow
from src.ui.components.confirmation_dialog import ConfirmationDialog, DialogResult
from src.core.config import COR_VAZAO, COR_FUNDO_DROP, MAPA_COLUNAS, ColumnMapping
from src.utils.logger import get_logger


logger = get_logger(__name__)


# Tipo para informacoes do medidor
MedidorInfo = Tuple[str, str, str]  # (tipo, modelo, local)


class AppAnalise(ctk.CTk, TkinterDnD.DnDWrapper):
    """
    Classe principal da aplicacao GUI Medidados.
    
    Gerencia a tela inicial, selecao/arrasto de arquivos e inicia o dashboard.
    
    Attributes:
        medidor_lookup_service: Servico de lookup de medidores.
        data_processing_service: Servico de processamento de dados.
        btn_manual: Botao de busca manual de arquivo.
        frame_drop: Frame para drag-and-drop de arquivos.
    """
    
    def __init__(self) -> None:
        """
        Inicializa a aplicacao, configura a janela principal e os widgets.
        """
        super().__init__()
        
        # Configurar tema
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")
        
        # Configurar drag-and-drop
        self.TkdndVersion = TkinterDnD._require(self)
        
        # Configurar janela
        self.title("Medidados")
        largura: int = 600
        altura: int = 750
        x: int = (self.winfo_screenwidth() // 2) - (largura // 2)
        y: int = (self.winfo_screenheight() // 2) - (altura // 2)
        self.geometry(f"{largura}x{altura}+{x}+{y}")
        self.configure(fg_color="#F0F0F0")
        
        # Tentar definir icone
        try:
            self.iconbitmap(resource_path("logo.ico"))
        except Exception:
            pass
        
        # Configurar drag-and-drop
        self.drop_target_register(DND_FILES)
        self.dnd_bind('<<Drop>>', self.soltar_arquivo)
        
        # Criar widgets
        self._create_widgets()
        
        # Inicializar servicos
        self.medidor_lookup_service: MedidorLookupService = MedidorLookupService()
        self.data_processing_service: DataProcessingService = DataProcessingService()
    
    def _create_widgets(self) -> None:
        """Cria e posiciona todos os widgets da interface."""
        # Titulo
        ctk.CTkLabel(
            self, 
            text="Medidados", 
            font=("Arial", 32, "bold"), 
            text_color=COR_VAZAO
        ).pack(pady=(50, 5))
        
        ctk.CTkLabel(
            self, 
            text="Sistema de Analise Tecnica", 
            font=("Arial", 14), 
            text_color="gray"
        ).pack(pady=(0, 40))
        
        # Botao manual
        self.btn_manual: ctk.CTkButton = ctk.CTkButton(
            self, 
            text="BUSCAR ARQUIVO MANUALMENTE", 
            command=self.run_manual, 
            height=55, 
            width=380, 
            font=("Arial", 14, "bold"), 
            fg_color=COR_VAZAO
        )
        self.btn_manual.pack(pady=30)
        
        # Frame de drop
        self.frame_drop: ctk.CTkFrame = ctk.CTkFrame(
            self, 
            width=450, 
            height=160, 
            fg_color=COR_FUNDO_DROP, 
            border_width=2, 
            border_color=COR_VAZAO, 
            corner_radius=20
        )
        self.frame_drop.pack(pady=10)
        self.frame_drop.pack_propagate(False)
        
        ctk.CTkLabel(
            self.frame_drop, 
            text="ARRASTE O ARQUIVO AQUI\n(Excel ou CSV)", 
            font=("Arial", 15, "bold"), 
            text_color=COR_VAZAO
        ).pack(expand=True)
        
        # Rodape
        ctk.CTkLabel(
            self, 
            text="v7.0 | Medidados\nGustavo Lopes Lameu\nGEMED", 
            font=("Arial", 10), 
            text_color="gray"
        ).pack(side="bottom", pady=15)
    
    def _set_processing_state(self, is_processing: bool) -> None:
        """
        Define o estado visual do botao de busca manual durante o processamento.
        
        Args:
            is_processing: True se estiver processando, False caso contrario.
        """
        if self.winfo_exists():
            estado: str = "disabled" if is_processing else "normal"
            texto: str = "PROCESSANDO DADOS..." if is_processing else "BUSCAR ARQUIVO MANUALMENTE"
            self.btn_manual.configure(state=estado, text=texto)
    
    def soltar_arquivo(self, event: Any) -> None:
        """
        Manipulador para evento de drop de arquivo.
        
        Args:
            event: Evento de drop com caminho do arquivo em event.data.
        """
        filepath: str = event.data.strip('{}')
        self.processar_caminho(filepath)
    
    def run_manual(self) -> None:
        """Abre dialogo de selecao de arquivo e processa o arquivo selecionado."""
        filepath: str = filedialog.askopenfilename(
            filetypes=[("Arquivos de Dados", "*.csv *.xlsx *.xls")]
        )
        if filepath:
            self.processar_caminho(filepath)
    
    def processar_caminho(self, path: str) -> None:
        """
        Inicia a identificacao do arquivo em uma thread separada.
        
        Args:
            path: Caminho completo para o arquivo de dados.
        """
        self._set_processing_state(True)
        
        def tarefa_background() -> None:
            try:
                # 1. Extrair numero de serie
                serial_number: Optional[str] = self.data_processing_service.peek_serial_number(path)
                
                if not serial_number:
                    raise ValueError(
                        "Nao foi possivel extrair o numero de serie do arquivo. "
                        "Verifique o formato."
                    )
                
                # 2. Buscar informacoes do medidor
                medidor_info: Optional[MedidorInfo] = self.medidor_lookup_service.get_medidor_info(serial_number)
                
                if not medidor_info:
                    raise ValueError(
                        f"N�mero de s�rie '{serial_number}' n�o encontrado na base de medidores. "
                        "Verifique o arquivo 'Medidores - 2026.xlsx'."
                    )
                
                medidor_type: str
                medidor_model: str
                medidor_local: str
                medidor_type, medidor_model, medidor_local = medidor_info
                
                # 3. Calcular vazao media para exibicao no popup
                df_temp: pd.DataFrame = self.data_processing_service._load_raw_data(path)
                df_temp.columns = [str(col).strip().upper() for col in df_temp.columns]
                
                logger.info(f"Colunas detectadas no arquivo: {df_temp.columns.tolist()}")
                
                column_mapping: ColumnMapping = MAPA_COLUNAS.get(medidor_model.strip().upper(), {})
                
                if column_mapping:
                    logger.info(f"Aplicando mapeamento para {medidor_model}: {column_mapping}")
                    df_temp = df_temp.rename(columns=column_mapping)
                
                logger.info(f"Colunas apos mapeamento: {df_temp.columns.tolist()}")
                
                mean_flow: float = 0.0
                if 'Vazao' in df_temp.columns:
                    logger.info(f"Coluna 'Vazao' encontrada. Primeiros valores: {df_temp['Vazao'].head().tolist()}")
                    vazao_col: pd.Series = pd.to_numeric(
                        df_temp['Vazao'].astype(str).str.replace(',', '.'), 
                        errors='coerce'
                    )
                    logger.info(f"Valores apos conversao numerica: {vazao_col.head().tolist()}")
                    vazao_col = vazao_col.dropna()
                    mean_flow = vazao_col.mean() if not vazao_col.empty else 0.0
                    logger.info(f"Media de vazao calculada: {mean_flow}")
                else:
                    logger.warning("Coluna 'Vazao' NAO encontrada apos o mapeamento!")
                
                # 4. Chamar popup de confirmacao na thread principal
                self.after(
                    0, 
                    lambda: self._mostrar_confirmacao(
                        path, medidor_type, medidor_model, medidor_local, mean_flow
                    )
                )
                
            except Exception as e:
                logger.error(f"Erro no processamento: {e}")
                self.after(0, lambda: messagebox.showerror("Erro", str(e)))
                self.after(0, self._reset_interface)
        
        thread: threading.Thread = threading.Thread(target=tarefa_background, daemon=True)
        thread.start()
    
    def _mostrar_confirmacao(
        self, 
        path: str, 
        medidor_type: str, 
        medidor_model: str, 
        medidor_local: str, 
        mean_flow: float
    ) -> None:
        """
        Exibe dialogo de confirmacao com informacoes do medidor.
        
        Args:
            path: Caminho do arquivo de dados.
            medidor_type: Tipo do medidor.
            medidor_model: Modelo do medidor.
            medidor_local: Local de instalacao.
            mean_flow: Vazao media calculada.
        """
        dialog: ConfirmationDialog = ConfirmationDialog(
            self, medidor_type, medidor_model, medidor_local, mean_flow
        )
        self.wait_window(dialog)
        
        result: Optional[DialogResult] = dialog.get_result()
        
        if result and result[0]:  # Confirmado
            unit: Optional[str] = result[1]
            
            thread: threading.Thread = threading.Thread(
                target=self._tarefa_processamento_completo, 
                args=(path, medidor_model, medidor_type, unit), 
                daemon=True
            )
            thread.start()
        else:
            self._reset_interface()
    
    def _tarefa_processamento_completo(
        self, 
        path: str, 
        medidor_model: str, 
        medidor_type: str, 
        unit: Optional[str]
    ) -> None:
        """
        Processa dados completos e abre dashboard em thread separada.
        
        Args:
            path: Caminho do arquivo de dados.
            medidor_model: Modelo do medidor.
            medidor_type: Tipo do medidor.
            unit: Unidade de medida selecionada.
        """
        try:
            processed_df: pd.DataFrame = self.data_processing_service.process_medidor_data(
                path, medidor_model
            )
            
            self.after(
                0, 
                lambda: self._finalizar_carregamento(
                    processed_df, medidor_model, medidor_type, unit or "m�/h"
                )
            )
            
        except Exception as e:
            logger.error(f"Erro no processamento completo: {e}")
            self.after(0, lambda: messagebox.showerror("Erro no Processamento", str(e)))
            self.after(0, self._reset_interface)
    
    def _finalizar_carregamento(
        self, 
        df: pd.DataFrame, 
        medidor_model: str, 
        medidor_type: str, 
        unit: str
    ) -> None:
        """
        Finaliza o carregamento e abre a janela do dashboard.
        
        Args:
            df: DataFrame processado com dados do medidor.
            medidor_model: Modelo do medidor.
            medidor_type: Tipo do medidor.
            unit: Unidade de medida de vazao.
        """
        self.withdraw()
        
        dashboard: DashboardWindow = DashboardWindow(
            self, df, medidor_model, medidor_type, unit=unit
        )
        self.wait_window(dashboard)
        
        # Verificar se janela pai ainda existe antes de operar
        if self.winfo_exists():
            self.deiconify()
            self._reset_interface()
    
    def _reset_interface(self) -> None:
        """
        Reseta a interface do usuario para o estado inicial apos o processamento.
        """
        if self.winfo_exists():
            self._set_processing_state(False)