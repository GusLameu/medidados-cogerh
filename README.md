# Medidados

Sistema desktop em Python para análise técnica de arquivos de medidores, com identificação automática do equipamento, processamento dos dados e geração de dashboards interativos com gráficos e indicadores.

## Sobre o projeto

O **Medidados** foi reorganizado em uma arquitetura modular para separar interface, serviços, configuração e utilitários, facilitando manutenção, evolução do código e inclusão de novos modelos de medidores. O ponto de entrada da aplicação fica em `main.py`, enquanto a lógica foi distribuída em módulos dentro de `src/`.[1][2][3][4][5]

Atualmente, a aplicação permite importar arquivos CSV, XLSX e XLS, identificar o número de série do medidor, consultar sua base de referência e abrir um dashboard com visualizações e métricas adequadas ao modelo detectado.[2][4][6]

## Estrutura do projeto

A nova organização do projeto está dividida da seguinte forma:

```text
medidados/
├── main.py
├── requirements.txt
├── packages.txt
├── src/
│   ├── core/
│   │   └── config.py
│   ├── services/
│   │   ├── data_processing.py
│   │   └── medidor_lookup.py
│   ├── ui/
│   │   ├── app.py
│   │   └── dashboard_window.py
│   └── utils/
│       └── helpers.py
```

### Responsabilidades dos módulos

- `main.py`: inicia a aplicação e abre a interface principal.[1]
- `src/ui/app.py`: tela inicial, seleção/arrasto de arquivos e fluxo principal da aplicação.[2]
- `src/ui/dashboard_window.py`: renderização dos dashboards, gráficos e painel lateral de indicadores.[3]
- `src/services/data_processing.py`: carregamento, limpeza, transformação e cálculo de métricas dos dados dos medidores.[4]
- `src/services/medidor_lookup.py`: consulta das informações do medidor com base no número de série.[6]
- `src/core/config.py`: centraliza mapeamentos, cores, configurações por modelo e parâmetros do sistema.[7]
- `src/utils/helpers.py`: utilitários compartilhados, como resolução de caminhos para recursos locais e empacotados.[5]

## Funcionalidades

- Importação manual de arquivos ou por arrastar e soltar na interface.[2]
- Suporte a arquivos `.csv`, `.xlsx` e `.xls`.[4]
- Identificação automática do número de série do medidor a partir do arquivo importado.[2][4]
- Consulta do tipo e modelo do medidor por base auxiliar.[2][6]
- Processamento dos dados com renomeação de colunas, padronização numérica e tratamento de datas.[4]
- Dashboard com gráficos de vazão, velocidade, volume e indicadores gerais, conforme o modelo do medidor.[3][4]
- Layout simplificado para MV145 e layout completo para outros modelos configurados.[3]
- Exportação do relatório gráfico em PNG.[3]

## Requisitos

O projeto utiliza dependências como `pandas`, `matplotlib`, `numpy` e `mplcursors`, conforme o arquivo `requirements.txt` anexado nesta versão.[8]

Também existe um `packages.txt`, que pode ser usado para dependências de empacotamento ou ambiente conforme sua estratégia de distribuição.[9]

## Como executar

1. Clone o repositório.
2. Acesse a pasta do projeto.
3. Crie e ative um ambiente virtual.
4. Instale as dependências.
5. Execute o arquivo principal.

Exemplo:

```bash
python -m venv .venv
source .venv/bin/activate  # Linux/macOS
# .venv\Scripts\activate   # Windows
pip install -r requirements.txt
python main.py
```

## Fluxo da aplicação

1. O usuário seleciona ou arrasta um arquivo de dados para a interface principal.[2]
2. A aplicação tenta extrair o número de série do arquivo importado.[2][4]
3. Com o número de série, o sistema consulta a base de medidores para descobrir tipo e modelo.[2][6]
4. Os dados são carregados, limpos, convertidos e padronizados conforme o modelo identificado.[4]
5. O dashboard correspondente é aberto com os gráficos e indicadores adequados.[3][4]

## Observações

- O projeto usa uma base auxiliar de medidores para mapear número de série, tipo e modelo do equipamento.[6][10]
- Recursos locais como ícones e outros arquivos podem ser resolvidos com compatibilidade para ambiente de desenvolvimento e PyInstaller por meio de `resource_path`.[5]
- A configuração visual e funcional dos dashboards depende dos dicionários definidos em `config.py`.[7]

## Próximos passos

- Refinar o versionamento da nova arquitetura com commits menores por etapa.
- Adicionar documentação dos modelos de medidores suportados.
- Incluir instruções de empacotamento da aplicação.
- Evoluir a cobertura de testes dos serviços de processamento e lookup.