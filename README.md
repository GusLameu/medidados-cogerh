# 📊 Medidados

O **Medidados** é uma aplicação desktop desenvolvida para análise técnica e visualização de dados de medidores de fluxo. O sistema automatiza o processo de leitura, tratamento e interpretação dos arquivos brutos, transformando dados de telemetria em dashboards interativos e relatórios visuais de apoio técnico. [file:2][file:3][file:4]

---

## 🚀 Estrutura do Projeto

O projeto foi reorganizado em uma arquitetura modular para separar responsabilidades entre interface, processamento, configuração e utilitários:

* **`main.py`**: O ponto de entrada da aplicação. Inicializa a interface principal e executa o loop da GUI. [file:11]
* **`src/ui/app.py`**: A interface principal do sistema. Gerencia a tela inicial, seleção manual de arquivos, drag-and-drop e abertura do dashboard. [file:2]
* **`src/ui/dashboard_window.py`**: Responsável pela janela de dashboard, gráficos, indicadores e exportação do relatório em imagem. [file:3]
* **`src/services/data_processing.py`**: O núcleo de processamento de dados. Realiza carregamento, limpeza, padronização e cálculo das métricas dos medidores. [file:4]
* **`src/services/medidor_lookup.py`**: Responsável por consultar tipo e modelo do medidor a partir do número de série. [file:5]
* **`src/core/config.py`**: Centraliza mapeamentos de colunas, parâmetros visuais, cores e configurações por modelo de medidor. [file:6]
* **`src/utils/helpers.py`**: Utilitários auxiliares, incluindo resolução de caminhos para recursos locais e empacotados. [file:1]

---

## 🛠️ Detalhes dos Módulos

### 1. `main.py`
É o ponto de entrada da aplicação. Sua função é iniciar a interface principal e manter a execução da aplicação.

> **Nota do Desenvolvedor:** Se o `main.py` fosse um estagiário, ele continuaria sendo aquele que abre a porta da sala e chama quem realmente vai tocar o serviço pesado. [file:11]

```python
from src.ui.app import AppAnalise

if __name__ == "__main__":
    app = AppAnalise()
    app.mainloop()
```

### 2. `src/services/data_processing.py`
Responsável por toda a inteligência de dados:
* **Carregamento:** Lê arquivos `.csv`, `.xlsx` e `.xls`. [file:4]
* **Saneamento:** Padroniza colunas, converte números no formato brasileiro e trata valores inválidos. [file:4]
* **Datas:** Converte e ordena séries temporais corretamente com `dayfirst=True`. [file:4]
* **Métricas:** Calcula faixas de vazão, qualidade dos dados, status hidráulico e indicadores gerais. [file:4]

### 3. `src/ui/app.py`
Interface principal baseada em `CustomTkinter`:
* **Drag & Drop:** Permite arrastar arquivos diretamente para a janela inicial. [file:2]
* **Automação:** Extrai o número de série do arquivo e consulta automaticamente o modelo do medidor. [file:2][file:4][file:5]
* **Fluxo de uso:** Encaminha os dados processados para o dashboard correspondente. [file:2][file:3]

### 4. `src/ui/dashboard_window.py`
Responsável pela parte visual da análise:
* **Visualização:** Gera gráficos com eixo temporal, linhas de vazão, velocidade e volume conforme o modelo. [file:3]
* **Interatividade:** Exibe tooltip com valores ao passar o mouse sobre o gráfico. [file:3]
* **Exportação:** Permite salvar o relatório atual em PNG com alta resolução. [file:3]
* **Layouts específicos:** Possui tratamento diferente para modelos como o MV145, com layout simplificado. [file:3]

---

## 📦 Instalação e Dependências

Para rodar o Medidados, instale as dependências do projeto em um ambiente virtual Python. O arquivo `requirements.txt` desta versão inclui `pandas`, `matplotlib`, `numpy` e `mplcursors`, enquanto a interface também usa bibliotecas como `customtkinter` e `tkinterdnd2` no código da aplicação. [file:10][file:2]

### Passo a Passo:

1. **Crie e ative um ambiente virtual**
   ```bash
   python -m venv .venv
   ```

2. **Ative o ambiente**
   ```bash
   .venv\Scripts\activate
   ```
   No Linux/macOS:
   ```bash
   source .venv/bin/activate
   ```

3. **Instale as dependências**
   ```bash
   pip install -r requirements.txt
   ```

4. **Inicie a aplicação**
   ```bash
   python main.py
   ```

---

## 💡 Como Usar

1. **Importação:** Arraste um arquivo CSV/Excel para a área indicada ou clique em **Buscar Arquivo Manualmente**. [file:2]
2. **Identificação:** O sistema tenta extrair o número de série automaticamente e localizar o tipo/modelo do medidor. [file:2][file:4][file:5]
3. **Processamento:** Os dados são limpos, convertidos e organizados conforme o modelo identificado. [file:4]
4. **Exploração:** O dashboard é aberto com gráficos, métricas e indicadores específicos do medidor. [file:3]
5. **Relatório:** Clique em **Exportar Relatório** para salvar a visualização atual em PNG. [file:3]

---

## 👤 Autor

* **Gustavo Lopes Lameu** - GEMED
* *v2.0 - Sistema de Análise Técnica*