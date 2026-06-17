import logging
import sys
from src.utils.helpers import resource_path

def setup_logging(log_file_name="medidados.log"):
    """
    Configura o sistema de logging para a aplicação.
    
    Args:
        log_file_name: Nome do arquivo onde os logs serão salvos.
    """
    # Caminho para o arquivo de log (na raiz do projeto ou junto ao executável)
    log_path = resource_path(log_file_name)
    
    # Formato do log: [Data/Hora] [Nível] [Módulo] - Mensagem
    log_format = logging.Formatter(
        '[%(asctime)s] [%(levelname)s] [%(name)s] - %(message)s',
        datefmt='%d/%m/%Y %H:%M:%S'
    )

    # Criar o logger raiz
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG) # Captura tudo, os handlers filtram depois

    # Limpar handlers existentes para evitar duplicidade em recarregamentos
    if logger.hasHandlers():
        logger.handlers.clear()

    # 1. Handler para arquivo (Salva logs de INFO para cima)
    try:
        file_handler = logging.FileHandler(log_path, encoding='utf-8')
        file_handler.setLevel(logging.INFO)
        file_handler.setFormatter(log_format)
        logger.addHandler(file_handler)
    except Exception as e:
        print(f"Erro ao configurar FileHandler de log: {e}")

    # 2. Handler para Console (Exibe logs no terminal)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.DEBUG)
    console_handler.setFormatter(log_format)
    logger.addHandler(console_handler)

    logging.info(f"Sistema de logging inicializado. Log sendo salvo em: {log_path}")
    return logger

def get_logger(name: str):
    """
    Retorna uma instância de logger para um módulo específico.
    
    Args:
        name: Nome do módulo ou classe.
    Returns:
        Uma instância de logging.Logger.
    """
    return logging.getLogger(name)

