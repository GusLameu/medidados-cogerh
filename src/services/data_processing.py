"""
Módulo responsável pelo carregamento, limpeza e processamento de dados de medidores.
"""
import pandas as pd
import numpy as np
from typing import Dict, Any, Tuple, List, Optional
from src.core.config import MAPA_COLUNAS
from src.utils.logger import get_logger

logger = get_logger(__name__)

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
        logger.info(f"Carregando arquivo bruto: {file_path}")
        try:
            if file_path.endswith('.csv'):
                df = pd.read_csv(file_path, sep=None, engine='python', encoding='utf-8-sig')
            elif file_path.endswith(('.xlsx', '.xls')):
                df = pd.read_excel(file_path)
            else:
                raise ValueError("Formato de arquivo não suportado. Use .csv, .xlsx ou .xls.")
            return df
        except Exception as e:
            logger.error(f"Falha ao carregar arquivo '{file_path}': {e}")
            raise IOError(f"Erro ao carregar o arquivo '{file_path}': {e}")

    @staticmethod
    def peek_serial_number(file_path: str) -> Optional[str]:
        """
        Tenta extrair o número de série do arquivo de dados sem carregar tudo.

        Args:
            file_path: Caminho para o arquivo de dados.
        Returns:
            O número de série encontrado ou None se não for possível extrair.
        """
        logger.debug(f"Tentando extrair número de série do arquivo: {file_path}")
        try:
            if file_path.endswith('.csv'):
                with open(file_path, 'r', encoding='utf-8-sig') as f:
                    f.readline()

                temp_df = pd.read_csv(
                    file_path,
                    sep=None,
                    engine='python',
                    encoding='utf-8-sig',
                    nrows=5
                )
                temp_df.columns = [str(col).strip().upper() for col in temp_df.columns]

                if 'NUMEROSERIE_ATUAL' in temp_df.columns:
                    return str(temp_df['NUMEROSERIE_ATUAL'].iloc[0])
                elif 'NUMERO_SERIE' in temp_df.columns:
                    return str(temp_df['NUMERO_SERIE'].iloc[0])

            elif file_path.endswith(('.xlsx', '.xls')):
                temp_df = pd.read_excel(file_path, nrows=5)
                temp_df.columns = [str(col).strip().upper() for col in temp_df.columns]

                if 'NUMEROSERIE_ATUAL' in temp_df.columns:
                    return str(temp_df['NUMEROSERIE_ATUAL'].iloc[0])
                elif 'NUMERO_SERIE' in temp_df.columns:
                    return str(temp_df['NUMERO_SERIE'].iloc[0])

            logger.warning(f"Número de série não encontrado no arquivo: {file_path}")
            return None
        except Exception as e:
            logger.error(f"Erro ao tentar extrair número de série de '{file_path}': {e}")
            return None

    @staticmethod
    def process_medidor_data(file_path: str, medidor_model: str) -> pd.DataFrame:
        """
        Carrega e processa os dados de um medidor, aplicando limpeza e transformações.

        Args:
            file_path: Caminho para o arquivo de dados (CSV ou Excel).
            medidor_model: O modelo do medidor (ex: \"MV110\", \"XMT1000\") para mapeamento de colunas.
        Returns:
            Um DataFrame pandas processado.
        Raises:
            Exception: Se ocorrer um erro durante o processamento.
        """
        logger.info(f"Iniciando processamento para o modelo {medidor_model} (arquivo: {file_path})")
        df = DataProcessingService._load_raw_data(file_path)

        df.columns = [str(col).strip().upper() for col in df.columns]

        for col in df.columns:
            if df[col].dtype == 'object':
                df[col] = (
                    df[col]
                    .astype(str)
                    .str.replace('.', '', regex=False)
                    .str.replace(',', '.', regex=False)
                )

        column_mapping = MAPA_COLUNAS.get(medidor_model.strip().upper(), {})
        if not column_mapping:
            logger.error(f"Mapeamento de colunas não encontrado para o modelo: {medidor_model}")
            raise ValueError(f"Mapeamento de colunas não encontrado para o modelo: {medidor_model}")

        df = df.rename(columns=column_mapping)

        if 'Data' not in df.columns:
            logger.error(f"Coluna de data ('Data') não encontrada após o mapeamento para o modelo {medidor_model}")
            raise ValueError(f"Coluna de data ('Data') não encontrada após o mapeamento para o modelo {medidor_model}")

        df['Data'] = pd.to_datetime(df['Data'], dayfirst=True, errors='coerce')
        df = df.dropna(subset=['Data'])
        df = df.sort_values('Data')

        numeric_cols = ['Vazao', 'Velocidade', 'Total', 'Qualidade', 'Process', 'QualidadeTrigger', 'Area', 'Nivel', 'QHidraulica']
        for col in numeric_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col].astype(str).str.replace(',', '.'), errors='coerce').fillna(0)

        logger.info(f"Processamento concluído para o modelo {medidor_model}. {len(df)} registros processados.")
        return df


    @staticmethod
    def calculate_dashboard_metrics(
        data_frame: pd.DataFrame
    ) -> Tuple[Dict[str, int], Dict[str, int], Dict[str, Any]]:
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
        logger.debug("Calculando métricas do dashboard")
        flow_values = data_frame['Vazao'].dropna()
        mean_flow = flow_values.mean() if not flow_values.empty else 0.0
        flow_limit = round(mean_flow, 1)

        flow_ranges: Dict[str, int] = {
            "Negativo": int(len(data_frame[data_frame['Vazao'] < 0])),
            "Zero": int(len(data_frame[data_frame['Vazao'] == 0])),
            f"0 a {flow_limit} (Média)": int(
                len(data_frame[(data_frame['Vazao'] > 0) & (data_frame['Vazao'] <= flow_limit)])
            ),
            f"Acima de {flow_limit}": int(len(data_frame[data_frame['Vazao'] > flow_limit]))
        }

        if 'Qualidade' in data_frame.columns:
            quality_counts = data_frame['Qualidade'].value_counts()
            data_quality: Dict[str, int] = {
                f"sinal {'bom' if int(k) == 192 else 'ruim'}: {int(k)}": int(v)
                for k, v in quality_counts.items()
            }
        else:
            data_quality = {}

        calculated_total_positive_flow = data_frame[data_frame['Vazao'] > 0]['Vazao'].sum()

        general_indicators: Dict[str, Any] = {
            "serial_number": (
                str(data_frame['NUMEROSERIE_ATUAL'].iloc[0])
                if 'NUMEROSERIE_ATUAL' in data_frame.columns else "N/A"
            ),
            "start_date": data_frame['Data'].min(),
            "end_date": data_frame['Data'].max(),
            "total_positive_accumulated": (
                data_frame['Total'].max()
                if ('Total' in data_frame.columns and data_frame['Total'].iloc[-1] > 0)
                else calculated_total_positive_flow
            )
        }

        return flow_ranges, data_quality, general_indicators

    @staticmethod
    def calculate_hydraulic_status(data_frame: pd.DataFrame) -> Dict[str, int]:
        """
        Calcula o status hidráulico baseado na coluna QHidraulica.

        Args:
            data_frame: O DataFrame pandas com os dados do medidor já processados.
        Returns:
            Um dicionário com a contagem de status hidráulico por categoria.
        """
        if 'QHidraulica' not in data_frame.columns:
            return {}

        status_counts: Dict[str, int] = {
            "< 65 (Crítico)": int(len(data_frame[data_frame['QHidraulica'] < 65])),
            "65-80 (Aceitavel)": int(
                len(data_frame[(data_frame['QHidraulica'] >= 65) & (data_frame['QHidraulica'] <= 80)])
            ),
            "> 80 (Excelente)": int(len(data_frame[data_frame['QHidraulica'] > 80]))
        }

        return {k: v for k, v in status_counts.items() if v > 0}

    @staticmethod
    def calculate_process_status(data_frame: pd.DataFrame) -> Dict[str, int]:
        """
        Calcula o status de processo baseado na coluna Process.

        Args:
            data_frame: O DataFrame pandas com os dados do medidor já processados.

        Returns:
            Um dicionário com a contagem de cada categoria presente na coluna Process.
        """
        if 'Process' not in data_frame.columns:
            return {}

        process_counts = data_frame['Process'].value_counts(dropna=False)

        process_status: Dict[str, int] = {}
        for key, value in process_counts.items():
            if pd.isna(key):
                label = "Sem Informação"
            else:
                if isinstance(key, float) and key.is_integer():
                    label = f"Processo {int(key)}"
                else:
                    label = f"Processo {key}"

            process_status[label] = int(value)

        return {k: v for k, v in process_status.items() if v > 0}

    @staticmethod
    def calculate_trigger_quality_status(data_frame: pd.DataFrame) -> Dict[str, int]:
        """
        Calcula o status da qualidade do trigger baseado na coluna QualidadeTrigger.

        Args:
            data_frame: O DataFrame pandas com os dados do medidor já processados.

        Returns:
            Um dicionário com a contagem de status de qualidade do trigger.
        """
        if 'QualidadeTrigger' not in data_frame.columns:
            return {}

        trigger_series = pd.to_numeric(data_frame['QualidadeTrigger'].astype(str).str.replace(',', '.'), errors='coerce')

        trigger_status: Dict[str, int] = {
            "< 60%": int((trigger_series < 60).sum()),
            "60 - 80%": int(((trigger_series >= 60) & (trigger_series <= 80)).sum()),
            "> 80%": int((trigger_series > 80).sum())
        }

        return {k: v for k, v in trigger_status.items() if v > 0}

