"""
Módulo de funções utilitárias genéricas para o projeto.
"""
import sys
import os

def resource_path(relative_path: str) -> str:
    """
    Obtém o caminho absoluto para recursos, compatível com PyInstaller e ambiente de desenvolvimento.

    Args:
        relative_path: O caminho relativo do recurso.
    Returns:
        O caminho absoluto do recurso.
    """
    try:
        base_path = sys._MEIPASS  # PyInstaller creates a temporary folder
    except AttributeError:
        base_path = os.path.abspath(".")  # Development environment

    return os.path.join(base_path, relative_path)