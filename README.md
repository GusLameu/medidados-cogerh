# Medidados – Análise de Medidores de Vazão

Aplicativo desktop em Python para análise técnica de medidores de vazão da COGERH, com leitura de arquivos CSV/Excel, cálculo de métricas de vazão e qualidade e visualização em dashboards interativos (gráficos de linha e roscas).

## Funcionalidades

- Leitura de arquivos de dados de medidores (CSV, XLS, XLSX).
- Identificação automática do tipo e modelo do medidor a partir do número de série.
- Cálculo de métricas de vazão (faixas, média, acumulado).
- Análise de qualidade de sinal e status hidráulico.
- Dashboard interativo com:
  - gráfico principal de vazão / volume,
  - gráficos de rosca para qualidade,
  - tela detalhada por modelo (ex.: NF750).

## Estrutura do projeto

```text
.
├── main.py                # Ponto de entrada da aplicação
├── medidados.spec         # Configuração do PyInstaller para gerar o .exe
├── Medidores - 2026.xlsx  # Base de lookup de medidores (NUMERO_SERIE, TIPO, MODELO)
├── logo.ico               # Ícone da aplicação
├── requirements.txt       # Dependências Python
└── src/
    ├── core/
    │   └── config.py      # Configurações globais (MAPA_COLUNAS, cores, modelos)
    ├── services/
    │   ├── data_processing.py    # Carregamento, limpeza e cálculo de métricas
    │   └── medidor_lookup.py     # Lookup de tipo/modelo via número de série
    ├── ui/
    │   ├── app.py                 # Janela inicial (drag and drop / seleção de arquivo)
    │   ├── dashboard_window.py    # Dashboard principal
    │   └── detailed_dashboard_window.py  # Tela de detalhamento
    └── utils/
        └── helpers.py     # Funções utilitárias (resource_path para PyInstaller)
```

## Como executar em desenvolvimento

1. Clonar o repositório:

```bash
git clone https://github.com/GusLameu/medidados-cogerh.git
cd medidados-cogerh
```

2. Criar e ativar um ambiente virtual (opcional, mas recomendado).

3. Instalar as dependências:

```bash
pip install -r requirements.txt
```

4. Garantir que o arquivo `Medidores - 2026.xlsx` esteja na raiz do projeto (mesmo nível de `main.py`).

5. Executar a aplicação:

```bash
python main.py
```

## Como gerar o executável (.exe)

O projeto inclui um arquivo `medidados.spec` preparado para o PyInstaller.

1. Instalar o PyInstaller:

```bash
pip install pyinstaller
```

2. Rodar o build usando o `.spec`:

```bash
pyinstaller medidados.spec
```

3. O executável será gerado na pasta `dist/Medidados/` (Windows). Dentro dela haverá o `Medidados.exe` e os arquivos necessários.

> Observação: o projeto usa `resource_path()` para encontrar `logo.ico` e `Medidores - 2026.xlsx` tanto em ambiente de desenvolvimento quanto no `.exe`.

## Requisitos

- Python 3.11 ou superior.
- Windows (testado em ambiente corporativo GEMED).

## Status do projeto

- Versão atual: v5.0 (branch `GusLameu-patch-5`).
- Foco atual: Preparação do sistema para integração com o banco de dados.

## Próximos passos (ideias)

- Integração direta com banco de dados (substituir leitura manual de arquivos).
- Novos dashboards específicos por modelo.
- Tela de configuração para faixas de qualidade / status hidráulico.
