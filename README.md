# 📊 Medidados

O **Medidados** é uma aplicação desktop de alta performance desenvolvida para a análise técnica e visualização de dados de medidores de fluxo. O sistema automatiza o processo de ETL (Extração, Transformação e Carga), transformando arquivos brutos de telemetria em dashboards interativos e relatórios visuais profissionais.


## 🚀 Estrutura do Projeto

O projeto é dividido em módulos para garantir que a lógica de dados, a interface e as configurações permaneçam organizadas e seguras:

* **`main.py`**: O "acendedor de luzes". Este arquivo é o porteiro do sistema; ele não faz o café, mas liga a máquina.
* **`gui.py`**: O coração visual. Gerencia janelas, eventos de drag-and-drop e a interatividade dos gráficos via Matplotlib.
* **`processador.py`**: O cérebro matemático. Responsável por limpar os dados e calcular as métricas de vazão e velocidade.
* **`config.py`**: (Arquivo Privado) Contém o mapeamento sensível de colunas e os modelos de medidores suportados.

---

## 🛠️ Detalhes dos Módulos

### 1. `main.py`
É o ponto de entrada da aplicação. Sua única missão na vida é instanciar a interface e garantir que o loop principal não pare.

> **Nota do Desenvolvedor:** Se o `main.py` fosse um estagiário, ele seria aquele que só tem a chave da sala: chega primeiro, abre a porta e chama quem realmente trabalha (`AppAnalise`).

```python
from gui import AppAnalise

if __name__ == "__main__":
    app = AppAnalise()
    app.mainloop()
```

### 2. `processador.py`
Responsável por toda a inteligência de dados:
* **Saneamento:** Converte vírgulas em pontos e trata strings para evitar erros de cálculo.
* **Séries Temporais:** Correção inteligente de datas (`dayfirst=True`) para garantir a ordem cronológica correta em arquivos brasileiros.
* **Métricas:** Cálculo dinâmico de limites de vazão e estatísticas de qualidade para o Dashboard.

### 3. `gui.py`
Interface moderna baseada em `CustomTkinter`:
* **Interatividade:** Gráficos com eixos duplos, tooltips (balões de informação) e cursor vertical de acompanhamento.
* **Drag & Drop:** Suporte para arrastar arquivos CSV ou Excel diretamente para a janela principal.
* **Exportação:** Salva o dashboard em PNG de alta resolução (300 DPI) para relatórios técnicos.

---

## 📦 Instalação e Dependências

Para rodar o Medidados, você precisará das bibliotecas listadas abaixo.

### Passo a Passo:

1. **Crie um arquivo chamado `requirements.txt`** na raiz do projeto:
   ```text
   pandas
   numpy
   openpyxl
   customtkinter
   matplotlib
   tkinterdnd2
   ```

2. **Instale tudo via terminal**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Inicie a aplicação**:
   ```bash
   python main.py
   ```

---

## 💡 Como Usar

1.  **Configuração:** Selecione o **Tipo** e o **Modelo** do medidor nos menus iniciais.
2.  **Importação:** Arraste o arquivo de dados para a "Drop Zone" azul ou busque manualmente pelo botão.
3.  **Exploração:** O dashboard abrirá em tela cheia. Passe o mouse sobre as linhas para ver valores exatos de Vazão e Velocidade.
4.  **Relatório:** Clique em **Exportar Relatório** para salvar a análise atual como imagem.

---

## 👤 Autor
* **Gustavo Lopes Lameu** - GEMED
* *v1.0 - Sistema de Análise Técnica*
