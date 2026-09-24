"""
Sistema de logging da aplicacao.
"""
import logging
import sys
from typing import Optional
from src.utils.helpers import resource_path


def setup_logging(log_file_name: str = "medidados.log") -> logging.Logger:
    """
    Configura o sistema de logging para a aplicacao.
    
    Args:
        log_file_name: Nome do arquivo onde os logs serao salvos.
    
    Returns:
        O logger raiz configurado.
    
    Side Effects:
        - Cria/limpa handlers do logger raiz.
        - Adiciona FileHandler (nivel INFO) e StreamHandler (nivel DEBUG).
        - Configura formato: [Data/Hora] [Nivel] [Modulo] - Mensagem
    """
    log_path: str = resource_path(log_file_name)
    
    log_format: logging.Formatter = logging.Formatter(
        '[%(asctime)s] [%(levelname)s] [%(name)s] - %(message)s',
        datefmt='%d/%m/%Y %H:%M:%S'
    )
    
    logger: logging.Logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)
    
    if logger.hasHandlers():
        logger.handlers.clear()
    
    # Handler para arquivo
    try:
        file_handler: logging.FileHandler = logging.FileHandler(log_path, encoding='utf-8')
        file_handler.setLevel(logging.INFO)
        file_handler.setFormatter(log_format)
        logger.addHandler(file_handler)
    except Exception as e:
        print(f"Erro ao configurar FileHandler de log: {e}")
    
    # Handler para Console
    console_handler: logging.StreamHandler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.DEBUG)
    console_handler.setFormatter(log_format)
    logger.addHandler(console_handler)
    
    logging.info(f"Sistema de logging inicializado. Log sendo salvo em: {log_path}")
    return logger


def get_logger(name: str) -> logging.Logger:
    """
    Retorna uma instancia de logger para um modulo especifico.
    
    Args:
        name: Nome do modulo ou classe (ex: __name__).
    
    Returns:
        Uma instancia de logging.Logger para o modulo especificado.
    
    Example:
        >>> logger = get_logger(__name__)
        >>> logger.info("Mensagem de log")
    """
    return logging.getLogger(name)