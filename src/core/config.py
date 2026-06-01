"""
Configurações e Constantes do Sistema
"""

# Mapeamento de colunas original -> padrão do sistema
MAPA_COLUNAS = {
    "MV110": {
        "E3TIMESTAMP": "Data",
        "TOTALIZADO": "Total",
        "TENSAOE1_QUALITY": "Qualidade",
        "VAZAO": "Vazao",
        "FLOWSPEED": "Velocidade",
        "PROCESS": "Process"
    },
    "MV145": {
        "DATA_DISPOSITIVO": "Data",
        "VAZAO": "Vazao",
        "VOLUME": "Volume"
    },
    "XMT1000": {
        "E3TIMESTAMP": "Data",
        "TOTAL_POS": "Total",
        "VELOCIDADE_SOM_QUALITY": "Qualidade",
        "VAZAO": "Vazao",
        "VELOCIDADE": "Velocidade"
    },
    "NF550": {
        "E3TIMESTAMP": "Data",
        "TOTALIZADO": "Total",
        "VELOCIDADE_SOM_QUALITY": "Qualidade",
        "VAZAO": "Vazao",
        "VELOCIDADE": "Velocidade",
        "QUALIDADE_HIDRAULICA": "QHidraulica"
    },
    "NF750": {
        "E3TIMESTAMP": "Data",
        "TOTALIZADO": "Total",
        "VELOCIDADE_SOM_QUALITY": "Qualidade",
        "VAZAO": "Vazao",
        "VELOCIDADE": "Velocidade",
        "QUALIDADE_HIDRAULICA": "QHidraulica",
        "QUALIDADE_TRIGGER": "QualidadeTrigger",
        "AREA": "Area",
        "NIVEL": "Nivel"
    },
    "AT600": {
        "E3TIMESTAMP": "Data",
        "TOTAL_POS": "Total",
        "VELOCIDADE_SOM_QUALITY": "Qualidade",
        "VAZAO": "Vazao",
        "VELOCIDADE": "Velocidade"
    }
}

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
            "< 90 (Ruim)": COR_STATUS_RUIM,
            "90-99 (Médio)": COR_STATUS_MEDIO,
            "= 100 (Bom)": COR_STATUS_BOM
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
