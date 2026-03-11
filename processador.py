import pandas as pd
import numpy as np
from config import MAPA_COLUNAS

def carregar_dados(caminho, modelo):
    try:
        if caminho.endswith('.csv'):
            df = pd.read_csv(caminho, sep=None, engine='python', encoding='utf-8-sig')
        else:
            df = pd.read_excel(caminho)
        
        df.columns = [str(col).strip() for col in df.columns]
        
        for col in df.columns:
            if df[col].dtype == 'object':
                df[col] = df[col].astype(str).str.replace(',', '.')

        df = df.rename(columns=MAPA_COLUNAS.get(modelo, {}))
        
        if 'Data' in df.columns:
            # CORREÇÃO: dayfirst=True evita que 02/09 vire 09 de fevereiro
            df['Data'] = pd.to_datetime(df['Data'], dayfirst=True, errors='coerce')
            df = df.dropna(subset=['Data'])
            df = df.sort_values('Data') 
        else:
            raise Exception("Coluna de data não encontrada.")
        
        for col in ['Vazao', 'Velocidade', 'Total']:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
                
        return df
    except Exception as e:
        raise Exception(f"Erro no processamento: {str(e)}")

def calcular_metricas_dashboard(df):
    v_pos = df[df['Vazao'] > 0]['Vazao']
    media = v_pos.mean() if not v_pos.empty else 0
    # Ajuste dinâmico do limite das faixas
    limite = (media // 10) * 10 if media > 10 else 100
    
    faixas = {
        f"Acima de {int(limite)}": len(df[df['Vazao'] > limite]),
        f"0 a {int(limite)}": len(df[(df['Vazao'] <= limite) & (df['Vazao'] > 0)]),
        "Negativa": len(df[df['Vazao'] <= 0])
    }
    
    # Qualidade formatada
    q_counts = df['Qualidade'].value_counts()
    qualidade = {str(int(k)): v for k, v in q_counts.items()}
    
    indicadores = {
        "serie": str(df['NUMEROSERIE_ATUAL'].iloc[0]) if 'NUMEROSERIE_ATUAL' in df.columns else "N/A",
        "data_inicio": df['Data'].min(),
        "data_fim": df['Data'].max(),
        "total_positivo": df['Total'].iloc[-1] if 'Total' in df.columns else 0
    }
    return faixas, qualidade, indicadores