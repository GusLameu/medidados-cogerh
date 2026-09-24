"""
Modulo responsavel por identificar o tipo e modelo do medidor
a partir de seu numero de serie, utilizando um arquivo de configuracao Excel.
"""
import os
from pathlib import Path
from typing import Optional, Tuple
import pandas as pd
from src.utils.helpers import resource_path


# Tipo para informacoes do medidor
MedidorInfo = Tuple[str, str, str]  # (tipo, modelo, local)


class MedidorLookupService:
    """
    Servico para buscar informacoes de medidores (tipo, modelo, local)
    com base no numero de serie, a partir de um arquivo Excel.
    
    Padrao: Singleton para evitar recarregar o arquivo Excel multiple vezes.
    
    Attributes:
        _instance: Instancia unica do servico.
        _medidores_df: DataFrame com dados dos medidores.
        _excel_path: Caminho para o arquivo Excel de medidores.
    """
    
    _instance: Optional['MedidorLookupService'] = None
    _medidores_df: Optional[pd.DataFrame] = None
    _excel_path: Path = Path(resource_path("Medidores - 2026.xlsx"))
    
    def __new__(cls) -> 'MedidorLookupService':
        """
        Implementa o padrao Singleton para garantir uma unica instancia do servico.
        
        Returns:
            A instancia unica do MedidorLookupService.
        """
        if cls._instance is None:
            cls._instance = super(MedidorLookupService, cls).__new__(cls)
            cls._instance._load_medidores_data()
        return cls._instance
    
    def _load_medidores_data(self) -> None:
        """
        Carrega os dados dos medidores do arquivo Excel.
        
        O arquivo deve conter as colunas:
        - 'NUMERO_SERIE' ou 'N� SÉ´RIE ELETR�NICA'
        - 'MODELO' ou 'MODELO ELETR�NICA'
        - 'TIPO' ou 'TIPO DE MEDIDOR'
        - 'LOCAL' ou 'LOCAL INSTALAC�O'
        
        Raises:
            FileNotFoundError: Se o arquivo Excel nao for encontrado.
            IOError: Se houver erro ao ler o arquivo.
        """
        if not self._excel_path.exists():
            raise FileNotFoundError(f"Arquivo de medidores nao encontrado: {self._excel_path}")
        
        try:
            self._medidores_df = pd.read_excel(self._excel_path)
            
            # Normalizar nomes de colunas
            self._medidores_df.columns = [col.strip().upper() for col in self._medidores_df.columns]
            
            # Mapear nomes alternativos para nomes padronizados
            column_rename_map: dict[str, str] = {
                'N� S�RIE ELETR�NICA': 'NUMERO_SERIE',
                'MODELO ELETR�NICA':   'MODELO',
                'TIPO DE MEDIDOR':     'TIPO',
                'LOCAL INSTALAC�O':    'LOCAL',
            }
            self._medidores_df.rename(columns=column_rename_map, inplace=True)
            
        except Exception as e:
            raise IOError(
                f"Erro ao carregar o arquivo de medidores '{self._excel_path.name}': {e}"
            ) from e
    
    def get_medidor_info(self, serial_number: str) -> Optional[MedidorInfo]:
        """
        Busca o tipo, modelo e local de instalacao do medidor pelo numero de serie.
        
        Args:
            serial_number: O numero de serie do medidor.
        
        Returns:
            Uma tupla (tipo, modelo, local) se encontrado, caso contrario None.
        
        Example:
            >>> service = MedidorLookupService()
            >>> info = service.get_medidor_info("123456")
            >>> if info:
            ...     tipo, modelo, local = info
        """
        if self._medidores_df is None:
            self._load_medidores_data()
        
        # Normaliza ambos os lados para string para evitar mismatch int vs str
        serial_normalizado: str = str(serial_number).strip().upper()
        
        result: pd.DataFrame = self._medidores_df[
            self._medidores_df['NUMERO_SERIE'].astype(str).str.strip().str.upper() == serial_normalizado
        ]
        
        if not result.empty:
            tipo: str = str(result['TIPO'].iloc[0])
            modelo: str = str(result['MODELO'].iloc[0])
            local: str = str(result['LOCAL'].iloc[0])
            return (tipo, modelo, local)
        
        return None