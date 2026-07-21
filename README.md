# Medidados V7 - Análise de Medidores de Vazão

Aplicativo desktop em Python para análise técnica de medidores de vazão da COGERH, com leitura de arquivos CSV/Excel, cálculo de métricas de vazão e qualidade e visualização em dashboards interativos (gráficos de linha e roscas). [file:2]

## Funcionalidades

- Leitura de arquivos de dados de medidores (CSV, XLS, XLSX).
- Identificação automática do tipo e modelo do medidor a partir do número de série.
- Cálculo de métricas de vazão (faixas, média, acumulado).
- Análise de qualidade de sinal e status hidráulico.
- Dashboard interativo com:
  - gráfico principal de vazão / velocidade / volume (conforme modelo),
  - gráficos de rosca para qualidade e status,
  - tela detalhada por modelo (ex.: NF750).
- Suporte a layout simplificado para o modelo MV145, com foco em vazão e volume. [file:12][file:8]

## Novidades da versão 7.0 (final)

- Barra lateral unificada entre os modelos, mantendo o layout clássico, com tratamento específico para o MV145 (sem campo de “Totalizado” quando não há acumulado disponível). [file:12]
- Aperfeiçoamento do dashboard simplificado do MV145, exibindo apenas as métricas relevantes (vazão/volume e período da campanha). [file:12][file:16]
- Melhoria na lógica de cálculo de métricas gerais (`calculate_dashboard_metrics`), tornando o uso de indicadores como período e número de série mais robusto. [file:8]
- Ajuste no fluxo de fechamento da janela de dashboard, evitando encerramento indevido da aplicação principal ao sair do dashboard. [file:12]
- Refino da experiência de hover nos gráficos (linha vertical, tooltip de vazão/velocidade/volume e interações com roscas). [file:12]

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
    │   └── config.py                  # Configurações globais (MAPA_COLUNAS, cores, modelos)
    ├── services/
    │   ├── data_processing.py         # Carregamento, limpeza e cálculo de métricas
    │   └── medidor_lookup.py          # Lookup de tipo/modelo via número de série
    ├── ui/
    │   ├── app.py                     # Janela inicial (drag and drop / seleção de arquivo)
    │   ├── dashboard_window.py        # Dashboard principal (layouts completo / simplificado)
    │   └── detailed_dashboard_window.py  # Tela de detalhamento por modelo
    └── utils/
        ├── helpers.py                 # Funções utilitárias (resource_path para PyInstaller)
        └── logger.py                  # Configuração de logging da aplicação
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

> 💡 Se estiver usando **Python 3.14+** e encontrar erros de compatibilidade, crie um ambiente virtual primeiro:
> ```bash
> py -m venv .venv
> .venv\Scripts\activate
> pip install -r requirements.txt
> ```

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

> Observação: o projeto usa `resource_path()` para encontrar `logo.ico` e `Medidores - 2026.xlsx` tanto em ambiente de desenvolvimento quanto no `.exe`. [file:14][file:7]

## Requisitos

- Python 3.11 ou superior.
- Windows (testado em ambiente corporativo GEMED).

## Status do projeto

- **Versão atual:** v7.0 (final)
- **Foco atual:** estabilização da versão final, melhorias incrementais de UX e manutenção. [file:2][file:12]

## Ideias futuras

- Integração direta com banco de dados (substituir leitura manual de arquivos).
- Novos dashboards específicos por modelo (além dos já existentes).
- Tela de configuração para faixas de qualidade / status hidráulico.
- Exportação avançada de relatórios (PDF com gráficos e indicadores consolidados).