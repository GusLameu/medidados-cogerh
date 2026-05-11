"""
Módulo responsável pelo carregamento, limpeza e processamento de dados de medidores.
"""
import pandas as pd
import numpy as np
from typing import Dict, Any, Tuple, List, Optional
from src.core.config import MAPA_COLUNAS

class DataProcessingService:
    """
    Serviço para carregar, limpar e calcular métricas a partir de dados de medidores.
    """

    @staticmethod
    def _load_raw_data(file_path: str) -> pd.DataFrame:
        """
        Carrega dados brutos de um arquivo CSV ou Excel.

        Args:
            file_path: Caminho completo para o arquivo de dados.
        Returns:
            Um DataFrame pandas com os dados carregados.
        Raises:
            ValueError: Se o formato do arquivo não for suportado.
            IOError: Se houver um erro ao ler o arquivo.
        """
        try:
            if file_path.endswith('.csv'):
                # sep=None com engine python detecta automaticamente se é vírgula ou ponto e vírgula
                df = pd.read_csv(file_path, sep=None, engine='python', encoding='utf-8-sig')
            elif file_path.endswith(('.xlsx', '.xls')):
                df = pd.read_excel(file_path)
            else:
                raise ValueError("Formato de arquivo não suportado. Use .csv, .xlsx ou .xls.")
            return df
        except Exception as e:
            raise IOError(f"Erro ao carregar o arquivo '{file_path}': {e}")

    @staticmethod
    def peek_serial_number(file_path: str) -> Optional[str]:
        """
        Tenta extrair o número de série do arquivo de dados sem carregar tudo.
        Assume que o número de série está na primeira linha/coluna ou em uma coluna específica.
        Esta é uma implementação simplificada e pode precisar ser ajustada
        com base na estrutura real dos arquivos de entrada.

        Args:
            file_path: Caminho para o arquivo de dados.
        Returns:
            O número de série encontrado ou None se não for possível extrair.
        """
        try:
            # Para CSV, tenta ler a primeira linha como string e buscar um padrão
            if file_path.endswith('.csv'):
                with open(file_path, 'r', encoding='utf-8-sig') as f:
                    first_line = f.readline()
                    # Exemplo: buscar "SN:12345" ou "Serial Number,12345"
                    # Isso é altamente dependente do formato do arquivo.
                    # Uma abordagem mais robusta seria carregar um pequeno chunk e procurar.
                    # Por simplicidade, vamos carregar as primeiras linhas e procurar por "NUMEROSERIE"
                    temp_df = pd.read_csv(file_path, sep=None, engine='python', encoding='utf-8-sig', nrows=5)
                    temp_df.columns = [str(col).strip().upper() for col in temp_df.columns]
                    if 'NUMEROSERIE_ATUAL' in temp_df.columns:
                        return str(temp_df['NUMEROSERIE_ATUAL'].iloc[0])
                    elif 'NUMERO_SERIE' in temp_df.columns:
                        return str(temp_df['NUMERO_SERIE'].iloc[0])

            # Para Excel, tenta ler a primeira planilha e procurar por "NUMEROSERIE"
            elif file_path.endswith(('.xlsx', '.xls')):
                temp_df = pd.read_excel(file_path, nrows=5)
                temp_df.columns = [str(col).strip().upper() for col in temp_df.columns]
                if 'NUMEROSERIE_ATUAL' in temp_df.columns:
                    return str(temp_df['NUMEROSERIE_ATUAL'].iloc[0])
                elif 'NUMERO_SERIE' in temp_df.columns:
                    return str(temp_df['NUMERO_SERIE'].iloc[0])
            return None
        except Exception:
            return None # Não foi possível extrair, retorna None

    @staticmethod
    def process_medidor_data(file_path: str, medidor_model: str) -> pd.DataFrame:
        """
        Carrega e processa os dados de um medidor, aplicando limpeza e transformações.

        Args:
            file_path: Caminho para o arquivo de dados (CSV ou Excel).
            medidor_model: O modelo do medidor (ex: "MV110", "XMT1000") para mapeamento de colunas.
        Returns:
            Um DataFrame pandas processado.
        Raises:
            Exception: Se ocorrer um erro durante o processamento.
        """
        df = DataProcessingService._load_raw_data(file_path)

        # 1. Limpeza de nomes de colunas
        df.columns = [str(col).strip() for col in df.columns]

        # 2. Tratamento de Números (Lida com o padrão brasileiro "1.234,56")
        for col in df.columns:
            if df[col].dtype == 'object':
                # Remove pontos de milhar e troca vírgula por ponto
                df[col] = df[col].astype(str).str.replace('.', '', regex=False).str.replace(',', '.', regex=False)

        # 3. Renomeação conforme o dicionário de mapeamento para o modelo específico
        column_mapping = MAPA_COLUNAS.get(medidor_model, {})
        if not column_mapping:
            raise ValueError(f"Mapeamento de colunas não encontrado para o modelo: {medidor_model}")
        df = df.rename(columns=column_mapping)
        
        # 4. Tratamento de Data
        if 'Data' in df.columns:
            df['Data'] = pd.to_datetime(df['Data'], dayfirst=True, errors='coerce')
            df = df.dropna(subset=['Data'])
            df = df.sort_values('Data') 
        else:
            raise ValueError("Coluna de data ('Data') não encontrada após o mapeamento. Verifique o arquivo e o mapeamento do modelo.")
        
        # 5. Conversão Final para Numérico para colunas chave
        numeric_cols = ['Vazao', 'Velocidade', 'Total', 'Qualidade', 'QHidraulica']
        for col in numeric_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
                
        return df

    @staticmethod
    def calculate_dashboard_metrics(data_frame: pd.DataFrame) -> Tuple[Dict[str, int], Dict[str, int], Dict[str, Any]]:
        """
        Calcula as métricas necessárias para o dashboard a partir de um DataFrame processado.

        Args:
            data_frame: O DataFrame pandas com os dados do medidor já processados.
        Returns:
            Uma tupla contendo:
            - faixas_vazao (Dict[str, int]): Contagem de pontos de vazão por faixa.
            - qualidade_dados (Dict[str, int]): Contagem de códigos de qualidade.
            - indicadores_gerais (Dict[str, Any]): Indicadores como número de série, datas e total acumulado.
        """
        # Cálculo da média apenas dos valores positivos para o limite
        positive_flow_values = data_frame[data_frame['Vazao'] > 0]['Vazao']
        mean_flow = positive_flow_values.mean() if not positive_flow_values.empty else 0.0
        flow_limit = round(mean_flow, 1)
        
        # Nova estrutura de faixas solicitada
        flow_ranges: Dict[str, int] = {
            "Negativo": int(len(data_frame[data_frame['Vazao'] < 0])),
            "Zero": int(len(data_frame[data_frame['Vazao'] == 0])),
            f"0 a {flow_limit} (Média)": int(len(data_frame[(data_frame['Vazao'] > 0) & (data_frame['Vazao'] <= flow_limit)])),
            f"Acima de {flow_limit}": int(len(data_frame[data_frame['Vazao'] > flow_limit]))
        }
        
        # Qualidade: só calcula se a coluna existir (ex: MV145 não tem)
        if 'Qualidade' in data_frame.columns:
            quality_counts = data_frame['Qualidade'].value_counts()
            data_quality: Dict[str, int] = {f"Cod. {int(k)}": int(v) for k, v in quality_counts.items()}
        else:
            data_quality: Dict[str, int] = {}
        
        calculated_total_positive_flow = data_frame[data_frame['Vazao'] > 0]['Vazao'].sum()

        general_indicators: Dict[str, Any] = {
            "serial_number": str(data_frame['NUMEROSERIE_ATUAL'].iloc[0]) if 'NUMEROSERIE_ATUAL' in data_frame.columns else "N/A",
            "start_date": data_frame['Data'].min(),
            "end_date": data_frame['Data'].max(),
            # Tenta pegar o acumulado do medidor (Total), se não existir, usa a soma da vazão
            "total_positive_accumulated": data_frame['Total'].max() if ('Total' in data_frame.columns and data_frame['Total'].iloc[-1] > 0) else calculated_total_positive_flow
        }
        return flow_ranges, data_quality, general_indicators

    @staticmethod
    def calculate_hydraulic_status(data_frame: pd.DataFrame) -> Dict[str, int]:
        """
        Calcula o status hidráulico baseado na coluna QHidraulica.
        Categoriza os valores em:
        - QHidraulica < 90: Ruim (Vermelho)
        - 90 <= QHidraulica < 100: Médio (Amarelo)
        - QHidraulica == 100: Bom (Azul)

        Args:
            data_frame: O DataFrame pandas com os dados do medidor já processados.
        Returns:
            Um dicionário com a contagem de status hidráulico por categoria.
        """
        if 'QHidraulica' not in data_frame.columns:
            return {}

        status_counts: Dict[str, int] = {
            "< 90 (Ruim)": int(len(data_frame[data_frame['QHidraulica'] < 90])),
            "90-99 (Médio)": int(len(data_frame[(data_frame['QHidraulica'] >= 90) & (data_frame['QHidraulica'] < 100)])),
            "= 100 (Bom)": int(len(data_frame[data_frame['QHidraulica'] == 100]))
        }
        return {k: v for k, v in status_counts.items() if v > 0}