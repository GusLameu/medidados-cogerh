import customtkinter as ctk
from tkinter import messagebox

class ConfirmationDialog(ctk.CTkToplevel):
    """
    Diálogo customizado para confirmar o processamento de um arquivo,
    exibindo informações do medidor e permitindo a escolha da unidade de medida.
    """
    def __init__(self, parent, tipo: str, modelo: str, local: str, vazao_media: float):
        super().__init__(parent)
        
        self.title("Confirmar Processamento")
        self.geometry("450x400")
        self.configure(fg_color="white")
        self.attributes("-topmost", True)
        self.grab_set()  # Make the dialog modal

        self.tipo = tipo
        self.modelo = modelo
        self.local = local
        self.vazao_media_original = vazao_media
        self.selected_unit = "m³/h"
        self.result = None # Will be (True, unit) or (False, None)

        # UI Elements
        self.label_title = ctk.CTkLabel(self, text="Confirmação de Dados", font=("Arial", 20, "bold"), text_color="black")
        self.label_title.pack(pady=(20, 10))

        self.info_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.info_frame.pack(pady=10, padx=20, fill="x")

        info_text = (
            f"Tipo: {self.tipo}\n"
            f"Modelo: {self.modelo}\n"
            f"Local: {self.local}"
        )
        self.label_info = ctk.CTkLabel(self.info_frame, text=info_text, font=("Arial", 14), text_color="black", justify="left")
        self.label_info.pack(pady=5, anchor="w")

        # Unit Selection
        self.unit_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.unit_frame.pack(pady=10)
        
        ctk.CTkLabel(self.unit_frame, text="Unidade de Vazão:", font=("Arial", 12, "bold"), text_color="black").pack(side="left", padx=5)
        
        self.unit_option = ctk.CTkOptionMenu(
            self.unit_frame, 
            values=["m³/h", "m³/s", "l/s"],
            command=self._update_vazao_display,
            fg_color="white",
            button_color="gray",
            text_color="black"
        )
        self.unit_option.pack(side="left", padx=5)
        self.unit_option.set("m³/h")

        # Vazao Display
        self.label_vazao = ctk.CTkLabel(self, text=f"Vazão Média: {self.vazao_media_original:.2f} m³/h", font=("Arial", 14, "bold"), text_color="black")
        self.label_vazao.pack(pady=10)

        # Buttons
        self.button_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.button_frame.pack(pady=(20, 20))

        self.btn_confirm = ctk.CTkButton(self.button_frame, text="Confirmar", command=self._on_confirm, fg_color="green", text_color="white", width=100)
        self.btn_confirm.pack(side="left", padx=10)

        self.btn_cancel = ctk.CTkButton(self.button_frame, text="Cancelar", command=self._on_cancel, fg_color="red", text_color="white", width=100)
        self.btn_cancel.pack(side="left", padx=10)

        # Center the window on the parent
        self.update_idletasks()

        # Get parent window position and size
        parent_x = parent.winfo_x()
        parent_y = parent.winfo_y()
        parent_width = parent.winfo_width()
        parent_height = parent.winfo_height()

        # Get dialog size
        dialog_width = self.winfo_width()
        dialog_height = self.winfo_height()

        # Calculate center position relative to parent
        x = parent_x + (parent_width // 2) - (dialog_width // 2)
        y = parent_y + (parent_height // 2) - (dialog_height // 2)

        # Ensure dialog stays within screen bounds
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()

        dialog_width = 450
        dialog_height = 400

        # Centro da tela
        x = (screen_width // 2) - (dialog_width // 2)
        y = (screen_height // 2) - (dialog_height // 2)

        self.geometry(f"{dialog_width}x{dialog_height}+{x}+{y}")

    def _update_vazao_display(self, new_unit):
        self.selected_unit = new_unit
        
        # Conversion factors relative to m3/h
        # 1 m3/h = 1/3600 m3/s
        # 1 m3/h = 1000 / 3600 l/s = 1/3.6 l/s
        
        val = self.vazao_media_original
        if new_unit == "m³/s":
            val = val / 3600
        elif new_unit == "l/s":
            val = val / 3.6
            
        self.label_vazao.configure(text=f"Vazão Média: {val:.4f} {new_unit}")

    def _on_confirm(self):
        self.result = (True, self.selected_unit)
        self.destroy()

    def _on_cancel(self):
        self.result = (False, None)
        self.destroy()

    def get_result(self):
        return self.result
