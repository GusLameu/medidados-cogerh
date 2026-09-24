"""
Modulo responsavel pelo carregamento, limpeza e processamento de dados de medidores.
"""
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple, Union
import pandas as pd
import numpy as np
from src.core.config import MAPA_COLUNAS
from src.utils.logger import get_logger


logger = get_logger(__name__)


# Tipos para metricas do dashboard
FlowRanges = Dict[str, int]  # Faixa de vazao -> contagem
QualityCounts = Dict[str, int]  # Codigo de qualidade -> contagem
StatusCounts = Dict[str, int]  # Categoria de status -> contagem


class GeneralIndicators(TypedDict):
    """Indicadores gerais do dashboard."""
    serial_number: str
    start_date: pd.Timestamp
    end_date: pd.Timestamp
    total_positive_accumulated: Union[int, float]


from typing import TypedDict


class DashboardMetrics(TypedDict):
    """Retorno completo de metricas do dashboard."""
    flow_ranges: FlowRanges
    quality_counts: QualityCounts
    general_indicators: GeneralIndicators


class DataProcessingService:
    """
    Servico para carregar, limpar e calcular metricas a partir de dados de medidores.
    
    Metodos Principais:
        - _load_raw_data: Carrega arquivo CSV/Excel bruto.
        - peek_serial_number: Extrai numero de serie sem carregar tudo.
        - process_medidor_data: Carrega, limpa e transforma dados.
        - calculate_dashboard_metrics: Calcula metricas para dashboard.
        - calculate_hydraulic_status: Calcula status hidraulico.
        - calculate_process_status: Calcula status de processo.
        - calculate_trigger_quality_status: Calcula qualidade do trigger.
    """
    
    # Colunas numericas esperadas apos processamento
    NUMERIC_COLUMNS: List[str] = [
        'Vazao', 'Velocidade', 'Total', 'Qualidade', 
        'Process', 'QualidadeTrigger', 'Area', 'Nivel', 'QHidraulica'
    ]
    
    @staticmethod
    def _load_raw_data(file_path: str) -> pd.DataFrame:
        """
        Carrega dados brutos de um arquivo CSV ou Excel.
        
        Args:
            file_path: Caminho completo para o arquivo de dados.
        
        Returns:
            DataFrame pandas com os dados carregados.
        
        Raises:
            ValueError: Se o formato do arquivo nao for suportado.
            IOError: Se houver erro ao ler o arquivo.
        """
        logger.info(f"Carregando arquivo bruto: {file_path}")
        
        try:
            if file_path.endswith('.csv'):
                df: pd.DataFrame = pd.read_csv(
                    file_path, 
                    sep=None, 
                    engine='python', 
                    encoding='utf-8-sig'
                )
            elif file_path.endswith(('.xlsx', '.xls')):
                df = pd.read_excel(file_path)
            else:
                raise ValueError(
                    "Formato de arquivo nao suportado. Use .csv, .xlsx ou .xls."
                )
            return df
            
        except Exception as e:
            logger.error(f"Falha ao carregar arquivo '{file_path}': {e}")
            raise IOError(f"Erro ao carregar o arquivo '{file_path}': {e}") from e
    
    @staticmethod
    def peek_serial_number(file_path: str) -> Optional[str]:
        """
        Tenta extrair o numero de serie do arquivo de dados sem carregar tudo.
        
        Args:
            file_path: Caminho para o arquivo de dados.
        
        Returns:
            O numero de serie encontrado ou None se nao for possivel extrair.
        """
        logger.debug(f"Tentando extrair numero de serie do arquivo: {file_path}")
        
        try:
            if file_path.endswith('.csv'):
                # Le apenas primeiras linhas para identificar colunas
                temp_df: pd.DataFrame = pd.read_csv(
                    file_path,
                    sep=None,
                    engine='python',
                    encoding='utf-8-sig',
                    nrows=5
                )
            elif file_path.endswith(('.xlsx', '.xls')):
                temp_df = pd.read_excel(file_path, nrows=5)
            else:
                logger.warning(f"Formato nao suportado para peek: {file_path}")
                return None
            
            # Normalizar nomes de colunas
            temp_df.columns = [str(col).strip().upper() for col in temp_df.columns]
            
            # Tentar colunas possiveis para numero de serie
            possible_columns: List[str] = ['NUMEROSERIE_ATUAL', 'NUMERO_SERIE']
            
            for col in possible_columns:
                if col in temp_df.columns and not temp_df.empty:
                    serial: str = str(temp_df[col].iloc[0])
                    logger.debug(f"Numero de serie encontrado: {serial}")
                    return serial
            
            logger.warning(f"Numero de serie nao encontrado no arquivo: {file_path}")
            return None
            
        except Exception as e:
            logger.error(f"Erro ao tentar extrair numero de serie de '{file_path}': {e}")
            return None
    
    @staticmethod
    def process_medidor_data(file_path: str, medidor_model: str) -> pd.DataFrame:
        """
        Carrega e processa os dados de um medidor, aplicando limpeza e transformacoes.
        
        Args:
            file_path: Caminho para o arquivo de dados (CSV ou Excel).
            medidor_model: Modelo do medidor (ex: "MV110", "XMT1000") para mapeamento.
        
        Returns:
            DataFrame pandas processado com colunas padronizadas.
        
        Raises:
            ValueError: Se mapeamento de colunas ou coluna de data nao for encontrado.
            Exception: Se ocorrer erro durante o processamento.
        """
        logger.info(f"Iniciando processamento para o modelo {medidor_model} (arquivo: {file_path})")
        
        # 1. Carregar dados brutos
        df: pd.DataFrame = DataProcessingService._load_raw_data(file_path)
        
        # 2. Normalizar nomes de colunas
        df.columns = [str(col).strip().upper() for col in df.columns]
        
        # 3. Converter colunas objeto para numerico (substituir virgula por ponto)
        for col in df.columns:
            if df[col].dtype == 'object':
                df[col] = (
                    df[col]
                    .astype(str)
                    .str.replace('.', '', regex=False)
                    .str.replace(',', '.', regex=False)
                )
        
        # 4. Aplicar mapeamento de colunas
        column_mapping: Dict[str, str] = MAPA_COLUNAS.get(medidor_model.strip().upper(), {})
        
        if not column_mapping:
            logger.error(f"Mapeamento de colunas nao encontrado para o modelo: {medidor_model}")
            raise ValueError(f"Mapeamento de colunas nao encontrado para o modelo: {medidor_model}")
        
        df = df.rename(columns=column_mapping)
        
        # 5. Validar e converter coluna de data
        if 'Data' not in df.columns:
            logger.error(f"Coluna de data ('Data') nao encontrada apos mapeamento para {medidor_model}")
            raise ValueError(f"Coluna de data ('Data') nao encontrada apos mapeamento para {medidor_model}")
        
        df['Data'] = pd.to_datetime(df['Data'], dayfirst=True, errors='coerce')
        df = df.dropna(subset=['Data'])
        df = df.sort_values('Data')
        
        # 6. Converter colunas numericas
        for col in DataProcessingService.NUMERIC_COLUMNS:
            if col in df.columns:
                df[col] = pd.to_numeric(
                    df[col].astype(str).str.replace(',', '.'), 
                    errors='coerce'
                ).fillna(0)
        
        logger.info(f"Processamento concluido para {medidor_model}. {len(df)} registros processados.")
        return df
    
    @staticmethod
    def calculate_dashboard_metrics(
        data_frame: pd.DataFrame
    ) -> Tuple[FlowRanges, QualityCounts, GeneralIndicators]:
        """
        Calcula as metricas necessarias para o dashboard.
        
        Args:
            data_frame: DataFrame com dados do medidor ja processados.
        
        Returns:
            Tupla contendo:
            - flow_ranges: Contagem de pontos de vazao por faixa.
            - quality_counts: Contagem de codigos de qualidade.
            - general_indicators: Indicadores como serial, datas e total.
        """
        logger.debug("Calculando metricas do dashboard")
        
        # 1. Calcular media de vazao para definir faixas
        flow_values: pd.Series = data_frame['Vazao'].dropna()
        mean_flow: float = flow_values.mean() if not flow_values.empty else 0.0
        flow_limit: float = round(mean_flow, 1)
        
        # 2. Calcular faixas de vazao
        flow_ranges: FlowRanges = {
            "Negativo": int(len(data_frame[data_frame['Vazao'] < 0])),
            "Zero": int(len(data_frame[data_frame['Vazao'] == 0])),
            f"0 a {flow_limit} (Media)": int(
                len(data_frame[(data_frame['Vazao'] > 0) & (data_frame['Vazao'] <= flow_limit)])
            ),
            f"Acima de {flow_limit}": int(len(data_frame[data_frame['Vazao'] > flow_limit]))
        }
        
        # 3. Calcular qualidade de sinal
        quality_counts: QualityCounts = {}
        if 'Qualidade' in data_frame.columns:
            quality_value_counts: pd.Series = data_frame['Qualidade'].value_counts()
            quality_counts = {
                f"sinal {'bom' if int(k) == 192 else 'ruim'}: {int(k)}": int(v)
                for k, v in quality_value_counts.items()
            }
        
        # 4. Calcular indicadores gerais
        calculated_total_positive_flow: float = data_frame[data_frame['Vazao'] > 0]['Vazao'].sum()
        
        general_indicators: GeneralIndicators = {
            "serial_number": (
                str(data_frame['NUMEROSERIE_ATUAL'].iloc[0])
                if 'NUMEROSERIE_ATUAL' in data_frame.columns 
                else "N/A"
            ),
            "start_date": data_frame['Data'].min(),
            "end_date": data_frame['Data'].max(),
            "total_positive_accumulated": (
                data_frame['Total'].max()
                if ('Total' in data_frame.columns and data_frame['Total'].iloc[-1] > 0)
                else calculated_total_positive_flow
            )
        }
        
        return flow_ranges, quality_counts, general_indicators
    
    @staticmethod
    def calculate_hydraulic_status(data_frame: pd.DataFrame) -> StatusCounts:
        """
        Calcula o status hidraulico baseado na coluna QHidraulica.
        
        Args:
            data_frame: DataFrame com dados do medidor ja processados.
        
        Returns:
            Dicionario com contagem de status hidraulico por categoria.
            Retorna dict vazio se coluna QHidraulica nao existir.
        """
        if 'QHidraulica' not in data_frame.columns:
            return {}
        
        status_counts: StatusCounts = {
            "< 65 (Critico)": int(len(data_frame[data_frame['QHidraulica'] < 65])),
            "65-80 (Aceitavel)": int(
                len(data_frame[(data_frame['QHidraulica'] >= 65) & (data_frame['QHidraulica'] <= 80)])
            ),
            "> 80 (Excelente)": int(len(data_frame[data_frame['QHidraulica'] > 80]))
        }
        
        # Filtrar categorias vazias
        return {k: v for k, v in status_counts.items() if v > 0}
    
    @staticmethod
    def calculate_process_status(data_frame: pd.DataFrame) -> StatusCounts:
        """
        Calcula o status de processo baseado na coluna Process.
        
        Args:
            data_frame: DataFrame com dados do medidor ja processados.
        
        Returns:
            Dicionario com contagem de cada categoria presente na coluna Process.
            Retorna dict vazio se coluna Process nao existir.
        """
        if 'Process' not in data_frame.columns:
            return {}
        
        process_counts: pd.Series = data_frame['Process'].value_counts(dropna=False)
        
        process_status: StatusCounts = {}
        for key, value in process_counts.items():
            if pd.isna(key):
                label: str = "Sem Informacao"
            else:
                if isinstance(key, (int, float)) and (isinstance(key, int) or key.is_integer()):
                    label = f"Processo {int(key)}"
                else:
                    label = f"Processo {key}"
            
            process_status[label] = int(value)
        
        return {k: v for k, v in process_status.items() if v > 0}
    
    @staticmethod
    def calculate_trigger_quality_status(data_frame: pd.DataFrame) -> StatusCounts:
        """
        Calcula o status da qualidade do trigger baseado na coluna QualidadeTrigger.
        
        Args:
            data_frame: DataFrame com dados do medidor ja processados.
        
        Returns:
            Dicionario com contagem de status de qualidade do trigger.
            Retorna dict vazio se coluna QualidadeTrigger nao existir.
        """
        if 'QualidadeTrigger' not in data_frame.columns:
            return {}
        
        trigger_series: pd.Series = pd.to_numeric(
            data_frame['QualidadeTrigger'].astype(str).str.replace(',', '.'), 
            errors='coerce'
        )
        
        trigger_status: StatusCounts = {
            "< 60%": int((trigger_series < 60).sum()),
            "60 - 80%": int(((trigger_series >= 60) & (trigger_series <= 80)).sum()),
            "> 80%": int((trigger_series > 80).sum())
        }
        
        return {k: v for k, v in trigger_status.items() if v > 0}