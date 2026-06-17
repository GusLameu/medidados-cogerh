"""
Configurações e Constantes do Sistema
"""
import json
from src.utils.helpers import resource_path
from src.utils.logger import get_logger

logger = get_logger(__name__)

# Mapeamento de colunas original -> padrão do sistema (carregado de arquivo externo)
def _load_column_mappings():
    try:
        path = resource_path("src/core/column_mappings.json")
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        # Fallback básico para evitar que o app quebre se o arquivo sumir
        logger.error(f"Erro ao carregar mapeamento de colunas: {e}")
        return {}

MAPA_COLUNAS = _load_column_mappings()

# Configurações Visuais (UI/Dashboard)
COR_VAZAO = '#0047AB'      
COR_VELOCIDADE = '#D32F2F' 
COR_NIVEL = '#2E7D32'
COR_AREA = '#DA6314'
COR_TEXTO = '#333333'
COR_FUNDO_DROP = "#F0F8FF"
CORES_ROSCA = [
    '#D32F2F', # vermelho (negativo)
    "#9E9E9E",  # cinza (zero)
    '#0047AB', # azul (faixa normal)
    '#FFC107', # amarelo (acima da média)
    '#DA6314', # laranja
    ]

COR_STATUS_RUIM = '#D32F2F'      # Vermelho - QHidraulica < 90
COR_STATUS_MEDIO = '#FFC107'     # Amarelo - 90 <= QHidraulica > 100
COR_STATUS_BOM = '#0047AB'       # Azul - QHidraulica = 100

PIE_COLORS = {
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
            "< 65 (Crítico)": COR_STATUS_RUIM,
            "65-80 (Aceitavel)": COR_STATUS_MEDIO,
            "> 80 (Excelente)": COR_STATUS_BOM
        },
        "default": CORES_ROSCA
    },
    "status_process": {
        "patterns": {
            "8192 (Ruim)": COR_STATUS_RUIM,
            "4096 (Médio)": COR_STATUS_MEDIO,
            "0 (Bom)": COR_STATUS_BOM
        },
        "default": CORES_ROSCA
    },
    "qualidade_trigger": {
        "patterns": {
            "< 60% (Ruim)": COR_STATUS_RUIM,
            "60 - 80% (Médio)": COR_STATUS_MEDIO,
            "> 80% (Bom)": COR_STATUS_BOM
        },
        "default": CORES_ROSCA
    },
}

MODELO_CONFIG = {
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

