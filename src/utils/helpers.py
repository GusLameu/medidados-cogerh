"""
Funcoes utilitarias do sistema.
"""
import os
import sys
from pathlib import Path


def resource_path(relative_path: str) -> str:
    """
    Retorna o caminho absoluto para um recurso, funcionando tanto em
    desenvolvimento quanto quando empacotado com PyInstaller.
    
    Args:
        relative_path: Caminho relativo ao recurso (ex: "logo.ico", "src/core/column_mappings.json").
    
    Returns:
        Caminho absoluto completo para o recurso.
    
    Example:
        >>> icon_path = resource_path("logo.ico")
        >>> config_path = resource_path("src/core/column_mappings.json")
    """
    if hasattr(sys, "_MEIPASS"):
        # Executando como executavel PyInstaller
        base_path: Path = Path(sys._MEIPASS)
    else:
        # Executando em ambiente de desenvolvimento
        base_path = Path(os.path.dirname(os.path.abspath(sys.argv[0])))
    
    return str(base_path / relative_path)