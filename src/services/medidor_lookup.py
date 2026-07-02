"""
Módulo responsável por identificar o tipo e modelo do medidor
a partir de seu número de série, utilizando um arquivo de configuração Excel.
"""
import pandas as pd
from typing import Dict, Optional, Tuple
import os
from src.utils.helpers import resource_path

class MedidorLookupService:
    """
    Serviço para buscar informações de medidores (tipo e modelo)
    com base no número de série, a partir de um arquivo Excel.
    """
    _instance: Optional['MedidorLookupService'] = None
    _medidores_df: Optional[pd.DataFrame] = None
    _excel_path: str = resource_path("Medidores - 2026.xlsx") # Assuming it's at the root

    def __new__(cls) -> 'MedidorLookupService':
        """Implementa o padrão Singleton para garantir uma única instância do serviço."""
        if cls._instance is None:
            cls._instance = super(MedidorLookupService, cls).__new__(cls)
            cls._instance._load_medidores_data()
        return cls._instance

    def _load_medidores_data(self) -> None:
        """
        Carrega os dados dos medidores do arquivo Excel.
        O arquivo deve conter as colunas 'NUMERO_SERIE', 'TIPO', 'MODELO'.
        """
        if not os.path.exists(self._excel_path):
            raise FileNotFoundError(f"Arquivo de medidores não encontrado: {self._excel_path}")
        try:
            self._medidores_df = pd.read_excel(self._excel_path)
            self._medidores_df.columns = [col.strip().upper() for col in self._medidores_df.columns]
            column_rename_map = {
                'Nº SÉRIE ELETRÔNICA': 'NUMERO_SERIE',
                'MODELO ELETRÔNICA':   'MODELO',
                'TIPO DE MEDIDOR':     'TIPO',
                'LOCAL INSTALAÇÃO':    'LOCAL',
            }
            self._medidores_df.rename(columns=column_rename_map, inplace=True)
        except Exception as e:
            raise IOError(f"Erro ao carregar o arquivo de medidores '{os.path.basename(self._excel_path)}': {e}")

    def get_medidor_info(self, serial_number: str) -> Optional[Tuple[str, str, str]]:
        """
        Busca o tipo, modelo e local de instalação do medidor pelo número de série.

        Args:
            serial_number: O número de série do medidor.
        Returns:
            Uma tupla (tipo, modelo, local) se encontrado, caso contrário None.
        """
        if self._medidores_df is None:
            self._load_medidores_data()

        # Normaliza ambos os lados para string para evitar mismatch int vs str
        serial_normalizado = str(serial_number).strip().upper()
        result = self._medidores_df[
            self._medidores_df['NUMERO_SERIE'].astype(str).str.strip().str.upper() == serial_normalizado
        ]
        if not result.empty:
            tipo = str(result['TIPO'].iloc[0])
            modelo = str(result['MODELO'].iloc[0])
            local = str(result['LOCAL'].iloc[0])
            return tipo, modelo, local
        return None