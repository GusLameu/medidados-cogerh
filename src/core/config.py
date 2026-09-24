"""
Configuracoes e Constantes do Sistema.
"""
import json
from typing import Any, Dict, List, Literal, TypedDict
from src.utils.helpers import resource_path
from src.utils.logger import get_logger


logger = get_logger(__name__)


# Tipos para o mapeamento de colunas
ColumnMapping = Dict[str, str]  # Coluna original -> Coluna padrao


# Tipo para configuracao de modelo
LayoutType = Literal["completo", "simplificado"]


class ModeloConfig(TypedDict):
    """Configuracao de layout e graficos por modelo de medidor."""
    layout: LayoutType
    show_flow_speed_graph: bool
    show_pie_charts: bool
    pie_charts: List[str]
    show_status_process: bool


# Tipo para cores de graficos de rosca
PieColorPatterns = Dict[str, str]  # Rotulo -> cor hex


class PieColorConfig(TypedDict):
    """Configuracao de cores para um tipo de grafico de rosca."""
    patterns: PieColorPatterns
    default: List[str]


# Tipo para todas as cores de rosca
PieColorsConfig = Dict[str, PieColorConfig]


def _load_column_mappings() -> Dict[str, ColumnMapping]:
    """
    Carrega o mapeamento de colunas do arquivo JSON.
    
    Returns:
        Dicionario com mapeamento por modelo: {modelo: {coluna_original: coluna_padrao}}.
    
    Raises:
        Retorna dict vazio em caso de erro (fallback para nao quebrar o app).
    """
    try:
        path: str = resource_path("src/core/column_mappings.json")
        with open(path, 'r', encoding='utf-8') as f:
            data: Dict[str, ColumnMapping] = json.load(f)
            return data
    except Exception as e:
        logger.error(f"Erro ao carregar mapeamento de colunas: {e}")
        return {}


# Mapeamento de colunas original -> padrao do sistema
MAPA_COLUNAS: Dict[str, ColumnMapping] = _load_column_mappings()


# Configuracoes Visuais (UI/Dashboard)
COR_VAZAO: str = '#0047AB'
COR_VELOCIDADE: str = '#D32F2F'
COR_NIVEL: str = '#2E7D32'
COR_AREA: str = '#DA6314'
COR_TEXTO: str = '#333333'
COR_FUNDO_DROP: str = "#F0F8FF"

CORES_ROSCA: List[str] = [
    '#D32F2F',  # vermelho (negativo)
    "#9E9E9E",  # cinza (zero)
    '#0047AB',  # azul (faixa normal)
    '#FFC107',  # amarelo (acima da media)
    '#DA6314',  # laranja
]

COR_STATUS_RUIM: str = '#D32F2F'   # Vermelho - QHidraulica < 90
COR_STATUS_MEDIO: str = '#FFC107'  # Amarelo - 90 <= QHidraulica > 100
COR_STATUS_BOM: str = '#0047AB'    # Azul - QHidraulica = 100


# Cores para graficos de rosca
PIE_COLORS: PieColorsConfig = {
    "vazao": {
        "patterns": {
            "Negativo": '#D32F2F',
            "Zero": '#9E9E9E',
            "0 a": '#0047AB',
            "Acima": '#FFC107'
        },
        "default": CORES_ROSCA
    },
    "qualidade": {
        "patterns": {
            "sinal ruim: 20": '#D32F2F',
            "sinal ruim: 24": '#FFC107',
            "sinal ruim: 28": '#DA6314',
            "sinal bom: 192": '#0047AB'
        },
        "default": CORES_ROSCA
    },
    "status_hidraulico": {
        "patterns": {
            "< 65 (Critico)": COR_STATUS_RUIM,
            "65-80 (Aceitavel)": COR_STATUS_MEDIO,
            "> 80 (Excelente)": COR_STATUS_BOM
        },
        "default": CORES_ROSCA
    },
    "status_process": {
        "patterns": {
            "8192 (Ruim)": COR_STATUS_RUIM,
            "4096 (Medio)": COR_STATUS_MEDIO,
            "0 (Bom)": COR_STATUS_BOM
        },
        "default": CORES_ROSCA
    },
    "qualidade_trigger": {
        "patterns": {
            "< 60% (Ruim)": COR_STATUS_RUIM,
            "60 - 80% (Medio)": COR_STATUS_MEDIO,
            "> 80% (Bom)": COR_STATUS_BOM
        },
        "default": CORES_ROSCA
    },
}


# Configuracao de modelos por tipo de medidor
MODELO_CONFIG: Dict[str, ModeloConfig] = {
    "MV110": {
        "layout": "completo",
        "show_flow_speed_graph": True,
        "show_pie_charts": True,
        "pie_charts": ["vazao", "qualidade", "status_process"],
        "show_status_process": True
    },
    "MV145": {
        "layout": "simplificado",
        "show_flow_speed_graph": True,
        "show_pie_charts": False,
        "pie_charts": [],
        "show_status_process": False
    },
    "XMT1000": {
        "layout": "completo",
        "show_flow_speed_graph": True,
        "show_pie_charts": True,
        "pie_charts": ["vazao", "qualidade"],
        "show_status_process": False
    },
    "NF550": {
        "layout": "completo",
        "show_flow_speed_graph": True,
        "show_pie_charts": True,
        "pie_charts": ["vazao", "qualidade", "status_hidraulico"],
        "show_status_process": True
    },
    "NF750": {
        "layout": "completo",
        "show_flow_speed_graph": True,
        "show_pie_charts": True,
        "pie_charts": ["vazao", "qualidade", "status_hidraulico", "qualidade_trigger"],
        "show_status_process": True
    },
    "AT600": {
        "layout": "completo",
        "show_flow_speed_graph": True,
        "show_pie_charts": True,
        "pie_charts": ["vazao", "qualidade"],
        "show_status_process": False
    }
}