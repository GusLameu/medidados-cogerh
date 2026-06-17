"""
Ponto de entrada principal para a aplicação Medidados.
"""
from src.ui.app import AppAnalise # Importa a classe principal da GUI
from src.utils.helpers import resource_path # Para compatibilidade com PyInstaller, se necessário
from src.utils.logger import setup_logging

if __name__ == '__main__':
    # Inicializa o sistema de logging
    setup_logging()
    
    # Inicializa a aplicação GUI
    app = AppAnalise()
    # Inicia o loop principal da aplicação
    app.mainloop()
