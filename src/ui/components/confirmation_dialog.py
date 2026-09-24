"""
Dialogo de confirmacao para processamento de arquivo.
"""
from typing import Optional, Tuple
import customtkinter as ctk
from tkinter import messagebox


# Tipo para resultado do dialogo
DialogResult = Tuple[bool, Optional[str]]  # (confirmado, unidade_selecionada)


class ConfirmationDialog(ctk.CTkToplevel):
    """
    Dialogo customizado para confirmar o processamento de um arquivo.
    
    Exibe informacoes do medidor (tipo, modelo, local, vazao media)
    e permite escolha da unidade de medida de vazao.
    
    Attributes:
        tipo: Tipo do medidor.
        modelo: Modelo do medidor.
        local: Local de instalacao.
        vazao_media_original: Valor medio de vazao calculado.
        selected_unit: Unidade de medida selecionada pelo usuario.
        result: Resultado do dialogo (confirmado, unidade).
    """
    
    def __init__(
        self, 
        parent: ctk.CTk, 
        tipo: str, 
        modelo: str, 
        local: str, 
        vazao_media: float
    ) -> None:
        """
        Inicializa o dialogo de confirmacao.
        
        Args:
            parent: Janela pai (AppAnalise).
            tipo: Tipo do medidor.
            modelo: Modelo do medidor.
            local: Local de instalacao.
            vazao_media: Vazao media calculada a partir dos dados.
        """
        super().__init__(parent)
        
        self.parent: ctk.CTk = parent
        self.tipo: str = tipo
        self.modelo: str = modelo
        self.local: str = local
        self.vazao_media_original: float = vazao_media
        self.selected_unit: str = "m³/h"
        self.result: Optional[DialogResult] = None
        
        self._setup_ui()
    
    def _setup_ui(self) -> None:
        """Configura a interface do dialogo."""
        self.title("Confirmar Processamento")
        self.geometry("600x500")
        self.configure(fg_color="white")
        self.attributes("-topmost", True)
        self.grab_set()  # Torna o dialogo modal
        
        # Titulo
        self.label_title: ctk.CTkLabel = ctk.CTkLabel(
            self, 
            text="Confirmacao de Dados", 
            font=("Arial", 20, "bold"), 
            text_color="black"
        )
        self.label_title.pack(pady=(20, 10))
        
        # Frame de informacoes
        self.info_frame: ctk.CTkFrame = ctk.CTkFrame(self, fg_color="transparent")
        self.info_frame.pack(pady=10, padx=20, fill="x")
        
        info_text: str = (
            f"Tipo: {self.tipo}\n"
            f"Modelo: {self.modelo}\n"
            f"Local: {self.local}"
        )
        self.label_info: ctk.CTkLabel = ctk.CTkLabel(
            self.info_frame, 
            text=info_text, 
            font=("Arial", 14), 
            text_color="black", 
            justify="left"
        )
        self.label_info.pack(pady=5, anchor="w")
        
        # Selecao de unidade
        self.unit_frame: ctk.CTkFrame = ctk.CTkFrame(self, fg_color="transparent")
        self.unit_frame.pack(pady=10)
        
        ctk.CTkLabel(
            self.unit_frame, 
            text="Unidade de Vazao:", 
            font=("Arial", 12, "bold"), 
            text_color="black"
        ).pack(side="left", padx=5)
        
        self.unit_option: ctk.CTkOptionMenu = ctk.CTkOptionMenu(
            self.unit_frame, 
            values=["m³/h", "m³/s", "l/s"],
            command=self._update_vazao_display,
            fg_color="white",
            button_color="gray",
            text_color="black"
        )
        self.unit_option.pack(side="left", padx=5)
        self.unit_option.set("m³/h")
        
        # Display de vazao
        self.label_vazao: ctk.CTkLabel = ctk.CTkLabel(
            self, 
            text=f"Vazao Media: {self.vazao_media_original:.2f} m�/h", 
            font=("Arial", 14, "bold"), 
            text_color="black"
        )
        self.label_vazao.pack(pady=10)
        
        # Botoes
        self.button_frame: ctk.CTkFrame = ctk.CTkFrame(self, fg_color="transparent")
        self.button_frame.pack(pady=(20, 20))
        
        self.btn_confirm: ctk.CTkButton = ctk.CTkButton(
            self.button_frame, 
            text="Confirmar", 
            command=self._on_confirm, 
            fg_color="green", 
            text_color="white", 
            width=100
        )
        self.btn_confirm.pack(side="left", padx=10)
        
        self.btn_cancel: ctk.CTkButton = ctk.CTkButton(
            self.button_frame, 
            text="Cancelar", 
            command=self._on_cancel, 
            fg_color="red", 
            text_color="white", 
            width=100
        )
        self.btn_cancel.pack(side="left", padx=10)
        
        # Centralizar janela
        self._center_window()
    
    def _center_window(self) -> None:
        """Centraliza o dialogo na tela."""
        self.update_idletasks()
        
        dialog_width: int = 600
        dialog_height: int = 500
        
        screen_width: int = self.winfo_screenwidth()
        screen_height: int = self.winfo_screenheight()
        
        x: int = (screen_width // 2) - (dialog_width // 2)
        y: int = (screen_height // 2) - (dialog_height // 2)
        
        self.geometry(f"{dialog_width}x{dialog_height}+{x}+{y}")
    
    def _update_vazao_display(self, new_unit: str) -> None:
        """
        Atualiza o display de vazao quando unidade e alterada.
        
        Args:
            new_unit: Nova unidade selecionada (m�/h, m�/s, l/s).
        """
        self.selected_unit = new_unit
        self.label_vazao.configure(
            text=f"Vazao Media: {self.vazao_media_original:.2f} {new_unit}"
        )
    
    def _on_confirm(self) -> None:
        """Manipulador para botao Confirmar."""
        self.result = (True, self.selected_unit)
        self.destroy()
    
    def _on_cancel(self) -> None:
        """Manipulador para botao Cancelar."""
        self.result = (False, None)
        self.destroy()
    
    def get_result(self) -> Optional[DialogResult]:
        """
        Retorna o resultado do dialogo.
        
        Returns:
            Tupla (confirmado, unidade_selecionada) ou None se nao finalizado.
        
        Example:
            >>> dialog = ConfirmationDialog(parent, "Tipo", "Modelo", "Local", 100.5)
            >>> self.wait_window(dialog)
            >>> result = dialog.get_result()
            >>> if result and result[0]:
            ...     confirmed, unit = result
        """
        return self.result